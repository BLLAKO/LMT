"""Piper offline text-to-speech.

Gemma cannot synthesize audio, so Piper handles the "mouth". Fully offline once the
voice model (.onnx + .onnx.json) is downloaded into models/piper/. Loaded lazily.
"""
from __future__ import annotations

import uuid
import wave
from functools import lru_cache
from pathlib import Path

from .. import config


@lru_cache(maxsize=1)
def _get_voice():
    from piper import PiperVoice

    if not config.PIPER_VOICE_PATH.exists():
        raise FileNotFoundError(
            f"Piper voice not found at {config.PIPER_VOICE_PATH}. Download the "
            f"'{config.PIPER_VOICE_NAME}' .onnx and .onnx.json into "
            f"{config.PIPER_VOICE_DIR}."
        )
    return PiperVoice.load(str(config.PIPER_VOICE_PATH))


def synthesize_to_file(text: str, out_path: str | Path | None = None) -> Path:
    """Synthesize `text` to a wav file and return its path."""
    config.ensure_dirs()
    voice = _get_voice()
    if out_path is None:
        out_path = config.TTS_OUTPUT_DIR / f"speech_{uuid.uuid4().hex[:8]}.wav"
    out_path = Path(out_path)
    with wave.open(str(out_path), "wb") as wav_file:
        # synthesize_wav writes the WAV header (channels/sample width/rate) itself.
        voice.synthesize_wav(text, wav_file)
    return out_path


def synthesize_to_bytes(text: str) -> bytes:
    """Synthesize `text` and return raw wav bytes."""
    path = synthesize_to_file(text)
    data = path.read_bytes()
    return data
