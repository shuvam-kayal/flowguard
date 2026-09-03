import type { ForecastResult } from "@/types/dashboard";
export function ForecastSummary({ forecast }: { forecast: ForecastResult }) { return <p className="muted">Expected trend: {forecast.trend.toLowerCase()} · Confidence is based on recent income history.</p>; }
