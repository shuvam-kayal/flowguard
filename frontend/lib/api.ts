/**
 * FlowGuard API client
 *
 * All network calls to the FastAPI backend live here.
 * Components should never call `fetch` directly — use these functions or the
 * TanStack Query hooks that wrap them.
 */

import type {
  DashboardResponse,
  DailyForecastPoint,
  ForecastChartPoint,
  CreditGuardResult,
  WorkerListItem,
  Scenario,
} from "@/types/dashboard";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

/**
 * Converts the backend's `daily_forecast` array (ISO date strings) into
 * chart-friendly points for Recharts.
 */
export function adaptForecastPoints(
  dailyForecast: DailyForecastPoint[]
): ForecastChartPoint[] {
  return dailyForecast.map((pt) => ({
    label: new Date(pt.date).toLocaleDateString("en-IN", {
      month: "short",
      day: "numeric",
    }),
    expected: pt.expected,
    lower: pt.lower,
    upper: pt.upper,
  }));
}

/**
 * Returns how many calendar days until an ISO date string.
 * Returns 0 if the date has already passed.
 */
export function daysUntil(isoDate: string): number {
  const now = new Date();
  const target = new Date(isoDate);
  const diffMs = target.getTime() - now.getTime();
  return Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
}

// ─── Workers ──────────────────────────────────────────────────────────────────

/** GET /workers — list all available demo workers */
export async function getWorkers(): Promise<WorkerListItem[]> {
  return apiFetch<WorkerListItem[]>("/workers");
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

/** GET /worker/{workerId}/dashboard — base dashboard for a worker */
export async function getDashboard(workerId: string): Promise<DashboardResponse> {
  return apiFetch<DashboardResponse>(`/worker/${workerId}/dashboard`);
}

// ─── Simulation Endpoints ─────────────────────────────────────────────────────

/** POST /simulate/shock — apply income shock simulation */
export async function simulateShock(
  workerId: string,
  factor?: number
): Promise<DashboardResponse> {
  return apiFetch<DashboardResponse>("/simulate/shock", {
    method: "POST",
    body: JSON.stringify({ worker_id: workerId, ...(factor !== undefined && { factor }) }),
  });
}

/** POST /simulate/recovery — apply recovery simulation */
export async function simulateRecovery(
  workerId: string
): Promise<DashboardResponse> {
  return apiFetch<DashboardResponse>("/simulate/recovery", {
    method: "POST",
    body: JSON.stringify({ worker_id: workerId }),
  });
}

/**
 * Fetches dashboard data for the given scenario:
 * - NORMAL   → GET  /worker/{id}/dashboard
 * - SHOCK    → POST /simulate/shock
 * - RECOVERY → POST /simulate/recovery
 */
export async function getDashboardForScenario(
  workerId: string,
  scenario: Scenario
): Promise<DashboardResponse> {
  if (scenario === "SHOCK") return simulateShock(workerId);
  if (scenario === "RECOVERY") return simulateRecovery(workerId);
  return getDashboard(workerId);
}

// ─── Credit ───────────────────────────────────────────────────────────────────

/** POST /credit/evaluate — evaluate a credit request */
export async function evaluateCredit(
  workerId: string,
  requestedAmount: number
): Promise<CreditGuardResult> {
  return apiFetch<CreditGuardResult>("/credit/evaluate", {
    method: "POST",
    body: JSON.stringify({ worker_id: workerId, requested_amount: requestedAmount }),
  });
}
