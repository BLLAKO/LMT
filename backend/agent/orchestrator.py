"""Single-turn orchestration: audio -> STT -> RAG -> reason (+tool loop) -> TTS.

State is intentionally NOT held here (the multi-turn procedure state machine is a
later build). This class wires the pieces into one testable turn.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import config
from ..data_loader import load_corpus
from ..index.retriever import Retriever
from ..tools import reference_tools
from ..tools.sensor_sim import get_simulator
from . import prompt_builder
from .schema import Decision, fallback_decision, parse_decision

# Cap images passed to the vision model to protect VRAM/latency.
_MAX_DIAGRAM_IMAGES = 1


class Orchestrator:
    def __init__(self, retriever: Retriever | None = None, gemma=None):
        self.corpus = load_corpus()
        self.retriever = retriever or Retriever()
        self._gemma = gemma  # injected lazily to keep imports light for tests
        self.simulator = get_simulator()

    # ------------------------------------------------------------------
    @property
    def gemma(self):
        if self._gemma is None:
            from ..models.gemma import get_runtime

            self._gemma = get_runtime()
        return self._gemma

    # ------------------------------------------------------------------
    def process_audio(
        self,
        audio_path: str | Path,
        live_image_path: str | Path | None = None,
        speak: bool = True,
    ) -> dict[str, Any]:
        query = self.gemma.transcribe(audio_path)
        result = self.process_text(query, live_image_path=live_image_path, speak=speak)
        result["transcribed"] = True
        return result

    def process_text(
        self,
        query: str,
        live_image_path: str | Path | None = None,
        speak: bool = True,
    ) -> dict[str, Any]:
        retrieval = self.retriever.retrieve(query)

        # Relevant live telemetry for the selected procedure.
        sensor_names = prompt_builder.relevant_sensor_names(self.corpus, retrieval)
        snapshot = [self.simulator.read(n) for n in sensor_names]

        # Assemble image inputs: top reference diagram(s) + optional live camera image.
        images = self._collect_images(retrieval, live_image_path)
        attached_diagram_ids = self._attached_diagram_ids(retrieval)
        has_live_image = live_image_path is not None

        tool_results: list[dict[str, Any]] = []
        decision: Decision | None = None
        max_iters = config.TOOL_LOOP_MAX_ITERS

        for i in range(max_iters + 1):
            # The final pass forbids more tool calls so the loop always ends with a
            # real, executable decision (never a dangling tool_request).
            force_final = i == max_iters
            prompt = prompt_builder.build_prompt(
                query=query,
                retrieval=retrieval,
                corpus=self.corpus,
                sensor_snapshot=snapshot,
                tool_results=tool_results or None,
                has_live_image=has_live_image,
                attached_diagram_ids=attached_diagram_ids,
                force_final=force_final,
            )
            raw = self.gemma.reason(prompt, images=images)
            decision = parse_decision(raw) or fallback_decision(raw)

            if (
                not force_final
                and decision.action == "tool_request"
                and decision.tool_request
            ):
                tr = decision.tool_request
                output = reference_tools.run_tool(tr.tool, tr.args)
                tool_results.append({"tool": tr.tool, "args": tr.args, "result": output})
                continue
            break

        if decision is None:
            decision = fallback_decision("I could not process that. Please repeat.")

        # Safety net: never hand the client a tool_request we did not execute.
        if decision.action == "tool_request":
            decision.action = "clarify" if not decision.spoken_text else "answer"
            decision.tool_request = None
            if not decision.spoken_text:
                decision.spoken_text = (
                    "I need more information to continue safely. Please repeat the "
                    "current step or the last reading."
                )

        tts_path = None
        if speak and decision.spoken_text:
            tts_path = self._speak(decision.spoken_text)

        return {
            "query": query,
            "decision": decision.to_dict(),
            "retrieval": {
                "procedures": [p.__dict__ for p in retrieval.procedures],
                "diagrams": [d.__dict__ for d in retrieval.diagrams],
            },
            "tool_calls": tool_results,
            "sensor_snapshot": snapshot,
            "tts_path": str(tts_path) if tts_path else None,
        }

    # ------------------------------------------------------------------
    def _collect_images(self, retrieval, live_image_path) -> list[str]:
        images: list[str] = []
        for d in retrieval.diagrams:
            if len(images) >= _MAX_DIAGRAM_IMAGES:
                break
            if d.image_exists:
                images.append(d.image_path)
        if live_image_path:
            images.append(str(live_image_path))
        return images

    def _attached_diagram_ids(self, retrieval) -> list[str]:
        """Ids of the diagrams actually sent to the vision model (same cap as images),
        so the prompt only claims an image is 'attached' when it truly is."""
        ids: list[str] = []
        for d in retrieval.diagrams:
            if len(ids) >= _MAX_DIAGRAM_IMAGES:
                break
            if d.image_exists:
                ids.append(d.diagram_id)
        return ids

    def _speak(self, text: str):
        from ..models import tts

        return tts.synthesize_to_file(text)
