"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useQueries } from "@tanstack/react-query";
import { Map as MapIcon, List as ListIcon, X, RefreshCw, Loader2 } from "lucide-react";
import { apiFetchNLP } from "@/lib/api";
import type { SentimentOut, Restaurant } from "@/lib/types";
import { TEAM } from "@/lib/mock";
import {
  useNearbyRestaurants,
  useRestaurants,
  useWeatherCurrent,
  useWeeklyNutrition,
} from "@/lib/queries";
import { DEFAULT_USER_ID } from "@/lib/api";
import { getCompositeScore } from "@/lib/scoring";
import { usePreferences } from "@/lib/usePreferences";
import { applyPersonalization } from "@/lib/preferences";
import { useGeolocation } from "@/lib/useGeolocation";
import RestaurantCard from "@/components/discover/RestaurantCard";
import DetailPanel from "@/components/discover/DetailPanel";
import FilterPills from "@/components/discover/FilterPills";
import SortDropdown, {
  type DiscoverSortKey,
} from "@/components/discover/SortDropdown";
import RadiusControl, {
  formatRadius,
} from "@/components/discover/RadiusControl";
import { SkeletonList, SkeletonMap } from "@/components/common/Skeleton";

// Lazy-load Kakao Maps — SSR disabled because SDK depends on `window`.
// 직접 KakaoMap.tsx 를 import 합니다. (KakaoMapClient 는 이미 dynamic 래핑이므로
// 여기서 또 dynamic 을 걸면 이중 래핑 → 로드 실패 원인이 됩니다.)
const KakaoMap = dynamic(() => import("@/components/map/KakaoMap"), {
  ssr: false,
  loading: () => <SkeletonMap height={340} />,
});

