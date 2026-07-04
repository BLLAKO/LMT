"""EmbeddingGemma text embeddings via sentence-transformers.

Runs on CPU by default so the GPU stays dedicated to Gemma 4. Uses Matryoshka
truncation (default 256 dims) for fast, compact vectors. Loaded lazily and cached
so importing this module never triggers a model download.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .. import config


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so the dependency is only needed when embeddings are used.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        config.EMBED_MODEL_ID,
        device=config.EMBED_DEVICE,
        truncate_dim=config.EMBED_DIM,
    )
    return model


def _encode(texts: list[str], prompt_name: str) -> np.ndarray:
    model = _get_model()
    vectors = model.encode(
        texts,
        prompt_name=prompt_name,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return np.asarray(vectors, dtype=np.float32)


def embed_documents(texts: list[str]) -> np.ndarray:
    """Embed corpus documents for storage in the vector index."""
    if not texts:
        return np.zeros((0, config.EMBED_DIM), dtype=np.float32)
    return _encode(texts, config.EMBED_DOCUMENT_PROMPT)


def embed_query(text: str) -> np.ndarray:
    """Embed a single search query (returns a 1D vector)."""
    return _encode([text], config.EMBED_QUERY_PROMPT)[0]


def embedding_dim() -> int:
    return config.EMBED_DIM
