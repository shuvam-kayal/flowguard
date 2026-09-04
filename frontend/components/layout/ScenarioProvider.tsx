"use client";

import { createContext, useContext, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDashboardForScenario, apiMe } from "@/lib/api";
import { DEFAULT_WORKER_ID } from "@/lib/constants";
import type { DashboardResponse, Scenario } from "@/types/dashboard";

// ─── Context Shape ────────────────────────────────────────────────────────────

interface ScenarioContextValue {
  data: DashboardResponse | null;
  scenario: Scenario;
  setScenario: (scenario: Scenario) => void;
  /** The active worker ID — exposed so pages like Credit can pass it to the API. */
  workerId: string;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const ScenarioContext = createContext<ScenarioContextValue | null>(null);

// ─── Provider ─────────────────────────────────────────────────────────────────

export function ScenarioProvider({ children }: { children: React.ReactNode }) {
  const [scenario, setScenario] = useState<Scenario>("NORMAL");

  // Fetch current user
  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiMe(),
    retry: false, // If it fails, they are probably not logged in
  });

  const workerId = user?.worker_id || DEFAULT_WORKER_ID;

  const {
    data = null,
    isFetching,
    isLoading: isLoadingDashboard,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ["dashboard", workerId, scenario],
    queryFn: () => getDashboardForScenario(workerId, scenario),
    enabled: !!user, // Only fetch dashboard if we know who the user is
  });

  const error =
    queryError instanceof Error
      ? queryError.message
      : queryError
      ? "Unable to load your financial data."
      : null;

  return (
    <ScenarioContext.Provider
      value={{
        data,
        scenario,
        setScenario,
        workerId,
        loading: isLoadingUser || isLoadingDashboard || isFetching,
        error,
        refetch,
      }}
    >
      {children}
    </ScenarioContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useScenario(): ScenarioContextValue {
  const ctx = useContext(ScenarioContext);
  if (!ctx) throw new Error("useScenario must be used inside ScenarioProvider");
  return ctx;
}
