/**
 * Mini TypeScript type definitions.
 * Mirrors Pydantic schemas in `NLP/nlp_mvp/api/schemas.py`.
 */

// =============================================================================
// NLP API
// =============================================================================
export interface NLPHealth {
  status: "ok" | "degraded";
  version: string;
  modules: Record<string, string>; // module -> "ok" | "error: ..." | "pending" | "skipped"
}

export interface SentimentOut {
  restaurant_id: string;
  score: number | null;
  pos_ratio: number;
  neu_ratio: number;
  neg_ratio: number;
  review_count: number;
  updated_at: string | null;
}

export interface SentimentTopItem {
  restaurant_id: string;
  name?: string | null;
  score: number;
  pos_ratio: number;
  review_count: number;
}

export type NormalizeMethod =
  | "rule"
  | "levenshtein"
  | "embedding"
  | "none"
  | "error";

export interface MenuNormalizeOut {
  raw: string;
  cleaned: string;
  matched_id?: string | null;
  matched_name?: string | null;
  confidence: number;
  method: NormalizeMethod;
  latency_ms: number;
}

export interface MenuStatsOut {
  total: number;
  by_method: Record<string, number>;
  hit_rate: number;
}

export interface ChatRecommendation {
  name: string;
  reason?: string | null;
  category?: string | null;
}

export interface ChatOut {
  response: string;
  recommendations: ChatRecommendation[];
  latency_ms: number;
  validation: Record<string, unknown>;
  context_summary: Record<string, number>;
}

export interface WeeklyReportOut {
  user_id: string;
  week_start: string;
  week_label: string;
  text: string;
  facts: Record<string, unknown>;
  generation_method: "llm" | "template" | "minimal";
  generated_at: string;
  validation: Record<string, unknown>;
}

// Phase 14: 멀티 LLM provider (ollama + gemini)
export type LLMProvider = "ollama" | "gemini";

export interface OllamaModelInfo {
  name: string; // "provider:model" 형식 (예: "gemini:gemini-2.5-pro")
  size?: string;
  modified?: string;
  provider?: LLMProvider;
}

export interface ModelListResponse {
  models: OllamaModelInfo[];
  host: string;
  active_chat: string;
  active_report: string;
  active_tools?: string;
  active_chat_provider?: LLMProvider;
  active_report_provider?: LLMProvider;
  active_tools_provider?: LLMProvider;
}

export interface SettingsResponse {
  chat_model: string;
  report_model: string;
  tools_model?: string;
  host: string;
  language: "en" | "ko" | "both";
  chat_provider?: LLMProvider;
  report_provider?: LLMProvider;
  tools_provider?: LLMProvider;
}

export type ModelRole = "chat" | "report" | "tools" | "both" | "all";

export interface SettingsUpdateRequest {
  model: string; // "provider:model" 권장
  role: ModelRole;
  provider?: LLMProvider;
}

export interface SettingsUpdateResponse {
  status: "ok" | "error";
  role: ModelRole;
  model: string;
  chat_model: string;
  report_model: string;
  tools_model?: string;
  chat_provider?: LLMProvider;
  report_provider?: LLMProvider;
  tools_provider?: LLMProvider;
  detail?: string | null;
}

// =============================================================================
// lunch-optimizer (subset used so far)
// =============================================================================
/**
 * Frontend-facing restaurant shape used by scoring + UI.
 *
 * `id` is `string | number` to support both legacy mock (numbers) and the
 * lunch-optimizer API (string UUID-like ids).
 */
export interface Restaurant {
  id: string | number;
  name: string;
  category: string;
  distance: number;
  rating: number;
  price: number;
  indoor: boolean;
  menuType: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  visits: number;
  lastVisit: string;
  /** 지도용 좌표 (optional — mock 데이터엔 없을 수 있음) */
  lat?: number;
  lng?: number;
  /** 주소 (지도 팝업에 사용) */
  address?: string | null;
  /** 백엔드 distance_m (지도 표시용) — adaptRestaurant 가 distance 와 동시에 보존 */
  distance_m?: number;
  place_url?: string | null;
}

/** Raw `/api/restaurants` response from lunch-optimizer FastAPI. */
export interface RestaurantApiOut {
  id: string;
  name: string;
  category: string | null;
  sub_category: string | null;
  menu_type: string | null;
  address: string | null;
  phone: string | null;
  lat: number;
  lng: number;
  distance_m: number;
  distance_score: number;
  place_url: string | null;
  indoor: boolean;
  rating: number | null;
  visit_count: number;
  is_active: boolean;
}

/** Raw `/api/restaurants/stats` response. */
export interface LunchStatsOut {
  total: number;
  active: number;
  inactive: number;
  categories: Record<string, number>;
  avg_distance_m: number | null;
  avg_distance_score: number | null;
  last_collected_at: string | null;
}

