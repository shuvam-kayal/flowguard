"use client";

import { useScenario } from "@/components/layout/ScenarioProvider";
import type { Scenario } from "@/types/dashboard";
import { formatINR } from "@/lib/formatters";
import { Skeleton } from "@/components/ui/Skeleton";
import { CheckCircle2, RefreshCw, Server } from "lucide-react";
import { useState, useEffect } from "react";

const SCENARIO_CARDS: {
  value: Scenario;
  label: string;
  description: string;
  badge: string;
  badgeColor: string;
}[] = [
  {
    value:       "NORMAL",
    label:       "Normal",
    description: "Baseline scenario with real dashboard data for the selected worker.",
    badge:       "Live data",
    badgeColor:  "status-pill-green",
  },
  {
    value:       "SHOCK",
    label:       "Income Shock",
    description: "Simulates a significant income dip via /simulate/shock. Risk and forecast are adjusted.",
    badge:       "Simulation",
    badgeColor:  "status-pill-red",
  },
  {
    value:       "RECOVERY",
    label:       "Recovery",
    description: "Post-shock recovery mode via /simulate/recovery. Income trend turns positive.",
    badge:       "Simulation",
    badgeColor:  "status-pill-blue",
  },
];

export default function SettingsPage() {
  const { scenario, setScenario, data, loading, refetch } = useScenario();
  const [apiStatus, setApiStatus] = useState<"unknown" | "ok" | "error">("unknown");

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    fetch(`${url}/`)
      .then((r) => setApiStatus(r.ok ? "ok" : "error"))
      .catch(() => setApiStatus("error"));
  }, []);

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <p className="eyebrow">Settings</p>
      <h1 className="mt-1 text-3xl font-extrabold tracking-tight">Demo &amp; worker settings</h1>
      <p className="muted mt-2">
        Use scenarios to demonstrate how FlowGuard adapts to different financial conditions.
      </p>

      <div className="mt-7 grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Scenario picker */}
        <section className="panel">
          <p className="eyebrow mb-4">Demo scenario</p>
          <div className="space-y-3">
            {SCENARIO_CARDS.map((card) => {
              const active = scenario === card.value;
              return (
                <button
                  key={card.value}
                  onClick={() => setScenario(card.value)}
                  disabled={loading}
                  className={`w-full rounded-xl border-2 p-4 text-left transition-all duration-200 disabled:opacity-50 ${
                    active
                      ? "border-[#087344] bg-[#f1faf4]"
                      : "border-[#e4ebe5] bg-white hover:border-[#b9dfc8] hover:bg-[#fafcfa]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={`grid h-5 w-5 place-items-center rounded-full border-2 ${
                          active
                            ? "border-[#087344] bg-[#087344]"
                            : "border-[#c0d0c4] bg-white"
                        }`}
                      >
                        {active && <CheckCircle2 size={12} className="text-white" />}
                      </div>
                      <p className="font-bold text-[#16231a]">{card.label}</p>
                    </div>
                    <span className={card.badgeColor}>{card.badge}</span>
                  </div>
                  <p className="muted mt-2 ml-8 text-xs">{card.description}</p>
                </button>
              );
            })}
          </div>

          <button
            onClick={() => refetch()}
            disabled={loading}
            className="btn-ghost mt-4 w-full justify-center text-sm disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            {loading ? "Loading…" : "Refresh data"}
          </button>
        </section>

        {/* Worker profile + API status */}
        <div className="flex flex-col gap-5">
          {/* Worker profile */}
          <section className="panel">
            <p className="eyebrow mb-4">Worker context</p>
            {loading && !data ? (
              <div className="space-y-3">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-40" />
              </div>
            ) : data ? (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="grid h-12 w-12 place-items-center rounded-full bg-[#dff1e5] text-lg font-extrabold text-[#087344]">
                    {data.worker.name.split(" ").slice(0,2).map(n=>n[0]).join("")}
                  </div>
                  <div>
                    <p className="font-extrabold">{data.worker.name}</p>
                    <p className="muted text-xs">{data.worker.worker_id}</p>
                  </div>
                </div>
                <div className="space-y-2 text-sm">
                  {[
                    { label: "Occupation",       value: data.worker.occupation },
                    { label: "Current balance",  value: formatINR(data.worker.current_balance) },
                    { label: "Resilience score", value: `${data.resilience.resilience_score} / 100` },
                    { label: "Risk level",       value: data.risk.risk_level },
                    { label: "Mode",             value: data.resilience.mode },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex justify-between border-b border-[#edf1ee] pb-2 last:border-0">
                      <span className="text-[#718078]">{label}</span>
                      <strong className="text-[#16231a]">{value}</strong>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="muted">No worker data loaded.</p>
            )}
          </section>

          {/* API Health */}
          <section className="panel">
            <div className="flex items-center gap-2 mb-3">
              <Server size={16} className="text-[#718078]" />
              <p className="eyebrow">API health</p>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={`h-2.5 w-2.5 rounded-full ${
                  apiStatus === "ok"
                    ? "bg-[#23aa6b] shadow-[0_0_6px_#23aa6b]"
                    : apiStatus === "error"
                    ? "bg-[#b93a3a]"
                    : "bg-[#e8a838] animate-pulse"
                }`}
              />
              <p className="text-sm font-bold">
                {apiStatus === "ok"
                  ? "Backend connected"
                  : apiStatus === "error"
                  ? "Backend unreachable"
                  : "Checking…"}
              </p>
            </div>
            <p className="muted mt-1 text-xs">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
