"use client";

import { useState } from "react";
import { CircleHelp, X } from "lucide-react";
import { formatINR } from "@/lib/formatters";
import type { ResilienceResult } from "@/types/dashboard";

interface SafeToSpendCardProps {
  resilience: ResilienceResult;
}

function WalletRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: number;
  highlight?: boolean;
}) {
  return (
    <div
      className={`flex justify-between text-sm ${
        highlight ? "font-extrabold text-[#087344]" : "text-[#526158]"
      }`}
    >
      <span>{label}</span>
      <span>{formatINR(value)}</span>
    </div>
  );
}

export function SafeToSpendCard({ resilience }: SafeToSpendCardProps) {
  const [open, setOpen] = useState(false);
  const { safe_to_spend_daily, buffer_current, buffer_target, wallet_allocation } = resilience;
  const bufferPct = Math.min(100, Math.round((buffer_current / buffer_target) * 100));

  return (
    <>
    <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#087344] to-[#065e36] p-6 text-white shadow-lg sm:p-8">
        {/* Decorative circle */}
        <div className="pointer-events-none absolute -right-10 -top-10 h-48 w-48 rounded-full bg-white/5" />
        <div className="pointer-events-none absolute -right-4 top-16 h-32 w-32 rounded-full bg-white/5" />

        <p className="eyebrow !text-[#b9e6c8]">Safe to spend today</p>
        <p className="mt-5 text-5xl font-extrabold tracking-[-0.07em] sm:text-6xl">
          {formatINR(safe_to_spend_daily)}
        </p>
        <p className="mt-2 text-sm text-[#d9f4e3]">
          Recommended daily discretionary spending
        </p>

        {/* Wallet allocation pills */}
        <div className="mt-6 flex flex-wrap gap-2">
          {[
            { label: "Daily", val: wallet_allocation.daily },
            { label: "Bills",  val: wallet_allocation.bills },
            { label: "Buffer", val: wallet_allocation.buffer },
            { label: "Growth", val: wallet_allocation.growth },
          ].map(({ label, val }) => (
            <span
              key={label}
              className="rounded-full bg-white/15 px-3 py-1 text-xs font-bold text-white"
            >
              {label}: {formatINR(val)}
            </span>
          ))}
        </div>

        {/* Buffer bar */}
        <div className="mt-6">
          <div className="mb-1 flex justify-between text-xs text-[#d9f4e3]">
            <span>Emergency buffer</span>
            <span>{bufferPct}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-white/20">
            <div
              className="h-full rounded-full bg-[#35bb7a] transition-all duration-700"
              style={{ width: `${bufferPct}%` }}
            />
          </div>
        </div>


        <button
          onClick={() => setOpen(true)}
          className="mt-5 inline-flex items-center gap-1.5 text-xs font-bold text-[#d9f4e3] underline underline-offset-4 hover:text-white transition-colors"
        >
          <CircleHelp size={14} />
          How is this calculated?
        </button>
      </section>

      {open && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-30 grid place-items-center bg-[#102017]/50 p-4 animate-fade-in"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-base font-extrabold">Wallet allocation plan</h2>
              <button
                aria-label="Close"
                onClick={() => setOpen(false)}
                className="grid h-8 w-8 place-items-center rounded-full hover:bg-[#f6f8f5] transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="mt-5 space-y-3">
              <WalletRow label="Daily discretionary" value={wallet_allocation.daily} highlight />
              <WalletRow label="Bills & obligations"  value={wallet_allocation.bills} />
              <WalletRow label="Emergency buffer top-up" value={wallet_allocation.buffer} />
              <WalletRow label="Growth / savings"     value={wallet_allocation.growth} />
              <div className="border-t border-[#edf1ee] pt-3">
                <WalletRow
                  label="Buffer progress"
                  value={buffer_current}
                />
                <p className="muted mt-1 text-xs">
                  Target: {formatINR(buffer_target)} · {bufferPct}% achieved
                </p>
              </div>
            </div>

            <p className="muted mt-4 border-t border-[#edf1ee] pt-4 text-xs">
              FlowGuard calculates a safe daily spend by subtracting upcoming obligations, 
              required buffer top-ups, and savings goals from your forecasted income, 
              then spreading the remainder across days until next income.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
