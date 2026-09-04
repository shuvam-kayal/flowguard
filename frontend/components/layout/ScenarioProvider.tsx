"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getDashboardForScenario, apiMe } from "@/lib/api";
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
  const queryClient = useQueryClient();

  useEffect(() => {
    const handleAuthChanged = () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
    };

    window.addEventListener("flowguard-auth-changed", handleAuthChanged);

    return () => {
      window.removeEventListener("flowguard-auth-changed", handleAuthChanged);
    };
  }, [queryClient]);

  // Fetch current user
  const {
    data: user,
    isLoading: isLoadingUser,
    isFetching: isFetchingUser,
  } = useQuery({
    queryKey: ["me"],
    queryFn: apiMe,
    retry: false, // If it fails, they are probably not logged in
  });

  // Never silently fall back to the shared demo worker. The dashboard must
  // always be scoped to the identity returned by the authenticated API call.
  const workerId = user?.worker_id ?? "";

  const {
    data = null,
    isFetching,
    isLoading: isLoadingDashboard,
    error: queryError,
    refetch,
  } = useQuery({
    queryKey: ["dashboard", workerId, scenario],
    queryFn: () => getDashboardForScenario(workerId, scenario),
    enabled: !!user?.worker_id, // Only fetch dashboard for an identified user
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
        loading: isLoadingUser || isFetchingUser || isLoadingDashboard || isFetching,
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
