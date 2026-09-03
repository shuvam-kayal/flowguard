"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, ChevronRight, RefreshCw } from "lucide-react";
import { formatINR } from "@/lib/formatters";
import { evaluateCredit } from "@/lib/api";
import { useScenario } from "@/components/layout/ScenarioProvider";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Skeleton";
import type { CreditGuardResult } from "@/types/dashboard";

// ─── Validation Schema ────────────────────────────────────────────────────────

const creditSchema = z.object({
  requested_amount: z
    .number({ message: "Enter a valid amount" })
    .min(500, "Minimum credit request is ₹500")
    .max(500000, "Maximum credit request is ₹5,00,000"),
  months: z
    .number({ message: "Select a repayment period" })
    .min(1)
    .max(24),
});

type CreditFormValues = z.infer<typeof creditSchema>;

// ─── Decision Styling ─────────────────────────────────────────────────────────

const DECISION_META: Record<
  CreditGuardResult["decision"],
  { label: string; icon: React.ElementType; bg: string; text: string; border: string }
> = {
  NO_CREDIT_NEEDED: {
    label: "No credit needed",
    icon:  CheckCircle2,
    bg: "bg-[#f1faf4]", text: "text-[#087344]", border: "border-[#b9dfc8]",
  },
  PARTIAL_CREDIT: {
    label: "Partial credit recommended",
    icon:  ShieldCheck,
    bg: "bg-[#fff8ed]", text: "text-[#9a570a]", border: "border-[#f3cc8d]",
  },
  FULL_CREDIT: {
    label: "Full credit approved",
    icon:  CheckCircle2,
    bg: "bg-[#eff5fe]", text: "text-[#1a56db]", border: "border-[#b6cef7]",
  },
  CREDIT_DECLINED: {
    label: "Credit declined",
    icon:  XCircle,
    bg: "bg-[#fff6f6]", text: "text-[#b93a3a]", border: "border-[#efc5c5]",
  },
};

const WATERFALL_LABELS: Record<string, string> = {
  savings:          "Savings",
  emergency_buffer: "Emergency buffer",
  delay_expense:    "Deferred expense",
  future_income:    "Future income",
  credit:           "External credit",
};

// ─── Component ────────────────────────────────────────────────────────────────

