"""Load and parse the data/ corpus into typed Python objects.

The corpus is authored as hybrid Markdown (YAML front-matter + prose) plus
machine-readable YAML reference files. This module is the single place that knows
how to read all of it, so the rest of the backend works with clean objects.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from . import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Procedure:
    procedure_id: str
    title: str
    summary: str
    system: str
    file: Path
    front_matter: dict[str, Any]
    prose: str

    @property
    def steps(self) -> list[dict[str, Any]]:
        return self.front_matter.get("steps", []) or []

    @property
    def related_diagrams(self) -> list[str]:
        return self.front_matter.get("related_diagrams", []) or []

    @property
    def sensors_watched(self) -> list[str]:
        return self.front_matter.get("sensors_watched", []) or []


@dataclass
class DiagramAnnotation:
    diagram_id: str
    title: str
    file: Path            # the annotation YAML file (may not exist)
    image_path: Path      # the PNG the agent feeds to the vision model
    data: dict[str, Any]
    used_by: list[str] = field(default_factory=list)

    @property
    def image_exists(self) -> bool:
        return self.image_path.exists()


@dataclass
class Corpus:
    manifest: dict[str, Any]
    procedures: dict[str, Procedure] = field(default_factory=dict)
    diagrams: dict[str, DiagramAnnotation] = field(default_factory=dict)
    reference: dict[str, dict[str, Any]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Front-matter parsing
# ---------------------------------------------------------------------------
def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a Markdown doc into (yaml_front_matter, prose).

    Front matter is the block between the first two `---` fences.
    """
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}, text
    # Find the closing fence after the opening one.
    lines = stripped.splitlines()
    # lines[0] == '---'
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return {}, text
    fm_block = "\n".join(lines[1:end_idx])
    prose = "\n".join(lines[end_idx + 1 :]).strip()
    front_matter = yaml.safe_load(fm_block) or {}
    return front_matter, prose


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_manifest() -> dict[str, Any]:
    with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_procedures(manifest: dict[str, Any]) -> dict[str, Procedure]:
    procedures: dict[str, Procedure] = {}
    for entry in manifest.get("procedures", []) or []:
        rel = entry.get("file")
        if not rel:
            continue
        path = config.DATA_DIR / rel
        if not path.exists():
            logger.warning("Procedure file listed in manifest is missing: %s", path)
            continue
        text = path.read_text(encoding="utf-8")
        fm, prose = split_front_matter(text)
        proc = Procedure(
            procedure_id=fm.get("procedure_id", entry.get("id", path.stem)),
            title=fm.get("title", entry.get("title", "")),
            summary=fm.get("summary", entry.get("summary", "")),
            system=fm.get("system", entry.get("system", "")),
            file=path,
            front_matter=fm,
            prose=prose,
        )
        procedures[proc.procedure_id] = proc
    return procedures


def load_diagrams(
    manifest: dict[str, Any], procedures: dict[str, Procedure]
) -> dict[str, DiagramAnnotation]:
    """Discover diagrams from the manifest ids, the generated PNGs, and any annotation
    YAML files. Annotations are optional (the vision model reads the PNG directly)."""
    ids: set[str] = set()
    ids.update((manifest.get("diagrams") or {}).get("ids", []) or [])
    if config.DIAGRAMS_DIR.exists():
        ids.update(p.stem for p in config.DIAGRAMS_DIR.glob("*.png"))
    if config.ANNOTATIONS_DIR.exists():
        ids.update(p.stem for p in config.ANNOTATIONS_DIR.glob("*.yaml"))

    diagrams: dict[str, DiagramAnnotation] = {}
    for diagram_id in sorted(ids):
        ann_path = config.ANNOTATIONS_DIR / f"{diagram_id}.yaml"
        data: dict[str, Any] = {}
        if ann_path.exists():
            data = yaml.safe_load(ann_path.read_text(encoding="utf-8")) or {}
        used_by = [
            pid for pid, proc in procedures.items() if diagram_id in proc.related_diagrams
        ]
        diagrams[diagram_id] = DiagramAnnotation(
            diagram_id=diagram_id,
            title=data.get("title") or _prettify(diagram_id),
            file=ann_path,
            image_path=config.DIAGRAMS_DIR / f"{diagram_id}.png",
            data=data,
            used_by=used_by,
        )
    return diagrams


def load_reference() -> dict[str, dict[str, Any]]:
    """Load every reference YAML keyed by filename stem (e.g. 'inventory')."""
    reference: dict[str, dict[str, Any]] = {}
    if not config.REFERENCE_DIR.exists():
        return reference
    for path in sorted(config.REFERENCE_DIR.glob("*.yaml")):
        reference[path.stem] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return reference


@lru_cache(maxsize=1)
def load_corpus() -> Corpus:
    """Load the full corpus once and cache it."""
    manifest = load_manifest()
    procedures = load_procedures(manifest)
    return Corpus(
        manifest=manifest,
        procedures=procedures,
        diagrams=load_diagrams(manifest, procedures),
        reference=load_reference(),
    )


# ---------------------------------------------------------------------------
# Text rendering helpers (used for embedding documents)
# ---------------------------------------------------------------------------
def procedure_document_text(proc: Procedure) -> str:
    """Compact retrieval document for a procedure: what it is + when it applies."""
    step_titles = [f"- {s.get('id')}: {s.get('title')}" for s in proc.steps]
    tags = ", ".join(_manifest_tags_for(proc.procedure_id))
    return (
        f"Procedure {proc.procedure_id}: {proc.title}\n"
        f"System: {proc.system}\n"
        f"Summary: {proc.summary}\n"
        f"Tags: {tags}\n"
        f"Steps:\n" + "\n".join(step_titles)
    )


def diagram_document_text(diagram: DiagramAnnotation) -> str:
    """Retrieval document for a diagram. Uses annotation labels when available, else
    falls back to the (prettified) id and the procedures that reference it."""
    data = diagram.data
    labels: list[str] = []
    for item in data.get("must_render", []) or []:
        if isinstance(item, dict):
            txt = item.get("exact_text") or item.get("title_text") or item.get("panel")
            if txt:
                labels.append(str(txt))
    key_state = data.get("key_state_for_demo", "")
    used_by = ", ".join(diagram.used_by)
    keywords = _prettify(diagram.diagram_id)
    return (
        f"Diagram {diagram.diagram_id}: {diagram.title}\n"
        f"Keywords: {keywords}\n"
        f"Used by: {used_by}\n"
        f"Labels: {', '.join(labels)}\n"
        f"Key state: {key_state}"
    )


def _prettify(diagram_id: str) -> str:
    return diagram_id.replace("-", " ").replace("_", " ")


def _manifest_tags_for(procedure_id: str) -> list[str]:
    corpus_manifest = load_manifest()
    for entry in corpus_manifest.get("procedures", []) or []:
        if entry.get("id") == procedure_id:
            return entry.get("tags", []) or []
    return []
