import type { RiskResult, RiskFactor } from "@/types/dashboard";

const LEVEL_META: Record<
  string,
  { label: string; pillClass: string; ringColor: string }
> = {
  LOW:      { label: "Low",      pillClass: "status-pill-green", ringColor: "#23aa6b" },
  MODERATE: { label: "Moderate", pillClass: "status-pill-amber", ringColor: "#e8a838" },
  HIGH:     { label: "High",     pillClass: "status-pill-red",   ringColor: "#b93a3a" },
};

function humanize(feature: string): string {
  return feature.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function RiskCard({ risk }: { risk: RiskResult }) {
  const { risk_level, risk_score, confidence, top_factors } = risk;
  const meta = LEVEL_META[risk_level] ?? LEVEL_META.MODERATE;
  const pct = Math.round(risk_score * 100);

  // Sort by impact magnitude descending (copy to avoid mutation).
  const sorted = [...top_factors].sort((a, b) => b.impact - a.impact);

  return (
    <section className="panel animate-fade-in">
      <div className="mb-1 flex items-center justify-between">
        <p className="eyebrow">Risk assessment</p>
        <span className={meta.pillClass}>{meta.label}</span>
      </div>

      <div className="mt-4 flex items-center gap-5">
        {/* Conic gradient ring (mirrors ResilienceScore) */}
        <div
          className="grid h-24 w-24 shrink-0 place-items-center rounded-full transition-all duration-700"
          style={{
            background: `conic-gradient(${meta.ringColor} ${pct}%, #edf2ee 0)`,
          }}
        >
          <div className="grid h-[74px] w-[74px] place-items-center rounded-full bg-white text-xl font-extrabold text-[#16231a]">
            {pct}%
          </div>
        </div>
        <div>
          <p className="text-base font-extrabold">{pct}% distress probability</p>
          <p className="muted">
            {Math.round(confidence * 100)}% model confidence
          </p>
        </div>
      </div>

      {/* Top contributing factors */}
      {sorted.length > 0 && (
        <div className="mt-4 space-y-2">
          <p className="text-xs font-bold uppercase tracking-wide text-[#718078]">
            Top factors
          </p>
          {sorted.map((factor: RiskFactor) => {
            const isRisk = factor.direction === "increases_risk";
            return (
              <div
                key={factor.feature}
                className="flex items-center justify-between rounded-lg bg-[#f6f8f5] px-3 py-2 text-sm"
              >
                <span className="font-medium text-[#16231a]">
                  {humanize(factor.feature)}
                </span>
                <span
                  className={`font-bold ${
                    isRisk ? "text-[#b93a3a]" : "text-[#087344]"
                  }`}
                >
                  {isRisk ? "+" : "−"}{factor.impact.toFixed(3)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
