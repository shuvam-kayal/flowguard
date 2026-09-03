"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  CreditCard,
  LayoutDashboard,
  ShieldCheck,
  WalletCards,
} from "lucide-react";

const links = [
  { href: "/dashboard",    label: "Home",        icon: LayoutDashboard },
  { href: "/forecast",     label: "Forecast",    icon: BarChart3 },
  { href: "/resilience",   label: "Resilience",  icon: ShieldCheck },
  { href: "/transactions", label: "Activity",    icon: WalletCards },
  { href: "/credit",       label: "Credit",      icon: CreditCard },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 flex justify-around border-t border-[#e4ebe5] bg-white/95 backdrop-blur-sm px-1 py-2 lg:hidden">
      {links.map(({ href, label, icon: Icon }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={`flex flex-col items-center gap-1 px-3 py-1 text-[10px] font-bold transition-colors ${
              active ? "text-[#087344]" : "text-[#718078]"
            }`}
          >
            <div
              className={`grid h-7 w-7 place-items-center rounded-xl transition-all ${
                active ? "bg-[#dff1e5]" : ""
              }`}
            >
              <Icon size={17} />
            </div>
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
