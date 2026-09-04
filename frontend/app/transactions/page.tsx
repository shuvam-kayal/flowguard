"use client";

import { useState } from "react";
import { useScenario } from "@/components/layout/ScenarioProvider";
import { ErrorState } from "@/components/ui/ErrorState";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { formatINR } from "@/lib/formatters";
import { daysUntil } from "@/lib/api";
import { AlertCircle } from "lucide-react";

type FilterCategory = "All" | "FIXED" | "DEBT" | "UTILITY" | "OTHER" | "HOUSING";

const CATEGORY_LABEL: Record<string, string> = {
  FIXED:   "Fixed",
  DEBT:    "Loan/EMI",
  UTILITY: "Utility",
  OTHER:   "Other",
  HOUSING: "Housing",
};

const CATEGORY_BADGE: Record<string, string> = {
  FIXED:   "badge-blue",
  DEBT:    "badge-red",
  UTILITY: "badge-amber",
  OTHER:   "badge-gray",
  HOUSING: "badge-blue",
};

export default function TransactionsPage() {
  const { data, loading, error, refetch } = useScenario();
  const [filter, setFilter] = useState<FilterCategory>("All");

  if (loading) return <TableSkeleton rows={6} />;
  if (!data || error) {
    return <ErrorState message={error ?? "Unable to load bills data."} onRetry={refetch} />;
  }

  const { obligations, resilience } = data;
  const allObs = obligations.upcoming_obligations;
  const filtered = filter === "All" ? allObs : allObs.filter((o) => o.category === filter);

  // Unique categories present
  const categories = ["All", ...Array.from(new Set(allObs.map((o) => o.category)))] as FilterCategory[];

  // Urgent bills
  const urgentCount = allObs.filter((o) => daysUntil(o.due_date) <= 5).length;

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-[#111827] tracking-tight">Bills & Payments</h1>
        <p className="mt-1 text-sm text-[#6b7280]">
          All upcoming payments tracked by FlowGuard.
        </p>
      </div>

      {/* ── Urgent alert ── */}
      {urgentCount > 0 && (
        <div className="flex items-start gap-3 rounded-xl border border-[#f5c6c2] bg-[#fef5f4] px-4 py-3">
          <AlertCircle size={16} className="mt-0.5 shrink-0 text-[#c0392b]" />
          <p className="text-sm font-semibold text-[#c0392b]">
            {urgentCount} payment{urgentCount > 1 ? "s are" : " is"} due within 5 days
          </p>
        </div>
      )}

      {/* ── Summary ── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <section className="panel text-center">
          <p className="text-xs text-[#9ca3af]">Total due</p>
          <p className="mt-1 text-xl font-bold text-[#c0392b]">{formatINR(obligations.total_upcoming)}</p>
          <p className="mt-0.5 text-[10px] text-[#9ca3af]">{allObs.length} bills</p>
        </section>
        <section className="panel text-center">
          <p className="text-xs text-[#9ca3af]">Minimum daily spend</p>
          <p className="mt-1 text-xl font-bold text-[#111827]">
            {formatINR(obligations.essential_daily_spend)}
          </p>
          <p className="mt-0.5 text-[10px] text-[#9ca3af]">to cover essentials</p>
        </section>
        <section className="panel text-center col-span-2 sm:col-span-1">
          <p className="text-xs text-[#9ca3af]">Safe to spend</p>
          <p className="mt-1 text-xl font-bold text-[#087344]">
            {formatINR(resilience.safe_to_spend_daily)}
          </p>
          <p className="mt-0.5 text-[10px] text-[#9ca3af]">after all bills covered</p>
        </section>
      </div>

      {/* ── Filter ── */}
      <div className="flex flex-wrap gap-2">
        {categories.map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`rounded-full px-3.5 py-1 text-xs font-semibold transition-all duration-150 ${
              filter === tab
                ? "bg-[#087344] text-white"
                : "bg-white text-[#6b7280] ring-1 ring-[#e5e7eb] hover:ring-[#c3e6d3]"
            }`}
          >
            {tab === "All" ? "All" : CATEGORY_LABEL[tab] ?? tab}
          </button>
        ))}
      </div>

      {/* ── Bills list ── */}
      <section className="panel overflow-hidden !p-0">
        {filtered.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-sm font-semibold text-[#9ca3af]">No bills in this category</p>
            <p className="mt-1 text-xs text-[#c4c9ce]">Switch to "All" to see everything.</p>
          </div>
        ) : (
          <div className="divide-y divide-[#f0f0f0]">
            {filtered.map((ob) => {
              const days   = daysUntil(ob.due_date);
              const urgent = days <= 5;
              const badgeClass = CATEGORY_BADGE[ob.category] ?? "badge-gray";
              return (
                <div
                  key={`${ob.name}-${ob.due_date}`}
                  className={`flex items-center justify-between px-5 py-4 transition-colors ${urgent ? "bg-[#fef5f4]" : "hover:bg-[#f9fafb]"}`}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-[#111827]">{ob.name}</p>
                      <span className={badgeClass}>
                        {CATEGORY_LABEL[ob.category] ?? ob.category}
                      </span>
                    </div>
                    <p className={`mt-0.5 text-xs ${urgent ? "font-semibold text-[#c0392b]" : "text-[#9ca3af]"}`}>
                      {days === 0 ? "Due today!" : urgent ? `Due in ${days} days — urgent` : `Due in ${days} days · ${ob.due_date}`}
                    </p>
                  </div>
                  <strong className={`text-sm ${urgent ? "text-[#c0392b]" : "text-[#111827]"}`}>
                    {formatINR(ob.amount)}
                  </strong>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* ── Coming soon notice ── */}
      <div className="rounded-xl border border-[#e5e7eb] bg-[#f9fafb] px-5 py-4 text-sm text-[#6b7280]">
        <strong className="text-[#374151]">Transaction history coming soon.</strong>{" "}
        FlowGuard will connect to your gig platforms to automatically track earnings and
        spending. Right now, it uses your scheduled bills and obligations.
      </div>
    </div>
  );
}
