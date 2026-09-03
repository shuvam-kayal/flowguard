"use client";

import { useScenario } from "./ScenarioProvider";

function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase() ?? "")
    .join("");
}

export function Topbar() {
  const { data, loading, scenario } = useScenario();

  const workerName       = data?.worker.name ?? "Loading…";
  const workerOccupation = data?.worker.occupation ?? "";
  const initials         = data ? getInitials(data.worker.name) : "—";

  const scenarioLabel: Record<string, string> = {
    NORMAL:   "Live · Normal",
    SHOCK:    "Sim · Income Shock",
    RECOVERY: "Sim · Recovery",
  };

  return (
    <header className="flex h-[68px] items-center justify-between border-b border-[#e4ebe5] bg-white px-5 sm:px-8">
      <div className="flex items-center gap-3">
        <p className="text-sm font-semibold text-[#526158] hidden sm:block">
          Financial resilience, made visible
        </p>
        <span
          className={`hidden rounded-full px-2.5 py-0.5 text-[10px] font-bold tracking-wide sm:inline-block ${
            scenario === "SHOCK"
              ? "bg-[#fde8e8] text-[#9b2c2c]"
              : scenario === "RECOVERY"
              ? "bg-[#e8f0fe] text-[#1a56db]"
              : "bg-[#dff1e8] text-[#087344]"
          }`}
        >
          {scenarioLabel[scenario]}
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Worker info */}
        <div className={`hidden text-right sm:block transition-opacity duration-300 ${loading ? "opacity-50" : ""}`}>
          <p className="text-sm font-bold leading-tight">{workerName}</p>
          <p className="text-xs text-[#718078] leading-tight">{workerOccupation}</p>
        </div>

        {/* Avatar */}
        <div className="grid h-9 w-9 place-items-center rounded-full bg-[#dff1e5] text-sm font-extrabold text-[#087344] ring-2 ring-[#b9e6c8] select-none">
          {initials}
        </div>
      </div>
    </header>
  );
}
