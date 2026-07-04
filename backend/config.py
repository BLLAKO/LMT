"""Central configuration for the ZeroDelay backend.

All paths, model ids, and tunables live here so the rest of the code stays clean.
Everything is designed to run fully offline once the models are downloaded.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"

PROCEDURES_DIR = DATA_DIR / "procedures"
REFERENCE_DIR = DATA_DIR / "reference"
DIAGRAMS_DIR = DATA_DIR / "diagrams"
ANNOTATIONS_DIR = DIAGRAMS_DIR / "annotations"
MANIFEST_PATH = DATA_DIR / "manifest.yaml"

# Generated artifacts (gitignored).
ARTIFACTS_DIR = BACKEND_DIR / "artifacts"
VECTOR_DB_PATH = ARTIFACTS_DIR / "vectorstore.sqlite"
TTS_OUTPUT_DIR = ARTIFACTS_DIR / "tts"

# ---------------------------------------------------------------------------
# Models (Hugging Face ids; downloaded once, then run offline)
# ---------------------------------------------------------------------------
# Main brain: audio STT + text reasoning + image vision. Switch to E2B on tight VRAM.
GEMMA_MODEL_ID = os.environ.get("ZD_GEMMA_MODEL", "google/gemma-4-E4B-it")
GEMMA_FALLBACK_MODEL_ID = "google/gemma-4-E2B-it"

# Load Gemma in 4-bit (bitsandbytes) to fit 8GB GPUs. Audio modules stay bf16.
GEMMA_LOAD_IN_4BIT = os.environ.get("ZD_GEMMA_4BIT", "1") == "1"
# Device placement. On an 8GB GPU, bitsandbytes 4-bit forbids CPU-offloaded layers,
# so we pin the whole model to one GPU rather than letting "auto" spill to CPU.
# Override with ZD_GEMMA_DEVICE_MAP (e.g. "auto", "cpu", "cuda:0").
GEMMA_DEVICE_MAP = os.environ.get("ZD_GEMMA_DEVICE_MAP", "").strip()
# Modules that must NOT be quantized (Gemma 4 audio pitfall) + the lm_head.
GEMMA_QUANT_SKIP_MODULES = [
    "lm_head",
    "audio_tower",
    "embed_audio",
    "model.audio_tower",
    "model.embed_audio",
]

# Embeddings: EmbeddingGemma via sentence-transformers, on CPU to keep GPU for Gemma.
EMBED_MODEL_ID = os.environ.get("ZD_EMBED_MODEL", "google/embeddinggemma-300M")
EMBED_DEVICE = os.environ.get("ZD_EMBED_DEVICE", "cpu")
# Matryoshka truncation: 256 dims is ~3x faster with minimal quality loss.
EMBED_DIM = int(os.environ.get("ZD_EMBED_DIM", "256"))
EMBED_QUERY_PROMPT = "Retrieval-query"
EMBED_DOCUMENT_PROMPT = "Retrieval-document"

# TTS: Piper voice (download the .onnx + .onnx.json pair into models/piper/).
PIPER_VOICE_DIR = BACKEND_DIR / "models" / "piper"
PIPER_VOICE_NAME = os.environ.get("ZD_PIPER_VOICE", "en_US-lessac-medium")
PIPER_VOICE_PATH = PIPER_VOICE_DIR / f"{PIPER_VOICE_NAME}.onnx"

# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
AUDIO_SAMPLE_RATE = 16000  # Gemma expects 16kHz mono
AUDIO_MAX_SECONDS = 30     # Gemma 4 audio clips are capped at 30s

# ---------------------------------------------------------------------------
# Retrieval / agent tunables
# ---------------------------------------------------------------------------
RETRIEVAL_TOP_K = int(os.environ.get("ZD_TOP_K", "3"))
TOOL_LOOP_MAX_ITERS = int(os.environ.get("ZD_TOOL_LOOP", "2"))
GEMMA_MAX_NEW_TOKENS = int(os.environ.get("ZD_MAX_NEW_TOKENS", "512"))
ASR_MAX_NEW_TOKENS = int(os.environ.get("ZD_ASR_MAX_NEW_TOKENS", "128"))


def ensure_dirs() -> None:
    """Create generated-artifact directories if missing."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PIPER_VOICE_DIR.mkdir(parents=True, exist_ok=True)
