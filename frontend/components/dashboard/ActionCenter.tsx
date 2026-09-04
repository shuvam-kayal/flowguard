import { ArrowRight, AlertTriangle, TrendingUp, BookOpen, CreditCard, Shield } from "lucide-react";
import Link from "next/link";
import type { Recommendation } from "@/types/dashboard";
import { formatINR } from "@/lib/formatters";

const TYPE_META: Record<
  Recommendation["type"],
  { label: string; icon: React.ElementType; pillClass: string }
> = {
  SAVE:          { label: "Save",         icon: TrendingUp,    pillClass: "status-pill-green" },
  REDUCE_SPEND:  { label: "Reduce Spend", icon: BookOpen,      pillClass: "status-pill-amber" },
  RESERVE_BILL:  { label: "Reserve Bill", icon: BookOpen,      pillClass: "status-pill-blue" },
  AVOID_CREDIT:  { label: "Avoid Credit", icon: CreditCard,    pillClass: "status-pill-red" },
  USE_BUFFER:    { label: "Use Buffer",   icon: Shield,        pillClass: "status-pill-amber" },
  TAKE_CREDIT:   { label: "Take Credit",  icon: CreditCard,    pillClass: "status-pill-blue" },
};

const PRIORITY_COLORS: Record<Recommendation["priority"], string> = {
  HIGH:   "text-[#b93a3a]",
  MEDIUM: "text-[#b66b0b]",
  LOW:    "text-[#087344]",
};

interface ActionCenterProps {
  recommendations: Recommendation[];
  shock: boolean;
}

export function ActionCenter({ recommendations, shock }: ActionCenterProps) {
  return (
    <section
      className={`animate-slide-up rounded-2xl border p-6 transition-colors ${
        shock
          ? "border-[#efc5c5] bg-[#fff6f6]"
          : "border-[#d5eadb] bg-[#f5fbf6]"
      }`}
    >
      <div className="flex items-start gap-3">
        <AlertTriangle
          size={20}
          className={shock ? "mt-0.5 text-[#b93a3a]" : "mt-0.5 text-[#087344]"}
        />
        <div>
          <p className="eyebrow">{shock ? "⚠ Alert" : "Action center"}</p>
          <h2 className="mt-1 text-lg font-extrabold">
            {shock ? "Income dip detected" : "Your next best actions"}
          </h2>
        </div>
      </div>

      <div className="mt-5 space-y-4">
        {recommendations.map((rec, i) => {
          const meta = TYPE_META[rec.type] ?? TYPE_META.SAVE;
          const Icon = meta.icon;
          return (
            <div
              key={i}
              className="flex items-start gap-3 rounded-xl bg-white/60 p-3 ring-1 ring-white/80"
            >
              <div className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-white shadow-sm">
                <Icon size={13} className="text-[#087344]" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-bold">{rec.message}</p>
                  <span className={`${meta.pillClass} shrink-0`}>{meta.label}</span>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wide ${PRIORITY_COLORS[rec.priority]}`}
                  >
                    {rec.priority}
                  </span>
                </div>
                <p className="muted mt-0.5">{rec.reason}</p>
                {rec.amount !== null && (
                  <p className="mt-1 text-sm font-extrabold text-[#087344]">
                    {formatINR(rec.amount)}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <Link href="/resilience" className="btn-primary mt-5 inline-flex items-center gap-1 text-sm">
        Review full plan <ArrowRight size={14} />
      </Link>
    </section>
  );
}
