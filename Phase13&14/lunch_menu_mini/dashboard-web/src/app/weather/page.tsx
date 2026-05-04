"use client";

import { useEffect, useMemo, useState } from "react";
import CurrentWeatherCard from "@/components/weather/CurrentWeatherCard";
import WeatherTips from "@/components/weather/WeatherTips";
import MenuFitnessChart, {
  type MenuFitnessRow,
} from "@/components/weather/MenuFitnessChart";
import WeatherTopPicks, {
  type WeatherScoredRestaurant,
} from "@/components/weather/WeatherTopPicks";
import WeatherMoodSelector from "@/components/weather/WeatherMoodSelector";
import LocationSelector, {
  type LocationOption,
} from "@/components/weather/LocationSelector";
import {
  useRestaurants,
  useNearbyRestaurants,
  useWeatherCurrent,
} from "@/lib/queries";
import { useGeolocation } from "@/lib/useGeolocation";
import { getWeatherScore } from "@/lib/scoring";
import type { MoodOption, WeatherNow, MoodRecommendationItem, Restaurant, MealType } from "@/lib/types";
import { loadStoredMealType } from "@/components/concierge/MealTimeSelector";

/* ------------------------------------------------------------------ */
/* 프론트엔드 로컬 무드 옵션 생성 (백엔드 불필요)                       */
/* mealType 이 지정되면 시간대별 무드 옵션을 가장 위에 prepend        */
/* ------------------------------------------------------------------ */
function buildMoodOptions(w: WeatherNow, mealType: MealType = "any"): MoodOption[] {
  const opts: MoodOption[] = [];
  const rainy = w.rain > 50 || (w.rainTypeStr != null && w.rainTypeStr !== "없음");

  // 시간대별 전용 무드 (heavy 옵션 / 다중 식사 시간)
  if (mealType === "breakfast") {
    opts.push(
      { id: "morning_coffee", emoji: "☕", label: "카페인 충전", description: "출근길 카페·베이커리에서 빠르게" },
      { id: "brunch", emoji: "🥞", label: "브런치 갈래요", description: "느긋하게 브런치 카페" },
      { id: "light_morning", emoji: "🍞", label: "가볍게 시작", description: "샌드위치·죽·김밥 가벼운 한 끼" },
    );
  } else if (mealType === "dinner") {
    opts.push(
      { id: "team_dinner", emoji: "🍷", label: "회식 분위기", description: "한식·일식 회식 가능한 곳" },
      { id: "family_dinner", emoji: "🥘", label: "가족 식사", description: "다양한 메뉴, 푸짐한 식사" },
      { id: "after_work", emoji: "🍻", label: "한 잔 곁들여", description: "퇴근 후 술집·이자카야" },
    );
  }

  if (rainy) {
    opts.push(
      { id: "stay_close", emoji: "🏠", label: "나가기 싫어요", description: "가까운 곳에서 빠르게 해결" },
      { id: "soup_craving", emoji: "🍜", label: "국물이 땡겨요", description: "따뜻한 국물요리가 먹고 싶어요" },
      { id: "rain_anju", emoji: "🍶", label: "막걸리+안주 먹고싶어요", description: "비 오는 날 전에 막걸리 한잔" },
      { id: "rainy_walk", emoji: "🚶", label: "산책 겸 다녀올래요", description: "비 소리 들으며 여유롭게" },
    );
  }
  if (w.temp < 10) {
    opts.push(
      { id: "warm_food", emoji: "🔥", label: "따뜻한 음식이요", description: "추운 날씨에 몸을 녹일 음식" },
      { id: "spicy_craving", emoji: "🌶️", label: "매운거 먹고싶어요", description: "얼큰하고 매운 음식으로" },
    );
    if (!rainy) opts.push({ id: "stay_close", emoji: "🏠", label: "나가기 싫어요", description: "추워서 가까운 곳에서" });
  }
  if (w.temp >= 10 && w.temp < 17) {
    opts.push(
      { id: "soup_craving", emoji: "🍜", label: "국물이 땡겨요", description: "쌀쌀한 날씨에 따뜻한 국물" },
      { id: "warm_food", emoji: "🔥", label: "든든하게 먹고싶어요", description: "몸을 녹이는 따뜻한 식사" },
    );
  }
  if (w.temp >= 28) {
    opts.push(
      { id: "cool_food", emoji: "🧊", label: "시원한 음식이요", description: "더위를 식힐 냉면이나 초밥" },
      { id: "light_meal", emoji: "🥗", label: "가볍게 먹을래요", description: "더운 날 가벼운 식사" },
    );
  }
  if (w.dust === "나쁨" || w.dust === "매우나쁨") {
    opts.push({ id: "indoor_only", emoji: "😷", label: "실내에서만 먹을래요", description: "미세먼지가 나빠서 실내 식당만" });
  }
  if ((w.sky === "흐림" || w.sky === "구름많음") && !rainy) {
    opts.push({ id: "spicy_craving", emoji: "🌶️", label: "매운거 먹고싶어요", description: "흐린 날 얼큰한 한 그릇" });
  }
  if (w.temp >= 17 && w.temp <= 25 && !rainy && w.dust !== "나쁨" && w.dust !== "매우나쁨") {
    opts.push({ id: "walk_enjoy", emoji: "🚶", label: "좀 걸어가도 좋아요", description: "날씨가 좋으니 멀어도 괜찮아요" });
  }
  opts.push(
    { id: "stay_close", emoji: "🏠", label: "가까운 곳에서", description: "가까운 곳에서 빠르게" },
    { id: "default", emoji: "😐", label: "평소대로 먹을래요", description: "날씨 상관없이 평소처럼" },
  );

  // 중복 id 제거
  const seen = new Set<string>();
  return opts.filter((o) => {
    if (seen.has(o.id)) return false;
    seen.add(o.id);
    return true;
  });
}

