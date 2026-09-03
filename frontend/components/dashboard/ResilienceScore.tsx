import type { ResilienceResult } from "@/types/dashboard";

const MODE_META: Record<
  string,
  { label: string; pillClass: string; ringColor: string }
> = {
  NORMAL:   { label: "Stable",    pillClass: "status-pill-green", ringColor: "#23aa6b" },
  WATCH:    { label: "Watch",     pillClass: "status-pill-amber", ringColor: "#e8a838" },
  SHOCK:    { label: "Shock",     pillClass: "status-pill-red",   ringColor: "#b93a3a" },
  RECOVERY: { label: "Recovery",  pillClass: "status-pill-blue",  ringColor: "#1a56db" },
};

export function ResilienceScore({ resilience }: { resilience: ResilienceResult }) {
  const { resilience_score: score, resilience_days: days, mode } = resilience;
  const meta = MODE_META[mode] ?? MODE_META.NORMAL;
  const pct = Math.min(100, score);

  return (
    <section className="panel animate-fade-in">
      <div className="mb-1 flex items-center justify-between">
        <p className="eyebrow">Financial health</p>
        <span className={meta.pillClass}>{meta.label}</span>
      </div>
      <div className="mt-4 flex items-center gap-5">
        {/* Conic gradient ring */}
        <div
          className="grid h-24 w-24 shrink-0 place-items-center rounded-full transition-all duration-700"
          style={{
            background: `conic-gradient(${meta.ringColor} ${pct}%, #edf2ee 0)`,
          }}
        >
          <div className="grid h-[74px] w-[74px] place-items-center rounded-full bg-white text-xl font-extrabold text-[#16231a]">
            {score}
          </div>
        </div>
        <div>
          <p className="text-base font-extrabold">{meta.label} mode</p>
          <p className="muted">{days} resilience days available</p>
          <p className="mt-1 text-xs text-[#718078]">
            Save{" "}
            <strong className="text-[#087344]">
              ₹{resilience.recommended_save.toLocaleString("en-IN")}
            </strong>{" "}
            to reach target buffer
          </p>
        </div>
      </div>
    </section>
  );
}
