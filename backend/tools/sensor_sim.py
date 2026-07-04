"""Simulated live telemetry.

Provides current sensor values and classifies them against the nominal / caution /
critical bands defined in data/reference/telemetry-nominal-ranges.yaml. Values start
at the nominal midpoint; the demo can inject anomalies (e.g. a stuck airlock at
14.6 psia) to trigger the agent's blocking / emergency behavior.
"""
from __future__ import annotations

import threading
from typing import Any

from ..data_loader import load_corpus


class SensorSimulator:
    def __init__(self):
        self._lock = threading.Lock()
        self._specs: dict[str, dict[str, Any]] = {}
        self._values: dict[str, Any] = {}
        self._load_specs()

    def _load_specs(self) -> None:
        corpus = load_corpus()
        telemetry = corpus.reference.get("telemetry-nominal-ranges", {})
        for sensor in telemetry.get("sensors", []) or []:
            name = sensor.get("name")
            if not name:
                continue
            self._specs[name] = sensor
            self._values[name] = _default_value(sensor)

    # ------------------------------------------------------------------
    def known_sensors(self) -> list[str]:
        return list(self._specs.keys())

    def inject(self, name: str, value: Any) -> dict[str, Any]:
        """Override a sensor value (for demo anomalies). Returns the new reading."""
        with self._lock:
            if name not in self._specs:
                raise KeyError(f"Unknown sensor: {name}")
            self._values[name] = value
        return self.read(name)

    def reset(self) -> None:
        with self._lock:
            for name, spec in self._specs.items():
                self._values[name] = _default_value(spec)

    def read(self, name: str) -> dict[str, Any]:
        spec = self._specs.get(name)
        if spec is None:
            return {"sensor": name, "known": False, "error": "unknown sensor"}
        value = self._values.get(name)
        status = _classify(spec, value)
        return {
            "sensor": name,
            "known": True,
            "value": value,
            "unit": spec.get("unit"),
            "status": status,
            "label": spec.get("label"),
        }

    def snapshot(self) -> list[dict[str, Any]]:
        return [self.read(name) for name in self._specs]


def _default_value(spec: dict[str, Any]) -> Any:
    if spec.get("unit") == "enum":
        nominal = spec.get("nominal_state") or spec.get("enum") or ["nominal"]
        return nominal[0]
    nominal = spec.get("nominal", {})
    lo, hi = nominal.get("min"), nominal.get("max")
    if lo is not None and hi is not None:
        return round((lo + hi) / 2, 3)
    return lo if lo is not None else 0.0


def _classify(spec: dict[str, Any], value: Any) -> str:
    # Categorical sensors (e.g. cdra_valve_state).
    if spec.get("unit") == "enum":
        fault_states = spec.get("fault_state", []) or []
        return "critical" if value in fault_states else "nominal"

    if value is None:
        return "unknown"

    crit_below = spec.get("critical_below")
    crit_above = spec.get("critical_above")
    if crit_below is not None and value < crit_below:
        return "critical"
    if crit_above is not None and value > crit_above:
        return "critical"

    nominal = spec.get("nominal", {})
    n_lo, n_hi = nominal.get("min"), nominal.get("max")
    if n_lo is not None and n_hi is not None and n_lo <= value <= n_hi:
        return "nominal"

    return "caution"


# Process-wide singleton.
_sim: SensorSimulator | None = None


def get_simulator() -> SensorSimulator:
    global _sim
    if _sim is None:
        _sim = SensorSimulator()
    return _sim
