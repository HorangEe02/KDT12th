/**
 * Reusable TanStack Query hooks for Mini NLP/Lunch endpoints.
 * Keeping hook names short + consistent so pages stay tidy.
 */
import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { apiFetchLunch, apiFetchNLP } from "./api";
import { isWarmingUp } from "./errors";

/**
 * Retry policy for NLP calls:
 *  - 503 warming up  → retry up to 5× with exponential backoff
 *  - any other error → fail fast (no retry)
 */
const nlpRetry = (count: number, err: unknown) =>
  isWarmingUp(err) && count < 5;
const nlpRetryDelay = (attempt: number, err: unknown) => {
  if (isWarmingUp(err) && err.retryAfter) return err.retryAfter * 1000;
  return Math.min(1000 * 2 ** attempt, 10_000);
};
import {
  adaptRestaurant,
  adaptTrendToWeekly,
  adaptWeather,
  adaptWeeklyNutrition,
} from "./adapters";
import {
  RESTAURANTS as MOCK_RESTAURANTS,
  WEATHER as MOCK_WEATHER,
  WEEKLY_NUTRITION as MOCK_NUTRITION,
} from "./mock";
import type {
  ChatMessage,
  LunchStatsOut,
  NaturalMealAnalysisOut,
  NaturalMealPayload,
  MenuStatsOut,
  MoodOption,
  ModelListResponse,
  MoodRecommendationGroup,
  MoodRecommendationItem,
  NLPHealth,
  NutritionParseOut,
  NutrientTrendItem,
  RecentVisitItem,
  Restaurant,
  RestaurantApiOut,
  SentimentOut,
  SentimentTopItem,
  SettingsResponse,
  TeamMember,
  UserAccount,
  VoteStatusOut,
  WeatherCurrentApiOut,
  WeatherMoodOptionsOut,
  WeatherNow,
  WeeklyNutritionApiOut,
  WeeklyNutritionDay,
  WeeklyReportOut,
  NutritionTargetsOut,
} from "./types";
import { TEAM as MOCK_TEAM } from "./mock";

export function useNLPHealth() {
  return useQuery({
    queryKey: ["nlp", "health"],
    queryFn: () => apiFetchNLP<NLPHealth>("/nlp/health"),
    refetchInterval: 10_000,
    retry: nlpRetry,
    retryDelay: nlpRetryDelay,
  });
}

export function useSentimentTop(limit = 10) {
  return useQuery({
    queryKey: ["nlp", "sentiment", "top", limit],
    queryFn: () =>
      apiFetchNLP<SentimentTopItem[]>(`/nlp/sentiment/top?limit=${limit}`),
    retry: false,
  });
}

export function useSentimentFor(restaurantId: number | string) {
  return useQuery({
    queryKey: ["nlp", "sentiment", String(restaurantId)],
    queryFn: () =>
      apiFetchNLP<SentimentOut>(`/nlp/sentiment/${restaurantId}`),
    retry: false,
  });
}

export function useMenuStats() {
  return useQuery({
    queryKey: ["nlp", "menu", "stats"],
    queryFn: () => apiFetchNLP<MenuStatsOut>("/nlp/menu/stats"),
    retry: false,
  });
}

export function useChatbotStats() {
  return useQuery({
    queryKey: ["nlp", "chatbot", "stats"],
    queryFn: () => apiFetchNLP<Record<string, unknown>>("/nlp/chatbot/stats"),
    refetchInterval: 15_000,
    retry: false,
  });
}

export function useWeeklyReport(userId: string | number) {
  const uid = String(userId);
  return useQuery({
    queryKey: ["nlp", "reports", "weekly", uid],
    queryFn: () =>
      apiFetchNLP<WeeklyReportOut>(`/nlp/reports/weekly/${encodeURIComponent(uid)}`),
    retry: nlpRetry,
    retryDelay: nlpRetryDelay,
  });
}