export default function DiscoverPage() {
  const [filter, setFilter] = useState<string>("전체");
  // 모바일 첫인상으로 "가까운 순" 이 직관적. 사용자는 SortDropdown 으로 자유 변경 가능.
  const [sortBy, setSortBy] = useState<DiscoverSortKey>("distance");
  const [selectedId, setSelectedId] = useState<string | number | null>(null);
  const [mobileView, setMobileView] = useState<"map" | "list">("list");
  const [radius, setRadius] = useState(800);

  // ── 사용자 위치 (Geolocation API + fallback) ──
  const {
    position,
    loading: geoLoading,
    error: geoError,
    refresh: refreshGeo,
  } = useGeolocation();

  // ── 위치 기반 주변 음식점 (동적 반경 + 반경에 비례한 limit) ──
  // 반경 200m당 +50, 최소 50 / 최대 500 (백엔드 캡과 동일).
  // 300m=50, 500m=100, 700m=150, 1000m=200, 2000m=450, 2100m+=500.
  const nearbyLimit = Math.min(
    500,
    Math.max(50, 50 + Math.floor((radius - 300) / 200) * 50),
  );
  const { data: nearbyRestaurants, isLoading: nearbyLoading } =
    useNearbyRestaurants(position?.lat, position?.lng, radius, nearbyLimit);
  const { data: allRestaurants = [], isLoading: restLoading } = useRestaurants();
  const restaurants =
    nearbyRestaurants && nearbyRestaurants.length > 0
      ? nearbyRestaurants
      : allRestaurants;

  const { data: weather } = useWeatherCurrent();
  const { data: weekly = [] } = useWeeklyNutrition(DEFAULT_USER_ID);
  const prefs = usePreferences();

  // ── Parallel sentiment fetch for each restaurant ──
  const sentimentQueries = useQueries({
    queries: restaurants.map((r) => ({
      queryKey: ["nlp", "sentiment", String(r.id)] as const,
      queryFn: () => apiFetchNLP<SentimentOut>(`/nlp/sentiment/${r.id}`),
      retry: false,
      enabled: restaurants.length > 0,
    })),
  });

  const sentimentMap = useMemo(() => {
    const m = new Map<string | number, SentimentOut | null>();
    restaurants.forEach((r, i) => {
      const q = sentimentQueries[i];
      m.set(r.id, q?.data ?? null);
    });
    return m;
  }, [sentimentQueries, restaurants]);

  const loadedCount = sentimentQueries.filter((q) => q.data != null).length;
  const failedCount = sentimentQueries.filter((q) => q.isError).length;

  const categories = useMemo(() => {
    const set = new Set<string>();
    restaurants.forEach((r) => set.add(r.category));
    return ["전체", ...Array.from(set)];
  }, [restaurants]);

  const scored = useMemo(() => {
    if (!weather || restaurants.length === 0) return [];
    const base = restaurants.map((r) => ({
      ...r,
      score: getCompositeScore(r, weather, weekly, TEAM),
      sentiment: sentimentMap.get(r.id) ?? null,
    }));
    if (!prefs.enabled) return base;
    const enriched = applyPersonalization(base, prefs);
    return enriched.map((r) => ({
      ...r,
      score: r.personalizedScore,
    }));
  }, [restaurants, sentimentMap, weather, weekly, prefs]);

  const sorted = useMemo(() => {
    const arr = [...scored];
    switch (sortBy) {
      case "sentiment":
        return arr.sort((a, b) => {
          const sa = a.sentiment?.score ?? -Infinity;
          const sb = b.sentiment?.score ?? -Infinity;
          if (sa !== sb) return sb - sa;
          return b.score - a.score;
        });
      case "distance":
        return arr.sort((a, b) => a.distance - b.distance);
      case "rating":
        return arr.sort((a, b) => b.rating - a.rating);
      case "price":
        return arr.sort((a, b) => a.price - b.price);
      case "composite":
      default:
        return arr.sort((a, b) => b.score - a.score);
    }
  }, [scored, sortBy]);

  const filtered = useMemo(
    () =>
      filter === "전체" ? sorted : sorted.filter((r) => r.category === filter),
    [sorted, filter],
  );

  const selected: Restaurant | null = useMemo(() => {
    if (selectedId == null) return null;
    // KakaoMap 콜백이 String(r.id) 로 호출하므로 String 비교 (id가 number 라도 매칭됨)
    return restaurants.find((r) => String(r.id) === String(selectedId)) ?? null;
  }, [selectedId, restaurants]);

  const selectedSentiment = selected
    ? sentimentMap.get(selected.id) ?? null
    : null;

  const isInitialLoading =
    (geoLoading || nearbyLoading || restLoading) && restaurants.length === 0;

  // Selecting an item on mobile pops a bottom sheet instead of a side panel
  const handleSelect = (id: string | number) => {
    setSelectedId(id);
  };

  return (
    <div>
      {/* Mobile header — App Store Today 스타일 */}
      <header className="md:hidden mb-5">
        <p className="appstore-eyebrow">DISCOVERY</p>
        <h1 className="appstore-title mt-1">음식점 탐색</h1>
        <p className="text-[12px] text-text-tertiary mt-1.5 font-mono">
          {loadedCount}/{restaurants.length} 감성 분석
          {failedCount > 0 && (
            <span className="text-error ml-1">· {failedCount} failed</span>
          )}
        </p>
      </header>

      {/* Desktop header */}
      <div className="hidden md:flex items-start justify-between mb-6 gap-3">
        <div className="min-w-0">
          <h1 className="text-xl md:text-2xl font-heading font-bold text-text-primary uppercase tracking-tight">
            Discovery
          </h1>
          <p className="text-[10px] md:text-xs text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            Restaurant Explorer &amp; Composite Ranking
          </p>
          <p
            className="text-[11px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            거리 · 날씨 · 영양 · 팀 선호 + 감성 점수 종합
          </p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-[10px] text-text-tertiary uppercase tracking-[0.08em]">
            Sentiment
          </p>
          <p className="text-base md:text-lg font-heading font-bold text-text-primary tracking-tight font-mono">
            {loadedCount}/{restaurants.length}
            {restLoading && (
              <span className="text-text-tertiary text-xs ml-1">…</span>
            )}
          </p>
          {failedCount > 0 && (
            <p className="text-[10px] text-error">{failedCount} failed</p>
          )}
        </div>
      </div>

      {/* Location Status */}
      <div className="flex items-center gap-2 mb-3 text-[11px] text-text-tertiary flex-wrap">
        <span
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border ${
            position?.source === "gps"
              ? "border-primary/30 text-primary bg-primary/5"
              : position?.source === "default"
              ? "border-warning/30 text-warning bg-warning/5"
              : "border-outline/30 bg-surface-2"
          }`}
        >
          {position == null
            ? "📍 위치 확인 중..."
            : position.source === "gps"
            ? `📍 현재 위치${position.accuracy ? ` (±${Math.round(position.accuracy)}m)` : ""}`
            : position.source === "ip"
            ? `📍 IP 위치${position.label ? ` (${position.label})` : ""}`
            : `📍 기본 위치${position.label ? ` (${position.label})` : ""}`}
        </span>
        <button
          type="button"
          onClick={refreshGeo}
          disabled={geoLoading}
          aria-label="위치 다시 확인"
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-outline/30 text-text-tertiary hover:text-text-primary hover:border-outline/50 disabled:opacity-50 transition-colors"
        >
          {geoLoading ? (
            <Loader2 size={11} className="animate-spin" />
          ) : (
            <RefreshCw size={11} />
          )}
          위치 새로고침
        </button>
        <span>
          반경 {formatRadius(radius)} ·{" "}
          {geoLoading || nearbyLoading
            ? "음식점 검색 중..."
            : `${restaurants.length}개 발견`}
        </span>
        {geoError && (
          <span className="text-text-tertiary opacity-60">· {geoError}</span>
        )}
      </div>

      {/* Radius Control — 반경 조절 (300m ~ 5km) */}
      <div className="mb-4">
        <RadiusControl value={radius} onChange={setRadius} />
      </div>

      {/* Mobile view toggle */}
      <div className="flex md:hidden mb-3">
        <div
          role="tablist"
          aria-label="지도/리스트 전환"
          className="inline-flex border border-outline/25 rounded-sm overflow-hidden"
        >
          <button
            role="tab"
            aria-selected={mobileView === "list"}
            onClick={() => setMobileView("list")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase ${
              mobileView === "list"
                ? "bg-primary/10 text-primary"
                : "text-text-tertiary"
            }`}
          >
            <ListIcon size={12} />
            List
          </button>
          <button
            role="tab"
            aria-selected={mobileView === "map"}
            onClick={() => setMobileView("map")}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase border-l border-outline/25 ${
              mobileView === "map"
                ? "bg-primary/10 text-primary"
                : "text-text-tertiary"
            }`}
          >
            <MapIcon size={12} />
            Map
          </button>
        </div>
      </div>

      {/* Mobile-only LIST status pill — "내 주변 · 가까운 순" */}
      {mobileView === "list" && (
        <div className="md:hidden mb-3 flex items-center gap-2 flex-wrap">
          <span className="appstore-pill bg-primary/10 text-primary">
            📍 내 주변 · {sortBy === "distance" ? "가까운 순" : sortBy}
          </span>
          {position && (
            <span className="text-[11px] text-text-tertiary font-mono">
              반경 {radius >= 1000 ? `${(radius / 1000).toFixed(radius % 1000 === 0 ? 0 : 1)}km` : `${radius}m`} · {filtered.length}개
            </span>
          )}
        </div>
      )}

      {/* Silent fallback 가시화 — nearbyRestaurants가 비어 전역 풀로 fallback 됐을 때 */}
      {position != null &&
        !nearbyLoading &&
        (!nearbyRestaurants || nearbyRestaurants.length === 0) && (
          <div className="mb-3 px-3 py-2 rounded-2xl bg-warning/10 border border-warning/30 text-[11px] text-warning">
            ⚠ 주변 데이터를 가져오지 못해 전체 풀에서 표시 중입니다. 위치
            새로고침 또는 반경 조정을 시도해보세요.
          </div>
        )}

      {/* Map — always on desktop, conditional on mobile.
          위치가 null 인 동안에는 (0,0) 으로 렌더하지 않고 Skeleton 을 표시.
          MAP 도 카테고리 필터 적용 → LIST 와 동일한 식당 셋 표시. */}
      <div className={`mb-4 ${mobileView === "map" ? "" : "hidden md:block"}`}>
        {position ? (
          <KakaoMap
            userLat={position.lat}
            userLng={position.lng}
            restaurants={filtered}
            selectedId={selectedId != null ? String(selectedId) : null}
            onSelect={(id) => handleSelect(id)}
            height="340px"
            zoom={4}
            showRadius={radius}
          />
        ) : (
          <SkeletonMap height={340} />
        )}
      </div>

      {/* Toolbar */}
      <div
        className={`items-center justify-between gap-4 mb-4 flex-wrap ${
          mobileView === "map" ? "hidden md:flex" : "flex"
        }`}
      >
        <FilterPills
          categories={categories}
          active={filter}
          onChange={setFilter}
        />
        <SortDropdown value={sortBy} onChange={setSortBy} />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div
          className={`lg:col-span-3 space-y-2 lg:max-h-[calc(100vh-280px)] lg:overflow-y-auto pr-0 lg:pr-1 ${
            mobileView === "map" ? "hidden md:block" : ""
          }`}
        >
          {isInitialLoading && <SkeletonList count={6} />}
          {!isInitialLoading && filtered.length === 0 && (
            <div className="p-6 text-center text-text-tertiary text-sm bg-surface-1 border border-dashed border-outline/30 rounded-sm">
              해당 카테고리의 음식점이 없습니다.
            </div>
          )}
          {!isInitialLoading &&
            filtered.map((r, i) => (
              <RestaurantCard
                key={r.id}
                r={r}
                score={r.score}
                rank={i + 1}
                selected={selectedId === r.id}
                sentiment={r.sentiment}
                onClick={() => handleSelect(r.id)}
              />
            ))}
        </div>

        {/* Desktop side panel */}
        <div className="lg:col-span-2 hidden lg:block">
          <DetailPanel restaurant={selected} sentiment={selectedSentiment} />
        </div>
      </div>

      {/* Mobile/tablet bottom sheet — App Store 스타일 식당 디테일.
          z-50 으로 부유 캡슐 BottomNav(z-40)보다 위에. 패딩 하단에 캡슐 + safe-area 만큼 확보. */}
      {selected && (
        <div className="lg:hidden fixed inset-x-0 bottom-0 z-50 animate-slide-up pointer-events-none">
          <div
            className="mx-auto max-w-2xl bg-surface-1 border-t border-outline/30 rounded-t-3xl shadow-[0_-8px_30px_rgba(0,0,0,0.18)] max-h-[75vh] overflow-y-auto pointer-events-auto"
            style={{
              paddingBottom: "calc(env(safe-area-inset-bottom, 0px) + 92px)",
            }}
          >
            {/* 핸들 (drag indicator) */}
            <div className="sticky top-0 bg-surface-1 z-10 pt-2 pb-1 flex flex-col items-center">
              <div className="w-10 h-1 rounded-full bg-text-tertiary/30" aria-hidden />
            </div>
            <div className="sticky top-3 flex items-center justify-between px-4 pb-2 bg-surface-1 z-10">
              <span className="text-[11px] font-bold uppercase tracking-[0.1em] text-text-tertiary">
                Detail · 식당 정보
              </span>
              <button
                onClick={() => setSelectedId(null)}
                aria-label="닫기"
                className="p-1.5 rounded-full hover:bg-surface-2 active:scale-95"
              >
                <X size={16} />
              </button>
            </div>
            <div className="px-4">
              <DetailPanel
                restaurant={selected}
                sentiment={selectedSentiment}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
