"use client";

import { Plotly } from "@/components/charts/plot";

interface EngagementChartProps {
  data: Array<{ date: string; activeUsers: number }>;
}

export function EngagementChart({ data }: EngagementChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-[280px] items-center justify-center rounded-2xl border border-dashed border-se-outline-variant bg-se-surface-container-low text-sm text-se-on-surface-variant">
        데이터 수집 중 — 회원 로그인이 누적되면 표시됩니다.
      </div>
    );
  }

  const last = data.length - 1;
  const colors = data.map((_, i) => (i === last ? "#00193c" : "#abc7ff"));

  return (
    <Plotly
      data={[
        {
          type: "bar",
          x: data.map((d) => d.date),
          y: data.map((d) => d.activeUsers),
          marker: { color: colors, line: { width: 0 } },
          hovertemplate: "%{x|%m월 %d일}<br>%{y:,}명<extra></extra>",
        },
      ]}
      layout={{
        autosize: true,
        height: 280,
        margin: { t: 10, r: 16, b: 36, l: 40 },
        plot_bgcolor: "transparent",
        paper_bgcolor: "transparent",
        font: { family: "Manrope, sans-serif", size: 11, color: "#43474f" },
        xaxis: {
          showgrid: false,
          tickformat: "%m/%d",
          tickfont: { size: 10 },
        },
        yaxis: {
          gridcolor: "#e1e3e4",
          gridwidth: 0.5,
          zeroline: false,
          tickfont: { size: 10 },
        },
        bargap: 0.3,
      }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%" }}
    />
  );
}