export function useAnalyzeMealText() {
  return useMutation({
    mutationFn: async (payload: {
      user_id: string;
      text: string;
      base_date?: string;
      locale?: string;
      restaurant_id?: string | null;
      restaurant_snapshot?: NaturalMealPayload["restaurant_snapshot"];
    }) => {
      const parsed = await apiFetchNLP<NutritionParseOut>("/nlp/nutrition/parse", {
        method: "POST",
        body: JSON.stringify({
          user_id: payload.user_id,
          text: payload.text,
          base_date: payload.base_date,
          locale: payload.locale ?? "ko-KR",
        }),
      });
      const previewPayload: NaturalMealPayload = {
        user_id: payload.user_id,
        raw_text: parsed.raw_text,
        meal_date: parsed.meal_date,
        meal_type: parsed.meal_type,
        restaurant_id: payload.restaurant_id ?? null,
        restaurant_snapshot: payload.restaurant_snapshot ?? null,
        satisfaction: parsed.satisfaction ?? null,
        items: parsed.items.map((item) => ({
          raw_name: item.raw_name,
          normalized_name: item.normalized_name,
          quantity: item.quantity,
          unit: item.unit,
          needs_review: item.needs_review,
          match_confidence: item.confidence,
          match_type: "nlp_parse",
          source: null,
        })),
      };
      const analysis = await apiFetchLunch<NaturalMealAnalysisOut>(
        "/nutrition/meal-natural/preview",
        { method: "POST", body: JSON.stringify(previewPayload) }
      );
      return { parsed, analysis };
    },
  });
}

export function useSaveNaturalMeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: NaturalMealPayload) =>
      apiFetchLunch<NaturalMealAnalysisOut>("/nutrition/meal-natural", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (_data, variables) => {
      const uid = String(variables.user_id);
      queryClient.invalidateQueries({ queryKey: ["lunch", "nutrition", "weekly", uid] });
      queryClient.invalidateQueries({ queryKey: ["lunch", "nutrition", "meals", uid] });
      queryClient.invalidateQueries({ queryKey: ["nlp", "reports", "weekly", uid] });
    },
  });
}

export function useMealHistory(userId: string | number, limit = 20) {
  const uid = String(userId);
  return useQuery<NaturalMealAnalysisOut[]>({
    queryKey: ["lunch", "nutrition", "meals", uid, limit],
    queryFn: async () => {
      try {
        return await apiFetchLunch<NaturalMealAnalysisOut[]>(
          `/nutrition/meals?user_id=${encodeURIComponent(uid)}&limit=${limit}`
        );
      } catch (e) {
        console.warn("[useMealHistory] failed", e);
        return [];
      }
    },
    retry: false,
    placeholderData: [],
  });
}

export function useDeleteMeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ mealId, userId }: { mealId: number; userId: string | number }) =>
      apiFetchLunch<{ deleted: boolean; meal_id: number }>(
        `/nutrition/meals/${mealId}?user_id=${encodeURIComponent(String(userId))}`,
        { method: "DELETE" }
      ),
    onSuccess: (_data, variables) => {
      const uid = String(variables.userId);
      queryClient.invalidateQueries({ queryKey: ["lunch", "nutrition", "weekly", uid] });
      queryClient.invalidateQueries({ queryKey: ["lunch", "nutrition", "meals", uid] });
      queryClient.invalidateQueries({ queryKey: ["nlp", "reports", "weekly", uid] });
    },
  });
}

export function useOllamaModels() {
  return useQuery({
    queryKey: ["nlp", "models"],
    queryFn: () => apiFetchNLP<ModelListResponse>("/nlp/models"),
    retry: false,
    refetchInterval: 30_000,
  });
}

export function useNLPSettings() {
  return useQuery({
    queryKey: ["nlp", "settings"],
    queryFn: () => apiFetchNLP<SettingsResponse>("/nlp/settings"),
    retry: false,
    refetchInterval: 15_000,
  });
}

// =============================================================================
// Phase 6 research v2 (A2 ABSA · E1 ML personalization)
// =============================================================================
export interface V2AspectSentiment {
  aspect: string;
  sentiment: "positive" | "neutral" | "negative";
  confidence: number;
  score: number;
}

export interface V2ABSAResponse {
  restaurant_id: string;
  aspects: V2AspectSentiment[];
  backend: "trained" | "dummy" | "seeded";
}

