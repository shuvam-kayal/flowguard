"use client";

import { useScenario } from "./ScenarioProvider";
import { LogOut } from "lucide-react";

function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase() ?? "")
    .join("");
}

export function Topbar() {
  const { data, loading } = useScenario();

  const workerName       = data?.worker.name ?? "";
  const workerOccupation = data?.worker.occupation ?? "";
  const initials         = data ? getInitials(data.worker.name) : "—";

  return (
    <header className="flex h-14 items-center justify-between border-b border-[#e5e7eb] bg-white px-5 sm:px-8">
      {/* Left: page context — shown on mobile where sidebar is hidden */}
      <div className="flex items-center lg:hidden">
        <span className="text-base font-bold text-[#0f3726]">FlowGuard</span>
      </div>

      {/* Right: user info */}
      <div className="ml-auto flex items-center gap-3">
        {/* Worker info — desktop */}
        {!loading && workerName && (
          <div className="hidden text-right sm:block">
            <p className="text-sm font-semibold leading-tight text-[#111827]">{workerName}</p>
            <p className="text-xs text-[#6b7280] leading-tight">{workerOccupation}</p>
          </div>
        )}

        {/* Avatar */}
        <div className="grid h-8 w-8 place-items-center rounded-full bg-[#e8f5ee] text-xs font-bold text-[#087344] ring-2 ring-[#c3e6d3] select-none">
          {initials}
        </div>

        {/* Sign out — mobile only (desktop uses sidebar) */}
        <button
          onClick={() => {
            localStorage.removeItem("flowguard_token");
            window.location.href = "/login";
          }}
          className="grid h-8 w-8 place-items-center rounded-lg text-[#9ca3af] hover:bg-red-50 hover:text-red-500 transition-colors lg:hidden"
          title="Sign out"
          aria-label="Sign out"
        >
          <LogOut size={15} />
        </button>
      </div>
    </header>
  );
}
