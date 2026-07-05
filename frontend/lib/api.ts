// Thin client for the ZeroDelay FastAPI backend (backend/api/server.py).
// The backend has open CORS, so a browser on :3000 can call it on :8000 directly.

import type { Decision, Sensor } from "./types";

export const API_BASE = (
  process.env.NEXT_PUBLIC_ZD_API || "http://127.0.0.1:8000"
).replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export type RetrievedDiagram = {
  diagram_id: string;
  title: string;
  image_path: string;
  image_exists: boolean;
  score: number;
};

export type ConverseResponse = {
  query: string;
  decision: Decision;
  retrieval?: { procedures: unknown[]; diagrams: RetrievedDiagram[] };
  sensor_snapshot: Sensor[];
  tool_calls: unknown[];
  tts_wav_base64: string | null;
  transcribed?: boolean;
};

/** URL for a diagram PNG served by the backend's /diagrams static mount. */
export function diagramUrl(diagramId: string): string {
  return `${API_BASE}/diagrams/${encodeURIComponent(diagramId)}.png`;
}

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail: string = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

/** POST recorded mic audio (WAV) -> STT + RAG + reasoning + TTS in one turn. */
export async function converse(wav: Blob): Promise<ConverseResponse> {
  const form = new FormData();
  form.append("audio", wav, "input.wav");
  const res = await fetch(`${API_BASE}/converse`, { method: "POST", body: form });
  return asJson<ConverseResponse>(res);
}

export async function getSensors(): Promise<{ sensors: Sensor[] }> {
  return asJson(await fetch(`${API_BASE}/sensors`));
}

export async function injectSensor(
  name: string,
  value: number | string
): Promise<{ reading: Sensor }> {
  const res = await fetch(`${API_BASE}/sensors/inject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, value }),
  });
  return asJson(res);
}

export async function resetSensors(): Promise<{ status: string }> {
  return asJson(await fetch(`${API_BASE}/sensors/reset`, { method: "POST" }));
}

export async function health(): Promise<{ status: string; gemma_model: string }> {
  return asJson(await fetch(`${API_BASE}/health`));
}
