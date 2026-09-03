import type { ObligationSummary } from "@/types/dashboard";
import { formatINR } from "@/lib/formatters";
import { daysUntil } from "@/lib/api";
import { Calendar } from "lucide-react";

const CATEGORY_COLORS: Record<string, string> = {
  FIXED:   "bg-[#e8f0fe] text-[#1a56db]",
  DEBT:    "bg-[#fde8e8] text-[#9b2c2c]",
  UTILITY: "bg-[#fff0d6] text-[#9a570a]",
  OTHER:   "bg-[#edf2ee] text-[#526158]",
};

export function UpcomingObligations({ summary }: { summary: ObligationSummary }) {
  return (
    <section className="panel">
      <div className="mb-4 flex items-center justify-between">
        <p className="eyebrow">Upcoming obligations</p>
        <span className="text-sm font-bold text-[#087344]">
          {formatINR(summary.total_upcoming)} total
        </span>
      </div>

      <div className="divide-y divide-[#edf1ee]">
        {summary.upcoming_obligations.map((item) => {
          const days = daysUntil(item.due_date);
          const urgent = days <= 5;
          const catClass = CATEGORY_COLORS[item.category] ?? CATEGORY_COLORS.OTHER;
          return (
            <div
              key={`${item.name}-${item.due_date}`}
              className="flex items-center justify-between py-3"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`grid h-7 w-7 shrink-0 place-items-center rounded-full ${catClass.split(" ")[0]}`}
                >
                  <Calendar size={13} className={catClass.split(" ")[1]} />
                </div>
                <div>
                  <p className="text-sm font-bold">{item.name}</p>
                  <p className={`text-xs ${urgent ? "text-[#b93a3a] font-semibold" : "text-[#718078]"}`}>
                    {days === 0 ? "Due today" : `Due in ${days} day${days === 1 ? "" : "s"}`}
                  </p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <strong className="text-sm">{formatINR(item.amount)}</strong>
                <span className={`status-pill ${catClass}`}>{item.category}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 rounded-xl bg-[#f6f8f5] px-4 py-3">
        <p className="text-xs text-[#718078]">
          Essential daily spend:{" "}
          <strong className="text-[#16231a]">
            {formatINR(summary.essential_daily_spend)}/day
          </strong>
        </p>
      </div>
    </section>
  );
}
