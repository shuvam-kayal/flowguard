"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, RefreshCw, ChevronRight } from "lucide-react";
import { formatINR } from "@/lib/formatters";
import { evaluateCredit } from "@/lib/api";
import { useScenario } from "@/components/layout/ScenarioProvider";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import type { CreditGuardResult } from "@/types/dashboard";

const creditSchema = z.object({
  requested_amount: z
    .number({ message: "Enter a valid amount" })
    .min(500, "Minimum amount is ₹500")
    .max(500000, "Maximum amount is ₹5,00,000"),
  months: z
    .number({ message: "Select a repayment period" })
    .min(1)
    .max(24),
});

type CreditFormValues = z.infer<typeof creditSchema>;

const DECISION_PLAIN: Record<
  CreditGuardResult["decision"],
  { label: string; description: string; icon: React.ElementType; bg: string; border: string; color: string }
> = {
  NO_CREDIT_NEEDED: {
    label: "You don't need to borrow",
    description: "Your savings and upcoming income are enough to cover your need. No loan required.",
    icon: CheckCircle2, bg: "bg-[#f0faf4]", border: "border-[#c3e6d3]", color: "text-[#087344]",
  },
  PARTIAL_CREDIT: {
    label: "A smaller loan is safer",
    description: "Borrowing the full amount would strain your budget. We suggest a smaller amount you can comfortably repay.",
    icon: ShieldCheck, bg: "bg-[#fef9ec]", border: "border-[#f0d080]", color: "text-[#92580a]",
  },
  FULL_CREDIT: {
    label: "You can afford this loan",
    description: "Based on your income and savings, you can manage this repayment safely.",
    icon: CheckCircle2, bg: "bg-[#eef3fd]", border: "border-[#c3d4f7]", color: "text-[#1a56db]",
  },
  CREDIT_DECLINED: {
    label: "Borrowing not recommended right now",
    description: "Your current income and savings make this loan risky. It could put you in financial difficulty.",
    icon: XCircle, bg: "bg-[#fef5f4]", border: "border-[#f5c6c2]", color: "text-[#c0392b]",
  },
};

const WATERFALL_PLAIN: Record<string, string> = {
  savings:          "Your existing savings",
  emergency_buffer: "Your emergency fund",
  delay_expense:    "Delaying a non-urgent payment",
  future_income:    "Upcoming income",
  credit:           "External loan",
};

