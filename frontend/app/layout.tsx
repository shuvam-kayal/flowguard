import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { ScenarioProvider } from "@/components/layout/ScenarioProvider";
import { QueryProvider } from "@/components/layout/QueryProvider";

export const metadata: Metadata = {
  title: "FlowGuard — Financial Resilience for Gig Workers",
  description:
    "FlowGuard helps irregular-income workers protect cash flow, forecast income, and build financial resilience before stress arrives.",
  keywords: ["financial resilience", "gig workers", "income forecast", "cash flow"],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <ScenarioProvider>
            <AppShell>{children}</AppShell>
          </ScenarioProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
