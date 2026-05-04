"use client";

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import type { Restaurant, SentimentOut } from "@/lib/types";
import { WEATHER, WEEKLY_NUTRITION } from "@/lib/mock";
import {
  getDistanceScore,
  getWeatherScore,
  getNutritionScore,
} from "@/lib/scoring";
import SentimentBadge from "./SentimentBadge";
import KakaoMap from "@/components/map/KakaoMapClient";
import { useGeolocation } from "@/lib/useGeolocation";

export default function DetailPanel({
  restaurant,
  sentiment,
}: {
  restaurant: Restaurant | null;
  sentiment: SentimentOut | null;
}) {
  const { position } = useGeolocation();
  if (!restaurant) {
    return (
      <div className="bg-surface-1 border border-dashed border-outline/30 rounded-sm h-full p-10 flex items-center justify-center text-center text-text-tertiary text-sm">
        <div>
          음식점을 선택하면
          <br />
          상세 분석이 표시됩니다
          <p
            className="mt-3 text-[11px] opacity-70"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            Click a card to see the radar chart.
          </p>
        </div>
      </div>
    );
  }

  const sentimentNormalized =
    sentiment && sentiment.score != null
      ? Math.round(((sentiment.score + 1) / 2) * 100)
      : 50;

  const radarData = [
    { metric: "거리", value: getDistanceScore(restaurant.distance) },
    { metric: "날씨", value: getWeatherScore(restaurant, WEATHER) },
    { metric: "영양", value: getNutritionScore(restaurant, WEEKLY_NUTRITION) },
    { metric: "평점", value: Math.round(restaurant.rating * 20) },
    { metric: "가격", value: Math.max(0, 100 - restaurant.price / 200) },
    { metric: "감성", value: sentimentNormalized },
  ];

  const meta: [string, string][] = [
    ["거리", `${restaurant.distance}m`],
    ["가격", `₩${restaurant.price.toLocaleString()}`],
    ["칼로리", `${restaurant.calories}kcal`],
    ["방문 횟수", `${restaurant.visits}회`],
    ["평점", `★ ${restaurant.rating.toFixed(1)}`],
    ["최근 방문", restaurant.lastVisit],
  ];

  return (
    <div className="bento-card h-full">
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-xl font-heading font-bold text-text-primary leading-tight">
          {restaurant.name}
        </h3>
        <p
          className="text-[11px] text-text-tertiary mt-0.5"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          {restaurant.category} · {restaurant.menuType}
        </p>
        <div className="mt-3">
          <SentimentBadge sentiment={sentiment} />
        </div>
      </div>

      {/* Radar */}
      <div>
        <div className="text-[10px] font-bold text-text-secondary uppercase tracking-[0.1em] mb-2">
          6-Axis Score
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="var(--color-outline)" strokeOpacity={0.3} />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fill: "var(--color-text-secondary)", fontSize: 11 }}
            />
            <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
            <Radar
              dataKey="value"
              stroke="var(--color-primary)"
              fill="var(--color-primary)"
              fillOpacity={0.25}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Meta grid */}
      <div className="grid grid-cols-2 gap-2 mt-4">
        {meta.map(([k, v]) => (
          <div
            key={k}
            className="bg-surface-2 border border-outline/10 rounded-sm px-3 py-2"
          >
            <div className="text-[10px] text-text-tertiary uppercase tracking-[0.08em]">
              {k}
            </div>
            <div className="text-sm font-bold text-text-primary font-mono mt-0.5">
              {v}
            </div>
          </div>
        ))}
      </div>

      {/* Mini Map — 좌표가 있을 때만 표시 */}
      {typeof restaurant.lat === "number" && typeof restaurant.lng === "number" && (
        <div className="mt-5">
          <div className="text-[11px] uppercase tracking-wider text-text-tertiary mb-2 font-bold">
            위치 · Location
          </div>
          <KakaoMap
            userLat={position?.lat ?? 0}
            userLng={position?.lng ?? 0}
            restaurants={[restaurant]}
            selectedId={String(restaurant.id)}
            height="220px"
            zoom={3}
            centerOn="selected"
          />
        </div>
      )}
    </div>
  );
}