export default function CreditPage() {
  const { data: dashData, loading: dashLoading, error: dashError, refetch, workerId } = useScenario();
  const [result,     setResult]     = useState<CreditGuardResult | null>(null);
  const [apiError,   setApiError]   = useState<string | null>(null);
  const [evaluating, setEvaluating] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<CreditFormValues>({
    resolver: zodResolver(creditSchema),
    defaultValues: { requested_amount: 5000, months: 4 },
  });

  const months = watch("months");
  const requestedAmount = watch("requested_amount");
  const estimatedMonthly = result
    ? result.safe_monthly_repayment
    : Math.ceil((requestedAmount || 0) / (months || 1));

  const onSubmit = async (values: CreditFormValues) => {
    setEvaluating(true);
    setApiError(null);
    setResult(null);
    try {
      const res = await evaluateCredit(workerId, values.requested_amount);
      setResult(res);
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Check failed. Please try again.");
    } finally {
      setEvaluating(false);
    }
  };

  if (dashLoading) return <Skeleton className="h-96" />;
  if (dashError || !dashData) {
    return <ErrorState message={dashError ?? "No data found."} onRetry={refetch} />;
  }

  const decisionMeta = result ? DECISION_PLAIN[result.decision] : null;
  const DecisionIcon = decisionMeta?.icon ?? ShieldCheck;

  return (
    <div className="animate-fade-in space-y-6">
      {/* ── Header ── */}
      <div>
        <h1 className="text-2xl font-bold text-[#111827] tracking-tight">Borrow Safely</h1>
        <p className="mt-1 text-sm text-[#6b7280]">
          Before you take a loan, we check if it's safe for your finances.
        </p>
      </div>

      {/* ── Explainer banner ── */}
      <div className="rounded-xl border border-[#c3e6d3] bg-[#f0faf4] px-5 py-4 flex items-start gap-3">
        <ShieldCheck size={18} className="mt-0.5 shrink-0 text-[#087344]" />
        <div>
          <p className="text-sm font-semibold text-[#087344]">How FlowGuard protects you</p>
          <p className="mt-1 text-xs text-[#4b5563] leading-relaxed">
            We first check if you can meet your need using savings, upcoming income, or by
            delaying a non-urgent payment — before recommending a loan. Credit is always
            the last option.
          </p>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        {/* ── Left: Form ── */}
        <section className="panel space-y-5">
          <p className="text-base font-bold text-[#111827]">How much do you need?</p>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
            {/* Amount */}
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#374151]" htmlFor="requested_amount">
                Amount (₹)
              </label>
              <input
                id="requested_amount"
                type="number"
                step="500"
                min="500"
                max="500000"
                className={`input ${errors.requested_amount ? "input-error" : ""}`}
                placeholder="e.g. 5000"
                {...register("requested_amount", { valueAsNumber: true })}
              />
              {errors.requested_amount && (
                <p className="mt-1 flex items-center gap-1 text-xs text-[#c0392b]">
                  <AlertTriangle size={11} />
                  {errors.requested_amount.message}
                </p>
              )}
            </div>

            {/* Months */}
            <div>
              <label className="mb-1.5 block text-sm font-semibold text-[#374151]" htmlFor="months">
                How long to repay?
              </label>
              <select
                id="months"
                className={`input ${errors.months ? "input-error" : ""}`}
                {...register("months", { valueAsNumber: true })}
              >
                {[3, 4, 6, 9, 12, 18, 24].map((m) => (
                  <option key={m} value={m}>{m} months</option>
                ))}
              </select>
            </div>

            {/* Simple repayment preview */}
            <div className="rounded-lg bg-[#f9fafb] border border-[#f0f0f0] px-4 py-3">
              <p className="text-xs text-[#6b7280]">Estimated monthly repayment</p>
              <p className="mt-1 text-xl font-bold text-[#111827]">{formatINR(estimatedMonthly)}</p>
              <p className="mt-0.5 text-[10px] text-[#9ca3af]">
                {result ? "Based on our safety analysis" : "Quick estimate — click Check below for full analysis"}
              </p>
            </div>

            <button
              type="submit"
              disabled={evaluating}
              className="btn-primary w-full justify-center"
            >
              {evaluating ? (
                <><RefreshCw size={14} className="animate-spin" /> Checking…</>
              ) : (
                <><ShieldCheck size={14} /> Check if this is safe</>
              )}
            </button>

            {apiError && (
              <p className="flex items-center gap-2 text-sm text-[#c0392b]">
                <AlertTriangle size={13} />
                {apiError}
              </p>
            )}
          </form>
        </section>

        {/* ── Right: Result ── */}
        <div className="space-y-4">
          {result && decisionMeta ? (
            <>
              {/* Decision */}
              <div className={`rounded-xl border ${decisionMeta.bg} ${decisionMeta.border} p-5 animate-slide-up`}>
                <div className="flex items-start gap-3">
                  <DecisionIcon size={20} className={`mt-0.5 shrink-0 ${decisionMeta.color}`} />
                  <div>
                    <p className={`text-base font-bold ${decisionMeta.color}`}>{decisionMeta.label}</p>
                    <p className="mt-1 text-sm text-[#4b5563]">{decisionMeta.description}</p>
                    <p className="mt-2 text-xs text-[#6b7280]">{result.message}</p>
                  </div>
                </div>
              </div>

              {/* Key numbers */}
              <section className="panel animate-slide-up space-y-2">
                <p className="eyebrow mb-3">The numbers</p>
                {[
                  { label: "You asked for",              value: formatINR(result.requested_amount) },
                  { label: "Available from your savings", value: formatINR(result.buffer_available) },
                  { label: "Still need to cover",        value: formatINR(result.expected_shortfall) },
                  { label: "Recommended loan amount",    value: formatINR(result.recommended_credit), emph: true },
                  { label: "Safe monthly repayment",     value: formatINR(result.safe_monthly_repayment) },
                ].map(({ label, value, emph }) => (
                  <div
                    key={label}
                    className={`flex justify-between py-2 border-b border-[#f0f0f0] last:border-0 text-sm ${
                      emph ? "font-bold text-[#087344]" : "text-[#4b5563]"
                    }`}
                  >
                    <span>{label}</span>
                    <span>{value}</span>
                  </div>
                ))}
              </section>

              {/* Waterfall — how we protect you */}
              {result.waterfall.length > 0 && (
                <section className="panel animate-slide-up">
                  <p className="eyebrow mb-1">How we protect you first</p>
                  <p className="mb-4 text-xs text-[#9ca3af]">
                    We try these options before recommending a loan, in this order:
                  </p>
                  <div className="space-y-2">
                    {result.waterfall.map((step, i) => (
                      <div
                        key={i}
                        className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm ${
                          step.used ? "bg-[#f0faf4] ring-1 ring-[#c3e6d3]" : "bg-[#f9fafb] opacity-50"
                        }`}
                      >
                        <div className={`grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px] font-bold ${
                          step.used ? "bg-[#087344] text-white" : "bg-[#e5e7eb] text-[#9ca3af]"
                        }`}>
                          {i + 1}
                        </div>
                        <span className="flex-1 font-medium text-[#374151]">
                          {WATERFALL_PLAIN[step.source] ?? step.source}
                        </span>
                        <span className={`font-semibold ${step.used ? "text-[#087344]" : "text-[#9ca3af]"}`}>
                          {step.used ? formatINR(step.amount) : "Not used"}
                        </span>
                        <ChevronRight size={14} className="text-[#c4c9ce]" />
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </>
          ) : (
            <section className="panel flex h-full min-h-[240px] flex-col items-center justify-center gap-3 text-center">
              <div className="grid h-12 w-12 place-items-center rounded-full bg-[#f0faf4]">
                <ShieldCheck size={22} className="text-[#087344]" />
              </div>
              <p className="text-sm font-semibold text-[#111827]">Ready to check</p>
              <p className="muted max-w-xs text-xs">
                Enter how much you need and click <strong>Check if this is safe</strong> to get
                a personalised borrowing assessment.
              </p>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
