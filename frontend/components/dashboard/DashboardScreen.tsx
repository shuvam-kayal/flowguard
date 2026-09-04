"use client";

import { useScenario } from "@/components/layout/ScenarioProvider";
import { SafeToSpendCard } from "./SafeToSpendCard";
import { ResilienceScore } from "./ResilienceScore";
import { FinancialWeather } from "./FinancialWeather";
import { CashFlowChart } from "./CashFlowChart";
import { UpcomingObligations } from "./UpcomingObligations";
import { ActionCenter } from "./ActionCenter";
import { DashboardSkeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { formatINR } from "@/lib/formatters";
import { adaptForecastPoints } from "@/lib/api";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function DashboardScreen() {
  const { data, loading, error, refetch } = useScenario();

  if (loading) return <DashboardSkeleton />;
  if (error || !data) {
    return <ErrorState message={error ?? "Unable to load your financial data."} onRetry={refetch} />;
  }

  const { resilience, forecast, worker, obligations, recommendations } = data;
  const chartPoints = adaptForecastPoints(forecast.daily_forecast);
  const isShock = resilience.mode === "SHOCK";
  const firstName = worker.name.split(" ")[0];

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Page Header ── */}
      <div>
        <p className="text-sm text-[#6b7280]">Good day, {firstName}</p>
        <h1 className="mt-0.5 text-2xl font-bold text-[#111827] tracking-tight">
          Your financial overview
        </h1>
      </div>

      {/* ── Row 1: Hero + Health + Weather ── */}
      <div className="grid gap-4 xl:grid-cols-[1fr_380px]">
        {/* Hero: safe to spend */}
        <SafeToSpendCard resilience={resilience} />

        {/* Right column: health + weather stacked */}
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
          <ResilienceScore resilience={resilience} />
          <FinancialWeather forecast={forecast} />
        </div>
      </div>

      {/* ── Row 2: Upcoming bills + Action ── */}
      <div className="grid gap-4 lg:grid-cols-2">
        <UpcomingObligations summary={obligations} />
        <ActionCenter recommendations={recommendations} shock={isShock} />
      </div>

      {/* ── Row 3: Income chart ── */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <p className="text-sm font-semibold text-[#374151]">Income this month</p>
          <Link
            href="/forecast"
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#087344] hover:underline"
          >
            Full income details <ArrowRight size={12} />
          </Link>
        </div>
        <CashFlowChart points={chartPoints} />
      </div>

      {/* ── Row 4: Quick summary strip ── */}
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-3">
        {[
          {
            label: "Expected this month",
            value: formatINR(forecast.next_30_days),
            href: "/forecast",
          },
          {
            label: "Safety net savings",
            value: `${Math.min(100, Math.round((resilience.buffer_current / resilience.buffer_target) * 100))}% of goal`,
            href: "/resilience",
          },
          {
            label: "Safe to spend / day",
            value: formatINR(resilience.safe_to_spend_daily),
            href: "/resilience",
          },
        ].map(({ label, value, href }) => (
          <Link
            key={label}
            href={href}
            className="panel text-center hover:border-[#c3e6d3] hover:shadow-sm transition-all"
          >
            <p className="text-xs text-[#9ca3af]">{label}</p>
            <p className="mt-1 text-lg font-bold text-[#111827]">{value}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
