export function BufferProgress({ current, target }: { current: number; target: number }) {
  const pct = Math.min(100, Math.round((current / target) * 100));
  const color =
    pct >= 70 ? "bg-[#23aa6b]"
    : pct >= 40 ? "bg-[#e8a838]"
    : "bg-[#b93a3a]";

  return (
    <div className="progress-track">
      <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}
