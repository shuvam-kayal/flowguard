import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { ScenarioProvider } from "@/components/layout/ScenarioProvider";
export const metadata: Metadata = { title: "FlowGuard", description: "Financial resilience for irregular income" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body><ScenarioProvider><AppShell>{children}</AppShell></ScenarioProvider></body></html>; }
