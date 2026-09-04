"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Shield,
  Receipt,
  CreditCard,
  Settings,
  LogOut,
} from "lucide-react";

const links = [
  { href: "/dashboard",    label: "Overview",       sub: "Your daily summary",   icon: LayoutDashboard },
  { href: "/forecast",     label: "Income Outlook", sub: "What you'll likely earn", icon: TrendingUp },
  { href: "/resilience",   label: "Safety Net",     sub: "Your financial cushion",  icon: Shield },
  { href: "/transactions", label: "Bills & Payments", sub: "What you owe",         icon: Receipt },
  { href: "/credit",       label: "Borrow Safely",  sub: "Check before borrowing",  icon: CreditCard },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden min-h-screen w-60 flex-shrink-0 flex-col bg-[#0f3726] lg:flex">
      {/* Logo */}
      <div className="px-5 py-6">
        <Link
          href="/dashboard"
          className="flex items-center gap-2.5 transition-opacity hover:opacity-90"
        >
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#1a9459] text-white text-sm font-black">
            F
          </span>
          <span className="text-lg font-bold text-white tracking-tight">FlowGuard</span>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 space-y-0.5">
        <p className="px-2 py-2 text-[10px] font-semibold uppercase tracking-widest text-[#6b9e85]">
          Menu
        </p>
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                active
                  ? "bg-white/10 text-white"
                  : "text-[#a8c9b8] hover:bg-white/5 hover:text-white"
              }`}
            >
              {active && (
                <span className="absolute left-3 h-4 w-0.5 rounded-r bg-[#35bb7a]" />
              )}
              <Icon size={15} className="shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-white/10 space-y-0.5">
        <p className="px-2 py-2 text-[10px] font-semibold uppercase tracking-widest text-[#6b9e85]">
          Account
        </p>
        <Link
          href="/settings"
          className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
            pathname === "/settings"
              ? "bg-white/10 text-white"
              : "text-[#a8c9b8] hover:bg-white/5 hover:text-white"
          }`}
        >
          <Settings size={15} className="shrink-0" />
          Settings
        </Link>
        <button
          onClick={() => {
            localStorage.removeItem("flowguard_token");
            window.location.href = "/login";
          }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium text-[#a8c9b8] hover:bg-red-900/30 hover:text-red-400 transition-colors"
        >
          <LogOut size={15} className="shrink-0" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