export function useV2Sentiment(
  restaurantId: string | number | null,
  enabled = true,
) {
  const ridStr = restaurantId == null ? "" : String(restaurantId);
  return useQuery<V2ABSAResponse>({
    queryKey: ["nlp", "v2", "sentiment", ridStr],
    queryFn: () =>
      apiFetchNLP<V2ABSAResponse>(
        `/nlp/v2/sentiment/${encodeURIComponent(ridStr)}`,
      ),
    retry: false,
    enabled: enabled && ridStr.length > 0,
    staleTime: 5 * 60_000,
  });
}

interface V2Recommendation {
  menu: string;
  restaurant?: string | null;
  score: number;
  similar_user_count: number;
  reason?: string | null;
}

interface V2RecommendResponse {
  user_id: string;
  recommendations: V2Recommendation[];
  backend: string;
}

export function useV2Recommendations(
  userId: number | string,
  topN = 5,
  enabled = true,
) {
  return useQuery<V2RecommendResponse>({
    queryKey: ["nlp", "v2", "recommend", String(userId), topN],
    queryFn: () =>
      apiFetchNLP<V2RecommendResponse>(
        `/nlp/v2/recommend?user_id=${encodeURIComponent(String(userId))}&top_n=${topN}`,
      ),
    retry: false,
    enabled,
    staleTime: 5 * 60_000,
  });
}

// =============================================================================
// lunch-optimizer hooks (Phase 2 wiring)
//
// Each hook tries the real API first; on failure it falls back to mock so
// the UI keeps working even if lunch-optimizer is offline.
// =============================================================================
export function useRestaurants() {
  return useQuery<Restaurant[]>({
    queryKey: ["lunch", "restaurants"],
    queryFn: async () => {
      try {
        const raw = await apiFetchLunch<RestaurantApiOut[]>(
          "/restaurants?limit=200"
        );
        if (Array.isArray(raw) && raw.length > 0) {
          return raw.map(adaptRestaurant);
        }
        return MOCK_RESTAURANTS;
      } catch {
        return MOCK_RESTAURANTS;
      }
    },
    retry: false,
    refetchInterval: 60_000,
    placeholderData: MOCK_RESTAURANTS,
  });
}

/**
 * 사용자 현재 위치 기반 주변 음식점 검색 (#위치기반).
 *
 * - 백엔드의 /api/restaurants/nearby 를 호출 → 서버에서 5분 TTL + 100m 그리드 캐싱
 * - 프론트 queryKey 에 100m 그리드 좌표를 포함 → 100m 이상 이동해야 재요청
 * - staleTime 5분 → 탭 포커스만으로 재요청 방지
 */
