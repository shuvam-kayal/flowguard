import type { DashboardData } from "@/types/dashboard";
export const bufferProgress = (data: DashboardData) => Math.min(100, data.resilience.buffer_current / data.resilience.buffer_target * 100);
