"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Sidebar from "@/components/app-shell/Sidebar";
import VoiceVisual from "@/components/app-shell/VoiceVisual";
import StepOverlay from "@/components/app-shell/StepOverlay";
import { activeProcedure } from "@/lib/mock-data";
import { useMicAmplitude } from "@/lib/useMicAmplitude";
import type { Conversation } from "@/lib/types";

const AI_SPEAKING_MS = 1600;

export default function AppPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [phase, setPhase] = useState<"speaking" | "listening">("speaking");
  const [completed, setCompleted] = useState(false);
  const [aiAmplitude, setAiAmplitude] = useState(0);

  const isLastStep = stepIndex === activeProcedure.steps.length - 1;

  const handleVoiceConfirmed = useCallback(() => {
    setStepIndex((i) => {
      const last = i === activeProcedure.steps.length - 1;
      if (last) {
        setCompleted(true);
        return i;
      }
      setPhase("speaking");
      return i + 1;
    });
  }, []);

  const micActive = selectedId !== null && !completed;
  const { amplitude: micAmplitude, permission } = useMicAmplitude(
    micActive,
    phase === "listening",
    handleVoiceConfirmed
  );

  // AI's own turn: no real TTS playback to analyze yet, so a synthetic wave
  // stands in for it. TODO: replace with the actual TTS output level.
  useEffect(() => {
    if (phase !== "speaking" || selectedId === null || completed) return;
    let raf: number;
    const start = performance.now();
    const tick = (t: number) => {
      const elapsed = t - start;
      setAiAmplitude(0.35 + 0.25 * Math.sin(elapsed / 180));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    const timer = setTimeout(() => {
      setPhase("listening");
      setAiAmplitude(0);
    }, AI_SPEAKING_MS);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(timer);
    };
  }, [phase, stepIndex, selectedId, completed]);

  function selectConversation(id: string) {
    setSelectedId(id);
    setStepIndex(0);
    setPhase("speaking");
    setCompleted(false);
  }

  function startNewSession() {
    // TODO: real integration — a new session should be created by the
    // procedure engine once the technician describes the fault by voice,
    // rather than always loading the same demo procedure.
    const id = `session-${Date.now()}`;
    setConversations((prev) => [
      { id, title: "New discussion", procedureId: activeProcedure.id, updatedAt: "Just now" },
      ...prev,
    ]);
    selectConversation(id);
  }

  const step = activeProcedure.steps[stepIndex];
  const displayAmplitude =
    selectedId === null ? 0 : phase === "speaking" ? aiAmplitude : micAmplitude;

  return (
    <div className="flex h-screen bg-page">
      <Sidebar
        conversations={conversations}
        activeId={selectedId}
        onSelect={selectConversation}
        onNewSession={startNewSession}
      />

      <main className="relative flex-1 overflow-hidden bg-page">
        {selectedId === null ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
            <p className="max-w-xs text-sm text-secondary">
              Click "+ New" to start a hands-free walkthrough, or pick a past
              discussion from the sidebar.
            </p>
          </div>
        ) : permission === "denied" ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
            <p className="max-w-xs text-sm text-secondary">
              Microphone access is required for hands-free voice control.
              Please allow microphone access and reopen this session.
            </p>
          </div>
        ) : completed ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
            <p className="max-w-xs text-sm text-secondary">
              Session complete — all steps confirmed.
            </p>
          </div>
        ) : (
          <div className="h-full overflow-y-auto px-6 pb-56 pt-16">
            <div className="mx-auto flex max-w-xl justify-center">
              <StepOverlay
                step={step}
                stepNumber={stepIndex + 1}
                totalSteps={activeProcedure.steps.length}
              />
            </div>
          </div>
        )}

        {selectedId !== null && !completed && permission !== "denied" && (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-col items-center gap-2 bg-gradient-to-t from-page via-page/90 to-transparent pb-10 pt-10">
            <VoiceVisual amplitude={displayAmplitude} size="compact" />
            <p className="text-xs text-muted">
              {permission === "pending"
                ? "Requesting microphone access…"
                : phase === "speaking"
                  ? "ZeroDelay is speaking…"
                  : "Listening…"}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
