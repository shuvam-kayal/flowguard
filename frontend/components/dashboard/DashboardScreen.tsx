"use client";

import { useScenario } from "@/components/layout/ScenarioProvider";
import { SafeToSpendCard } from "./SafeToSpendCard";
import { ResilienceScore } from "./ResilienceScore";
import { RiskCard } from "./RiskCard";
import { FinancialWeather } from "./FinancialWeather";
import { CashFlowChart } from "./CashFlowChart";
import { UpcomingObligations } from "./UpcomingObligations";
import { ActionCenter } from "./ActionCenter";
import { DashboardSkeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { formatINR } from "@/lib/formatters";
import { adaptForecastPoints } from "@/lib/api";

export function DashboardScreen() {
  const { data, loading, error, refetch } = useScenario();

  if (loading) return <DashboardSkeleton />;
  if (error || !data) {
    return <ErrorState message={error ?? "No dashboard data found."} onRetry={refetch} />;
  }

  const { resilience, forecast, risk, worker, obligations, recommendations } = data;
  const chartPoints = adaptForecastPoints(forecast.daily_forecast);
  const isShock = resilience.mode === "SHOCK";
  const firstName = worker.name.split(" ")[0];

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <p className="eyebrow">Good day, {firstName}</p>
      <h1 className="mt-1 text-3xl font-extrabold tracking-tight">
        Your financial health for today
      </h1>
      <p className="muted mt-2">
        FlowGuard helps you protect cash flow before stress arrives.
      </p>

      {/* Row 1: Keep the primary decision cards balanced. */}
      <div className="mt-7 grid items-start gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <SafeToSpendCard resilience={resilience} />
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-1">
          <ResilienceScore resilience={resilience} />
          <FinancialWeather forecast={forecast} />
        </div>
      </div>

      {/* Row 2: Risk and forecast share the same visual band. */}
      <div className="mt-5 grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <CashFlowChart points={chartPoints} />
        <RiskCard risk={risk} />
      </div>

      {/* Row 3: Obligations and buffer share one horizontal row. */}
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <UpcomingObligations summary={obligations} />
        {/* Emergency buffer card */}
        <section className="panel lg:col-span-1">
          <p className="eyebrow">Emergency buffer</p>
          <div className="mt-3 flex items-end justify-between">
            <h2 className="text-2xl font-extrabold">
              {formatINR(resilience.buffer_current)}{" "}
              <span className="text-base font-normal text-[#718078]">
                / {formatINR(resilience.buffer_target)}
              </span>
            </h2>
            <span className="text-sm font-bold text-[#087344]">
              {Math.round((resilience.buffer_current / resilience.buffer_target) * 100)}%
            </span>
          </div>
          <div className="progress-track mt-3">
            <div
              className="progress-fill-green"
              style={{
                width: `${Math.min(100, (resilience.buffer_current / resilience.buffer_target) * 100)}%`,
              }}
            />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 rounded-xl bg-[#f6f8f5] p-4 text-xs">
            {Object.entries({
              "Income stability": resilience.score_breakdown.income_stability,
              "Emergency buffer": resilience.score_breakdown.emergency_buffer,
              "Expense coverage": resilience.score_breakdown.expense_coverage,
              "Debt burden":      resilience.score_breakdown.debt_burden,
              "Savings consistency": resilience.score_breakdown.savings_consistency,
            }).map(([label, val]) => (
              <div key={label}>
                <p className="text-[#718078]">{label}</p>
                <p className="font-bold text-[#16231a]">{val}</p>
              </div>
            ))}
          </div>
          <p className="muted mt-3 text-xs">
            Your first line of defence for essential expenses.
          </p>
        </section>

        <div className="lg:col-span-2">
          <ActionCenter recommendations={recommendations} shock={isShock} />
        </div>
      </div>
    </div>
  );
}
