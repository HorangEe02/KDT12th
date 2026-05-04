"use client";

import dynamic from "next/dynamic";
import type { Restaurant } from "@/lib/types";

export interface WeatherScoredRestaurant extends Restaurant {
  weatherScore: number;
}

// SSR 비활성 — KakaoMap SDK 는 window 의존
const KakaoMap = dynamic(() => import("@/components/map/KakaoMap"), {
  ssr: false,
  loading: () => (
    <div
      className="w-full bg-surface-2 rounded-sm animate-pulse"
      style={{ height: 180 }}
    />
  ),
});

interface WeatherTopPicksProps {
  items: WeatherScoredRestaurant[];
  userLat?: number;
  userLng?: number;
  loading?: boolean;
}

export default function WeatherTopPicks({
  items,
  userLat,
  userLng,
  loading = false,
}: WeatherTopPicksProps) {
  const top5 = items.slice(0, 5);
  const hasCoords = userLat != null && userLng != null;

  return (
    <div className="bento-card h-full">
      <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em] mb-1">
        Top 5 · Weather Match
      </h3>
      <p
        className="text-[11px] text-text-tertiary mb-3"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        오늘 날씨 TOP 5
      </p>

      {/* 미니 지도 — 사용자 위치 + 추천 5곳 */}
      {hasCoords && top5.length > 0 ? (
        <div className="mb-3">
          <KakaoMap
            userLat={userLat as number}
            userLng={userLng as number}
            restaurants={top5}
            selectedId={top5[0] ? String(top5[0].id) : null}
            height="180px"
            zoom={4}
            showRadius={2000}
          />
        </div>
      ) : !hasCoords ? (
        <div
          className="mb-3 w-full flex items-center justify-center text-[11px] text-text-tertiary bg-surface-2 rounded-sm"
          style={{ height: 180, fontFamily: "var(--font-ko)" }}
        >
          위치 권한이 필요합니다
        </div>
      ) : null}

      {/* 리스트 */}
      <div className="space-y-2">
        {loading
          ? Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="h-14 rounded-sm bg-surface-2 animate-pulse"
              />
            ))
          : top5.map((r, i) => {
              const highlight = i === 0;
              return (
                <div
                  key={r.id}
                  className={`flex items-center gap-3 p-3 rounded-sm border ${
                    highlight
                      ? "bg-success/10 border-success/40"
                      : "bg-surface-2 border-outline/15"
                  }`}
                >
                  <div
                    className={`w-7 h-7 flex items-center justify-center font-heading font-bold text-sm rounded-sm ${
                      highlight ? "text-success" : "text-text-tertiary"
                    }`}
                  >
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-text-primary truncate">
                      {r.name}
                    </div>
                    <div className="text-[11px] text-text-tertiary font-mono">
                      {r.menuType} · {r.distance}m
                    </div>
                  </div>
                  <div className="text-lg font-heading font-bold text-success leading-none">
                    {r.weatherScore}
                  </div>
                </div>
              );
            })}
      </div>
    </div>
  );
}
