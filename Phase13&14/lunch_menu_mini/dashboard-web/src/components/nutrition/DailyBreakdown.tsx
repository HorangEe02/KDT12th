"use client";

import {
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { WeeklyNutritionDay } from "@/lib/types";

export default function DailyBreakdown({
  data,
}: {
  data: WeeklyNutritionDay[];
}) {
  const eaten = data.filter((d) => d.calories > 0);
  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-4 md:p-5">
      <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em] mb-1">
        Daily Macros
      </h3>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        일별 영양소 섭취
      </p>
      <div className="w-full" style={{ height: "clamp(200px, 38vw, 260px)" }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={eaten}>
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
          <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
          <Bar
            dataKey="protein"
            name="단백질"
            fill="var(--color-secondary)"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="carbs"
            name="탄수화물"
            fill="#3B8BD4"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="fat"
            name="지방"
            fill="var(--color-tertiary)"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
