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

export type ConverseStreamHandlers = {
  /** Fired once with the transcribed technician utterance. */
  onQuery?: (query: string) => void;
  /** Fired with each chunk of the spoken answer as the model generates it. */
  onDelta?: (text: string) => void;
};

/**
 * Streaming version of {@link converse}: transcribes, then streams the single
 * reasoning pass as newline-delimited JSON. `onDelta` fires continuously as the
 * spoken answer is generated; the resolved {@link ConverseResponse} (decision,
 * retrieval, TTS) is returned once the turn completes.
 */
export async function converseStream(
  wav: Blob,
  handlers: ConverseStreamHandlers = {}
): Promise<ConverseResponse> {
  const form = new FormData();
  form.append("audio", wav, "input.wav");
  const res = await fetch(`${API_BASE}/converse/stream`, {
    method: "POST",
    body: form,
  });
  // Non-2xx (incl. 422 "no speech") has a JSON error body — reuse the error path.
  if (!res.ok || !res.body) {
    return asJson<ConverseResponse>(res);
  }

  type StreamEvent =
    | { type: "query"; text: string }
    | { type: "delta"; text: string }
    | { type: "final"; result: ConverseResponse }
    | { type: "error"; detail: string };

  let final: ConverseResponse | null = null;
  const handleLine = (line: string) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    const msg = JSON.parse(trimmed) as StreamEvent;
    if (msg.type === "query") handlers.onQuery?.(msg.text);
    else if (msg.type === "delta") handlers.onDelta?.(msg.text);
    else if (msg.type === "final") final = msg.result;
    else if (msg.type === "error") throw new ApiError(500, msg.detail);
  };

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let nl: number;
    while ((nl = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, nl);
      buffer = buffer.slice(nl + 1);
      handleLine(line);
    }
  }
  if (buffer.trim()) handleLine(buffer); // trailing line without newline

  if (!final) throw new ApiError(500, "Stream ended without a final result.");
  return final;
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
