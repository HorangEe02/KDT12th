"use client";

import { useMemo } from "react";
import { Plotly } from "@/components/charts/plot";
import type { POI } from "@/lib/types";

interface ScatterProps {
  places: POI[];
  category: "food" | "stay" | "tour";
}

function inferRating(idx: number, contentId?: string): number {
  // 평점이 없을 때 content_id 기반 재현 가능한 3.5~4.8 값
  const seed = contentId ?? String(idx);
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) | 0;
  const pseudo = (Math.abs(h) % 1000) / 1000;
  return Math.round((3.5 + pseudo * 1.3) * 10) / 10;
}

/**
 * 거리 × 평점 산점도 (Plotly).
 * 포팅 원본: src/viz/plotly_charts.py scatter_places()
 */
export function ScatterPlaces({ places, category }: ScatterProps) {
  const { data, layout } = useMemo(() => {
    if (places.length === 0) {
      return {
        data: [],
        layout: {
          title: { text: "데이터 없음" },
          height: 340,
          annotations: [
            {
              text: "POI 데이터가 없습니다",
              xref: "paper",
              yref: "paper",
              x: 0.5,
              y: 0.5,
              showarrow: false,
              font: { size: 14, color: "#888" },
            },
          ],
        },
      };
    }
    const x = places.map((p) => p.dist_m ?? 0);
    const y = places.map((p, i) =>
      typeof p.rating === "number" ? p.rating : inferRating(i, p.content_id),
    );
    const text = places.map((p) => p.title);
    const sizes = x.map((d) => Math.max(8, 20 - d / 200));
    const color =
      category === "food"
        ? "#F97316"
        : category === "stay"
          ? "#2563eb"
          : "#16a34a";
    return {
      data: [
        {
          type: "scatter" as const,
          mode: "markers" as const,
          x,
          y,
          text,
          marker: {
            size: sizes,
            color,
            opacity: 0.72,
            line: { color: "white", width: 1.2 },
          },
          hovertemplate:
            "<b>%{text}</b><br>거리: %{x:.0f}m<br>평점: %{y:.1f}<extra></extra>",
        },
      ],
      layout: {
        title: {
          text: `경기장 주변 POI — 거리 vs 평점 (총 ${places.length}개)`,
          font: { size: 14 },
        },
        xaxis: { title: { text: "경기장에서 거리 (m)" } },
        yaxis: { title: { text: "평점" }, range: [3.0, 5.0] },
        template: "simple_white" as const,
        height: 400,
        font: {
          family:
            "var(--font-display), Plus Jakarta Sans, Pretendard, Noto Sans KR, sans-serif",
          color: "#00193c",
        },
        margin: { l: 50, r: 20, t: 60, b: 50 },
      },
    };
  }, [places, category]);

  return (
    <Plotly
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data={data as any}
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      layout={layout as any}
      style={{ width: "100%", height: 400 }}
      config={{ displayModeBar: false, responsive: true }}
    />
  );
}
