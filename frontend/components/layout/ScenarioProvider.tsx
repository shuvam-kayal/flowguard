"use client";

import { createContext, useContext, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDashboardForScenario } from "@/lib/api";
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
  // Worker is fixed at DEFAULT_WORKER_ID for this demo. If multi-worker support
  // is needed, lift this into a separate WorkerProvider or URL param.
  const workerId = DEFAULT_WORKER_ID;

  const {
    data = null,
    isFetching,
    isLoading,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ["dashboard", workerId, scenario],
    queryFn: () => getDashboardForScenario(workerId, scenario),
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
        loading: isLoading || isFetching,
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
