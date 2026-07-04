"""Build the sqlite-vec vector index over the corpus.

Two kinds of documents are indexed so retrieval is multimodal-aware:
  * procedure documents  -> pick WHICH procedure applies
  * diagram documents    -> pick WHICH diagram/image is relevant (payload keeps the
                            PNG path so the orchestrator can feed it to Gemma vision)

Run:  python -m backend.index.build_index
"""
from __future__ import annotations

import sqlite3

import sqlite_vec
from sqlite_vec import serialize_float32

from .. import config
from ..data_loader import (
    diagram_document_text,
    load_corpus,
    procedure_document_text,
)
from ..models import embedder


def connect(db_path=None) -> sqlite3.Connection:
    """Open a sqlite connection with the sqlite-vec extension loaded."""
    path = str(db_path or config.VECTOR_DB_PATH)
    conn = sqlite3.connect(path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def _create_schema(conn: sqlite3.Connection, dim: int) -> None:
    conn.execute("DROP TABLE IF EXISTS documents;")
    conn.execute("DROP TABLE IF EXISTS vec_documents;")
    conn.execute(
        """
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            doc_type TEXT NOT NULL,     -- 'procedure' | 'diagram'
            ref_id TEXT NOT NULL,       -- procedure_id or diagram_id
            title TEXT,
            image_path TEXT,            -- PNG path for diagrams, else NULL
            text TEXT NOT NULL
        );
        """
    )
    conn.execute(
        f"CREATE VIRTUAL TABLE vec_documents USING vec0(embedding float[{dim}]);"
    )


def build(db_path=None) -> dict:
    """(Re)build the index. Returns a small summary dict."""
    config.ensure_dirs()
    corpus = load_corpus()

    rows: list[dict] = []
    for proc in corpus.procedures.values():
        rows.append(
            {
                "doc_type": "procedure",
                "ref_id": proc.procedure_id,
                "title": proc.title,
                "image_path": None,
                "text": procedure_document_text(proc),
            }
        )
    for diagram in corpus.diagrams.values():
        rows.append(
            {
                "doc_type": "diagram",
                "ref_id": diagram.diagram_id,
                "title": diagram.title,
                "image_path": str(diagram.image_path),
                "text": diagram_document_text(diagram),
            }
        )

    texts = [r["text"] for r in rows]
    vectors = embedder.embed_documents(texts)
    dim = embedder.embedding_dim()

    conn = connect(db_path)
    try:
        _create_schema(conn, dim)
        for i, row in enumerate(rows):
            cur = conn.execute(
                "INSERT INTO documents (doc_type, ref_id, title, image_path, text)"
                " VALUES (?, ?, ?, ?, ?);",
                (row["doc_type"], row["ref_id"], row["title"], row["image_path"], row["text"]),
            )
            rowid = cur.lastrowid
            conn.execute(
                "INSERT INTO vec_documents (rowid, embedding) VALUES (?, ?);",
                (rowid, serialize_float32(vectors[i].tolist())),
            )
        conn.commit()
    finally:
        conn.close()

    summary = {
        "db_path": str(db_path or config.VECTOR_DB_PATH),
        "procedures": len(corpus.procedures),
        "diagrams": len(corpus.diagrams),
        "documents": len(rows),
        "dim": dim,
    }
    return summary


if __name__ == "__main__":
    result = build()
    print("Index built:")
    for k, v in result.items():
        print(f"  {k}: {v}")
