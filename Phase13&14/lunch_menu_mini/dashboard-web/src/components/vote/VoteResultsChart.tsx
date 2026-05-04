"use client";

import {
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export interface VoteRow {
  id: number;
  name: string;
  voteCount: number;
}

export default function VoteResultsChart({ rows }: { rows: VoteRow[] }) {
  if (rows.length === 0) {
    return (
      <div className="bg-surface-2 border border-dashed border-outline/30 rounded-sm p-10 text-center text-text-tertiary text-sm">
        아직 투표가 없습니다
        <br />
        팀원별 투표를 진행해주세요
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={rows} layout="vertical">
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="var(--color-outline)"
          strokeOpacity={0.25}
        />
        <XAxis
          type="number"
          allowDecimals={false}
          tick={{ fill: "var(--color-text-secondary)", fontSize: 11 }}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fill: "var(--color-text-secondary)", fontSize: 12 }}
          width={80}
        />
        <Tooltip
          contentStyle={{
            background: "var(--color-surface-2)",
            border: "1px solid var(--color-outline)",
            borderRadius: 6,
            fontSize: 12,
          }}
        />
        <Bar
          dataKey="voteCount"
          name="투표 수"
          fill="var(--color-primary)"
          radius={[0, 8, 8, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