/* ------------------------------------------------------------------ */
/* 프론트엔드 로컬 무드 점수 계산                                       */
/* ------------------------------------------------------------------ */
function calcMoodScore(r: Restaurant, w: WeatherNow, moodId: string): { score: number; reason: string } {
  let base = 50;
  let reason = "날씨 기본 추천";

  // 날씨 기본 보너스
  if (w.temp < 10 && ["국물", "죽", "탕"].includes(r.menuType)) base += 25;
  if (w.temp > 28 && ["면류", "초밥"].includes(r.menuType)) base += 20;
  const rainy = w.rain > 50;
  if (rainy && r.distance <= 200) base += 10;

  switch (moodId) {
    case "stay_close":
      if (r.distance <= 100) { base += 30; reason = "100m 이내 초근접"; }
      else if (r.distance <= 200) { base += 15; reason = "200m 이내 가까운 거리"; }
      else if (r.distance >= 300) { base -= 25; reason = "거리가 멀어요"; }
      break;
    case "soup_craving":
      if (["국물", "죽", "탕"].includes(r.menuType)) { base += 35; reason = "따뜻한 국물 요리"; }
      else if (r.menuType === "면류") { base += 15; reason = "따뜻한 면 요리"; }
      else base -= 10;
      break;
    case "rain_anju":
      if (r.category === "한식" || r.menuType === "국물") { base += 25; reason = "비 오는 날 한식 안주"; }
      break;
    case "rainy_walk":
      if (r.distance >= 200 && r.distance <= 400) { base += 20; reason = "산책하기 좋은 거리"; }
      else if (r.distance > 400) { base += 10; reason = "여유롭게 걸어가기"; }
      break;
    case "warm_food":
      if (["국물", "죽", "탕"].includes(r.menuType)) { base += 30; reason = "몸을 녹이는 국물"; }
      else if (r.menuType === "면류") { base += 20; reason = "따뜻한 면 요리"; }
      break;
    case "spicy_craving":
      if (r.menuType === "국물") { base += 20; reason = "매운탕·찌개류"; }
      break;
    case "cool_food":
      if (["초밥", "샐러드"].includes(r.menuType)) { base += 35; reason = "시원한 한 그릇"; }
      break;
    case "light_meal":
      if (["샐러드", "샌드위치", "카페"].includes(r.menuType)) { base += 30; reason = "가벼운 식사"; }
      break;
    case "indoor_only":
      if (r.indoor) { base += 25; reason = "실내 식당"; } else base -= 30;
      break;
    case "walk_enjoy":
      if (r.distance >= 300) { base += 15; reason = "날씨 좋은 날 산책 코스"; }
      base += 5;
      break;
    // ── 시간대별 무드 (heavy 옵션) ──
    case "morning_coffee":
      if (["카페", "베이커리"].includes(r.category)) { base += 35; reason = "출근길 카페 한 잔"; }
      else if (["김밥", "샌드위치"].includes(r.category)) { base += 15; reason = "가벼운 아침"; }
      break;
    case "brunch":
      if (["브런치", "카페", "베이커리"].includes(r.category)) { base += 30; reason = "느긋한 브런치"; }
      break;
    case "light_morning":
      if (["김밥", "죽", "샌드위치", "분식", "도시락"].includes(r.category)) { base += 30; reason = "가벼운 아침 한 끼"; }
      break;
    case "team_dinner":
      if (["한식", "일식", "고깃집", "구이", "뷔페"].includes(r.category)) { base += 30; reason = "회식하기 좋은 곳"; }
      break;
    case "family_dinner":
      if (["한식", "일식", "중식", "양식", "뷔페", "샤브샤브"].includes(r.category)) { base += 25; reason = "가족 식사 메뉴"; }
      break;
    case "after_work":
      if (["술집", "주점", "이자카야", "호프", "곱창", "치킨"].includes(r.category)) { base += 30; reason = "퇴근 후 한 잔"; }
      break;
  }
  return { score: Math.max(0, Math.min(100, base)), reason };
}

