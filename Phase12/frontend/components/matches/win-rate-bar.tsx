"use client";

import { useMemo } from "react";
import { Plotly } from "@/components/charts/plot";
import { getTeamPalette } from "@/lib/team-colors";

interface Row {
  team: string;
  away_win_rate: number;
}

interface WinRateBarProps {
  rows: Row[];
  highlight: string;
}

/**
 * 구단별 최근 3년 원정 승률 막대그래프.
 * 포팅 원본: src/viz/plotly_charts.py bar_away_win_rate()
 * 선택 팀만 팀 컬러로 강조, 나머지는 회색.
 */
export function WinRateBar({ rows, highlight }: WinRateBarProps) {
  const highlightColor = getTeamPalette(highlight).color;

  const { x, y, colors, text } = useMemo(() => {
    const sorted = [...rows].sort((a, b) => b.away_win_rate - a.away_win_rate);
    return {
      x: sorted.map((r) => r.team),
      y: sorted.map((r) => r.away_win_rate),
      colors: sorted.map((r) =>
        r.team === highlight ? highlightColor : "#D1D5DB",
      ),
      text: sorted.map((r) => r.away_win_rate.toFixed(3)),
    };
  }, [rows, highlight, highlightColor]);

  const data = useMemo(
    () => [
      {
        type: "bar" as const,
        x,
        y,
        marker: { color: colors },
        text,
        textposition: "outside" as const,
        hovertemplate: "<b>%{x}</b><br>원정 승률: %{y:.3f}<extra></extra>",
      },
    ],
    [x, y, colors, text],
  );

  const yMax = Math.max(0.7, Math.max(...y) * 1.15);
  const layout = useMemo(
    () => ({
      title: {
        text: `구단별 최근 3년 원정 승률 (강조: ${highlight})`,
        font: { size: 15 },
      },
      xaxis: { title: { text: "구단" } },
      yaxis: { title: { text: "원정 승률" }, range: [0, yMax] },
      template: "simple_white" as const,
      height: 380,
      font: {
        family:
          "var(--font-display), Plus Jakarta Sans, Pretendard, Noto Sans KR, sans-serif",
        color: "#00193c",
      },
      margin: { l: 50, r: 20, t: 60, b: 50 },
    }),
    [highlight, yMax],
  );

  return (
    <Plotly
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data={data as any}
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      layout={layout as any}
      style={{ width: "100%", height: 380 }}
      config={{ displayModeBar: false, responsive: true }}
    />
  );
}
