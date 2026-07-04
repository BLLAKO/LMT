"use client";

import { useEffect, useRef, useState } from "react";
import type { MicPermission } from "./types";

// TODO: real integration — this reads raw mic volume to drive the voice
// visual and to detect "the technician said something and then stopped" as
// a stand-in for step confirmation. A real pipeline would wire actual
// speech-to-text/VAD here instead of a volume threshold.
const VOICE_THRESHOLD = 0.08;
const SPEECH_MIN_MS = 250;
const SILENCE_CONFIRM_MS = 900;

/**
 * @param active    keep the mic stream open (requests permission once).
 * @param listening whether voice-activity confirmation should be armed
 *                  right now (paused while the AI's own turn is playing).
 */
export function useMicAmplitude(
  active: boolean,
  listening: boolean,
  onVoiceConfirmed: () => void
) {
  const [amplitude, setAmplitude] = useState(0);
  const [permission, setPermission] = useState<MicPermission>("idle");

  const rafRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const listeningRef = useRef(listening);
  const speechStartRef = useRef<number | null>(null);
  const silenceStartRef = useRef<number | null>(null);
  const hasSpokenRef = useRef(false);
  const confirmedRef = useRef(false);
  const onVoiceConfirmedRef = useRef(onVoiceConfirmed);
  onVoiceConfirmedRef.current = onVoiceConfirmed;

  // Re-arm detection each time a fresh listening window begins.
  useEffect(() => {
    listeningRef.current = listening;
    if (listening) {
      speechStartRef.current = null;
      silenceStartRef.current = null;
      hasSpokenRef.current = false;
      confirmedRef.current = false;
    }
  }, [listening]);

  useEffect(() => {
    if (!active) {
      setPermission("idle");
      setAmplitude(0);
      return;
    }

    let cancelled = false;

    async function start() {
      setPermission("pending");
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        setPermission("granted");

        const audioCtx = new AudioContext();
        audioCtxRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 512;
        source.connect(analyser);
        const data = new Uint8Array(analyser.frequencyBinCount);

        const tick = () => {
          analyser.getByteTimeDomainData(data);
          let sumSquares = 0;
          for (let i = 0; i < data.length; i++) {
            const v = (data[i] - 128) / 128;
            sumSquares += v * v;
          }
          const rms = Math.sqrt(sumSquares / data.length);
          const level = Math.min(1, rms * 5);
          setAmplitude(level);

          if (listeningRef.current && !confirmedRef.current) {
            const now = performance.now();
            if (level > VOICE_THRESHOLD) {
              silenceStartRef.current = null;
              if (speechStartRef.current === null) speechStartRef.current = now;
              if (now - speechStartRef.current > SPEECH_MIN_MS) hasSpokenRef.current = true;
            } else {
              speechStartRef.current = null;
              if (hasSpokenRef.current) {
                if (silenceStartRef.current === null) silenceStartRef.current = now;
                if (now - silenceStartRef.current > SILENCE_CONFIRM_MS) {
                  confirmedRef.current = true;
                  onVoiceConfirmedRef.current();
                }
              }
            }
          }

          rafRef.current = requestAnimationFrame(tick);
        };
        tick();
      } catch {
        if (!cancelled) setPermission("denied");
      }
    }

    start();

    return () => {
      cancelled = true;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      audioCtxRef.current?.close().catch(() => {});
      streamRef.current = null;
      audioCtxRef.current = null;
      setAmplitude(0);
    };
  }, [active]);

  return { amplitude, permission };
}
