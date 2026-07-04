"""Audio utilities + Silero voice-activity detection.

Normalizes incoming clips to 16 kHz mono and caps them at 30 s (Gemma 4's audio
limit) before STT. Silero VAD is optional and used to reject empty/silent clips.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from .. import config


def read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    audio, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if audio.ndim > 1:  # stereo -> mono
        audio = audio.mean(axis=1)
    return audio.astype(np.float32), int(sr)


def resample_to_16k_mono(audio: np.ndarray, sr: int) -> tuple[np.ndarray, int]:
    target = config.AUDIO_SAMPLE_RATE
    if sr == target:
        return audio, sr
    # Lightweight linear resample (no scipy/librosa dependency).
    duration = audio.shape[0] / float(sr)
    new_len = int(round(duration * target))
    if new_len <= 0:
        return audio, sr
    old_idx = np.linspace(0.0, 1.0, num=audio.shape[0], endpoint=False)
    new_idx = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
    resampled = np.interp(new_idx, old_idx, audio).astype(np.float32)
    return resampled, target


def cap_duration(audio: np.ndarray, sr: int, max_seconds: int | None = None) -> np.ndarray:
    max_s = max_seconds or config.AUDIO_MAX_SECONDS
    max_samples = int(max_s * sr)
    return audio[:max_samples] if audio.shape[0] > max_samples else audio


def write_wav(path: str | Path, audio: np.ndarray, sr: int) -> Path:
    path = Path(path)
    sf.write(str(path), audio, sr, subtype="PCM_16")
    return path


def prepare_audio(input_path: str | Path, out_path: str | Path | None = None) -> Path:
    """Normalize any input clip to a 16 kHz mono, <=30s wav; return the new path."""
    config.ensure_dirs()
    audio, sr = read_wav(input_path)
    if audio.size == 0:
        raise ValueError("Audio clip is empty (no samples).")
    audio, sr = resample_to_16k_mono(audio, sr)
    audio = cap_duration(audio, sr)
    if out_path is None:
        out_path = config.ARTIFACTS_DIR / f"norm_{Path(input_path).stem}.wav"
    return write_wav(out_path, audio, sr)


def detect_speech(input_path: str | Path) -> bool:
    """Return True if the clip contains speech. Fails open (True) if VAD unavailable."""
    try:
        from silero_vad import get_speech_timestamps, load_silero_vad

        audio, sr = read_wav(input_path)
        audio, sr = resample_to_16k_mono(audio, sr)
        model = _load_vad()
        import torch

        timestamps = get_speech_timestamps(
            torch.from_numpy(audio), model, sampling_rate=sr
        )
        return len(timestamps) > 0
    except Exception:
        return True


_vad_model = None


def _load_vad():
    global _vad_model
    if _vad_model is None:
        from silero_vad import load_silero_vad

        _vad_model = load_silero_vad()
    return _vad_model
