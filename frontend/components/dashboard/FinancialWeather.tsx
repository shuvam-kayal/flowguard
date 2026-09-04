import { Sun, Cloud, CloudRain } from "lucide-react";
import type { ForecastResult } from "@/types/dashboard";
import { formatPercent } from "@/lib/formatters";

const WEATHER_CONFIG = {
  STABLE: {
    icon: Sun,
    label: "Income looks stable",
    detail: "Your earnings are expected to stay consistent in the coming days.",
    color: "text-[#087344]",
    bg: "bg-[#f0faf4]",
  },
  WATCH: {
    icon: Cloud,
    label: "Some ups and downs ahead",
    detail: "Minor changes in your income pattern detected. Keep monitoring.",
    color: "text-[#92580a]",
    bg: "bg-[#fef9ec]",
  },
  SHOCK: {
    icon: CloudRain,
    label: "Income drop expected",
    detail: "Your earnings may fall soon. Your plan has been adjusted to protect essentials.",
    color: "text-[#c0392b]",
    bg: "bg-[#fef5f4]",
  },
} as const;

export function FinancialWeather({ forecast }: { forecast: ForecastResult }) {
  const cfg = WEATHER_CONFIG[forecast.weather] ?? WEATHER_CONFIG.STABLE;
  const Icon = cfg.icon;
  const riskPct = Math.round(forecast.shock_probability * 100);

  return (
    <section className="panel">
      <div className="flex items-start gap-3">
        <div className={`rounded-lg p-2 ${cfg.bg}`}>
          <Icon size={18} className={cfg.color} />
        </div>
        <div className="min-w-0">
          <p className="eyebrow">Income forecast</p>
          <p className={`mt-0.5 text-sm font-semibold ${cfg.color}`}>{cfg.label}</p>
          <p className="mt-1 text-xs text-[#6b7280] leading-relaxed">{cfg.detail}</p>
        </div>
      </div>

      {/* Risk indicator — only show if non-trivial */}
      {riskPct > 10 && (
        <div className="mt-4 flex items-center justify-between rounded-lg bg-[#f9fafb] border border-[#f0f0f0] px-3 py-2 text-xs">
          <span className="text-[#6b7280]">Chance of income drop this month</span>
          <strong className={cfg.color}>{riskPct}%</strong>
        </div>
      )}
    </section>
  );
}
