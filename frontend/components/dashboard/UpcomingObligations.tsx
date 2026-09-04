import type { ObligationSummary } from "@/types/dashboard";
import { formatINR } from "@/lib/formatters";
import { daysUntil } from "@/lib/api";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function UpcomingObligations({ summary }: { summary: ObligationSummary }) {
  const obligations = summary.upcoming_obligations.slice(0, 3); // Show top 3 on dashboard

  return (
    <section className="panel">
      <div className="mb-4 flex items-center justify-between">
        <p className="eyebrow">Upcoming bills</p>
        <span className="text-sm font-bold text-[#c0392b]">
          {formatINR(summary.total_upcoming)} due
        </span>
      </div>

      {obligations.length === 0 ? (
        <p className="py-4 text-center text-sm text-[#9ca3af]">
          No upcoming bills tracked yet.
        </p>
      ) : (
        <div className="space-y-1">
          {obligations.map((item) => {
            const days = daysUntil(item.due_date);
            const urgent = days <= 5;
            return (
              <div
                key={`${item.name}-${item.due_date}`}
                className="flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-[#f9fafb] transition-colors"
              >
                <div>
                  <p className="text-sm font-semibold text-[#111827]">{item.name}</p>
                  <p className={`text-xs mt-0.5 ${urgent ? "text-[#c0392b] font-semibold" : "text-[#9ca3af]"}`}>
                    {days === 0 ? "Due today!" : urgent ? `Due in ${days} days — urgent` : `Due in ${days} days`}
                  </p>
                </div>
                <strong className="text-sm text-[#111827]">{formatINR(item.amount)}</strong>
              </div>
            );
          })}
        </div>
      )}

      {summary.upcoming_obligations.length > 3 && (
        <Link
          href="/transactions"
          className="mt-3 flex items-center gap-1.5 text-xs font-semibold text-[#087344] hover:underline"
        >
          View all {summary.upcoming_obligations.length} bills <ArrowRight size={12} />
        </Link>
      )}
    </section>
  );
}
