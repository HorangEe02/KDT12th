"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

export interface MacroSlice {
  name: string;
  value: number;
  color: string;
  target: number;
  percent: number;
}

export default function MacroDonut({ macros }: { macros: MacroSlice[] }) {
  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-4 md:p-5 h-full">
      <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em] mb-1">
        Macronutrient Ratio
      </h3>
      <p
        className="text-[11px] text-text-tertiary mb-4"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        탄단지 비율
      </p>

      <div className="w-full" style={{ height: "clamp(180px, 32vw, 220px)" }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={macros}
            cx="50%"
            cy="50%"
            innerRadius={45}
            outerRadius={75}
            dataKey="percent"
            paddingAngle={3}
          >
            {macros.map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(v) => `${v}%`}
            contentStyle={{
              background: "var(--color-surface-2)",
              border: "1px solid var(--color-outline)",
              borderRadius: 6,
              fontSize: 12,
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      </div>

      <div className="flex justify-center gap-4 md:gap-5 mt-3 flex-wrap">
        {macros.map((d) => (
          <div key={d.name} className="text-center">
            <div
              className="w-2.5 h-2.5 rounded-full mx-auto mb-1"
              style={{ background: d.color }}
            />
            <div
              className="text-[11px] text-text-secondary"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              {d.name}
            </div>
            <div className="text-sm font-bold text-text-primary font-mono">
              {d.percent}%
            </div>
            <div className="text-[9px] text-text-tertiary">
              목표 {d.target}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
