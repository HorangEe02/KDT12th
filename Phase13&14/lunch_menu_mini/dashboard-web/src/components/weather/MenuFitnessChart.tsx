"use client";

import {
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";

export interface MenuFitnessRow {
  type: string;
  avgScore: number;
}

export default function MenuFitnessChart({ data }: { data: MenuFitnessRow[] }) {
  return (
    <div className="bento-card h-full">
      <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em] mb-1">
        Menu Type Fitness
      </h3>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        메뉴 유형별 날씨 적합도
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--color-outline)"
            strokeOpacity={0.25}
          />
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fill: "var(--color-text-secondary)", fontSize: 11 }}
          />
          <YAxis
            type="category"
            dataKey="type"
            tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }}
            width={70}
          />
          <Tooltip
            contentStyle={{
              background: "var(--color-surface-2)",
              border: "1px solid var(--color-outline)",
              borderRadius: 6,
              fontSize: 12,
            }}
          />
          <Bar dataKey="avgScore" radius={[0, 6, 6, 0]}>
            {data.map((d, i) => (
              <Cell
                key={i}
                fill={
                  d.avgScore >= 70
                    ? "var(--color-success)"
                    : d.avgScore >= 50
                    ? "var(--color-tertiary)"
                    : "var(--color-error)"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
