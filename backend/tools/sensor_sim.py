"""Simulated live telemetry.

Provides current sensor values and classifies them against the nominal / caution /
critical bands defined in data/reference/telemetry-nominal-ranges.yaml. Values start
at the nominal midpoint; the demo can inject anomalies (e.g. a stuck airlock at
14.6 psia) to trigger the agent's blocking / emergency behavior.
"""
from __future__ import annotations

import math
import random
import threading
import time
from typing import Any

from ..data_loader import load_corpus


class SensorSimulator:
    def __init__(self):
        self._lock = threading.Lock()
        self._specs: dict[str, dict[str, Any]] = {}
        self._values: dict[str, Any] = {}
        # Per-sensor random phase + a shared clock so numeric readings gently
        # drift over time (realistic "live" telemetry) instead of sitting flat.
        self._phase: dict[str, float] = {}
        self._t0 = time.monotonic()
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
            self._phase[name] = random.uniform(0.0, 2 * math.pi)

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
        value = self._display_value(name, spec, self._values.get(name))
        status = _classify(spec, value)
        return {
            "sensor": name,
            "known": True,
            "value": value,
            "unit": spec.get("unit"),
            "status": status,
            "label": spec.get("label"),
        }

    def _display_value(self, name: str, spec: dict[str, Any], base: Any) -> Any:
        """Add a small, smooth, time-varying wobble to numeric readings.

        The drift stays close to the base value and never pushes a nominal
        sensor out of its band, so it looks alive without changing severity or
        surprising the agent's safety logic. Enum/categorical sensors are left
        untouched, as is an injected fault value (we only wobble around it).
        """
        if spec.get("unit") == "enum" or not isinstance(base, (int, float)):
            return base

        nominal = spec.get("nominal", {})
        lo, hi = nominal.get("min"), nominal.get("max")
        if lo is not None and hi is not None and hi > lo:
            span = hi - lo
        else:
            span = max(abs(base) * 0.1, 1.0)

        t = time.monotonic() - self._t0
        phase = self._phase.get(name, 0.0)
        drift = 0.04 * span * math.sin(t / 7.0 + phase) + 0.015 * span * math.sin(
            t / 2.3 + phase * 1.7
        )
        value = base + drift

        # Keep the wobble tight around the base value.
        value = max(base - 0.06 * span, min(base + 0.06 * span, value))
        # If the base sits inside the nominal band, never let noise leave it.
        if lo is not None and hi is not None and lo <= base <= hi:
            value = max(lo, min(hi, value))

        return round(value, 3)

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


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _classify(spec: dict[str, Any], value: Any) -> str:
    # Categorical sensors (e.g. cdra_valve_state).
    if spec.get("unit") == "enum":
        enum_values = _as_list(spec.get("enum"))
        fault_states = _as_list(spec.get("fault_state"))
        nominal_states = _as_list(spec.get("nominal_state"))
        if value in fault_states:
            return "critical"
        if value in nominal_states:
            return "nominal"
        # A value outside the declared enum is bad data, not a safe reading.
        if enum_values and value not in enum_values:
            return "unknown"
        return "caution"

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
