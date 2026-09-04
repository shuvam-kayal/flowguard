"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  TooltipProps,
  XAxis,
  YAxis,
} from "recharts";
import type { ForecastChartPoint } from "@/types/dashboard";
import { formatINR } from "@/lib/formatters";

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const expected = payload.find((p) => p.dataKey === "expected");
  const lower    = payload.find((p) => p.dataKey === "lower");
  const upper    = payload.find((p) => p.dataKey === "upper");
  return (
    <div className="rounded-lg border border-[#e5e7eb] bg-white p-3 shadow-lg text-xs">
      <p className="font-semibold text-[#111827] mb-1.5">{label}</p>
      {expected && (
        <p className="text-[#087344]">
          Expected: <strong>{formatINR(expected.value as number)}</strong>
        </p>
      )}
      {lower && upper && (
        <p className="text-[#9ca3af] mt-0.5">
          Range: {formatINR(lower.value as number)} – {formatINR(upper.value as number)}
        </p>
      )}
    </div>
  );
}

function formatINRShort(value: number) {
  if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  if (value >= 1000) return `₹${(value / 1000).toFixed(0)}k`;
  return `₹${value}`;
}

export function CashFlowChart({ points }: { points: ForecastChartPoint[] }) {
  // Compute summary for plain language headline
  const lastExpected = points.at(-1)?.expected ?? 0;
  const firstExpected = points[0]?.expected ?? 0;
  const trend = lastExpected > firstExpected * 1.05 ? "increasing" : lastExpected < firstExpected * 0.95 ? "decreasing" : "steady";

  return (
    <section className="panel">
      <div className="mb-5">
        <p className="eyebrow">Income this month</p>
        <h2 className="mt-1 text-base font-bold text-[#111827]">
          Your expected earnings are {trend}
        </h2>
        <p className="mt-1 text-xs text-[#6b7280]">
          The solid line shows expected income. The shaded area shows the possible range.
        </p>
      </div>

      {points.length === 0 ? (
        <div className="flex h-52 items-center justify-center">
          <p className="text-sm text-[#9ca3af]">
            Not enough income data to show a forecast yet.
          </p>
        </div>
      ) : (
        <div className="h-52">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={points} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
              <defs>
                <linearGradient id="fg-expected" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%"   stopColor="#087344" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#087344" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="fg-band" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%"   stopColor="#087344" stopOpacity={0.06} />
                  <stop offset="100%" stopColor="#087344" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis
                dataKey="label"
                tickLine={false}
                axisLine={false}
                tick={{ fill: "#9ca3af", fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis
                tickFormatter={formatINRShort}
                tickLine={false}
                axisLine={false}
                tick={{ fill: "#9ca3af", fontSize: 10 }}
                width={44}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="upper"
                stroke="none"
                fill="url(#fg-band)"
                legendType="none"
              />
              <Area
                type="monotone"
                dataKey="lower"
                stroke="none"
                fill="white"
                legendType="none"
              />
              <Area
                type="monotone"
                dataKey="expected"
                stroke="#087344"
                strokeWidth={2}
                fill="url(#fg-expected)"
                dot={false}
                activeDot={{ r: 4, fill: "#087344", strokeWidth: 2, stroke: "#fff" }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
