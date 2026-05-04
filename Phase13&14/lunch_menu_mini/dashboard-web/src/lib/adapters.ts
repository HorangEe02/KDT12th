/**
 * Adapters: lunch-optimizer FastAPI shapes → frontend Restaurant/WeatherNow/...
 *
 * The lunch-optimizer backend tracks fewer fields than the legacy mock data
 * (no price, no per-restaurant nutrition snapshot, no visit history). For
 * scoring functions and existing components to keep working, the adapter
 * fills missing fields with sensible defaults so M5~M8 pages stay intact.
 */
import type {
  NutrientTrendItem,
  Restaurant,
  RestaurantApiOut,
  WeatherCurrentApiOut,
  WeatherNow,
  WeeklyNutritionApiOut,
  WeeklyNutritionDay,
} from "./types";

// =============================================================================
// Restaurant
// =============================================================================
const FALLBACK_PRICE = 8000;
const FALLBACK_NUTRITION = {
  calories: 550,
  protein: 22,
  carbs: 70,
  fat: 18,
};

export function adaptRestaurant(r: RestaurantApiOut): Restaurant {
  return {
    id: r.id,
    name: r.name,
    category: r.category || "기타",
    distance: r.distance_m,
    rating: r.rating ?? 4.0,
    price: FALLBACK_PRICE, // backend doesn't track price yet
    indoor: r.indoor ?? true,
    menuType: r.menu_type || r.sub_category || "기타",
    ...FALLBACK_NUTRITION,
    visits: r.visit_count ?? 0,
    lastVisit: "—",
    // 지도용 좌표·주소 — 백엔드 필드 그대로 전달
    lat: r.lat,
    lng: r.lng,
    address: r.address,
    distance_m: r.distance_m,
    place_url: r.place_url,
  };
}

// =============================================================================
// Weather
// =============================================================================
/** Map API dust grade ("좋음"/"보통"/"나쁨"/"매우나쁨") → mock-shaped. */
function dustLabel(api: WeatherCurrentApiOut): string {
  if (api.dust_grade) return api.dust_grade;
  return "보통";
}

/** Map sky integer (1=맑음, 3=구름많음, 4=흐림) → 한글 단어. */
function skyLabel(api: WeatherCurrentApiOut): string {
  if (api.sky_str) return api.sky_str;
  switch (api.sky) {
    case 1:
      return "맑음";
    case 3:
      return "구름많음";
    case 4:
      return "흐림";
    default:
      return "맑음";
  }
}

export function adaptWeather(api: WeatherCurrentApiOut): WeatherNow {
  return {
    temp: Math.round(api.temp ?? 18),
    humidity: api.humidity ?? 55,
    dust: dustLabel(api),
    sky: skyLabel(api),
    rain: api.pop ?? 0,
    windSpeed: api.wind_speed ?? undefined,
    rainTypeStr: api.rain_type_str ?? undefined,
  };
}

// =============================================================================
// Weekly Nutrition
// =============================================================================
const KO_DAYS = ["월", "화", "수", "목", "금", "토", "일"];

/**
 * Map `/api/nutrition/weekly` (월~일 daily_records) → 5-row mock layout (월~금).
 * Saturday/Sunday are dropped. Missing days emit zero rows.
 */
export function adaptWeeklyNutrition(
  api: WeeklyNutritionApiOut
): WeeklyNutritionDay[] {
  const byDate = new Map<string, WeeklyNutritionApiOut["daily_records"][number]>();
  for (const rec of api.daily_records ?? []) {
    const recDate = rec.meal_date ?? rec.date;
    if (recDate) byDate.set(recDate, rec);
  }
  // Build week starting Monday from period.start
  const start = api.period?.start ? new Date(api.period.start) : new Date();
  const result: WeeklyNutritionDay[] = [];
  for (let i = 0; i < 5; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const iso = d.toISOString().slice(0, 10);
    const rec = byDate.get(iso);
    result.push({
      day: KO_DAYS[i],
      calories: Math.round(rec?.calories ?? 0),
      protein: Math.round(rec?.protein ?? 0),
      carbs: Math.round(rec?.carbs ?? 0),
      fat: Math.round(rec?.fat ?? 0),
      target: 700,
    });
  }
  return result;
}

/** Map `/api/nutrition/trend` items → 5-row mock layout. */
export function adaptTrendToWeekly(
  trend: NutrientTrendItem[]
): WeeklyNutritionDay[] {
  return trend.slice(-5).map((t, i) => ({
    day: KO_DAYS[i],
    calories: Math.round(t.calories || 0),
    protein: Math.round(t.protein || 0),
    carbs: Math.round(t.carbs || 0),
    fat: Math.round(t.fat || 0),
    target: 700,
  }));
}
