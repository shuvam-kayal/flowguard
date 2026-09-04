import { TrendingUp, AlertTriangle, Shield, BookOpen, CreditCard, ArrowRight } from "lucide-react";
import Link from "next/link";
import type { Recommendation } from "@/types/dashboard";
import { formatINR } from "@/lib/formatters";

// Plain language mapping — no badge clutter
const TYPE_PLAIN: Record<Recommendation["type"], { verb: string; icon: React.ElementType }> = {
  SAVE:         { verb: "Set money aside",    icon: TrendingUp },
  REDUCE_SPEND: { verb: "Reduce spending",    icon: BookOpen },
  RESERVE_BILL: { verb: "Reserve for a bill", icon: Shield },
  AVOID_CREDIT: { verb: "Avoid borrowing",    icon: CreditCard },
  USE_BUFFER:   { verb: "Use your savings",   icon: Shield },
  TAKE_CREDIT:  { verb: "Consider a small loan", icon: CreditCard },
};

interface ActionCenterProps {
  recommendations: Recommendation[];
  shock: boolean;
}

export function ActionCenter({ recommendations, shock }: ActionCenterProps) {
  // Show max 2 most important recommendations
  const topRecs = recommendations.slice(0, 2);

  if (topRecs.length === 0) {
    return (
      <section className="panel flex flex-col items-center justify-center gap-3 py-8 text-center">
        <div className="grid h-10 w-10 place-items-center rounded-full bg-[#f0faf4]">
          <TrendingUp size={18} className="text-[#087344]" />
        </div>
        <p className="text-sm font-semibold text-[#111827]">You're all good!</p>
        <p className="muted max-w-xs text-xs">No urgent actions right now. Keep your spending steady.</p>
      </section>
    );
  }

  return (
    <section
      className={`rounded-xl border p-5 ${
        shock
          ? "border-[#f5c6c2] bg-[#fef5f4]"
          : "border-[#c3e6d3] bg-[#f0faf4]"
      }`}
    >
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg ${shock ? "bg-[#fca5a5]/30" : "bg-[#087344]/10"}`}>
          <AlertTriangle size={15} className={shock ? "text-[#c0392b]" : "text-[#087344]"} />
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-widest text-[#6b7280]">
            {shock ? "Urgent attention needed" : "What to do next"}
          </p>
          <p className="mt-0.5 text-base font-bold text-[#111827]">
            {shock ? "Income dip detected" : "Your top actions"}
          </p>
        </div>
      </div>

      {/* Recommendations — plain, focused */}
      <div className="mt-4 space-y-3">
        {topRecs.map((rec, i) => {
          const meta = TYPE_PLAIN[rec.type] ?? TYPE_PLAIN.SAVE;
          const Icon = meta.icon;
          return (
            <div
              key={i}
              className="rounded-lg bg-white border border-white/80 p-3.5 shadow-sm"
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[#f0faf4]">
                  <Icon size={12} className="text-[#087344]" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#111827]">{rec.message}</p>
                  <p className="mt-0.5 text-xs text-[#6b7280]">{rec.reason}</p>
                  {rec.amount !== null && (
                    <p className="mt-1.5 text-sm font-bold text-[#087344]">
                      {formatINR(rec.amount)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {recommendations.length > 2 && (
        <Link
          href="/resilience"
          className="mt-4 inline-flex items-center gap-1.5 text-xs font-semibold text-[#087344] hover:underline"
        >
          See all {recommendations.length} recommendations <ArrowRight size={12} />
        </Link>
      )}
    </section>
  );
}
