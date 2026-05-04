"use client";

import { useEffect, useMemo, useState } from "react";
import KPICards from "@/components/dashboard/KPICards";
import CategoryChart from "@/components/dashboard/CategoryChart";
import OllamaStatus from "@/components/dashboard/OllamaStatus";
import TodaysTop5 from "@/components/dashboard/TodaysTop5";
import ForYouCard from "@/components/dashboard/ForYouCard";
import MealTimeSelector, {
  loadStoredMealType,
} from "@/components/concierge/MealTimeSelector";
// App Store Today-style mobile components
import EditorialSection from "@/components/mobile/EditorialSection";
import HeroPickCard from "@/components/mobile/HeroPickCard";
import TodaysTopFiveAppRows from "@/components/mobile/TodaysTopFiveAppRows";
import CategoryHorizontalScroll from "@/components/mobile/CategoryHorizontalScroll";
import WeeklyNutritionMiniCard from "@/components/mobile/WeeklyNutritionMiniCard";
import { TEAM, CATEGORY_COLORS } from "@/lib/mock";
import { getCompositeScore } from "@/lib/scoring";
import {
  useChatbotStats,
  useLunchStats,
  useRestaurants,
  useSentimentTop,
  useWeatherCurrent,
  useWeeklyNutrition,
} from "@/lib/queries";
import { DEFAULT_USER_ID } from "@/lib/api";
import { usePreferences } from "@/lib/usePreferences";
import { applyPersonalization } from "@/lib/preferences";
import { filterByMealType, MEAL_LABEL_KO } from "@/lib/mealTime";
import type { MealType } from "@/lib/types";

const KO_DAYS = ["일", "월", "화", "수", "목", "금", "토"];

function formatDateKo(d: Date) {
  return `${d.getMonth() + 1}월 ${d.getDate()}일 ${KO_DAYS[d.getDay()]}요일`;
}

