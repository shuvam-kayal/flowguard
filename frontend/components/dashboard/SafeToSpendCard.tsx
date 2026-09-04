"use client";

import { CircleHelp, X } from "lucide-react";
import { useState } from "react";
import { formatINR } from "@/lib/formatters";
import type { ResilienceResult } from "@/types/dashboard";

interface SafeToSpendCardProps {
  resilience: ResilienceResult;
}

export function SafeToSpendCard({ resilience }: SafeToSpendCardProps) {
  const [open, setOpen] = useState(false);
  const { safe_to_spend_daily, buffer_current, buffer_target } = resilience;
  const bufferPct = Math.min(100, Math.round((buffer_current / buffer_target) * 100));

  const healthLabel =
    safe_to_spend_daily > 800 ? "Looking healthy"
    : safe_to_spend_daily > 300 ? "Spend carefully"
    : "Be very careful";

  const healthColor =
    safe_to_spend_daily > 800 ? "text-[#d0f0e0]"
    : safe_to_spend_daily > 300 ? "text-[#fde68a]"
    : "text-[#fca5a5]";

  return (
    <>
      <section className="rounded-xl bg-[#0f3726] p-6 text-white sm:p-7">
        {/* Label */}
        <p className="text-[11px] font-semibold uppercase tracking-widest text-[#7daa8f]">
          Safe to spend today
        </p>

        {/* Big number */}
        <p className="mt-3 text-5xl font-bold tracking-tight sm:text-6xl">
          {formatINR(safe_to_spend_daily)}
        </p>
        <p className="mt-1 text-sm text-[#a8c9b8]">per day, after all your bills are covered</p>

        {/* Status */}
        <span className={`mt-4 inline-block text-sm font-semibold ${healthColor}`}>
          {healthLabel}
        </span>

        {/* Buffer bar */}
        <div className="mt-6">
          <div className="mb-1.5 flex items-center justify-between text-xs">
            <span className="text-[#7daa8f]">Emergency savings</span>
            <span className="font-semibold text-white">{bufferPct}% of goal</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-[#35bb7a] transition-all duration-700"
              style={{ width: `${bufferPct}%` }}
            />
          </div>
          <p className="mt-1 text-[11px] text-[#7daa8f]">
            {formatINR(buffer_current)} saved · goal is {formatINR(buffer_target)}
          </p>
        </div>

        {/* How is this calculated? */}
        <button
          onClick={() => setOpen(true)}
          className="mt-5 inline-flex items-center gap-1.5 text-xs text-[#7daa8f] hover:text-white transition-colors"
        >
          <CircleHelp size={13} />
          How is this calculated?
        </button>
      </section>

      {/* Modal */}
      {open && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-30 grid place-items-center bg-black/40 p-4 animate-fade-in"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-base font-bold text-[#111827]">How we calculate this</h2>
                <p className="mt-1 text-sm text-[#6b7280]">
                  Your safe-to-spend amount is personalised to your situation.
                </p>
              </div>
              <button
                aria-label="Close"
                onClick={() => setOpen(false)}
                className="grid h-8 w-8 place-items-center rounded-lg hover:bg-[#f3f4f6] transition-colors text-[#6b7280]"
              >
                <X size={16} />
              </button>
            </div>

            <div className="mt-5 space-y-3 text-sm">
              {[
                { step: "1", text: "We look at how much income you're likely to earn this week." },
                { step: "2", text: "We subtract your upcoming bills and EMIs." },
                { step: "3", text: "We keep some aside to grow your emergency savings." },
                { step: "4", text: "Whatever is left is spread across your remaining days." },
              ].map(({ step, text }) => (
                <div key={step} className="flex gap-3">
                  <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-[#e8f5ee] text-[10px] font-bold text-[#087344]">
                    {step}
                  </span>
                  <p className="text-[#4b5563]">{text}</p>
                </div>
              ))}
            </div>

            <div className="mt-5 rounded-lg bg-[#f9fafb] p-3 text-xs text-[#6b7280] border border-[#f0f0f0]">
              This is a recommendation, not a guarantee. It updates daily based on your income
              and spending patterns.
            </div>
          </div>
        </div>
      )}
    </>
  );
}
