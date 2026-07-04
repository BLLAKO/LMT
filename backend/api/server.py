"""FastAPI service exposing the ZeroDelay pipeline to the (JS) front-end.

Run:  uvicorn backend.api.server:app --port 8000
The heavy models load lazily on first use (or eagerly if ZD_WARMUP=1).
"""
from __future__ import annotations

import base64
import binascii
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Guardrail so a huge upload / base64 blob can't exhaust memory or disk.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB

from .. import config
from ..data_loader import load_corpus
from ..models import vad
from ..tools.sensor_sim import get_simulator

app = FastAPI(title="ZeroDelay Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_orchestrator = None


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from ..agent.orchestrator import Orchestrator

        _orchestrator = Orchestrator()
    return _orchestrator


@app.on_event("startup")
def _startup() -> None:
    config.ensure_dirs()
    if os.environ.get("ZD_WARMUP") == "1":
        get_orchestrator().gemma.warmup()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class AskRequest(BaseModel):
    query: str
    image_base64: str | None = None
    speak: bool = True


class TTSRequest(BaseModel):
    text: str


class InjectRequest(BaseModel):
    name: str
    value: float | str


# ---------------------------------------------------------------------------
# Info endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "gemma_model": config.GEMMA_MODEL_ID}


@app.get("/ready")
def ready() -> dict:
    """Deep readiness: is the vector index built and the TTS voice present?
    The frontend can poll this before enabling voice features."""
    from ..index.retriever import index_is_ready

    checks = {
        "vector_index": index_is_ready(),
        "piper_voice": config.PIPER_VOICE_PATH.exists(),
        "offline_mode": config.OFFLINE,
    }
    checks["ready"] = bool(checks["vector_index"] and checks["piper_voice"])
    return checks


@app.get("/procedures")
def procedures() -> dict:
    corpus = load_corpus()
    return {
        "procedures": [
            {
                "id": p.procedure_id,
                "title": p.title,
                "system": p.system,
                "summary": p.summary,
                "steps": len(p.steps),
            }
            for p in corpus.procedures.values()
        ]
    }


@app.get("/sensors")
def sensors() -> dict:
    return {"sensors": get_simulator().snapshot()}


@app.post("/sensors/inject")
def inject(req: InjectRequest) -> dict:
    try:
        return {"reading": get_simulator().inject(req.name, req.value)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/sensors/reset")
def reset_sensors() -> dict:
    get_simulator().reset()
    return {"status": "reset"}


# ---------------------------------------------------------------------------
# Pipeline endpoints
# ---------------------------------------------------------------------------
@app.post("/transcribe")
def transcribe(audio: UploadFile = File(...)) -> dict:
    tmp = _save_upload(audio, suffix=".wav")
    try:
        norm = vad.prepare_audio(tmp)
        text = get_orchestrator().gemma.transcribe(norm)
    finally:
        _cleanup(tmp)
    return {"text": text}


@app.post("/ask")
def ask(req: AskRequest) -> dict:
    image_path = _decode_image(req.image_base64) if req.image_base64 else None
    try:
        result = get_orchestrator().process_text(
            req.query, live_image_path=image_path, speak=req.speak
        )
    finally:
        _cleanup(image_path)
    return _with_audio(result)


@app.post("/converse")
def converse(
    audio: UploadFile = File(...),
    image: UploadFile | None = File(None),
    speak: bool = Form(True),
) -> dict:
    tmp = _save_upload(audio, suffix=".wav")
    image_path = None
    try:
        norm = vad.prepare_audio(tmp)
        if not vad.detect_speech(norm):
            raise HTTPException(status_code=422, detail="No speech detected in audio.")
        if image is not None:
            image_path = _save_upload(
                image, suffix=Path(image.filename or "img.png").suffix
            )
        result = get_orchestrator().process_audio(
            norm, live_image_path=image_path, speak=speak
        )
    finally:
        _cleanup(tmp)
        _cleanup(image_path)
    return _with_audio(result)


@app.post("/tts")
def tts(req: TTSRequest):
    from fastapi.responses import Response

    from ..models import tts as tts_engine

    data = tts_engine.synthesize_to_bytes(req.text)
    return Response(content=data, media_type="audio/wav")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _save_upload(upload: UploadFile, suffix: str) -> Path:
    data = upload.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload too large.")
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return Path(path)


def _decode_image(b64: str) -> Path:
    if "," in b64:  # strip data URL prefix
        b64 = b64.split(",", 1)[1]
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Invalid base64 image.")
    if not raw:
        raise HTTPException(status_code=400, detail="Empty image.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large.")
    fd, path = tempfile.mkstemp(suffix=".png")
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
    return Path(path)


def _cleanup(path) -> None:
    """Best-effort delete of a temp file."""
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


def _with_audio(result: dict) -> dict:
    """Inline the TTS wav as base64 so the front-end can play it directly."""
    tts_path = result.get("tts_path")
    if tts_path and Path(tts_path).exists():
        result["tts_wav_base64"] = base64.b64encode(Path(tts_path).read_bytes()).decode()
    else:
        result["tts_wav_base64"] = None
    return result