export default function DashboardPage() {
  const [mealType, setMealType] = useState<MealType>("any");
  useEffect(() => {
    setMealType(loadStoredMealType());
  }, []);
  const mealLabel = MEAL_LABEL_KO[mealType];
  const { data: restaurants = [] } = useRestaurants();
  const { data: weather } = useWeatherCurrent();
  const { data: weekly = [] } = useWeeklyNutrition(DEFAULT_USER_ID);
  const { data: lunchStats } = useLunchStats();
  const prefs = usePreferences();
  const [now, setNow] = useState<string>("");

  // Update local server time every second
  useEffect(() => {
    const fmt = () => {
      const d = new Date();
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
        d.getDate()
      ).padStart(2, "0")} | ${String(d.getHours()).padStart(2, "0")}:${String(
        d.getMinutes()
      ).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
    };
    setNow(fmt());
    const id = setInterval(() => setNow(fmt()), 1000);
    return () => clearInterval(id);
  }, []);

  // KPI data
  const trackedMeals = weekly.filter((d) => d.calories > 0).length;

  const { data: sentimentTop } = useSentimentTop(100);
  const avgSentiment =
    sentimentTop && sentimentTop.length > 0
      ? sentimentTop.reduce((s, x) => s + (x.score || 0), 0) / sentimentTop.length
      : null;

  const { data: chatStats } = useChatbotStats();
  const chatLatencyMs = (() => {
    if (!chatStats || typeof chatStats !== "object") return null;
    const v = (chatStats as Record<string, unknown>).avg_latency_ms;
    const n = typeof v === "number" ? v : Number(v);
    return Number.isFinite(n) ? n : null;
  })();

  // Category counts — prefer real /api/restaurants/stats; fall back to derived
  const categories = (() => {
    const source =
      lunchStats?.categories ??
      restaurants.reduce<Record<string, number>>((acc, r) => {
        acc[r.category] = (acc[r.category] ?? 0) + 1;
        return acc;
      }, {});
    return Object.entries(source)
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => ({
        name,
        count,
        color: CATEGORY_COLORS[name] || "var(--color-primary)",
      }));
  })();

  // Top 5 composite — needs weather + restaurants loaded
  // 헤비 옵션: meal_type 으로 카테고리 필터링 후 랭킹
  const top5 = (() => {
    if (!weather) return [];
    const filtered = filterByMealType(restaurants, mealType);
    const base = filtered.map((r) => ({
      ...r,
      score: getCompositeScore(r, weather, weekly, TEAM),
    }));
    const personalized = prefs.enabled
      ? applyPersonalization(base, prefs).map((r) => ({
          ...r,
          score: r.personalizedScore,
        }))
      : base;
    return personalized.sort((a, b) => b.score - a.score);
  })();

  const todayDateKo = useMemo(() => formatDateKo(new Date()), []);

  return (
    <div>
      {/* ────────────────────────────────────────────────
          모바일: Apple App Store "투데이 탭" 스타일 (md:hidden)
          ──────────────────────────────────────────────── */}
      <div className="md:hidden space-y-7 pb-28">
        {/* 큰 타이틀 + 날짜 eyebrow */}
        <header className="pt-1">
          <p className="appstore-eyebrow">{todayDateKo}</p>
          <h1 className="appstore-title mt-1">오늘의 {mealLabel}</h1>
        </header>

        {/* 시간대 칩 (가로 스크롤) */}
        <MealTimeSelector value={mealType} onChange={setMealType} compact />

        {/* Hero — 1위 식당 */}
        {top5[0] ? (
          <HeroPickCard restaurant={top5[0]} eyebrow="오늘의 픽" />
        ) : (
          <div className="appstore-hero grid place-items-center text-text-tertiary text-sm">
            추천 준비 중...
          </div>
        )}

        {/* TOP 5 식당 */}
        <EditorialSection eyebrow="EDITORS' PICKS" title="오늘의 추천 5곳">
          <TodaysTopFiveAppRows items={top5} />
        </EditorialSection>

        {/* 카테고리 가로 스크롤 */}
        {categories.length > 0 && (
          <EditorialSection eyebrow="EXPLORE" title="카테고리별 탐색">
            <CategoryHorizontalScroll categories={categories} limit={12} />
          </EditorialSection>
        )}

        {/* 이번 주 영양 미니 */}
        <EditorialSection eyebrow="NUTRITION" title="이번 주 영양">
          <WeeklyNutritionMiniCard weekly={weekly} />
        </EditorialSection>

        {/* 시스템 상태 */}
        <EditorialSection eyebrow="STATUS" title="시스템 상태">
          <div className="appstore-card">
            <OllamaStatus />
          </div>
        </EditorialSection>
      </div>

      {/* ────────────────────────────────────────────────
          데스크톱: 기존 그리드 레이아웃 (hidden md:block)
          ──────────────────────────────────────────────── */}
      <div className="hidden md:block">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-heading font-bold text-text-primary uppercase tracking-tight">
              Dashboard
            </h1>
            <p className="text-xs text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
              System Overview &amp; Lunch Metrics
            </p>
            <p
              className="text-[11px] text-text-tertiary mt-0.5"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              오늘의 {mealLabel} 추천 요약과 시스템 상태를 한눈에 확인합니다.
            </p>
            <div className="mt-2">
              <MealTimeSelector value={mealType} onChange={setMealType} compact />
            </div>
          </div>
          <div className="text-right">
            <p className="text-[10px] text-text-tertiary uppercase tracking-[0.08em]">
              Local Server Time
            </p>
            <p className="text-lg font-heading font-bold text-text-primary tracking-tight">
              {now || "—"}
            </p>
          </div>
        </div>

        {/* KPI */}
        <KPICards
          totalRestaurants={lunchStats?.active ?? restaurants.length}
          trackedMeals={trackedMeals}
          avgSentiment={avgSentiment}
          chatLatencyMs={chatLatencyMs}
        />

        {/* Row: Category (6) + NLP Status (4) */}
        <div className="grid grid-cols-1 md:grid-cols-10 gap-4 mt-6">
          <div className="md:col-span-6">
            <CategoryChart categories={categories} />
          </div>
          <div className="md:col-span-4">
            <OllamaStatus />
          </div>
        </div>

        {/* Today's Top 5 + For You (ML personalized) */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <TodaysTop5 items={top5} />
          <ForYouCard userId={DEFAULT_USER_ID} />
        </div>
      </div>
    </div>
  );
}