export default function CreditPage() {
  const { data: dashData, loading: dashLoading, error: dashError, refetch, workerId } = useScenario();
  const [result,    setResult]    = useState<CreditGuardResult | null>(null);
  const [apiError,  setApiError]  = useState<string | null>(null);
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
      setApiError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  };

  if (dashLoading) return <Skeleton className="h-96" />;
  if (dashError || !dashData) {
    return <ErrorState message={dashError ?? "No data found."} onRetry={refetch} />;
  }

  const decisionMeta = result ? DECISION_META[result.decision] : null;
  const DecisionIcon = decisionMeta?.icon ?? ShieldCheck;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <p className="eyebrow">Credit Guard</p>
      <h1 className="mt-1 text-3xl font-extrabold tracking-tight">
        Credit is the last layer of protection
      </h1>
      <p className="muted mt-2">
        Before borrowing, FlowGuard checks your resilience and available buffer.
      </p>

      <div className="mt-7 grid gap-5 lg:grid-cols-2">
        {/* ── Left: Form ── */}
        <section className="panel">
          <div className="flex items-center gap-3 mb-6">
            <ShieldCheck className="text-[#087344]" size={22} />
            <div>
              <p className="eyebrow">Protection check</p>
              <h2 className="mt-0.5 text-base font-extrabold">Evaluate a credit request</h2>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
            {/* Amount */}
            <div>
              <label className="mb-1.5 block text-sm font-bold" htmlFor="requested_amount">
                Amount requested (₹)
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
                <p className="mt-1 text-xs text-[#b93a3a] flex items-center gap-1">
                  <AlertTriangle size={11} />
                  {errors.requested_amount.message}
                </p>
              )}
            </div>

            {/* Months */}
            <div>
              <label className="mb-1.5 block text-sm font-bold" htmlFor="months">
                Repayment period
              </label>
              <select
                id="months"
                className={`input ${errors.months ? "input-error" : ""}`}
                {...register("months", { valueAsNumber: true })}
              >
                {[3, 4, 6, 9, 12, 18, 24].map((m) => (
                  <option key={m} value={m}>
                    {m} months
                  </option>
                ))}
              </select>
            </div>

            {/* Estimated repayment preview */}
            <div className="rounded-xl bg-[#f6f8f5] px-4 py-3">
              <p className="eyebrow">Estimated monthly repayment</p>
              <p className="mt-1 text-2xl font-extrabold text-[#087344]">
                {formatINR(estimatedMonthly)}
              </p>
              <p className="muted text-xs mt-0.5">
                {result ? "Safe repayment per backend analysis" : "Simple estimate · click Evaluate for full analysis"}
              </p>
            </div>

            <button
              type="submit"
              disabled={evaluating}
              className="btn-primary w-full justify-center"
            >
              {evaluating ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  Evaluating…
                </>
              ) : (
                <>
                  <ShieldCheck size={14} />
                  Evaluate credit safety
                </>
              )}
            </button>

            {apiError && (
              <p className="text-sm text-[#b93a3a] flex items-center gap-2">
                <AlertTriangle size={14} />
                {apiError}
              </p>
            )}
          </form>
        </section>

        {/* ── Right: Result ── */}
        <div className="flex flex-col gap-5">
          {result && decisionMeta ? (
            <>
              {/* Decision banner */}
              <div className={`rounded-2xl border ${decisionMeta.bg} ${decisionMeta.border} p-5 animate-slide-up`}>
                <div className="flex items-center gap-3">
                  <DecisionIcon size={22} className={decisionMeta.text} />
                  <div>
                    <p className={`text-sm font-extrabold ${decisionMeta.text}`}>
                      {decisionMeta.label}
                    </p>
                    <p className="muted mt-0.5">{result.message}</p>
                  </div>
                </div>
              </div>

              {/* Numbers */}
              <section className="panel animate-slide-up">
                <p className="eyebrow mb-4">Credit analysis</p>
                <div className="space-y-3 text-sm">
                  {[
                    { label: "Requested amount",      value: formatINR(result.requested_amount) },
                    { label: "Buffer available",       value: formatINR(result.buffer_available) },
                    { label: "Expected shortfall",     value: formatINR(result.expected_shortfall) },
                    { label: "Recommended credit",     value: formatINR(result.recommended_credit), emph: true },
                    { label: "Safe monthly repayment", value: formatINR(result.safe_monthly_repayment) },
                  ].map(({ label, value, emph }) => (
                    <div
                      key={label}
                      className={`flex justify-between border-b border-[#edf1ee] pb-3 last:border-0 last:pb-0 ${
                        emph ? "font-extrabold text-[#087344]" : "text-[#526158]"
                      }`}
                    >
                      <span>{label}</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              </section>

              {/* Waterfall */}
              {result.waterfall.length > 0 && (
                <section className="panel animate-slide-up">
                  <p className="eyebrow mb-3">Protection waterfall</p>
                  <p className="muted mb-4 text-xs">
                    FlowGuard uses your own funds first before recommending credit.
                  </p>
                  <div className="space-y-2">
                    {result.waterfall.map((step, i) => (
                      <div
                        key={i}
                        className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm ${
                          step.used
                            ? "bg-[#f1faf4] ring-1 ring-[#b9dfc8]"
                            : "bg-[#f6f8f5] opacity-60"
                        }`}
                      >
                        <div
                          className={`grid h-6 w-6 shrink-0 place-items-center rounded-full text-[10px] font-bold ${
                            step.used ? "bg-[#087344] text-white" : "bg-[#e4ebe5] text-[#718078]"
                          }`}
                        >
                          {i + 1}
                        </div>
                        <span className="flex-1 font-medium">
                          {WATERFALL_LABELS[step.source] ?? step.source}
                        </span>
                        <span className={`font-bold ${step.used ? "text-[#087344]" : "text-[#718078]"}`}>
                          {step.used ? formatINR(step.amount) : "–"}
                        </span>
                        <ChevronRight size={14} className="text-[#b8d2c1]" />
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </>
          ) : (
            <section className="panel flex h-full min-h-[240px] flex-col items-center justify-center gap-3 text-center">
              <div className="grid h-14 w-14 place-items-center rounded-full bg-[#f1faf4]">
                <ShieldCheck size={26} className="text-[#23aa6b]" />
              </div>
              <p className="font-bold text-[#16231a]">Ready to evaluate</p>
              <p className="muted max-w-xs">
                Enter an amount and click <strong>Evaluate</strong> to see a full
                credit safety analysis with your buffer protection waterfall.
              </p>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
