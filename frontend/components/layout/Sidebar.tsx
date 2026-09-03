"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  CreditCard,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import { useScenario } from "./ScenarioProvider";
import type { Scenario } from "@/types/dashboard";

const links = [
  { href: "/dashboard",     label: "Dashboard",         icon: LayoutDashboard },
  { href: "/forecast",      label: "Financial Forecast", icon: BarChart3 },
  { href: "/resilience",    label: "Resilience",         icon: ShieldCheck },
  { href: "/transactions",  label: "Transactions",       icon: WalletCards },
  { href: "/credit",        label: "Credit Guard",       icon: CreditCard },
];

const SCENARIO_OPTIONS: { value: Scenario; label: string; description: string }[] = [
  { value: "NORMAL",   label: "Normal",        description: "Baseline income scenario" },
  { value: "SHOCK",    label: "Income Shock",  description: "Simulated income dip" },
  { value: "RECOVERY", label: "Recovery",      description: "Post-shock recovery" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { scenario, setScenario, loading } = useScenario();

  return (
    <aside className="hidden min-h-screen w-64 flex-col bg-[#0f3726] px-4 py-6 text-white lg:flex">
      {/* Logo */}
      <Link
        href="/dashboard"
        className="mb-10 flex items-center gap-3 px-2 text-xl font-extrabold transition-opacity hover:opacity-90"
      >
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#35bb7a] text-[#0f3726] text-lg font-black">
          ↗
        </span>
        FlowGuard
      </Link>

      {/* Nav */}
      <nav className="space-y-0.5">
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all duration-150 ${
                active
                  ? "bg-white/10 text-white"
                  : "text-[#b8d2c1] hover:bg-white/5 hover:text-white"
              }`}
            >
              {active && (
                <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-r bg-[#35bb7a]" />
              )}
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Scenario selector */}
      <div className="mt-auto border-t border-white/15 pt-5">
        <p className="eyebrow px-2 !text-[#8ab8a1] mb-2">Demo scenario</p>
        <div className="space-y-1">
          {SCENARIO_OPTIONS.map(({ value, label, description }) => {
            const active = scenario === value;
            return (
              <button
                key={value}
                onClick={() => setScenario(value)}
                disabled={loading}
                className={`w-full rounded-xl px-3 py-2 text-left text-sm transition-all duration-150 ${
                  active
                    ? "bg-white/15 text-white font-bold"
                    : "text-[#b8d2c1] hover:bg-white/5 hover:text-white"
                } disabled:opacity-50`}
              >
                <p className={active ? "font-bold" : "font-medium"}>{label}</p>
                <p className="text-[10px] text-[#7daa8f] mt-0.5">{description}</p>
              </button>
            );
          })}
        </div>

        <Link
          href="/settings"
          className="mt-4 flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-[#b8d2c1] hover:bg-white/5 hover:text-white transition-colors"
        >
          <Settings size={15} />
          Settings
        </Link>
      </div>
    </aside>
  );
}
