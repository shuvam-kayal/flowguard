"use client";

import { useScenario } from "@/components/layout/ScenarioProvider";
import { ErrorState } from "@/components/ui/ErrorState";
import { ResilienceSkeleton } from "@/components/ui/Skeleton";
import { formatINR } from "@/lib/formatters";
import type { ScoreBreakdown } from "@/types/dashboard";

const SCORE_PLAIN: Record<keyof ScoreBreakdown, { label: string; description: string }> = {
  income_stability:    { label: "Income stability",    description: "How consistent your earnings have been" },
  emergency_buffer:    { label: "Emergency savings",   description: "How much you have saved for tough times" },
  expense_coverage:    { label: "Bill coverage",       description: "Whether your income covers all your bills" },
  debt_burden:         { label: "Debt level",          description: "How manageable your loans and EMIs are" },
  savings_consistency: { label: "Saving habits",       description: "How regularly you save money" },
};

const MODE_PLAIN: Record<string, { label: string; description: string; bg: string; border: string; color: string }> = {
  NORMAL:   { label: "Your finances are on track", description: "You're covering your bills and building a safety net. Keep going.", bg: "bg-[#f0faf4]", border: "border-[#c3e6d3]", color: "text-[#087344]" },
  WATCH:    { label: "Keep an eye on spending", description: "Your expenses are rising. Try to reduce non-essential spending this week.", bg: "bg-[#fef9ec]", border: "border-[#f0d080]", color: "text-[#92580a]" },
  SHOCK:    { label: "Income is low — be careful", description: "Your income has dropped significantly. Focus on essential expenses only.", bg: "bg-[#fef5f4]", border: "border-[#f5c6c2]", color: "text-[#c0392b]" },
  RECOVERY: { label: "Things are getting better", description: "Your income is recovering. Slowly start rebuilding your savings.", bg: "bg-[#eef3fd]", border: "border-[#c3d4f7]", color: "text-[#1a56db]" },
};

function scoreColor(val: number) {
  if (val >= 70) return "bg-[#087344]";
  if (val >= 50) return "bg-[#d97706]";
  return "bg-[#c0392b]";
}

function scoreWord(val: number) {
  if (val >= 75) return "Strong";
  if (val >= 55) return "Fair";
  if (val >= 35) return "Weak";
  return "Critical";
}

export default function ResiliencePage() {
  const { data, loading, error, refetch } = useScenario();

  if (loading) return <ResilienceSkeleton />;
  if (!data || error) {
    return <ErrorState message={error ?? "Unable to load safety net data."} onRetry={refetch} />;
  }

  const { resilience } = data;
  const {
    resilience_score, resilience_days,
    safe_to_spend_daily,
    buffer_current, buffer_target, recommended_save,
    mode, wallet_allocation, score_breakdown,
  } = resilience;

  const bufferPct  = Math.min(100, Math.round((buffer_current / buffer_target) * 100));
  const modeMeta   = MODE_PLAIN[mode] ?? MODE_PLAIN.NORMAL;

  const walletItems = [
    { label: "Daily spending",   value: wallet_allocation.daily,  color: "#087344", pct: 0 },
    { label: "Bills & EMIs",     value: wallet_allocation.bills,  color: "#d97706", pct: 0 },
    { label: "Savings top-up",   value: wallet_allocation.buffer, color: "#1a56db", pct: 0 },
    { label: "Growth savings",   value: wallet_allocation.growth, color: "#6b7280", pct: 0 },
  ];
  const walletTotal = walletItems.reduce((s, i) => s + i.value, 0);
  walletItems.forEach(i => { i.pct = walletTotal > 0 ? Math.round((i.value / walletTotal) * 100) : 0; });

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-[#111827] tracking-tight">Your Safety Net</h1>
        <p className="mt-1 text-sm text-[#6b7280]">
          How well you're protected if your income slows down or stops.
        </p>
      </div>

      {/* ── Status banner ── */}
      <div className={`rounded-xl border ${modeMeta.bg} ${modeMeta.border} px-5 py-4`}>
        <p className={`text-sm font-bold ${modeMeta.color}`}>{modeMeta.label}</p>
        <p className="mt-1 text-sm text-[#4b5563]">{modeMeta.description}</p>
      </div>

      {/* ── Score + Runway ── */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Health score */}
        <section className="panel space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="eyebrow">Financial health score</p>
              <p className="mt-1 text-3xl font-bold text-[#111827]">
                {resilience_score} <span className="text-base font-normal text-[#9ca3af]">/ 100</span>
              </p>
              <p className="mt-0.5 text-sm text-[#6b7280]">
                {scoreWord(resilience_score)} — {resilience_days} days of runway
              </p>
            </div>
          </div>

          {/* Overall bar */}
          <div>
            <div className="progress-track">
              <div
                className={`h-full rounded-full transition-all duration-700 ${scoreColor(resilience_score)}`}
                style={{ width: `${resilience_score}%` }}
              />
            </div>
          </div>

          {/* Detailed breakdown */}
          <div className="space-y-3 pt-2">
            {(Object.entries(score_breakdown) as [keyof ScoreBreakdown, number][]).map(([key, val]) => {
              const plain = SCORE_PLAIN[key];
              return (
                <div key={key}>
                  <div className="flex items-center justify-between mb-1">
                    <div>
                      <span className="text-sm text-[#374151]">{plain.label}</span>
                    </div>
                    <span className={`text-xs font-semibold ${val >= 70 ? "text-[#087344]" : val >= 50 ? "text-[#92580a]" : "text-[#c0392b]"}`}>
                      {scoreWord(val)}
                    </span>
                  </div>
                  <div className="progress-track-sm">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${scoreColor(val)}`}
                      style={{ width: `${val}%` }}
                    />
                  </div>
                  <p className="mt-0.5 text-[10px] text-[#9ca3af]">{plain.description}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Buffer + Wallet */}
        <div className="space-y-4">
          {/* Emergency savings */}
          <section className="panel space-y-3">
            <p className="eyebrow">Emergency savings</p>
            <div className="flex items-baseline justify-between">
              <p className="text-2xl font-bold text-[#111827]">{formatINR(buffer_current)}</p>
              <p className="text-sm text-[#9ca3af]">goal: {formatINR(buffer_target)}</p>
            </div>
            <div className="progress-track">
              <div className="progress-fill-green" style={{ width: `${bufferPct}%` }} />
            </div>
            <p className="text-sm text-[#6b7280]">
              You've reached <strong className="text-[#111827]">{bufferPct}%</strong> of your safety goal.
            </p>
            <div className="rounded-lg bg-[#f0faf4] border border-[#c3e6d3] px-4 py-3">
              <p className="text-xs font-semibold text-[#087344]">Suggested this week</p>
              <p className="mt-1 text-sm text-[#374151]">
                Try to save <strong>{formatINR(recommended_save)}</strong> to reach your goal faster.
              </p>
            </div>
          </section>

          {/* How your money is split */}
          <section className="panel space-y-3">
            <div>
              <p className="eyebrow">How your income is split</p>
              <p className="mt-1 text-xs text-[#9ca3af]">Out of {formatINR(walletTotal)} monthly income</p>
            </div>
            {walletItems.map(({ label, value, color, pct }) => (
              <div key={label}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-[#374151]">{label}</span>
                  <span className="text-sm font-semibold text-[#111827]">{formatINR(value)}</span>
                </div>
                <div className="progress-track-sm">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, background: color }}
                  />
                </div>
              </div>
            ))}
          </section>
        </div>
      </div>
    </div>
  );
}
