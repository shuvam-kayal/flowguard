import { scenarios } from "@/mock/dashboard";
import { USE_MOCK_DATA } from "@/lib/constants";
import type { DashboardData, Scenario } from "@/types/dashboard";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
let activeScenario: Scenario = "NORMAL";
export const setScenario = (scenario: Scenario) => { activeScenario = scenario; };
export const getDashboard = async (_workerId: string): Promise<DashboardData> => {
  if (USE_MOCK_DATA) return scenarios[activeScenario];
  const response = await fetch(`${API_URL}/worker/${_workerId}/dashboard`);
  if (!response.ok) throw new Error("Unable to load financial data.");
  return response.json() as Promise<DashboardData>;
};
export const getRisk = async (workerId: string) => (await getDashboard(workerId)).risk;
export const getForecast = async (workerId: string) => (await getDashboard(workerId)).forecast;
export const getResilience = async (workerId: string) => (await getDashboard(workerId)).resilience;
export const getTransactions = async (workerId: string) => (await getDashboard(workerId)).transactions;
export const getCreditRecommendation = async (workerId: string) => ({ requested: 5000, useBuffer: 2100, creditNeeded: 1100, workerId });
