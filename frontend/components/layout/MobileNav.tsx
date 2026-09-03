"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, CreditCard, LayoutDashboard, ShieldCheck, WalletCards } from "lucide-react";
const links = [{ href: "/dashboard", label: "Home", icon: LayoutDashboard }, { href: "/forecast", label: "Forecast", icon: BarChart3 }, { href: "/resilience", label: "Resilience", icon: ShieldCheck }, { href: "/transactions", label: "Activity", icon: WalletCards }, { href: "/credit", label: "Credit", icon: CreditCard }];
export function MobileNav() { const pathname = usePathname(); return <nav className="fixed inset-x-0 bottom-0 z-20 flex justify-around border-t border-[#e4ebe5] bg-white px-1 py-2 lg:hidden">{links.map(({ href, label, icon: Icon }) => <Link key={href} href={href} className={`flex flex-col items-center gap-1 px-2 py-1 text-[10px] font-bold ${pathname === href ? "text-[#087344]" : "text-[#718078]"}`}><Icon size={18} />{label}</Link>)}</nav>; }
