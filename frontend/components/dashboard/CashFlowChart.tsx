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
    <div className="rounded-xl border border-[#e4ebe5] bg-white p-3 shadow-lg text-xs">
      <p className="font-bold text-[#16231a] mb-1">{label}</p>
      {expected && (
        <p className="text-[#087344]">Expected: <strong>{formatINR(expected.value as number)}</strong></p>
      )}
      {lower && upper && (
        <p className="text-[#718078] mt-0.5">
          Range: {formatINR(lower.value as number)} – {formatINR(upper.value as number)}
        </p>
      )}
    </div>
  );
}

export function CashFlowChart({ points }: { points: ForecastChartPoint[] }) {
  return (
    <section className="panel animate-fade-in">
      <div className="mb-5">
        <p className="eyebrow">Income forecast</p>
        <h2 className="mt-1 text-base font-bold">
          Expected earnings and confidence range
        </h2>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={points} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="fg-expected" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%"   stopColor="#23aa6b" stopOpacity={0.28} />
                <stop offset="100%" stopColor="#23aa6b" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="fg-band" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%"   stopColor="#087344" stopOpacity={0.09} />
                <stop offset="100%" stopColor="#087344" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f4f1" vertical={false} />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              tick={{ fill: "#718078", fontSize: 11 }}
            />
            <YAxis
              hide
              domain={["auto", "auto"]}
            />
            <Tooltip content={<CustomTooltip />} />
            {/* Confidence band — upper */}
            <Area
              type="monotone"
              dataKey="upper"
              stroke="none"
              fill="url(#fg-band)"
              legendType="none"
            />
            {/* Confidence band — lower (reset fill) */}
            <Area
              type="monotone"
              dataKey="lower"
              stroke="none"
              fill="white"
              legendType="none"
            />
            {/* Expected income line */}
            <Area
              type="monotone"
              dataKey="expected"
              stroke="#087344"
              strokeWidth={2.5}
              fill="url(#fg-expected)"
              dot={false}
              activeDot={{ r: 4, fill: "#087344", strokeWidth: 2, stroke: "#fff" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 text-xs text-[#718078]">
        Solid line: expected income · Shaded band: confidence range
      </p>
    </section>
  );
}
