import { Cloud, CloudRain, Sun } from "lucide-react";
import type { ForecastResult } from "@/types/dashboard";
import { formatPercent } from "@/lib/formatters";

const WEATHER_CONFIG = {
  STABLE: {
    icon:  Sun,
    title: "Stable cash flow",
    desc:  "Your next income window remains manageable.",
    ringColor: "#23aa6b",
    textColor: "text-[#087344]",
  },
  WATCH: {
    icon:  Cloud,
    title: "Elevated volatility",
    desc:  "Minor income fluctuation detected. Monitor closely.",
    ringColor: "#e8a838",
    textColor: "text-[#b66b0b]",
  },
  SHOCK: {
    icon:  CloudRain,
    title: "Income dip expected",
    desc:  "Your plan has adjusted to protect essentials.",
    ringColor: "#b93a3a",
    textColor: "text-[#b93a3a]",
  },
} as const;

export function FinancialWeather({ forecast }: { forecast: ForecastResult }) {
  const cfg = WEATHER_CONFIG[forecast.weather] ?? WEATHER_CONFIG.STABLE;
  const Icon = cfg.icon;
  const shockPct = Math.min(100, Math.round(forecast.shock_probability * 100));

  return (
    <section className="panel">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="eyebrow">Financial weather</p>
          <h2 className="mt-2 text-base font-bold">{cfg.title}</h2>
        </div>
        <Icon size={32} className={cfg.textColor} />
      </div>
      <p className="muted mt-2 text-xs">{cfg.desc}</p>

      {/* Shock probability bar */}
      <div className="mt-4">
        <div className="progress-track">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${shockPct}%`, background: cfg.ringColor }}
          />
        </div>
        <div className="mt-1.5 flex justify-between text-xs text-[#718078]">
          <span>30-day shock probability</span>
          <strong className={cfg.textColor}>{formatPercent(forecast.shock_probability)}</strong>
        </div>
      </div>
    </section>
  );
}