/** Raw `/api/weather/current` response. */
export interface WeatherCurrentApiOut {
  collected_at: string | null;
  temp: number | null;
  humidity: number | null;
  rain_type: number | null;
  rain_type_str: string | null;
  rain_1h: number | null;
  wind_speed: number | null;
  sky: number | null;
  sky_str: string | null;
  pop: number | null;
  pm10: number | null;
  pm25: number | null;
  dust_grade: string | null;
  outdoor_comfort: string | null;
  tips: string[];
}

/** Raw `/api/nutrition/weekly` response. */
export interface WeeklyNutritionApiOut {
  period: { start: string; end: string };
  meal_count: number;
  daily_records: Array<{
    meal_date?: string;
    date?: string;
    day?: string;
    calories: number;
    carbs: number;
    protein: number;
    fat: number;
    sodium?: number;
    has_record?: boolean;
  }>;
  weekly_avg: Record<string, number>;
  weekly_total: Record<string, number>;
  macro_ratio: { carbs_pct: number; protein_pct: number; fat_pct: number };
  recorded_days: number;
  missing_days: string[];
}

export type MealType =
  | "breakfast"
  | "lunch"
  | "dinner"
  | "snack"
  | "unknown"
  | "any";

export interface NutritionParsedItem {
  raw_name: string;
  normalized_name?: string | null;
  quantity: number;
  unit: string;
  confidence: number;
  needs_review: boolean;
}

export interface NutritionParseOut {
  user_id: string;
  raw_text: string;
  meal_date: string;
  meal_type: MealType;
  restaurant_hint?: string | null;
  satisfaction?: number | null;
  items: NutritionParsedItem[];
  warnings: string[];
  parser: {
    method: string;
    confidence: number;
  };
}

export interface NaturalMealItem {
  id?: number | null;
  raw_name: string;
  normalized_name?: string | null;
  food_code?: string | null;
  quantity: number;
  unit: string;
  serving_size?: number | null;
  calories?: number | null;
  carbs?: number | null;
  protein?: number | null;
  fat?: number | null;
  sugar?: number | null;
  sodium?: number | null;
  source?: string | null;
  match_type?: string | null;
  match_confidence?: number | null;
  needs_review: boolean;
}

export interface RestaurantSnapshot {
  id?: string | null;
  name?: string | null;
  category?: string | null;
  address?: string | null;
  lat?: number | null;
  lng?: number | null;
  place_url?: string | null;
}

export interface NaturalMealPayload {
  user_id: string;
  raw_text: string;
  meal_date?: string | null;
  meal_type?: MealType | null;
  restaurant_id?: string | null;
  restaurant_snapshot?: RestaurantSnapshot | null;
  satisfaction?: number | null;
  items: NaturalMealItem[];
}

export interface NaturalMealAnalysisOut {
  id?: number | null;
  user_id: string;
  raw_text: string;
  meal_date: string;
  meal_type?: MealType | null;
  restaurant_id?: string | null;
  restaurant_name_snapshot?: string | null;
  restaurant_place_url?: string | null;
  menu_name?: string | null;
  calories?: number | null;
  carbs?: number | null;
  protein?: number | null;
  fat?: number | null;
  sugar?: number | null;
  sodium?: number | null;
  satisfaction?: number | null;
  nutrition_source?: string | null;
  match_confidence?: number | null;
  needs_review: boolean;
  created_at?: string | null;
  updated_at?: string | null;
  items: NaturalMealItem[];
}

/** Raw `/api/nutrition/trend` item. */
export interface NutrientTrendItem {
  date: string;
  calories: number;
  carbs: number;
  protein: number;
  fat: number;
  sodium: number;
  has_record: boolean;
}

/** Raw `/api/vote/status` response. */
export interface VoteStatusOut {
  team_id?: string;
  vote_date?: string;
  status?: string;
  team_members?: number;
  voted_count?: number;
  total_votes?: number;
  total_members?: number;
  participation_rate?: number;
  /** Per-user votes (votes_detail in backend). */
  votes?: Array<{
    user_id: string;
    user_name?: string;
    restaurant_id: string;
    restaurant_name?: string;
    voted_at?: string;
  }>;
  /** Aggregated counts. */
  tally?: Array<{
    restaurant_id: string;
    restaurant_name?: string;
    votes: number;
  }>;
  not_voted?: string[];
  vetoed?: Array<Record<string, unknown>>;
  winner_restaurant_id?: string | null;
}

/** Raw `/api/history/visits` item. */
export interface RecentVisitItem {
  restaurant_id: string;
  restaurant_name?: string;
  visit_date: string;
  visit_count?: number;
}

