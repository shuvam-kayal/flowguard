"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { getDashboard, setScenario as setApiScenario } from "@/lib/api";
import { WORKER_ID } from "@/lib/constants";
import type { DashboardData, Scenario } from "@/types/dashboard";

interface ScenarioContextValue { data: DashboardData | null; scenario: Scenario; setScenario: (scenario: Scenario) => void; loading: boolean; error: string | null; }
const ScenarioContext = createContext<ScenarioContextValue | null>(null);

export function ScenarioProvider({ children }: { children: React.ReactNode }) {
  const [scenario, updateScenario] = useState<Scenario>("NORMAL");
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    setLoading(true); setError(null); setApiScenario(scenario);
    getDashboard(WORKER_ID).then(setData).catch(() => setError("Unable to load your financial data.")).finally(() => setLoading(false));
  }, [scenario]);
  return <ScenarioContext.Provider value={{ data, scenario, setScenario: updateScenario, loading, error }}>{children}</ScenarioContext.Provider>;
}
export function useScenario() { const context = useContext(ScenarioContext); if (!context) throw new Error("useScenario must be used inside ScenarioProvider"); return context; }
