import type { DashboardResponse } from "@/types/dashboard";

export const bufferProgress = (data: DashboardResponse) =>
  Math.min(
    100,
    (data.resilience.buffer_current / data.resilience.buffer_target) * 100
  );
