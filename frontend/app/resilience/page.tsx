"use client";

import { useScenario } from "@/components/layout/ScenarioProvider";
import { ErrorState } from "@/components/ui/ErrorState";
import { ResilienceSkeleton } from "@/components/ui/Skeleton";
import { formatINR } from "@/lib/formatters";
import type { ScoreBreakdown } from "@/types/dashboard";

const SCORE_LABELS: Record<keyof ScoreBreakdown, string> = {
  income_stability:    "Income stability",
  emergency_buffer:    "Emergency buffer",
  expense_coverage:    "Expense coverage",
  debt_burden:         "Debt burden",
  savings_consistency: "Savings consistency",
};

const MODE_BANNER: Record<
  string,
  { bg: string; border: string; text: string; desc: string }
> = {
  NORMAL:   { bg: "bg-[#f1faf4]",  border: "border-[#b9dfc8]", text: "text-[#087344]", desc: "Your finances are on track." },
  WATCH:    { bg: "bg-[#fff8ed]",  border: "border-[#f3cc8d]", text: "text-[#9a570a]", desc: "Keep an eye on expenses." },
  SHOCK:    { bg: "bg-[#fff6f6]",  border: "border-[#efc5c5]", text: "text-[#b93a3a]", desc: "Income dip detected. Conserve cash." },
  RECOVERY: { bg: "bg-[#eff5fe]",  border: "border-[#b6cef7]", text: "text-[#1a56db]", desc: "Income recovering. Rebuild gradually." },
};

export default function ResiliencePage() {
  const { data, loading, error, refetch } = useScenario();

  if (loading) return <ResilienceSkeleton />;
  if (!data || error) {
    return <ErrorState message={error ?? "No resilience data found."} onRetry={refetch} />;
  }

  const { resilience } = data;
  const {
    resilience_score, resilience_days,
    safe_to_spend_daily,
    buffer_current, buffer_target, recommended_save,
    mode, wallet_allocation, score_breakdown,
  } = resilience;

  const bufferPct   = Math.min(100, Math.round((buffer_current / buffer_target) * 100));
  const bannerMeta  = MODE_BANNER[mode] ?? MODE_BANNER.NORMAL;

  const walletItems = [
    { label: "Daily discretionary", value: wallet_allocation.daily,  color: "#087344" },
    { label: "Bills & obligations",  value: wallet_allocation.bills,  color: "#b66b0b" },
    { label: "Buffer top-up",        value: wallet_allocation.buffer, color: "#1a56db" },
    { label: "Growth / savings",     value: wallet_allocation.growth, color: "#23aa6b" },
  ];
  const walletTotal = walletItems.reduce((s, i) => s + i.value, 0);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <p className="eyebrow">Resilience</p>
      <h1 className="mt-1 text-3xl font-extrabold tracking-tight">
        Your financial shock absorber
      </h1>
      <p className="muted mt-2">
        How long your current buffer can cover essential expenses.
      </p>

      {/* Mode banner */}
      <div className={`mt-5 rounded-2xl border ${bannerMeta.bg} ${bannerMeta.border} px-5 py-4`}>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-extrabold ${bannerMeta.text} uppercase tracking-wide`}>
            {mode}
          </span>
          <span className="text-sm text-[#718078]">·</span>
          <span className="text-sm text-[#526158]">{bannerMeta.desc}</span>
        </div>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        {/* Score card */}
        <section className="panel">
          <div className="flex items-center gap-6">
            {/* Score ring */}
            <div
              className="grid h-32 w-32 shrink-0 place-items-center rounded-full transition-all duration-700"
              style={{
                background: `conic-gradient(${
                  resilience_score >= 70 ? "#23aa6b"
                  : resilience_score >= 55 ? "#e8a838"
                  : "#b93a3a"
                } ${resilience_score}%, #edf2ee 0)`,
              }}
            >
              <div className="grid h-[100px] w-[100px] place-items-center rounded-full bg-white text-3xl font-extrabold text-[#16231a]">
                {resilience_score}
              </div>
            </div>
            <div>
              <p className="eyebrow">Resilience score</p>
              <h2 className="mt-1 text-xl font-extrabold">{resilience_days} days of runway</h2>
              <p className="muted mt-1">
                Essential expenses covered for approx. this long.
              </p>
              <p className="mt-2 text-sm">
                Safe to spend:{" "}
                <strong className="text-[#087344]">{formatINR(safe_to_spend_daily)}/day</strong>
              </p>
            </div>
          </div>

          {/* Score breakdown bars */}
          <div className="mt-7 space-y-3">
            {(Object.entries(score_breakdown) as [keyof ScoreBreakdown, number][]).map(
              ([key, val]) => (
                <div key={key}>
                  <div className="flex justify-between text-sm">
                    <span className="text-[#526158]">{SCORE_LABELS[key]}</span>
                    <strong className="text-[#16231a]">{val}</strong>
                  </div>
                  <div className="progress-track mt-1">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        val >= 70 ? "bg-[#23aa6b]"
                        : val >= 50 ? "bg-[#e8a838]"
                        : "bg-[#b93a3a]"
                      }`}
                      style={{ width: `${val}%` }}
                    />
                  </div>
                </div>
              )
            )}
          </div>
        </section>

        {/* Buffer + Wallet allocation */}
        <div className="flex flex-col gap-5">
          <section className="panel">
            <p className="eyebrow">Emergency buffer</p>
            <div className="mt-2 flex items-end justify-between">
              <h2 className="text-2xl font-extrabold">
                {formatINR(buffer_current)}{" "}
                <span className="text-base font-normal text-[#718078]">
                  / {formatINR(buffer_target)}
                </span>
              </h2>
              <span className="text-sm font-bold text-[#087344]">{bufferPct}%</span>
            </div>
            <div className="progress-track mt-3">
              <div className="progress-fill-green" style={{ width: `${bufferPct}%` }} />
            </div>
            <p className="muted mt-3">{bufferPct}% of your target emergency buffer.</p>

            <div className="mt-5 rounded-xl bg-[#f1faf4] border border-[#c9e8d4] p-4">
              <p className="text-xs font-bold text-[#087344]">Recommended this week</p>
              <p className="mt-1 text-sm">
                Save{" "}
                <strong className="text-[#087344]">{formatINR(recommended_save)}</strong>{" "}
                to accelerate buffer recovery.
              </p>
            </div>
          </section>

          {/* Wallet allocation */}
          <section className="panel">
            <p className="eyebrow">Wallet allocation</p>
            <p className="muted mt-1">How your income is distributed each month</p>
            <div className="mt-5 space-y-3">
              {walletItems.map(({ label, value, color }) => {
                const pct = walletTotal > 0 ? Math.round((value / walletTotal) * 100) : 0;
                return (
                  <div key={label}>
                    <div className="flex justify-between text-sm">
                      <span className="text-[#526158]">{label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-[#718078]">{pct}%</span>
                        <strong style={{ color }}>{formatINR(value)}</strong>
                      </div>
                    </div>
                    <div className="progress-track mt-1">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, background: color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
