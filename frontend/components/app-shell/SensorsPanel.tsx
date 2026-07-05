"use client";

import { useCallback, useEffect, useState } from "react";
import { getSensors, injectSensor, resetSensors } from "@/lib/api";
import type { Sensor, SensorStatus } from "@/lib/types";

const statusStyles: Record<SensorStatus, string> = {
  nominal: "bg-success-bg text-success-text",
  caution: "bg-warning-bg text-warning-text",
  critical: "bg-danger-bg text-danger-text",
  unknown: "bg-subtle text-secondary",
};

// Demo anomalies that trip the agent's safety behavior (names come from
// data/reference/telemetry-nominal-ranges.yaml).
const FAULT_PRESETS: { label: string; name: string; value: number }[] = [
  { label: "Airlock still pressurized", name: "airlock_pressure_psia", value: 14.6 },
  { label: "Suit O₂ low", name: "suit_o2_pct", value: 88 },
  { label: "Cabin CO₂ high", name: "cabin_co2_mmHg", value: 6.1 },
];

function formatValue(sensor: Sensor): string {
  if (sensor.value === null || sensor.value === undefined) return "—";
  const unit = sensor.unit && sensor.unit !== "enum" ? ` ${sensor.unit}` : "";
  return `${sensor.value}${unit}`;
}

export default function SensorsPanel() {
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [offline, setOffline] = useState(false);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await getSensors();
      setSensors(res.sensors);
      setOffline(false);
    } catch {
      setOffline(true);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [refresh]);

  const inject = useCallback(
    async (name: string, value: number) => {
      setBusy(true);
      try {
        await injectSensor(name, value);
        await refresh();
      } catch {
        setOffline(true);
      } finally {
        setBusy(false);
      }
    },
    [refresh]
  );

  const reset = useCallback(async () => {
    setBusy(true);
    try {
      await resetSensors();
      await refresh();
    } catch {
      setOffline(true);
    } finally {
      setBusy(false);
    }
  }, [refresh]);

  return (
    <aside className="hidden w-72 shrink-0 flex-col border-l border-border bg-subtle xl:flex">
      <div className="flex items-center justify-between px-4 py-4">
        <h2 className="text-sm font-semibold tracking-tight">Live telemetry</h2>
        <span
          className={`h-2 w-2 rounded-full ${offline ? "bg-danger" : "bg-success"}`}
          title={offline ? "Backend unreachable" : "Live"}
        />
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4">
        {offline ? (
          <p className="px-1 text-sm text-muted">
            Backend offline — start the API on port 8000.
          </p>
        ) : sensors.length === 0 ? (
          <p className="px-1 text-sm text-muted">Loading sensors…</p>
        ) : (
          <div className="space-y-1">
            {sensors.map((s) => {
              const status = (s.status ?? "unknown") as SensorStatus;
              return (
                <div
                  key={s.sensor}
                  className="flex items-center justify-between gap-2 rounded-lg bg-card/60 px-3 py-2"
                >
                  <div className="min-w-0">
                    <p className="truncate text-xs font-medium text-primary">
                      {s.label ?? s.sensor}
                    </p>
                    <p className="text-xs text-muted">{formatValue(s)}</p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${statusStyles[status]}`}
                  >
                    {status}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="border-t border-border px-3 py-3">
        <p className="mb-2 px-1 text-xs font-medium uppercase tracking-wide text-muted">
          Inject fault (demo)
        </p>
        <div className="space-y-1">
          {FAULT_PRESETS.map((f) => (
            <button
              key={f.name}
              disabled={busy || offline}
              onClick={() => inject(f.name, f.value)}
              className="w-full rounded-lg border border-border bg-card px-3 py-1.5 text-left text-xs text-secondary transition-colors hover:bg-card/60 disabled:opacity-50"
            >
              {f.label}
            </button>
          ))}
          <button
            disabled={busy || offline}
            onClick={reset}
            className="mt-1 w-full rounded-lg bg-accent-500 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-accent-600 disabled:opacity-50"
          >
            Reset to nominal
          </button>
        </div>
      </div>
    </aside>
  );
}
