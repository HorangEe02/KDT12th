"use client";

import {
  AreaChart,
  Area,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { WeeklyNutritionDay } from "@/lib/types";

export default function CalorieTrend({
  data,
}: {
  data: WeeklyNutritionDay[];
}) {
  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-4 md:p-5 h-full flex flex-col">
      <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em] mb-1">
        Weekly Calorie Trend
      </h3>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        이번 주 칼로리 추이
      </p>
      <div className="flex-1 w-full" style={{ height: "clamp(220px, 40vw, 280px)" }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="calGrad" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor="var(--color-secondary)"
                stopOpacity={0.35}
              />
              <stop
                offset="95%"
                stopColor="var(--color-secondary)"
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-outline)"
            strokeOpacity={0.25}
          />
          <XAxis
            dataKey="day"
            tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }}
          />
          <YAxis tick={{ fill: "var(--color-text-secondary)", fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: "var(--color-surface-2)",
              border: "1px solid var(--color-outline)",
              borderRadius: 6,
              fontSize: 12,
            }}
          />
          <Area
            type="monotone"
            dataKey="calories"
            stroke="var(--color-secondary)"
            fillOpacity={1}
            fill="url(#calGrad)"
            strokeWidth={2.5}
            name="섭취 칼로리"
          />
          <Line
            type="monotone"
            dataKey="target"
            stroke="var(--color-primary)"
            strokeDasharray="5 5"
            strokeWidth={1.5}
            dot={false}
            name="목표"
          />
        </AreaChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