/** `/api/users` row. */
export interface UserAccount {
  id: string;
  name: string;
  team_id: string;
  avatar_emoji: string;
  dislike_categories?: string | null;
  allergy_info?: string | null;
  is_active: boolean;
}

/** `/api/notify/slack` response. */
export interface SlackNotifyResponse {
  sent: boolean;
  status_code?: number | null;
  error?: string | null;
}

// =============================================================================
// Phase 7 — Tool Calling
// =============================================================================
export interface ToolCallRecord {
  name: string;
  args: Record<string, unknown>;
}

export interface ToolResultRecord {
  ok: boolean;
  tool: string;
  data?: unknown;
  error?: string | null;
}

export interface ToolChatOut {
  response: string;
  tool_calls: ToolCallRecord[];
  tool_results: ToolResultRecord[];
  iterations: number;
  latency_ms: number;
  fallback_used: boolean;
}

export interface TeamMember {
  id: string;
  name: string;
  vote: number | null;
  avatar: string;
}

export interface ChatMessage {
  id: number;
  team_id: string;
  user_id: string;
  user_name: string;
  avatar_emoji: string;
  message: string;
  created_at: string;
}

export interface WeeklyNutritionDay {
  day: string;
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  target: number;
}

export interface WeatherNow {
  temp: number;
  humidity: number;
  dust: string;
  sky: string;
  rain: number;
  /** 바람 속도 (m/s) — 백엔드에서 제공 시 */
  windSpeed?: number;
  /** 강수 형태 문자열 ("없음"|"비"|"눈" 등) */
  rainTypeStr?: string;
}

// --- Mood-based Weather Recommendation ---
export interface MoodOption {
  id: string;
  emoji: string;
  label: string;
  description: string;
}

export interface WeatherMoodOptionsOut {
  weather_summary: string;
  mood_options: MoodOption[];
}

export interface MoodRecommendationItem {
  restaurant_id: string;
  restaurant_name: string;
  category: string | null;
  menu_type: string | null;
  distance_m: number;
  mood_score: number;
  reason: string;
}

export interface MoodRecommendationGroup {
  group_label: string;
  group_emoji: string;
  items: MoodRecommendationItem[];
}

// =============================================================================
// Helpers
// =============================================================================
/** True when every module in /nlp/health reports "ok" or "skipped". */
export function isNLPHealthy(h: NLPHealth | undefined): boolean {
  if (!h) return false;
  if (h.status === "degraded") return false;
  return Object.values(h.modules).every(
    (v) => v === "ok" || v === "skipped" || v === "pending"
  );
}

/**
 * Extract an Ollama model hint.
 *
 * @deprecated M9 에서 `/nlp/settings.chat_model` 로 교체. TopNav/OllamaStatus
 * 는 이제 `useSettings()` 를 사용해야 한다. 유지되는 이유는 health 응답만
 * 있는 초기 렌더 fallback 을 위해서.
 */
export function ollamaModelFromHealth(h: NLPHealth | undefined): string {
  if (!h) return "N/A";
  return "—";
}


// =============================================================================
// Buddy (밥친구 찾기)
// =============================================================================
export interface BuddyJoiner {
  user_id: string;
  user_name: string;
  avatar_emoji: string;
  joined_at: string | null;
}

export interface BuddyPostOut {
  id: number;
  team_id: string;
  author_id: string;
  author_name?: string;
  author_avatar?: string;
  restaurant_id?: string | null;
  restaurant_name: string;
  meal_date: string;
  meal_time: string;
  max_buddies: number;
  current_buddies: number;
  message?: string | null;
  status: string; // "open" | "full" | "closed" | "cancelled" | "expired"
  joiners: BuddyJoiner[];
  created_at: string | null;
}

export interface BuddyJoinResult {
  status: string; // "joined" | "already_joined" | "full" | "closed"
  post_id: number;
  current_buddies: number;
}

// =============================================================================
// 다중 식사 시간 (헤비 옵션) — MealType 은 위에서 정의됨 (snack/unknown 호환)
// =============================================================================
export interface MealNutritionTarget {
  ratio: number;
  calories: number;
  carbs_g: number;
  protein_g: number;
  fat_g: number;
  sodium_mg: number;
}

export interface NutritionTargetsOut {
  user_id: string;
  daily: {
    calories: number;
    carbs_g: number;
    protein_g: number;
    fat_g: number;
    sodium_mg: number;
  };
  by_meal: {
    breakfast: MealNutritionTarget;
    lunch: MealNutritionTarget;
    dinner: MealNutritionTarget;
  };
}

export interface MealTypeBucket {
  calories: number;
  carbs: number;
  protein: number;
  fat: number;
  sodium: number;
  count: number;
}
