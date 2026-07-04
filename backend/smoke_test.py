"""Dependency-light smoke test: validates the corpus wiring, tools, and JSON parsing
WITHOUT loading any ML models (no torch/transformers/sentence-transformers needed).

Run:  python -m backend.smoke_test
Exits non-zero on failure.
"""
from __future__ import annotations

import sys


def check(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def main() -> int:
    ok = True

    # 1. Corpus loads and parses front matter.
    from .data_loader import load_corpus, procedure_document_text

    corpus = load_corpus()
    ok &= check("manifest has procedures", len(corpus.procedures) >= 4)
    ok &= check("diagrams loaded", len(corpus.diagrams) >= 8)
    ok &= check("reference files loaded", len(corpus.reference) >= 4)

    hero = corpus.procedures.get("EVA-PREP-001")
    ok &= check("hero procedure parsed", hero is not None and len(hero.steps) > 0)
    if hero:
        ok &= check("procedure doc text builds", bool(procedure_document_text(hero)))

    # 2. Sensor simulator classifies bands and injects anomalies.
    from .tools.sensor_sim import get_simulator

    sim = get_simulator()
    reading = sim.read("airlock_pressure_psia")
    ok &= check("sensor reads nominal by default", reading["status"] == "nominal")
    injected = sim.inject("airlock_pressure_psia", 15.5)  # above critical_above (14.9)
    ok &= check("injected over-pressure is critical", injected["status"] == "critical")
    co2 = sim.inject("cabin_co2_mmHg", 6.0)  # above critical_above (5.3)
    ok &= check("injected high CO2 is critical", co2["status"] == "critical")
    sim.reset()

    # 3. Deterministic tools resolve against the reference tables.
    from .tools import reference_tools

    torque = reference_tools.get_torque_spec("QD-COLLAR-14")
    ok &= check("torque spec found", torque.get("found") is True)
    inv_missing = reference_tools.check_inventory("QD-JMP-14-CAP")
    ok &= check("missing cap flagged unavailable", inv_missing.get("available") is False)
    inv_ok = reference_tools.check_inventory("QD-JMP-14")
    ok &= check("jumper available", inv_ok.get("available") is True)
    tool_dispatch = reference_tools.run_tool("read_sensor", {"name": "cabin_co2_mmHg"})
    ok &= check("run_tool dispatch works", tool_dispatch.get("known") is True)

    # 4. Structured-output parsing is tolerant.
    from .agent.schema import parse_decision

    fenced = '```json\n{"action": "tool_request", "spoken_text": "checking", ' \
             '"tool_request": {"tool": "read_sensor", "args": {"name": "x"}}}\n```'
    d = parse_decision(fenced)
    ok &= check("parses fenced tool_request", d is not None and d.action == "tool_request")
    ok &= check("tool_request extracted", d is not None and d.tool_request is not None)

    print()
    print("SMOKE TEST:", "OK" if ok else "FAILURES DETECTED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
