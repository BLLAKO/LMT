"""Deterministic tool lookups over data/reference/*.yaml.

These are the exact-fact functions the agent calls instead of fuzzy retrieval:
  * read_sensor       -> live (simulated) telemetry + status
  * get_torque_spec   -> exact torque / PGT setting for a fastener
  * check_inventory   -> availability of a tool or spare part
  * lookup_fault_tree -> symptom -> branch target for diagnostic branching

`run_tool` dispatches by name for the orchestrator's tool-call loop.
"""
from __future__ import annotations

from typing import Any

from ..data_loader import load_corpus
from .sensor_sim import get_simulator


def read_sensor(name: str) -> dict[str, Any]:
    return get_simulator().read(name)


def get_torque_spec(fastener_id: str) -> dict[str, Any]:
    corpus = load_corpus()
    torque = corpus.reference.get("torque-specs", {})
    for fastener in torque.get("fasteners", []) or []:
        if fastener.get("fastener_id") == fastener_id:
            return {"found": True, **fastener}
    return {"found": False, "fastener_id": fastener_id, "error": "unknown fastener"}


def check_inventory(part_id: str) -> dict[str, Any]:
    corpus = load_corpus()
    inventory = corpus.reference.get("inventory", {})
    for group in ("tools", "parts"):
        for item in inventory.get(group, []) or []:
            if item.get("part_id") == part_id:
                qty = item.get("qty", 0)
                return {
                    "found": True,
                    "part_id": part_id,
                    "name": item.get("name"),
                    "available": bool(item.get("available", qty > 0)),
                    "qty": qty,
                    "location": item.get("location"),
                    "notes": item.get("notes"),
                }
    return {"found": False, "part_id": part_id, "available": False, "error": "unknown part"}


def lookup_fault_tree(tree_id: str, symptom: str | None = None) -> dict[str, Any]:
    corpus = load_corpus()
    trees = corpus.reference.get("fault-trees", {})
    for tree in trees.get("trees", []) or []:
        if tree.get("tree_id") != tree_id:
            continue
        if symptom is None:
            return {"found": True, **tree}
        # Try to match a branch whose symptom text overlaps the query.
        matches = []
        for test in tree.get("tests", []) or []:
            for branch in test.get("branches", []) or []:
                if _symptom_matches(symptom, branch.get("symptom", "")):
                    matches.append(branch)
        return {
            "found": True,
            "tree_id": tree_id,
            "symptom_query": symptom,
            "matches": matches or None,
        }
    return {"found": False, "tree_id": tree_id, "error": "unknown fault tree"}


def _symptom_matches(query: str, symptom: str) -> bool:
    q = query.lower()
    s = symptom.lower()
    if not s:
        return False
    if s in q or q in s:
        return True
    # loose keyword overlap
    q_words = {w for w in q.split() if len(w) > 3}
    s_words = {w for w in s.split() if len(w) > 3}
    return len(q_words & s_words) >= 2


# ---------------------------------------------------------------------------
# Dispatch + declaration (for prompts and the tool loop)
# ---------------------------------------------------------------------------
TOOLS = {
    "read_sensor": read_sensor,
    "get_torque_spec": get_torque_spec,
    "check_inventory": check_inventory,
    "lookup_fault_tree": lookup_fault_tree,
}

TOOL_DECLARATIONS = [
    {"name": "read_sensor", "args": {"name": "sensor name, e.g. airlock_pressure_psia"}},
    {"name": "get_torque_spec", "args": {"fastener_id": "e.g. QD-COLLAR-14"}},
    {"name": "check_inventory", "args": {"part_id": "e.g. QD-JMP-14"}},
    {"name": "lookup_fault_tree", "args": {"tree_id": "e.g. coolant_leak", "symptom": "text"}},
]


def run_tool(name: str, args: dict[str, Any] | None) -> dict[str, Any]:
    fn = TOOLS.get(name)
    if fn is None:
        return {"error": f"unknown tool: {name}"}
    args = args or {}
    try:
        return fn(**args)
    except TypeError as exc:
        return {"error": f"bad arguments for {name}: {exc}"}
    except Exception as exc:  # pragma: no cover - defensive
        return {"error": f"{name} failed: {exc}"}
