"use client";

import { useMemo } from "react";
import { Plotly } from "@/components/charts/plot";
import { getTeamPalette } from "@/lib/team-colors";

interface WinGaugeProps {
  prob: number; // 0~1
  team: string;
}

/**
 * 승률 게이지 (Plotly Indicator gauge+number+delta).
 * 포팅 원본: src/viz/plotly_charts.py gauge_win_rate()
 */
export function WinGauge({ prob, team }: WinGaugeProps) {
  const palette = getTeamPalette(team);
  const pct = Math.max(0, Math.min(1, prob)) * 100;

  const data = useMemo(
    () => [
      {
        type: "indicator" as const,
        mode: "gauge+number+delta" as const,
        value: pct,
        number: { suffix: "%", font: { size: 34 } },
        delta: {
          reference: 50,
          increasing: { color: palette.color },
          decreasing: { color: "#6B7280" },
        },
        title: { text: `${team} 승률 예측`, font: { size: 15 } },
        gauge: {
          axis: { range: [0, 100], tickwidth: 1, tickcolor: "#D1D5DB" },
          bar: { color: palette.color, thickness: 0.7 },
          steps: [
            { range: [0, 40], color: "#FEE2E2" },
            { range: [40, 60], color: "#FEF3C7" },
            { range: [60, 100], color: "#D1FAE5" },
          ],
          threshold: {
            line: { color: "#111827", width: 3 },
            thickness: 0.75,
            value: 50,
          },
        },
      },
    ],
    [pct, palette.color, team],
  );

  const layout = useMemo(
    () => ({
      height: 280,
      margin: { l: 20, r: 20, t: 50, b: 20 },
      font: {
        family:
          "var(--font-display), Plus Jakarta Sans, Pretendard, Noto Sans KR, sans-serif",
        color: "#00193c",
      },
    }),
    [],
  );

  return (
    <Plotly
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data={data as any}
      layout={layout}
      style={{ width: "100%", height: 280 }}
      config={{ displayModeBar: false, responsive: true }}
    />
  );
}
