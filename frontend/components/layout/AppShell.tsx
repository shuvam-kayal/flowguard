"use client";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { MobileNav } from "./MobileNav";
export function AppShell({ children }: { children: React.ReactNode }) { return <div className="min-h-screen lg:flex"><Sidebar /><div className="min-w-0 flex-1"><Topbar /><main className="mx-auto max-w-7xl px-5 py-8 pb-24 sm:px-8">{children}</main></div><MobileNav /></div>; }
