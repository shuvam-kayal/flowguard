"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  Shield,
  Receipt,
  CreditCard,
} from "lucide-react";

const links = [
  { href: "/dashboard",    label: "Overview",  icon: LayoutDashboard },
  { href: "/forecast",     label: "Income",    icon: TrendingUp },
  { href: "/resilience",   label: "Safety Net",icon: Shield },
  { href: "/transactions", label: "Bills",     icon: Receipt },
  { href: "/credit",       label: "Borrow",    icon: CreditCard },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 flex justify-around border-t border-[#e5e7eb] bg-white/95 backdrop-blur-sm px-1 py-2 lg:hidden">
      {links.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={`flex flex-col items-center gap-0.5 px-2 py-1 text-[10px] font-semibold transition-colors ${
              active ? "text-[#087344]" : "text-[#9ca3af]"
            }`}
          >
            <div
              className={`grid h-7 w-7 place-items-center rounded-lg transition-all ${
                active ? "bg-[#e8f5ee]" : ""
              }`}
            >
              <Icon size={16} />
            </div>
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
