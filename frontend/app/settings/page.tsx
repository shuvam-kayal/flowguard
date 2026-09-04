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
  badgeClass: string;
}[] = [
    {
      value: "NORMAL",
      label: "Normal",
      description: "Shows real dashboard data for the current worker with no changes.",
      badge: "Live",
      badgeClass: "badge-green",
    },
    {
      value: "SHOCK",
      label: "Income Shock",
      description: "Simulates a sudden income drop to see how the dashboard responds.",
      badge: "Simulation",
      badgeClass: "badge-red",
    },
    {
      value: "RECOVERY",
      label: "Recovery",
      description: "Shows what recovery looks like after an income shock.",
      badge: "Simulation",
      badgeClass: "badge-blue",
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
    <div className="animate-fade-in space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-[#111827] tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-[#6b7280]">
          Manage your account and try out simulation scenarios.
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
        {/* ── Demo scenario picker ── */}
        <section className="panel space-y-4">
          <div>
            <p className="text-base font-bold text-[#111827]">Demo Scenarios</p>
            <p className="mt-1 text-sm text-[#6b7280]">
              Switch between scenarios to see how FlowGuard responds to different financial
              situations.
            </p>
          </div>

          <div className="space-y-2">
            {SCENARIO_CARDS.map((card) => {
              const active = scenario === card.value;
              return (
                <button
                  key={card.value}
                  onClick={() => setScenario(card.value)}
                  disabled={loading}
                  className={`w-full rounded-xl border-2 p-4 text-left transition-all duration-150 disabled:opacity-50 ${active
                    ? "border-[#087344] bg-[#f0faf4]"
                    : "border-[#e5e7eb] bg-white hover:border-[#c3e6d3]"
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={`grid h-4 w-4 place-items-center rounded-full border-2 ${active ? "border-[#087344] bg-[#087344]" : "border-[#d1d5db]"
                          }`}
                      >
                        {active && <CheckCircle2 size={10} className="text-white" />}
                      </div>
                      <p className="text-sm font-semibold text-[#111827]">{card.label}</p>
                    </div>
                    <span className={card.badgeClass}>{card.badge}</span>
                  </div>
                  <p className="mt-2 ml-7 text-xs text-[#6b7280]">{card.description}</p>
                </button>
              );
            })}
          </div>

          <button
            onClick={() => refetch()}
            disabled={loading}
            className="btn-ghost w-full justify-center text-sm"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            {loading ? "Loading…" : "Refresh data"}
          </button>
        </section>

        {/* ── Right column ── */}
        <div className="space-y-4">
          {/* Profile */}
          <section className="panel">
            <p className="eyebrow mb-3">Your profile</p>
            {loading && !data ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-4 w-40" />
              </div>
            ) : data ? (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="grid h-10 w-10 place-items-center rounded-full bg-[#e8f5ee] text-sm font-bold text-[#087344]">
                    {data.worker.name.split(" ").slice(0, 2).map((n) => n[0]).join("")}
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[#111827]">{data.worker.name}</p>
                    <p className="text-xs text-[#9ca3af]">{data.worker.occupation}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  {[
                    { label: "Worker ID", value: data.worker.worker_id },
                    { label: "Current balance", value: formatINR(data.worker.current_balance) },
                    { label: "Health score", value: `${data.resilience.resilience_score} / 100` },
                    { label: "Risk level", value: data.risk.risk_level },
                  ].map(({ label, value }) => (
                    <div key={label} className="flex justify-between border-b border-[#f0f0f0] pb-2 last:border-0 text-sm">
                      <span className="text-[#6b7280]">{label}</span>
                      <strong className="text-[#111827]">{value}</strong>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-[#9ca3af]">No profile loaded.</p>
            )}
          </section>

          {/* API status */}
          <section className="panel">
            <div className="flex items-center gap-2 mb-3">
              <Server size={14} className="text-[#9ca3af]" />
              <p className="eyebrow">System status</p>
            </div>
            <div className="flex items-center gap-2.5">
              <div
                className={`h-2 w-2 rounded-full ${apiStatus === "ok"
                  ? "bg-[#087344]"
                  : apiStatus === "error"
                    ? "bg-[#c0392b]"
                    : "bg-[#d97706] animate-pulse"
                  }`}
              />
              <p className="text-sm font-semibold text-[#374151]">
                {apiStatus === "ok" ? "Backend connected" : apiStatus === "error" ? "Backend unreachable" : "Checking…"}
              </p>
            </div>
            <p className="mt-1.5 text-xs text-[#9ca3af]">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </p>
          </section>

          {/* Sign out */}
          <button
            onClick={() => {
              localStorage.removeItem("flowguard_token");
              window.location.href = "/login";
            }}
            className="w-full rounded-lg border border-[#f5c6c2] bg-[#fef5f4] px-4 py-3 text-sm font-semibold text-[#c0392b] hover:bg-[#fde8e4] transition-colors"
          >
            Sign out of FlowGuard
          </button>
        </div>
      </div>
    </div>
  );
}
