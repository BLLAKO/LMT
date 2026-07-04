# ZeroDelay Backend

Offline voice-copilot backend: **Gemma 4** (audio STT + text reasoning + vision) +
multimodal RAG over [`data/`](../data) + **Piper** TTS, served over FastAPI. Runs 100%
locally after a one-time model download. Built for 8GB GPUs (RTX 5060 / 3070).

## Pipeline

```
audio -> Gemma STT -> EmbeddingGemma + sqlite-vec retrieval (procedures + diagrams)
      -> prompt (rules + typed steps + live telemetry + tool results)
      -> Gemma reasoning -> structured JSON decision (+ tool-call loop, +vision)
      -> Piper TTS -> audio
```

Retrieval only chooses *which* procedure/diagram applies; exact facts (torque, sensor
ranges, inventory, fault branches) come from deterministic tool calls, not vector search.

## Setup and downloads (one time, then fully offline)

Windows / PowerShell steps. Total download is ~16-17 GB; everything runs offline after.

### 1. Virtual environment

```powershell
cd "c:\Users\abhij\OneDrive\Desktop\Brain Labs\Coding\LMT"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2. Install PyTorch FIRST (GPU-specific)

```powershell
# RTX 3070 (Ampere):
pip install torch --index-url https://download.pytorch.org/whl/cu124

# RTX 5060 (Blackwell - needs newer CUDA):
pip install --pre torch --index-url https://download.pytorch.org/whl/cu128
```

Verify the GPU is visible:

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

### 3. Install the rest

```powershell
pip install -r backend\requirements.txt
```

### 4. Hugging Face login + accept Gemma licenses

Gemma weights are gated. Click "agree" once (while logged in) on each model page:
`google/gemma-4-E4B-it`, `google/gemma-4-E2B-it`, `google/embeddinggemma-300M`. Then:

```powershell
huggingface-cli login    # paste a token from https://huggingface.co/settings/tokens
```

Tip: to keep the large cache off C:, set `$env:HF_HOME="D:\hf-cache"` before downloading.

### 5. Download the models

```powershell
huggingface-cli download google/gemma-4-E4B-it        # brain: STT + text + vision (~10 GB)
huggingface-cli download google/gemma-4-E2B-it        # smaller fallback (~5-6 GB)
huggingface-cli download google/embeddinggemma-300M   # retrieval embeddings (~1.2 GB)
```

These live in the HF cache and are found automatically (no path config needed).

### 6. Download a Piper voice (TTS)

The code expects the voice pair in `backend\models\piper\`:

```powershell
huggingface-cli download rhasspy/piper-voices `
  en/en_US/lessac/medium/en_US-lessac-medium.onnx `
  en/en_US/lessac/medium/en_US-lessac-medium.onnx.json `
  --local-dir backend\models\piper --local-dir-use-symlinks False
```

If the files land in nested subfolders, move the `.onnx` and `.onnx.json` directly into
`backend\models\piper\`. (Alternative: `python -m piper.download_voices en_US-lessac-medium`,
then move the files there.)

### 7. Diagram images (vision path)

The 8 diagram PNGs live in [`data/diagrams/`](../data/diagrams) using the filenames from
[`data/diagrams/prompts.md`](../data/diagrams/prompts.md). The vision model reads these
PNGs directly (annotation YAMLs are not required).

### Download / runtime footprint

| Item | Download | Runtime cost |
| --- | --- | --- |
| Gemma 4 E4B | ~10 GB | ~4-5 GB VRAM (4-bit) |
| Gemma 4 E2B (fallback) | ~5-6 GB | ~2-3 GB VRAM |
| EmbeddingGemma | ~1.2 GB | CPU |
| Piper voice | ~60 MB | CPU |

If E4B ever OOMs on an 8 GB card, switch with `$env:ZD_GEMMA_MODEL="google/gemma-4-E2B-it"`
(no code change). On Blackwell (5060), a `bitsandbytes` error usually means it needs the
newest `bitsandbytes`; as a last resort run on a machine with headroom or set
`$env:ZD_GEMMA_4BIT="0"`.

## Build the index

```
python -m backend.index.build_index
# or: python -m backend.cli build-index
```

## Test without the front-end

```
python -m backend.smoke_test                       # no ML deps needed
python -m backend.cli info                          # corpus stats
python -m backend.cli retrieve "airlock won't depressurize"
python -m backend.cli ask "coolant loop pressure is dropping"
python -m backend.cli converse MarsMind/astronaut_query.wav
```

## Run the API

```
uvicorn backend.api.server:app --port 8000
# set ZD_WARMUP=1 to load Gemma at startup instead of first request
```

### Endpoints (for the JS front-end)

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| GET | `/health` | - | status + model id |
| GET | `/procedures` | - | procedure list |
| GET | `/sensors` | - | live telemetry snapshot |
| POST | `/sensors/inject` | `{name, value}` | new reading (demo anomalies) |
| POST | `/sensors/reset` | - | reset to nominal |
| POST | `/transcribe` | multipart `audio` | `{text}` |
| POST | `/ask` | `{query, image_base64?, speak?}` | decision + `tts_wav_base64` |
| POST | `/converse` | multipart `audio` (+ `image?`) | `{query, decision, tts_wav_base64}` |
| POST | `/tts` | `{text}` | `audio/wav` |

The decision JSON shape is documented in [`agent/schema.py`](agent/schema.py).

## Configuration

Override via environment variables (see [`config.py`](config.py)): `ZD_GEMMA_MODEL`,
`ZD_GEMMA_4BIT`, `ZD_EMBED_MODEL`, `ZD_EMBED_DIM`, `ZD_PIPER_VOICE`, `ZD_TOP_K`,
`ZD_TOOL_LOOP`, `ZD_MAX_NEW_TOKENS`, `ZD_WARMUP`.

## Scope

This backend implements the RAG + models + TTS + tools + a single-turn orchestrator.
The multi-turn procedure state machine (step pointer, skipped-step detection, escalation
queue, session report) is the next build.
