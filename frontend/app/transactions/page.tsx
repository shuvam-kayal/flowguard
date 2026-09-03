"use client";

import { useState } from "react";
import { useScenario } from "@/components/layout/ScenarioProvider";
import { ErrorState } from "@/components/ui/ErrorState";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { formatINR } from "@/lib/formatters";
import { daysUntil } from "@/lib/api";
import { Calendar, Clock, TrendingDown, WalletCards } from "lucide-react";

type FilterCategory = "All" | "FIXED" | "DEBT" | "UTILITY" | "OTHER";

const CATEGORY_PILL: Record<string, string> = {
  FIXED:   "status-pill bg-[#e8f0fe] text-[#1a56db]",
  DEBT:    "status-pill bg-[#fde8e8] text-[#9b2c2c]",
  UTILITY: "status-pill bg-[#fff0d6] text-[#9a570a]",
  OTHER:   "status-pill bg-[#edf2ee] text-[#526158]",
};

export default function TransactionsPage() {
  const { data, loading, error, refetch } = useScenario();
  const [filter, setFilter] = useState<FilterCategory>("All");

  if (loading) return <TableSkeleton rows={6} />;
  if (!data || error) {
    return <ErrorState message={error ?? "No transaction data found."} onRetry={refetch} />;
  }

  const { obligations, resilience, forecast } = data;
  const filtered = obligations.upcoming_obligations.filter(
    (o) => filter === "All" || o.category === filter
  );

  const filterTabs: FilterCategory[] = ["All", "FIXED", "DEBT", "UTILITY", "OTHER"];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <p className="eyebrow">Transactions &amp; Obligations</p>
      <h1 className="mt-1 text-3xl font-extrabold tracking-tight">
        Know where your money flows
      </h1>
      <p className="muted mt-2">
        Upcoming financial obligations tracked by FlowGuard's resilience plan.
      </p>

      {/* Summary stats */}
      <div className="mt-5 grid gap-4 sm:grid-cols-3">
        <section className="stat-card">
          <div className="flex items-center justify-between">
            <p className="eyebrow">Total upcoming</p>
            <TrendingDown size={16} className="text-[#b93a3a]" />
          </div>
          <p className="mt-3 text-2xl font-extrabold">
            {formatINR(obligations.total_upcoming)}
          </p>
          <p className="muted text-xs mt-1">Across {obligations.upcoming_obligations.length} obligations</p>
        </section>

        <section className="stat-card">
          <div className="flex items-center justify-between">
            <p className="eyebrow">Daily essential</p>
            <Clock size={16} className="text-[#b66b0b]" />
          </div>
          <p className="mt-3 text-2xl font-extrabold">
            {formatINR(obligations.essential_daily_spend)}
            <span className="text-sm font-normal text-[#718078]">/day</span>
          </p>
          <p className="muted text-xs mt-1">Minimum spend to cover essentials</p>
        </section>

        <section className="stat-card">
          <div className="flex items-center justify-between">
            <p className="eyebrow">Safe to spend</p>
            <WalletCards size={16} className="text-[#087344]" />
          </div>
          <p className="mt-3 text-2xl font-extrabold text-[#087344]">
            {formatINR(resilience.safe_to_spend_daily)}
            <span className="text-sm font-normal text-[#718078]">/day</span>
          </p>
          <p className="muted text-xs mt-1">After all obligations covered</p>
        </section>
      </div>

      {/* Filter tabs */}
      <div className="mt-6 flex flex-wrap gap-2">
        {filterTabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`rounded-full px-4 py-1.5 text-xs font-bold transition-all duration-150 ${
              filter === tab
                ? "bg-[#087344] text-white shadow-sm"
                : "bg-white text-[#526158] ring-1 ring-[#e4ebe5] hover:ring-[#b9dfc8]"
            }`}
          >
            {tab === "All" ? "All" : tab.charAt(0) + tab.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Obligations table */}
      <section className="panel mt-4 overflow-x-auto">
        <table className="w-full min-w-[520px] text-left text-sm">
          <thead className="border-b border-[#e4ebe5] text-[11px] uppercase tracking-wider text-[#718078]">
            <tr>
              <th className="pb-3 pr-4">Obligation</th>
              <th className="pb-3 pr-4">Category</th>
              <th className="pb-3 pr-4">Due date</th>
              <th className="pb-3 text-right">Amount</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-10 text-center text-[#718078]">
                  No obligations in this category.
                </td>
              </tr>
            ) : (
              filtered.map((ob) => {
                const days   = daysUntil(ob.due_date);
                const urgent = days <= 5;
                return (
                  <tr
                    key={`${ob.name}-${ob.due_date}`}
                    className="border-b border-[#edf1ee] last:border-0 hover:bg-[#fafcfa] transition-colors"
                  >
                    <td className="py-4 pr-4">
                      <div className="flex items-center gap-2">
                        <Calendar size={14} className="text-[#718078]" />
                        <span className="font-bold">{ob.name}</span>
                      </div>
                    </td>
                    <td className="py-4 pr-4">
                      <span className={CATEGORY_PILL[ob.category] ?? CATEGORY_PILL.OTHER}>
                        {ob.category}
                      </span>
                    </td>
                    <td className="py-4 pr-4">
                      <div>
                        <p className={`text-xs font-semibold ${urgent ? "text-[#b93a3a]" : "text-[#718078]"}`}>
                          {days === 0 ? "Due today" : `${days} day${days === 1 ? "" : "s"}`}
                        </p>
                        <p className="text-[10px] text-[#b0bbb4]">{ob.due_date}</p>
                      </div>
                    </td>
                    <td className="py-4 text-right font-extrabold text-[#b93a3a]">
                      {formatINR(ob.amount)}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </section>

      {/* Raw transaction notice */}
      <section className="panel mt-5 flex items-start gap-4 bg-[#f6f8f5]">
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#e4ebe5]">
          <WalletCards size={16} className="text-[#718078]" />
        </div>
        <div>
          <p className="text-sm font-bold text-[#526158]">Transaction history</p>
          <p className="muted mt-0.5">
            Raw transaction history from connected gig platforms is coming soon.
            FlowGuard currently uses obligation forecasts for your spending plan.
          </p>
        </div>
      </section>
    </div>
  );
}
