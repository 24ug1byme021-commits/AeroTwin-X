import type {
  TelemetryFrame,
  ScenarioName,
  SystemStatus,
  EngineStateSnapshot,
  HealthIndexResult,
  RULEstimate,
  MissionInput,
  MissionResult,
  NaturalLanguageMissionParse,
  RunRecord,
  RunReport,
} from "../types/api";

// In local dev, Vite proxies /api and /health to the FastAPI backend (see
// vite.config.ts) — so leaving VITE_API_BASE_URL unset keeps working exactly
// as before. For a real deployment (frontend and backend on different
// hosts), set VITE_API_BASE_URL at build time to the backend's public URL,
// e.g. https://aerotwinx-backend.onrender.com
const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${options?.method ?? "GET"} ${path} failed: ${res.status} ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  liveness: () => request<{ status: string; service: string }>("/health"),

  systemStatus: () => request<SystemStatus>("/api/system/status"),
  engineState: () => request<EngineStateSnapshot>("/api/engine/state"),

  startSimulation: () => request<{ status: string; scenario: string }>("/api/simulation/start", { method: "POST" }),
  stopSimulation: () => request<{ status: string }>("/api/simulation/stop", { method: "POST" }),
  resetSimulation: () => request<{ status: string; scenario: string }>("/api/simulation/reset", { method: "POST" }),
  setDetectorMode: (mode: "statistical" | "ml" | "hybrid") =>
    request<{ status: string; detector_mode: string }>("/api/detector/mode", {
      method: "POST",
      body: JSON.stringify({ mode }),
    }),
  listRuns: () => request<{ runs: RunRecord[]; persistence: string }>("/api/runs?limit=8"),
  runReport: (id: number) => request<RunReport>(`/api/runs/${id}/report`),
  setScenario: (scenario: ScenarioName) =>
    request<{ status: string; scenario: string }>("/api/simulation/scenario", {
      method: "POST",
      body: JSON.stringify({ scenario }),
    }),

  telemetryCurrent: () => request<TelemetryFrame>("/api/telemetry/current"),
  telemetryHistory: (n = 100) => request<{ frames: TelemetryFrame[]; count: number }>(`/api/telemetry/history?n=${n}`),

  healthStatus: () => request<HealthIndexResult>("/api/health/status"),
  rul: () => request<RULEstimate>("/api/rul"),

  missionSimulate: (mission: MissionInput) =>
    request<MissionResult>("/api/mission/simulate", { method: "POST", body: JSON.stringify(mission) }),
  missionParse: (text: string) =>
    request<NaturalLanguageMissionParse>("/api/mission/parse", { method: "POST", body: JSON.stringify({ text }) }),
};
