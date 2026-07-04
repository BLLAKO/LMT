"""Compose the reasoning prompt from rules + retrieved context + tool results.

Only the selected procedure's structured steps and the relevant sensor snapshot are
injected (not the whole corpus), which keeps prompts small and fast.
"""
from __future__ import annotations

from typing import Any

import yaml

from ..data_loader import Corpus, Procedure
from ..index.retriever import RetrievalResult
from .schema import SCHEMA_HINT

RULEBOOK = """You are ZeroDelay, a hands-free offline voice copilot guiding a technician
through hazardous maintenance work (space/EVA domain). You cannot reach the cloud or
ground control in real time. Follow these rules:

1. SAFETY FIRST. Never advance past a step whose safety preconditions are not met.
2. GROUND EVERY FACT. For any sensor value, torque spec, part availability, or fault
   branch, use a tool_request to get the exact value. Do NOT guess numbers.
3. RESPECT SAFETY TIERS. routine = brief confirm; caution = state warnings then confirm;
   critical = state warnings, require explicit confirmation, and re-check preconditions.
4. CROSS-CHECK. If a live sensor contradicts what a step assumes (e.g. pressure too high
   before opening a hatch), BLOCK the step and explain why.
5. BRANCH ON SYMPTOMS. If the reported symptom changes the repair path, branch.
6. ESCALATE / EMERGENCY. If conditions are unsafe or irreversible, halt and give the
   immediate safety action; note that an alert is queued for when connectivity returns.
7. ASK, DON'T GUESS. If the request is ambiguous, ask ONE clarifying question.
8. SPEAK PLAINLY. spoken_text is read aloud by a voice engine: short, calm, no markdown.
"""


def build_prompt(
    query: str,
    retrieval: RetrievalResult,
    corpus: Corpus,
    sensor_snapshot: list[dict[str, Any]] | None = None,
    tool_results: list[dict[str, Any]] | None = None,
    has_live_image: bool = False,
) -> str:
    parts: list[str] = [RULEBOOK, ""]

    # Selected procedure (structured).
    proc = None
    if retrieval.top_procedure_id:
        proc = corpus.procedures.get(retrieval.top_procedure_id)
    if proc:
        parts.append("RETRIEVED PROCEDURE (structured, source of truth):")
        parts.append(_render_procedure(proc))
        parts.append("")

    # Other candidate procedures (titles only, for disambiguation).
    others = [p for p in retrieval.procedures[1:]]
    if others:
        parts.append("OTHER CANDIDATE PROCEDURES:")
        for p in others:
            parts.append(f"- {p.procedure_id}: {p.title} (score {p.score})")
        parts.append("")

    # Relevant diagrams (images).
    if retrieval.diagrams:
        parts.append("RELEVANT DIAGRAMS:")
        for d in retrieval.diagrams:
            status = "image attached" if d.image_exists else "image not generated yet"
            parts.append(f"- {d.diagram_id}: {d.title} ({status})")
        if has_live_image:
            parts.append(
                "A live camera image from the technician is also attached. Compare it "
                "against the reference diagram to verify the step's expected state."
            )
        parts.append("")

    # Live telemetry snapshot (relevant sensors only).
    if sensor_snapshot:
        parts.append("LIVE TELEMETRY (simulated):")
        for s in sensor_snapshot:
            if not s.get("known"):
                continue
            parts.append(
                f"- {s['sensor']} = {s.get('value')} {s.get('unit') or ''}"
                f" [{s.get('status')}]"
            )
        parts.append("")

    # Tool results gathered so far in this turn.
    if tool_results:
        parts.append("TOOL RESULTS THIS TURN:")
        for tr in tool_results:
            parts.append(f"- {tr}")
        parts.append("")

    parts.append(f'TECHNICIAN SAID: "{query}"')
    parts.append("")
    parts.append(SCHEMA_HINT)
    return "\n".join(parts)


def relevant_sensor_names(corpus: Corpus, retrieval: RetrievalResult) -> list[str]:
    if not retrieval.top_procedure_id:
        return []
    proc = corpus.procedures.get(retrieval.top_procedure_id)
    return proc.sensors_watched if proc else []


def _render_procedure(proc: Procedure) -> str:
    """Render a trimmed, token-efficient view of the procedure's typed steps."""
    header = {
        "procedure_id": proc.procedure_id,
        "title": proc.title,
        "system": proc.system,
        "summary": proc.summary,
        "sensors_watched": proc.sensors_watched,
        "related_diagrams": proc.related_diagrams,
    }
    trimmed_steps = []
    for step in proc.steps:
        trimmed_steps.append(
            {
                k: step.get(k)
                for k in (
                    "id",
                    "title",
                    "safety_tier",
                    "instruction",
                    "preconditions",
                    "specs",
                    "required_parts",
                    "verify",
                    "on_failure",
                    "warnings",
                    "branches",
                )
                if step.get(k) is not None
            }
        )
    doc = {"procedure": header, "steps": trimmed_steps}
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).strip()
