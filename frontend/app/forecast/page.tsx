"use client";

import { CashFlowChart } from "@/components/dashboard/CashFlowChart";
import { ErrorState } from "@/components/ui/ErrorState";
import { ForecastSkeleton } from "@/components/ui/Skeleton";
import { useScenario } from "@/components/layout/ScenarioProvider";
import { formatINR, formatPercent } from "@/lib/formatters";
import { adaptForecastPoints } from "@/lib/api";
import { TrendingUp, TrendingDown, Minus, Cloud, CloudRain, Sun } from "lucide-react";

const TREND_META = {
  RISING:   { icon: TrendingUp,   color: "text-[#087344]", label: "Rising",   pill: "status-pill-green" },
  STABLE:   { icon: Minus,        color: "text-[#b66b0b]", label: "Stable",   pill: "status-pill-amber" },
  DECLINING:{ icon: TrendingDown, color: "text-[#b93a3a]", label: "Declining",pill: "status-pill-red" },
} as const;

const WEATHER_META = {
  STABLE:  { icon: Sun,       label: "Clear skies",     pill: "status-pill-green", desc: "Your income outlook is steady." },
  WATCH:   { icon: Cloud,     label: "Watch",           pill: "status-pill-amber", desc: "Minor volatility detected." },
  SHOCK:   { icon: CloudRain, label: "Income shock",    pill: "status-pill-red",   desc: "Significant income dip ahead." },
} as const;

export default function ForecastPage() {
  const { data, loading, error, refetch } = useScenario();

  if (loading) return <ForecastSkeleton />;
  if (!data || error) {
    return <ErrorState message={error ?? "No forecast data found."} onRetry={refetch} />;
  }

  const { forecast } = data;
  const chartPoints = adaptForecastPoints(forecast.daily_forecast);
  const trendMeta   = TREND_META[forecast.trend] ?? TREND_META.STABLE;
  const weatherMeta = WEATHER_META[forecast.weather] ?? WEATHER_META.STABLE;
  const TrendIcon   = trendMeta.icon;
  const WeatherIcon = weatherMeta.icon;

  const stats = [
    {
      label: "Next 7 days",
      value: formatINR(forecast.next_7_days),
      sub:   "Expected income",
      icon:  TrendIcon,
      iconColor: trendMeta.color,
    },
    {
      label: "Next 30 days",
      value: formatINR(forecast.next_30_days),
      sub:   `Range: ${formatINR(forecast.lower_bound)} – ${formatINR(forecast.upper_bound)}`,
      icon:  TrendIcon,
      iconColor: trendMeta.color,
    },
    {
      label: "Shock probability",
      value: formatPercent(forecast.shock_probability),
      sub:   "30-day risk estimate",
      icon:  WeatherIcon,
      iconColor: forecast.shock_probability > 0.5 ? "text-[#b93a3a]" : "text-[#b66b0b]",
    },
  ];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <p className="eyebrow">Financial forecast</p>
      <h1 className="mt-1 text-3xl font-extrabold tracking-tight">
        What's likely to happen to your income?
      </h1>
      <p className="muted mt-2">Predictions are probability estimates, not guarantees.</p>

      {/* Weather + Trend badges */}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <span className={weatherMeta.pill}>
          <WeatherIcon size={11} className="mr-1 inline" />
          {weatherMeta.label}
        </span>
        <span className={trendMeta.pill}>
          <TrendIcon size={11} className="mr-1 inline" />
          {forecast.trend.charAt(0) + forecast.trend.slice(1).toLowerCase()}
        </span>
      </div>

      {/* Stat cards */}
      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        {stats.map(({ label, value, sub, icon: Icon, iconColor }) => (
          <section key={label} className="stat-card animate-slide-up">
            <div className="flex items-center justify-between">
              <p className="eyebrow">{label}</p>
              <Icon size={18} className={iconColor} />
            </div>
            <p className="mt-3 text-2xl font-extrabold">{value}</p>
            <p className="muted text-xs mt-1">{sub}</p>
          </section>
        ))}
      </div>

      {/* Chart */}
      <div className="mt-5">
        <CashFlowChart points={chartPoints} />
      </div>

      {/* Outlook explanation */}
      <section className="panel mt-5 animate-slide-up">
        <div className="flex items-start gap-4">
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#f1faf4]">
            <WeatherIcon size={18} className={forecast.weather === "SHOCK" ? "text-[#b93a3a]" : "text-[#087344]"} />
          </div>
          <div>
            <p className="eyebrow">Why this outlook?</p>
            <h2 className="mt-1 text-base font-bold">
              {forecast.trend === "DECLINING"
                ? "Income volatility is increasing."
                : forecast.trend === "RISING"
                ? "Your income is building momentum."
                : "Your recent income pattern is stabilising."}
            </h2>
            <p className="muted mt-2">
              {weatherMeta.desc} FlowGuard compares recent gig income with your normal earning
              range and upcoming obligations. Confidence:{" "}
              <strong>{formatPercent(1 - forecast.shock_probability)}</strong>.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
