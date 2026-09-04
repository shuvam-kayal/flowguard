import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { ScenarioProvider } from "@/components/layout/ScenarioProvider";
import { QueryProvider } from "@/components/layout/QueryProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

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
    <html lang="en" className={inter.variable}>
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
