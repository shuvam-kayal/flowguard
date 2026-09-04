"use client";

import { CashFlowChart } from "@/components/dashboard/CashFlowChart";
import { ErrorState } from "@/components/ui/ErrorState";
import { ForecastSkeleton } from "@/components/ui/Skeleton";
import { useScenario } from "@/components/layout/ScenarioProvider";
import { formatINR, formatPercent } from "@/lib/formatters";
import { adaptForecastPoints } from "@/lib/api";
import { TrendingUp, TrendingDown, Minus, Sun, Cloud, CloudRain } from "lucide-react";

const TREND_PLAIN: Record<string, { icon: React.ElementType; label: string; description: string; color: string }> = {
  RISING:    { icon: TrendingUp,   label: "Income is growing",    description: "You have been earning more recently. Keep it up!", color: "text-[#087344]" },
  STABLE:    { icon: Minus,        label: "Income is steady",     description: "Your earnings have been consistent. That's a good sign.", color: "text-[#92580a]" },
  DECLINING: { icon: TrendingDown, label: "Income has dropped",   description: "Your recent earnings are lower than before. Try to take on extra work if you can.", color: "text-[#c0392b]" },
};

const WEATHER_PLAIN: Record<string, { icon: React.ElementType; label: string; bg: string; color: string }> = {
  STABLE: { icon: Sun,       label: "Good outlook",     bg: "bg-[#f0faf4]", color: "text-[#087344]" },
  WATCH:  { icon: Cloud,     label: "Some uncertainty", bg: "bg-[#fef9ec]", color: "text-[#92580a]" },
  SHOCK:  { icon: CloudRain, label: "Income risk",      bg: "bg-[#fef5f4]", color: "text-[#c0392b]" },
};

export default function ForecastPage() {
  const { data, loading, error, refetch } = useScenario();

  if (loading) return <ForecastSkeleton />;
  if (!data || error) {
    return <ErrorState message={error ?? "Unable to load income forecast."} onRetry={refetch} />;
  }

  const { forecast } = data;
  const chartPoints  = adaptForecastPoints(forecast.daily_forecast);
  const trendMeta    = TREND_PLAIN[forecast.trend] ?? TREND_PLAIN.STABLE;
  const weatherMeta  = WEATHER_PLAIN[forecast.weather] ?? WEATHER_PLAIN.STABLE;
  const TrendIcon    = trendMeta.icon;
  const WeatherIcon  = weatherMeta.icon;

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-[#111827] tracking-tight">Income Outlook</h1>
        <p className="mt-1 text-sm text-[#6b7280]">
          Based on your recent gig earnings and spending patterns.
        </p>
      </div>

      {/* ── Trend banner ── */}
      <div className="flex items-start gap-4 rounded-xl border border-[#e5e7eb] bg-white p-4 shadow-sm">
        <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg ${weatherMeta.bg}`}>
          <TrendIcon size={18} className={trendMeta.color} />
        </div>
        <div>
          <p className={`text-base font-bold ${trendMeta.color}`}>{trendMeta.label}</p>
          <p className="mt-0.5 text-sm text-[#6b7280]">{trendMeta.description}</p>
        </div>
      </div>

      {/* ── Three key numbers ── */}
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          {
            label: "Expected in the next 7 days",
            value: formatINR(forecast.next_7_days),
            note: "This week's likely income",
            color: "text-[#111827]",
          },
          {
            label: "Expected this month",
            value: formatINR(forecast.next_30_days),
            note: `Could be between ${formatINR(forecast.lower_bound)} and ${formatINR(forecast.upper_bound)}`,
            color: "text-[#111827]",
          },
          {
            label: "Chance of income drop",
            value: `${Math.round(forecast.shock_probability * 100)}%`,
            note: "Probability of a significant fall this month",
            color: forecast.shock_probability > 0.4 ? "text-[#c0392b]" : forecast.shock_probability > 0.2 ? "text-[#92580a]" : "text-[#087344]",
          },
        ].map(({ label, value, note, color }) => (
          <section key={label} className="panel">
            <p className="eyebrow">{label}</p>
            <p className={`mt-3 text-3xl font-bold ${color}`}>{value}</p>
            <p className="mt-1 text-xs text-[#9ca3af]">{note}</p>
          </section>
        ))}
      </div>

      {/* ── Chart ── */}
      <CashFlowChart points={chartPoints} />

      {/* ── Plain language explanation ── */}
      <section className="panel">
        <div className="flex items-start gap-3">
          <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg ${weatherMeta.bg}`}>
            <WeatherIcon size={16} className={weatherMeta.color} />
          </div>
          <div>
            <p className="text-sm font-bold text-[#111827]">How we estimate your income</p>
            <p className="mt-2 text-sm text-[#6b7280] leading-relaxed">
              We look at your recent gig platform earnings, the time of month, and typical
              patterns for your type of work. The chart shows our best estimate (solid line)
              and a range of possible outcomes (shaded area). Confidence:{" "}
              <strong className="text-[#111827]">{formatPercent(1 - forecast.shock_probability)}</strong>.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
