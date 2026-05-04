/**
 * 식사 시간(meal_type) 카테고리 화이트리스트 — 프런트엔드 미러.
 *
 * 백엔드 `lunch-optimizer/pipeline/transformers/meal_time_filter.py` 와
 * 동일한 카테고리 셋을 유지한다. 백엔드 `useMealRecommend` 사용 시에는
 * 서버가 필터링하므로 이 파일은 사용되지 않지만, Dashboard 처럼 GPS 없이
 * 전체 식당 풀에서 시간대 필터링이 필요한 경우에 사용된다.
 */
import type { MealType } from "./types";
import type { Restaurant } from "./types";

export const BREAKFAST_CATEGORIES = new Set<string>([
  "카페",
  "베이커리",
  "샌드위치",
  "브런치",
  "김밥",
  "분식",
  "죽",
  "도시락",
  "간식",
]);

export const DINNER_CATEGORIES = new Set<string>([
  "한식",
  "일식",
  "중식",
  "양식",
  "고깃집",
  "구이",
  "회",
  "초밥",
  "술집",
  "주점",
  "이자카야",
  "호프",
  "뷔페",
  "동남아",
  "아시아음식",
  "샤브샤브",
  "치킨",
  "곱창",
  "전골",
  "찌개",
]);

export function matchesMealType(
  category: string | undefined | null,
  mealType: MealType,
): boolean {
  if (mealType === "any" || mealType === "lunch") return true;
  if (!category) return true; // 보수적 통과
  if (mealType === "breakfast") return BREAKFAST_CATEGORIES.has(category);
  if (mealType === "dinner") return DINNER_CATEGORIES.has(category);
  return true;
}

export function filterByMealType<T extends Restaurant>(
  restaurants: T[],
  mealType: MealType,
): T[] {
  if (mealType === "any" || mealType === "lunch") return restaurants;
  return restaurants.filter((r) => matchesMealType(r.category, mealType));
}

export function inferMealTypeFromHour(hour: number): MealType {
  if (hour >= 6 && hour < 10) return "breakfast";
  if (hour >= 10 && hour < 15) return "lunch";
  return "dinner";
}

export const MEAL_LABEL_KO: Record<MealType, string> = {
  breakfast: "아침",
  lunch: "점심",
  dinner: "저녁",
  any: "식사",
  snack: "간식",
  unknown: "식사",
};