export function useNearbyRestaurants(
  lat: number | undefined,
  lng: number | undefined,
  radius: number = 800,
  limit: number = 50
) {
  // 100m 그리드로 키 양자화 (서버 캐시 정책과 일치)
  const keyLat = lat != null ? Math.round(lat * 1000) / 1000 : 0;
  const keyLng = lng != null ? Math.round(lng * 1000) / 1000 : 0;
  const hasCoords = lat != null && lng != null;

  return useQuery<Restaurant[]>({
    queryKey: ["lunch", "nearby", keyLat, keyLng, radius, limit],
    enabled: hasCoords,
    queryFn: async () => {
      try {
        const raw = await apiFetchLunch<RestaurantApiOut[]>(
          `/restaurants/nearby?lat=${lat}&lng=${lng}&radius=${radius}&limit=${limit}`
        );
        if (Array.isArray(raw) && raw.length > 0) {
          return raw.map(adaptRestaurant);
        }
        return [];
      } catch (e) {
        console.warn("[useNearbyRestaurants] failed", e);
        return [];
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: false,
    placeholderData: keepPreviousData,
  });
}

/**
 * 다중 식사 시간 추천 — meal_type-aware 위치 기반 식당 추천 (헤비 옵션).
 * 백엔드 `/api/restaurants/recommend` 호출. nearby 와 같은 위치 데이터를
 * 재사용하지만 meal_type 카테고리 화이트리스트로 필터링됨.
 */
export function useMealRecommend(
  lat: number | undefined,
  lng: number | undefined,
  mealType: string = "any",
  radius: number = 2000,
  limit: number = 50,
) {
  const keyLat = lat != null ? Math.round(lat * 1000) / 1000 : 0;
  const keyLng = lng != null ? Math.round(lng * 1000) / 1000 : 0;
  const hasCoords = lat != null && lng != null;

  return useQuery<Restaurant[]>({
    queryKey: ["lunch", "recommend", keyLat, keyLng, mealType, radius, limit],
    enabled: hasCoords,
    queryFn: async () => {
      try {
        const raw = await apiFetchLunch<RestaurantApiOut[]>(
          `/restaurants/recommend?lat=${lat}&lng=${lng}&meal_type=${encodeURIComponent(mealType)}&radius=${radius}&limit=${limit}`,
        );
        if (Array.isArray(raw) && raw.length > 0) {
          return raw.map(adaptRestaurant);
        }
        return [];
      } catch (e) {
        console.warn("[useMealRecommend] failed", e);
        return [];
      }
    },
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    retry: false,
    placeholderData: keepPreviousData,
  });
}

/**
 * 일일 영양 목표 — 식사 시간별 분배 비율 포함 (아침 25% / 점심 35% / 저녁 40%).
 */
export function useNutritionTargets(userId: string | number) {
  return useQuery<NutritionTargetsOut>({
    queryKey: ["lunch", "nutrition", "targets", String(userId)],
    queryFn: async () =>
      apiFetchLunch<NutritionTargetsOut>(
        `/nutrition/targets/${encodeURIComponent(String(userId))}`,
      ),
    staleTime: 60 * 60 * 1000, // 1 hour — 잘 안 변함
    retry: false,
  });
}

export function useLunchStats() {
  return useQuery<LunchStatsOut | null>({
    queryKey: ["lunch", "stats"],
    queryFn: async () => {
      try {
        return await apiFetchLunch<LunchStatsOut>("/restaurants/stats");
      } catch {
        return null;
      }
    },
    retry: false,
    refetchInterval: 60_000,
  });
}

export function useWeatherCurrent(lat?: number, lng?: number) {
  const hasLocation = lat !== undefined && lng !== undefined;
  const keyLat = hasLocation ? Math.round(lat * 100) / 100 : "default";
  const keyLng = hasLocation ? Math.round(lng * 100) / 100 : "default";

  return useQuery<WeatherNow>({
    queryKey: ["lunch", "weather", "current", keyLat, keyLng],
    queryFn: async () => {
      try {
        const params = hasLocation ? `?lat=${lat}&lng=${lng}` : "";
        const api = await apiFetchLunch<WeatherCurrentApiOut>(
          `/weather/current${params}`
        );
        return adaptWeather(api);
      } catch {
        return MOCK_WEATHER;
      }
    },
    retry: false,
    refetchInterval: 5 * 60_000,
    placeholderData: MOCK_WEATHER,
  });
}

export function useWeeklyNutrition(userId: string | number) {
  return useQuery<WeeklyNutritionDay[]>({
    queryKey: ["lunch", "nutrition", "weekly", String(userId)],
    queryFn: async () => {
      // Try /api/nutrition/weekly first
      try {
        const api = await apiFetchLunch<WeeklyNutritionApiOut>(
          `/nutrition/weekly?user_id=${encodeURIComponent(String(userId))}`
        );
        const adapted = adaptWeeklyNutrition(api);
        if (adapted.some((d) => d.calories > 0)) return adapted;
      } catch {
        /* fall through */
      }
      // Fallback: /api/nutrition/trend (last 5 days)
      try {
        const trend = await apiFetchLunch<NutrientTrendItem[]>(
          `/nutrition/trend?user_id=${encodeURIComponent(String(userId))}&days=5`
        );
        const adapted = adaptTrendToWeekly(trend);
        if (adapted.length > 0) return adapted;
      } catch {
        /* fall through */
      }
      return MOCK_NUTRITION;
    },
    retry: false,
    placeholderData: MOCK_NUTRITION,
  });
}

export function useVoteStatus(teamId: string) {
  return useQuery<VoteStatusOut | null>({
    queryKey: ["lunch", "vote", "status", teamId],
    queryFn: async () => {
      try {
        return await apiFetchLunch<VoteStatusOut>(
          `/vote/status?team_id=${encodeURIComponent(teamId)}`
        );
      } catch {
        return null;
      }
    },
    retry: false,
    // 실시간 협업을 위해 3초 간격 폴링 (탭 비활성 시 자동 중단)
    refetchInterval: 3_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
  });
}

export function useRecentVisits(teamId: string, days = 10) {
  return useQuery<RecentVisitItem[]>({
    queryKey: ["lunch", "history", "visits", teamId, days],
    queryFn: async () => {
      try {
        return await apiFetchLunch<RecentVisitItem[]>(
          `/history/visits?team_id=${encodeURIComponent(teamId)}&days=${days}`
        );
      } catch {
        return [];
      }
    },
    retry: false,
  });
}

// =============================================================================
// Mood-based Weather Recommendation
// =============================================================================
/**
 * 날씨 조건에 따라 클라이언트 측에서 무드 옵션을 생성하는 fallback.
 * 백엔드 /api/weather/mood-options 가 사용 불가능할 때 사용.
 */
function buildLocalMoodOptions(w: WeatherNow): WeatherMoodOptionsOut {
  const opts: WeatherMoodOptionsOut["mood_options"] = [];
  const rainy = w.rain > 50 || (w.rainTypeStr && w.rainTypeStr !== "없음");

  // --- 비 관련 ---
  if (rainy) {
    opts.push(
      { id: "stay_close", emoji: "🏠", label: "나가기 싫어요", description: "가까운 곳에서 빠르게 해결" },
      { id: "soup_craving", emoji: "🍜", label: "국물이 땡겨요", description: "따뜻한 국물요리가 먹고 싶어요" },
      { id: "rain_anju", emoji: "🍶", label: "막걸리+안주 먹고싶어요", description: "비 오는 날 전에 막걸리 한잔" },
      { id: "rainy_walk", emoji: "🚶", label: "산책 겸 다녀올래요", description: "비 소리 들으며 여유롭게" },
    );
  }

  // --- 추움 (10°C 미만) ---
  if (w.temp < 10) {
    opts.push(
      { id: "warm_food", emoji: "🔥", label: "따뜻한 음식이요", description: "추운 날씨에 몸을 녹일 음식" },
      { id: "spicy_craving", emoji: "🌶️", label: "매운거 먹고싶어요", description: "얼큰하고 매운 음식으로" },
    );
    if (!rainy) opts.push({ id: "stay_close", emoji: "🏠", label: "나가기 싫어요", description: "추워서 가까운 곳에서" });
  }

  // --- 쌀쌀 (10~17°C) — 기존에 빠져있던 구간 ---
  if (w.temp >= 10 && w.temp < 17) {
    opts.push(
      { id: "soup_craving", emoji: "🍜", label: "국물이 땡겨요", description: "쌀쌀한 날씨에 따뜻한 국물" },
      { id: "warm_food", emoji: "🔥", label: "든든하게 먹고싶어요", description: "몸을 녹이는 따뜻한 식사" },
    );
  }

  // --- 더움 (28°C 이상) ---
  if (w.temp >= 28) {
    opts.push(
      { id: "cool_food", emoji: "🧊", label: "시원한 음식이요", description: "더위를 식힐 냉면이나 초밥" },
      { id: "light_meal", emoji: "🥗", label: "가볍게 먹을래요", description: "더운 날 가벼운 식사" },
    );
  }

  // --- 미세먼지 ---
  if (w.dust === "나쁨" || w.dust === "매우나쁨") {
    opts.push({ id: "indoor_only", emoji: "😷", label: "실내에서만 먹을래요", description: "미세먼지가 나빠서 실내 식당만" });
  }

  // --- 흐림/구름 (비 아닌데 흐린 날) ---
  if ((w.sky === "흐림" || w.sky === "구름많음") && !rainy) {
    opts.push({ id: "spicy_craving", emoji: "🌶️", label: "매운거 먹고싶어요", description: "흐린 날 얼큰한 한 그릇" });
  }

  // --- 날씨 좋은 날 ---
  if (w.temp >= 17 && w.temp <= 25 && !rainy && w.dust !== "나쁨" && w.dust !== "매우나쁨") {
    opts.push({ id: "walk_enjoy", emoji: "🚶", label: "좀 걸어가도 좋아요", description: "날씨가 좋으니 멀어도 괜찮아요" });
  }

  // --- 항상 공통 옵션 ---
  opts.push(
    { id: "stay_close", emoji: "🏠", label: "가까운 곳에서", description: "가까운 곳에서 빠르게" },
    { id: "default", emoji: "😐", label: "평소대로 먹을래요", description: "날씨 상관없이 평소처럼" },
  );

  // 중복 id 제거 (첫 번째 항목 유지)
  const seen = new Set<string>();
  const unique = opts.filter((o) => {
    if (seen.has(o.id)) return false;
    seen.add(o.id);
    return true;
  });

  const summary = `${w.temp}°C · ${w.sky}${rainy ? " · 비" : ""}`;
  return { weather_summary: summary, mood_options: unique };
}

export function useWeatherMoodOptions(lat?: number, lng?: number, weather?: WeatherNow) {
  const hasLocation = lat !== undefined && lng !== undefined;
  // weather를 키에 포함 — weather 로딩 후 재실행 보장
  const weatherKey = weather ? `${weather.temp}_${weather.sky}_${weather.rain}` : "none";
  return useQuery<WeatherMoodOptionsOut | null>({
    queryKey: ["lunch", "weather", "mood-options", lat, lng, weatherKey],
    queryFn: async () => {
      try {
        const params = hasLocation ? `?lat=${lat}&lng=${lng}` : "";
        const result = await apiFetchLunch<WeatherMoodOptionsOut>(
          `/weather/mood-options${params}`
        );
        if (result && result.mood_options && result.mood_options.length > 0) {
          return result;
        }
      } catch {
        // fallback below
      }
      // 백엔드 실패 시 → 클라이언트 weather 기반 옵션 생성
      if (weather) return buildLocalMoodOptions(weather);
      return buildLocalMoodOptions(MOCK_WEATHER);
    },
    retry: false,
    refetchInterval: 5 * 60_000,
  });
}

/**
 * 프론트엔드 로컬 무드 점수 계산 — 백엔드 API 실패 시 fallback.
 */
function localMoodScore(
  r: Restaurant,
  w: WeatherNow,
  moodId: string,
): { score: number; reason: string } {
  let base = 50;
  let reason = "날씨 기본 추천";

  // weather base
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
      if (r.category === "한식" || ["한식", "국물"].includes(r.menuType)) { base += 25; reason = "비 오는 날 한식 안주"; }
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
      if (r.indoor) { base += 25; reason = "실내 식당"; }
      else base -= 30;
      break;
    case "walk_enjoy":
      if (r.distance >= 300) { base += 15; reason = "날씨 좋은 날 산책 코스"; }
      base += 5;
      break;
  }

  return { score: Math.max(0, Math.min(100, base)), reason };
}

export function useMoodRecommendation(
  moodId: string | null,
  lat?: number,
  lng?: number,
  limit = 10
) {
  const hasLocation = lat !== undefined && lng !== undefined;
  return useQuery<MoodRecommendationItem[]>({
    queryKey: ["lunch", "weather", "mood-recommend", moodId, lat, lng],
    queryFn: async () => {
      if (!moodId) return [];
      try {
        const locParams = hasLocation ? `&lat=${lat}&lng=${lng}` : "";
        const resp = await apiFetchLunch<{ groups: MoodRecommendationGroup[] }>(
          `/weather/mood-recommend?mood_id=${encodeURIComponent(moodId)}&limit=${limit}${locParams}`
        );
        const items = resp.groups.flatMap((g) => g.items);
        if (items.length > 0) return items;
      } catch {
        // fallback below
      }
      // 백엔드 실패 → 프론트엔드 로컬 점수로 fallback
      const restaurants = MOCK_RESTAURANTS;
      const weather = MOCK_WEATHER;
      return restaurants
        .map((r) => {
          const { score, reason } = localMoodScore(r, weather, moodId);
          return {
            restaurant_id: String(r.id),
            restaurant_name: r.name,
            category: r.category,
            menu_type: r.menuType,
            distance_m: r.distance,
            mood_score: score,
            reason,
          } as MoodRecommendationItem;
        })
        .sort((a, b) => b.mood_score - a.mood_score)
        .slice(0, limit);
    },
    enabled: !!moodId,
    retry: false,
  });
}

export function useGroupedRecommendations(lat?: number, lng?: number) {
  const hasLocation = lat !== undefined && lng !== undefined;
  return useQuery<MoodRecommendationGroup[]>({
    queryKey: ["lunch", "weather", "grouped", lat, lng],
    queryFn: async () => {
      try {
        const params = hasLocation ? `?lat=${lat}&lng=${lng}` : "";
        return await apiFetchLunch<MoodRecommendationGroup[]>(
          `/weather/grouped-recommend${params}`
        );
      } catch {
        return [];
      }
    },
    retry: false,
    refetchInterval: 5 * 60_000,
  });
}


// =============================================================================
// Team Members — 팀 기반 멤버 조회
// =============================================================================
export function useTeamMembers(teamId: string | undefined) {
  return useQuery<TeamMember[]>({
    queryKey: ["team", "members", teamId],
    enabled: !!teamId,
    queryFn: async () => {
      try {
        const users = await apiFetchLunch<UserAccount[]>(
          `/users?team_id=${encodeURIComponent(teamId!)}`
        );
        return users
          .filter((u) => u.is_active)
          .map((u) => ({
            id: u.id,
            name: u.name,
            vote: null,
            avatar: u.avatar_emoji,
          }));
      } catch {
        // 백엔드 실패 시 목 데이터 폴백
        return MOCK_TEAM.map((t) => ({ ...t }));
      }
    },
    retry: false,
    staleTime: 30_000,
  });
}


// =============================================================================
// Chat History — 초기 로드용
// =============================================================================
export function useChatHistory(teamId: string | undefined, limit = 50) {
  return useQuery<ChatMessage[]>({
    queryKey: ["chat", "history", teamId, limit],
    enabled: !!teamId,
    queryFn: async () => {
      try {
        return await apiFetchLunch<ChatMessage[]>(
          `/chat/messages?team_id=${encodeURIComponent(teamId!)}&limit=${limit}`
        );
      } catch {
        return [];
      }
    },
    retry: false,
    staleTime: 60_000,
  });
}


// =============================================================================
// Buddy (밥친구 찾기)
// =============================================================================
import type { BuddyPostOut, BuddyJoinResult } from "./types";

export function useBuddyPosts(teamId: string | undefined, dateStr?: string) {
  const qs = new URLSearchParams();
  if (teamId) qs.set("team_id", teamId);
  if (dateStr) qs.set("date", dateStr);

  return useQuery<BuddyPostOut[]>({
    queryKey: ["buddy", "posts", teamId, dateStr ?? "today"],
    enabled: !!teamId,
    queryFn: async () => {
      try {
        return await apiFetchLunch<BuddyPostOut[]>(`/buddy/posts?${qs}`);
      } catch {
        return [];
      }
    },
    retry: false,
    staleTime: 15_000,
    refetchInterval: 30_000, // WebSocket 보조용 폴링
  });
}

export function useCreateBuddyPost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      team_id: string;
      author_id: string;
      restaurant_id?: string | null;
      restaurant_name: string;
      meal_date?: string;
      meal_time: string;
      max_buddies?: number;
      message?: string;
    }) => {
      return apiFetchLunch<BuddyPostOut>("/buddy/posts", {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["buddy", "posts"] });
    },
  });
}

export function useJoinBuddyPost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ postId, userId }: { postId: number; userId: string }) => {
      return apiFetchLunch<BuddyJoinResult>(`/buddy/posts/${postId}/join`, {
        method: "POST",
        body: JSON.stringify({ user_id: userId }),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["buddy", "posts"] });
    },
  });
}

export function useLeaveBuddyPost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ postId, userId }: { postId: number; userId: string }) => {
      return apiFetchLunch<{ status: string }>(
        `/buddy/posts/${postId}/join?user_id=${encodeURIComponent(userId)}`,
        { method: "DELETE" }
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["buddy", "posts"] });
    },
  });
}

export function useCloseBuddyPost() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      postId,
      authorId,
      status,
    }: {
      postId: number;
      authorId: string;
      status: "closed" | "cancelled";
    }) => {
      return apiFetchLunch<BuddyPostOut>(`/buddy/posts/${postId}`, {
        method: "PATCH",
        body: JSON.stringify({ author_id: authorId, status }),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["buddy", "posts"] });
    },
  });
}