/* ================================================================== */
/* 페이지 컴포넌트                                                     */
/* ================================================================== */
export default function WeatherPage() {
  const { position, loading: geoLoading, error: geoError } = useGeolocation();
  const [manualLocation, setManualLocation] = useState<LocationOption | null>(null);
  // 시각/저장된 선호 기반 자동 mealType — Mood 옵션의 시간대별 다양화에 사용
  const [mealType, setMealType] = useState<MealType>("any");
  useEffect(() => {
    setMealType(loadStoredMealType());
  }, []);

  const finalLat = manualLocation?.lat ?? position?.lat;
  const finalLng = manualLocation?.lng ?? position?.lng;
  const locationLabel = manualLocation
    ? manualLocation.label
    : position == null
    ? "위치 확인 중..."
    : position.source === "gps"
    ? `GPS (${position.lat.toFixed(4)}, ${position.lng.toFixed(4)})`
    : position.source === "default"
    ? position.label ?? "기본 위치"
    : position.label ?? "IP 기반 위치";
  const locationSource: "gps" | "ip" | "default" | "manual" = manualLocation
    ? "manual"
    : position?.source ?? "ip";

  // 위치 기반 풀 우선, 좌표 미확보 시 전체 풀로 폴백 (Discover 와 동일 패턴)
  const { data: nearby = [], isLoading: nearbyLoading } = useNearbyRestaurants(
    finalLat,
    finalLng,
    2000,
    100,
  );
  const { data: fallback = [], isLoading: restLoading } = useRestaurants();
  const restaurants: Restaurant[] = nearby.length > 0 ? nearby : fallback;
  const restaurantsLoading =
    nearbyLoading || (nearby.length === 0 && restLoading);
  const { data: weather } = useWeatherCurrent(finalLat, finalLng);

  // 무드 선택 상태
  const [selectedMood, setSelectedMood] = useState<string | null>(null);

  // --- 무드 옵션: weather + mealType 기반 (시간대별 다양화) ---
  const moodOptions = useMemo(() => {
    if (!weather) return [];
    return buildMoodOptions(weather, mealType);
  }, [weather, mealType]);

  const weatherSummary = useMemo(() => {
    if (!weather) return "";
    const rainy = weather.rain > 50 || (weather.rainTypeStr != null && weather.rainTypeStr !== "없음");
    return `${weather.temp}°C · ${weather.sky}${rainy ? " · 비" : ""}`;
  }, [weather]);

  // --- 무드 추천: 로컬 점수 계산 ---
  const moodRecommendations: MoodRecommendationItem[] = useMemo(() => {
    if (!selectedMood || !weather) return [];
    return restaurants
      .map((r) => {
        const { score, reason } = calcMoodScore(r, weather, selectedMood);
        return {
          restaurant_id: String(r.id),
          restaurant_name: r.name,
          category: r.category,
          menu_type: r.menuType,
          distance_m: r.distance,
          mood_score: score,
          reason,
        };
      })
      .sort((a, b) => b.mood_score - a.mood_score)
      .slice(0, 5);
  }, [selectedMood, weather, restaurants]);

  // 기존 점수 기반 데이터
  const scored: WeatherScoredRestaurant[] = useMemo(() => {
    if (!weather) return [];
    return restaurants
      .map((r) => ({ ...r, weatherScore: getWeatherScore(r, weather) }))
      .sort((a, b) => b.weatherScore - a.weatherScore);
  }, [restaurants, weather]);

  const menuTypeData: MenuFitnessRow[] = useMemo(() => {
    const acc = new Map<string, { total: number; count: number }>();
    for (const r of scored) {
      const cur = acc.get(r.menuType) ?? { total: 0, count: 0 };
      cur.total += r.weatherScore;
      cur.count += 1;
      acc.set(r.menuType, cur);
    }
    return Array.from(acc.entries())
      .map(([type, { total, count }]) => ({
        type,
        avgScore: Math.round(total / count),
      }))
      .sort((a, b) => b.avgScore - a.avgScore);
  }, [scored]);

  return (
    <div>
      {/* Mobile header — App Store Today 스타일 */}
      <header className="md:hidden mb-5">
        <p className="appstore-eyebrow">WEATHER</p>
        <h1 className="appstore-title mt-1">날씨 추천</h1>
        <p className="text-[12px] text-text-tertiary mt-1.5"
           style={{ fontFamily: "var(--font-ko)" }}>
          기온 · 미세먼지 · 강수에 맞는 메뉴
        </p>
        <div className="mt-3">
          <LocationSelector
            current={{ lat: finalLat ?? 0, lng: finalLng ?? 0, label: locationLabel }}
            onSelect={setManualLocation}
            geoSource={locationSource}
            geoError={geoError}
            loading={geoLoading}
          />
        </div>
      </header>

      {/* Desktop header */}
      <div className="hidden md:flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary uppercase tracking-tight">
            Weather
          </h1>
          <p className="text-xs text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            Climate-Aware Menu Recommendation
          </p>
          <p
            className="text-[11px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            기온 · 미세먼지 · 강수확률에 따른 메뉴 유형 매칭
          </p>
          <div className="mt-1.5">
            <LocationSelector
              current={{ lat: finalLat ?? 0, lng: finalLng ?? 0, label: locationLabel }}
              onSelect={setManualLocation}
              geoSource={locationSource}
              geoError={geoError}
              loading={geoLoading}
            />
          </div>
        </div>
      </div>

      {/* 현재 날씨 + 팁 */}
      {weather && <CurrentWeatherCard weather={weather} />}
      {weather && <WeatherTips weather={weather} />}

      {/* 무드 선택 */}
      {moodOptions.length > 0 && (
        <WeatherMoodSelector
          options={moodOptions}
          selected={selectedMood}
          onSelect={(id) =>
            setSelectedMood((prev) => (prev === id ? null : id))
          }
          weatherSummary={weatherSummary}
        />
      )}

      {/* 무드 선택 시 → 개인화 추천 */}
      {selectedMood && moodRecommendations.length > 0 && (
        <div className="bento-card mb-5">
          <h3
            className="text-base font-bold text-text-primary mb-3 flex items-center gap-2"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            <span className="text-xl">
              {moodOptions.find((o) => o.id === selectedMood)?.emoji || "⭐"}
            </span>
            {moodOptions.find((o) => o.id === selectedMood)?.label || "맞춤 추천"}
          </h3>
          <div className="space-y-2">
            {moodRecommendations.map((item, idx) => {
              const highlight = idx === 0;
              return (
                <div
                  key={item.restaurant_id}
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
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-text-primary truncate">
                      {item.restaurant_name}
                    </div>
                    <div className="text-[11px] text-text-tertiary font-mono">
                      {item.menu_type || item.category || "기타"} · {item.distance_m}m
                    </div>
                    <div
                      className="text-[10px] text-primary/80 mt-0.5"
                      style={{ fontFamily: "var(--font-ko)" }}
                    >
                      {item.reason}
                    </div>
                  </div>
                  <div className="text-lg font-heading font-bold text-success leading-none">
                    {item.mood_score}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 기존 차트 + Top 5 */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <MenuFitnessChart data={menuTypeData} />
        </div>
        <div className="lg:col-span-2">
          <WeatherTopPicks
            items={scored}
            userLat={finalLat}
            userLng={finalLng}
            loading={restaurantsLoading}
          />
        </div>
      </div>
    </div>
  );
}
