import type { ResilienceResult } from "@/types/dashboard";

const HEALTH_META: Record<
  string,
  { label: string; description: string; barColor: string; textColor: string; bgColor: string }
> = {
  NORMAL: {
    label: "Finances on track",
    description: "Your income covers your expenses and you have savings growing.",
    barColor: "bg-[#087344]",
    textColor: "text-[#087344]",
    bgColor: "bg-[#f0faf4]",
  },
  WATCH: {
    label: "Keep an eye on spending",
    description: "Your expenses are getting close to your income. Be careful this week.",
    barColor: "bg-[#d97706]",
    textColor: "text-[#92580a]",
    bgColor: "bg-[#fef9ec]",
  },
  SHOCK: {
    label: "Income dip — protect cash",
    description: "Your income has dropped. Focus on essentials only right now.",
    barColor: "bg-[#c0392b]",
    textColor: "text-[#c0392b]",
    bgColor: "bg-[#fef5f4]",
  },
  RECOVERY: {
    label: "Recovering — stay steady",
    description: "Things are improving. Slowly rebuild your savings.",
    barColor: "bg-[#1a56db]",
    textColor: "text-[#1a56db]",
    bgColor: "bg-[#eef3fd]",
  },
};

export function ResilienceScore({ resilience }: { resilience: ResilienceResult }) {
  const { resilience_score: score, resilience_days: days, mode } = resilience;
  const meta = HEALTH_META[mode] ?? HEALTH_META.NORMAL;

  // Interpret score in plain language
  const scoreLabel =
    score >= 75 ? "Strong"
    : score >= 55 ? "Fair"
    : score >= 35 ? "Weak"
    : "Critical";

  return (
    <section className="panel">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="eyebrow">Your financial health</p>
          <p className={`mt-1 text-sm font-semibold ${meta.textColor}`}>
            {meta.label}
          </p>
        </div>
        {/* Score badge — simple, not a conic ring */}
        <div className={`rounded-lg px-3 py-2 text-center ${meta.bgColor}`}>
          <p className={`text-xl font-bold ${meta.textColor}`}>{score}</p>
          <p className={`text-[10px] font-semibold ${meta.textColor}`}>{scoreLabel}</p>
        </div>
      </div>

      {/* Score bar */}
      <div className="mt-4 progress-track">
        <div
          className={`h-full rounded-full transition-all duration-700 ${meta.barColor}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-[#9ca3af]">
        <span>0</span>
        <span>100</span>
      </div>

      {/* Days runway */}
      <div className="mt-4 rounded-lg bg-[#f9fafb] border border-[#f0f0f0] px-4 py-3">
        <p className="text-sm text-[#4b5563]">
          If income stopped today, your savings would cover bills for{" "}
          <strong className="text-[#111827]">{days} days</strong>.
        </p>
      </div>

      {/* Description */}
      <p className="mt-3 text-xs text-[#6b7280]">{meta.description}</p>
    </section>
  );
}
