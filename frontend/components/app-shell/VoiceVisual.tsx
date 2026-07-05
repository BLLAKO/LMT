"use client";

import { useEffect, useRef } from "react";
import type { VoicePhase } from "@/lib/types";

// A minimalist, Siri-inspired voice visual: a soft accent glow behind a row of
// rounded bars that breathe continuously and swell with the live audio level
// (mic input while listening, TTS output while speaking). Heights are mutated
// per-frame via refs (no React re-render) so it stays smooth and cheap.

const BAR_WEIGHTS = [0.5, 0.78, 1, 0.78, 0.5];
const BAR_SPEED = [2.1, 3.3, 2.7, 3.1, 2.4];
const BAR_PHASE = [0.0, 1.1, 2.3, 0.7, 1.8];

// Accent palette (tailwind.config.ts) tinted per phase.
const PHASE_COLOR: Record<VoicePhase, string> = {
  listening: "#7A9B52", // accent-500
  speaking: "#5F7D3D", // accent-600
  thinking: "#AEC78A", // accent-300 (calmer while the model works)
  idle: "#C7D3AE",
};

export default function VoiceVisual({
  amplitude,
  phase = "listening",
  size = "default",
}: {
  amplitude: number;
  phase?: VoicePhase;
  size?: "default" | "compact";
}) {
  const compact = size === "compact";
  const minH = compact ? 6 : 8;
  const maxH = compact ? 34 : 56;
  const barWidth = compact ? "0.375rem" : "0.5rem";
  const gap = compact ? "0.4rem" : "0.6rem";
  const frame = compact ? "h-24 w-44" : "h-56 w-72";
  const glowSize = compact ? "7rem" : "11rem";

  const barsRef = useRef<Array<HTMLSpanElement | null>>([]);
  const glowRef = useRef<HTMLDivElement | null>(null);
  const ampRef = useRef(0);
  ampRef.current = Math.max(0, Math.min(1, amplitude));

  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const tick = (t: number) => {
      const elapsed = (t - start) / 1000;
      const amp = ampRef.current;
      for (let i = 0; i < BAR_WEIGHTS.length; i++) {
        const bar = barsRef.current[i];
        if (!bar) continue;
        const wave = 0.5 + 0.5 * Math.sin(elapsed * BAR_SPEED[i] + BAR_PHASE[i]);
        const energy = 0.09 + amp * 1.15; // idle breathing floor + live level
        const norm = Math.max(
          0,
          Math.min(1, BAR_WEIGHTS[i] * energy * (0.4 + 0.6 * wave))
        );
        bar.style.height = `${minH + (maxH - minH) * norm}px`;
      }
      if (glowRef.current) {
        glowRef.current.style.transform = `scale(${1 + amp * 0.7})`;
        glowRef.current.style.opacity = `${0.1 + amp * 0.4}`;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [minH, maxH]);

  const color = PHASE_COLOR[phase];

  return (
    <div className={`relative flex ${frame} items-center justify-center`}>
      <div
        ref={glowRef}
        className="pointer-events-none absolute rounded-full blur-2xl"
        style={{ width: glowSize, height: glowSize, background: color, opacity: 0.15 }}
      />
      <div className="relative flex items-end justify-center" style={{ gap }}>
        {BAR_WEIGHTS.map((_, i) => (
          <span
            key={i}
            ref={(el) => {
              barsRef.current[i] = el;
            }}
            className="rounded-full"
            style={{
              width: barWidth,
              height: `${minH}px`,
              backgroundColor: color,
              transition: "background-color 300ms ease",
            }}
          />
        ))}
      </div>
    </div>
  );
}
