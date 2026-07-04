"""Gemma 4 runtime: one model instance for audio STT + text reasoning + vision.

Loaded once via transformers `AutoModelForMultimodalLM` in 4-bit (bitsandbytes),
keeping the audio modules in bf16 (a known Gemma 4 quantization pitfall). Designed
to fit an 8GB GPU. Fully offline after the weights are downloaded once.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from .. import config

# The exact ASR instruction recommended in the Gemma 4 model card.
_ASR_PROMPT = (
    "Transcribe the following speech segment in its original language. "
    "Follow these specific instructions for formatting the answer:\n"
    "* Only output the transcription, with no newlines.\n"
    "* When transcribing numbers, write the digits, i.e. write 1.7 and not "
    "one point seven, and write 3 instead of three."
)


class GemmaRuntime:
    """Thin wrapper around a single Gemma 4 multimodal model."""

    def __init__(self, model_id: str | None = None, load_in_4bit: bool | None = None):
        self.model_id = model_id or config.GEMMA_MODEL_ID
        self.load_in_4bit = (
            config.GEMMA_LOAD_IN_4BIT if load_in_4bit is None else load_in_4bit
        )
        self._model = None
        self._processor = None
        self._lock = threading.Lock()
        # Serializes generation so concurrent API requests don't interleave on one GPU.
        self._gen_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            import torch
            from transformers import AutoProcessor

            model_cls = _resolve_model_class()

            quant_config = None
            if self.load_in_4bit:
                from transformers import BitsAndBytesConfig

                quant_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                    llm_int8_skip_modules=config.GEMMA_QUANT_SKIP_MODULES,
                )

            # Pick device placement. bitsandbytes 4-bit cannot keep layers on CPU,
            # so when a GPU is present we pin the whole model to it (device_map={"":0})
            # instead of "auto", which would offload to CPU on tight (8GB) VRAM.
            device_map = _resolve_device_map(torch)

            # Offline mode forbids any Hugging Face network call (privacy demo).
            offline = config.OFFLINE
            self._processor = AutoProcessor.from_pretrained(
                self.model_id, padding_side="left", local_files_only=offline
            )
            self._model = model_cls.from_pretrained(
                self.model_id,
                device_map=device_map,
                dtype=torch.bfloat16,
                quantization_config=quant_config,
                local_files_only=offline,
            ).eval()

    def warmup(self) -> None:
        """Load the model and run a tiny generation so the first real call is fast."""
        self.load()
        try:
            self.reason("Reply with the single word: ready.", max_new_tokens=8)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Generation helpers
    # ------------------------------------------------------------------
    def _generate(self, messages: list[dict[str, Any]], max_new_tokens: int) -> str:
        self.load()
        import torch

        inputs = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._model.device)

        input_len = inputs["input_ids"].shape[-1]
        with self._gen_lock, torch.inference_mode():
            generated = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
            )
        new_tokens = generated[0][input_len:]
        return self._processor.decode(new_tokens, skip_special_tokens=True).strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def transcribe(self, audio_path: str | Path, max_new_tokens: int | None = None) -> str:
        """Speech-to-text via Gemma 4's native audio understanding."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _ASR_PROMPT},
                    {"type": "audio", "audio": str(audio_path)},
                ],
            }
        ]
        return self._generate(
            messages, max_new_tokens or config.ASR_MAX_NEW_TOKENS
        )

    def reason(
        self,
        prompt: str,
        images: list[str | Path] | None = None,
        max_new_tokens: int | None = None,
    ) -> str:
        """Text (optionally + images) -> text. Used for the structured decision."""
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for img in images or []:
            content.append({"type": "image", "image": str(img)})
        messages = [{"role": "user", "content": content}]
        return self._generate(
            messages, max_new_tokens or config.GEMMA_MAX_NEW_TOKENS
        )


def _resolve_model_class():
    """Return the transformers auto-class for Gemma 4 that exists in this install.

    Newer transformers expose `AutoModelForMultimodalLM`; some versions only have
    `AutoModelForImageTextToText`. Trying both keeps the code portable across the
    versions teammates may have installed.
    """
    import transformers

    for name in ("AutoModelForMultimodalLM", "AutoModelForImageTextToText"):
        cls = getattr(transformers, name, None)
        if cls is not None:
            return cls
    raise ImportError(
        "No supported Gemma 4 auto-class found in transformers "
        f"{getattr(transformers, '__version__', '?')}. Upgrade with: "
        "pip install -U transformers"
    )


def _resolve_device_map(torch):
    """Resolve the device_map, parsing 'cuda:0'-style overrides into the dict form
    that from_pretrained expects (a bare 'cuda:0' string is not a valid device_map)."""
    override = config.GEMMA_DEVICE_MAP
    if override:
        # Keyword strategies stay as strings; explicit devices become {"": device}.
        if override in {"auto", "balanced", "balanced_low_0", "sequential"}:
            return override
        if override.isdigit():
            return {"": int(override)}
        return {"": override}
    if torch.cuda.is_available():
        return {"": 0}
    return "auto"


# Process-wide singleton so the model is loaded at most once.
_runtime: GemmaRuntime | None = None
_runtime_lock = threading.Lock()


def get_runtime() -> GemmaRuntime:
    global _runtime
    if _runtime is None:
        with _runtime_lock:
            if _runtime is None:
                _runtime = GemmaRuntime()
    return _runtime
