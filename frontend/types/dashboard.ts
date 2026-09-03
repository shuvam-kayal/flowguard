/**
 * FlowGuard Frontend Type Contracts
 *
 * These types mirror the Pydantic schemas in backend/schemas/contracts.py exactly.
 * If you change a field here, update the backend schema and docs/api-contract.md too.
 */

// ─── Primitives ────────────────────────────────────────────────────────────────

export type RiskLevel = "LOW" | "MODERATE" | "HIGH";
export type Trend = "RISING" | "STABLE" | "DECLINING";
export type Weather = "STABLE" | "WATCH" | "SHOCK";
export type Mode = "NORMAL" | "WATCH" | "SHOCK" | "RECOVERY";

/**
 * UI-only: the scenario the user has selected in the sidebar.
 * Maps to backend simulation endpoints: NORMAL = dashboard, SHOCK = /simulate/shock,
 * RECOVERY = /simulate/recovery.
 */
export type Scenario = "NORMAL" | "SHOCK" | "RECOVERY";

// ─── Worker ────────────────────────────────────────────────────────────────────

/** Matches backend WorkerSummary */
export interface WorkerSummary {
  worker_id: string;
  name: string;
  occupation: string;
  current_balance: number;
}

// ─── Risk ──────────────────────────────────────────────────────────────────────

/** Matches backend RiskFactor */
export interface RiskFactor {
  feature: string;
  impact: number;
  direction: "increases_risk" | "decreases_risk";
}

/** Matches backend RiskResult */
export interface RiskResult {
  worker_id: string;
  risk_score: number;   // 0.0 – 1.0
  risk_level: RiskLevel;
  confidence: number;   // 0.0 – 1.0
  top_factors: RiskFactor[];
}

// ─── Forecast ─────────────────────────────────────────────────────────────────

/** Matches backend DailyForecastPoint */
export interface DailyForecastPoint {
  date: string;       // ISO date string e.g. "2026-09-05"
  expected: number;   // expected income in INR
  lower: number;      // lower confidence bound
  upper: number;      // upper confidence bound
}

/**
 * Chart-friendly point produced by adaptForecastPoints() in api.ts.
 * This is NOT a backend type — it's derived for Recharts.
 */
export interface ForecastChartPoint {
  label: string;      // short display label e.g. "Sep 5" or "D+1"
  expected: number;
  lower: number;
  upper: number;
}

/** Matches backend ForecastResult */
export interface ForecastResult {
  worker_id: string;
  next_7_days: number;
  next_30_days: number;
  lower_bound: number;
  upper_bound: number;
  trend: Trend;
  shock_probability: number;  // 0.0 – 1.0
  weather: Weather;
  daily_forecast: DailyForecastPoint[];
}

// ─── Obligations ──────────────────────────────────────────────────────────────

/** Matches backend Obligation */
export interface Obligation {
  name: string;
  amount: number;
  due_date: string;   // ISO date string e.g. "2026-09-09"
  category: "FIXED" | "DEBT" | "UTILITY" | "OTHER";
}

/** Matches backend ObligationSummary */
export interface ObligationSummary {
  worker_id: string;
  upcoming_obligations: Obligation[];
  total_upcoming: number;
  essential_daily_spend: number;
}

// ─── Resilience ────────────────────────────────────────────────────────────────

/** Matches backend WalletAllocation */
export interface WalletAllocation {
  daily: number;
  bills: number;
  buffer: number;
  growth: number;
}

/** Matches backend ScoreBreakdown */
export interface ScoreBreakdown {
  income_stability: number;
  emergency_buffer: number;
  expense_coverage: number;
  debt_burden: number;
  savings_consistency: number;
}

/** Matches backend ResilienceResult */
export interface ResilienceResult {
  worker_id: string;
  safe_to_spend_daily: number;
  resilience_score: number;   // 0 – 100
  resilience_days: number;
  buffer_target: number;
  buffer_current: number;
  recommended_save: number;
  mode: Mode;
  wallet_allocation: WalletAllocation;
  score_breakdown: ScoreBreakdown;
}

// ─── Recommendations ──────────────────────────────────────────────────────────

/** Matches backend Recommendation */
export interface Recommendation {
  type: "SAVE" | "REDUCE_SPEND" | "RESERVE_BILL" | "AVOID_CREDIT" | "USE_BUFFER" | "TAKE_CREDIT";
  priority: "LOW" | "MEDIUM" | "HIGH";
  amount: number | null;
  message: string;
  reason: string;
}

// ─── Credit Guard ─────────────────────────────────────────────────────────────

/** Matches backend WaterfallStep */
export interface WaterfallStep {
  source: "savings" | "emergency_buffer" | "delay_expense" | "future_income" | "credit";
  amount: number;
  used: boolean;
}

/** Matches backend CreditGuardResult */
export interface CreditGuardResult {
  worker_id: string;
  requested_amount: number;
  buffer_available: number;
  expected_shortfall: number;
  recommended_credit: number;
  safe_monthly_repayment: number;
  decision: "NO_CREDIT_NEEDED" | "PARTIAL_CREDIT" | "FULL_CREDIT" | "CREDIT_DECLINED";
  waterfall: WaterfallStep[];
  message: string;
}

// ─── Dashboard Response ────────────────────────────────────────────────────────

/** Matches backend DashboardResponse */
export interface DashboardResponse {
  worker: WorkerSummary;
  risk: RiskResult;
  forecast: ForecastResult;
  resilience: ResilienceResult;
  obligations: ObligationSummary;
  recommendations: Recommendation[];
}

// ─── Workers List ─────────────────────────────────────────────────────────────

/** Shape returned by GET /workers — same as WorkerSummary */
export type WorkerListItem = WorkerSummary;
