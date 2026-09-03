export type Scenario = "NORMAL" | "INCOME_SHOCK" | "RECOVERY";
export type RiskLevel = "LOW" | "MODERATE" | "HIGH";

export interface Worker { id: string; name: string; occupation: string; monthlyIncome: number; balance: number; }
export interface RiskFactor { feature: string; impact: number; direction: "increases_risk" | "decreases_risk"; }
export interface RiskResult { risk_score: number; risk_level: RiskLevel; confidence: number; top_factors: RiskFactor[]; }
export interface ForecastPoint { label: string; historical?: number; forecast: number; lower: number; upper: number; }
export interface ForecastResult { next_7_days: number; next_30_days: number; trend: "RISING" | "STABLE" | "DECLINING"; shock_probability: number; weather: "STABLE" | "WATCH" | "SHOCK" | "RECOVERY"; points: ForecastPoint[]; }
export interface ResilienceResult { resilience_score: number; resilience_days: number; safe_to_spend_daily: number; buffer_current: number; buffer_target: number; mode: Scenario; factors: Array<{ label: string; value: number }>; }
export interface Obligation { name: string; amount: number; dueIn: string; }
export interface Recommendation { title: string; description: string; type: "SAVE" | "PAUSE" | "SPEND" | "MAINTAIN"; }
export interface Transaction { date: string; description: string; category: string; type: "Income" | "Expense" | "Bills"; amount: number; }
export interface DashboardData { scenario: Scenario; worker: Worker; risk: RiskResult; forecast: ForecastResult; resilience: ResilienceResult; obligations: Obligation[]; recommendations: Recommendation[]; transactions: Transaction[]; }
