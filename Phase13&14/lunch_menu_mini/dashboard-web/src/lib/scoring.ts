/**
 * Composite scoring utilities — ported from
 * Mini/lunch-optimizer-dashboard.jsx (legacy).
 *
 * Pure functions. No side effects. Unit-test friendly.
 */
import type { Restaurant, WeatherNow, WeeklyNutritionDay, TeamMember } from "./types";

export const SCORE_WEIGHTS = {
  distance: 0.3,
  weather: 0.2,
  nutrition: 0.2,
  team: 0.3,
} as const;

export function getDistanceScore(distance: number): number {
  if (distance <= 100) return 100;
  if (distance <= 200) return 85;
  if (distance <= 300) return 70;
  if (distance <= 400) return 50;
  return 30;
}

export function getWeatherScore(r: Restaurant, w: WeatherNow): number {
  let score = 50;

  // 기온 기반
  if (w.temp < 5) {
    if (["국물", "죽", "탕"].includes(r.menuType)) score += 30;
    else if (r.menuType === "면류") score += 15;
    else if (["초밥", "샐러드"].includes(r.menuType)) score -= 10;
  } else if (w.temp < 10) {
    if (["국물", "죽", "탕"].includes(r.menuType)) score += 25;
    else if (r.menuType === "면류") score += 10;
  } else if (w.temp >= 28) {
    if (["면류", "초밥", "샐러드"].includes(r.menuType)) score += 25;
    else if (["국물", "죽", "탕"].includes(r.menuType)) score -= 10;
  }

  // 미세먼지
  if ((w.dust === "나쁨" || w.dust === "매우나쁨") && r.indoor) score += 15;

  // 강수
  const rainy = w.rain > 50 || (w.rainTypeStr && w.rainTypeStr !== "없음");
  if (rainy) {
    if (r.distance <= 200) score += 15;
    else if (r.distance >= 400) score -= 15;
    if (["국물", "죽", "탕"].includes(r.menuType)) score += 10;
  }

  // 복합 효과: 비 + 쌀쌀 → 국물 추가 보너스
  if (rainy && w.temp < 15 && w.temp >= 5) {
    if (["국물", "죽", "탕"].includes(r.menuType)) score += 10;
  }
  // 비 + 추움 → 국물 극강
  if (rainy && w.temp < 5 && ["국물", "죽", "탕"].includes(r.menuType)) {
    score += 10;
  }

  // 흐림
  if (w.sky === "흐림" && ["국물", "죽", "면류"].includes(r.menuType)) score += 10;

  // 바람
  if (w.windSpeed && w.windSpeed > 8 && r.distance >= 300) score -= 10;

  return Math.max(0, Math.min(score, 100));
}

export function getNutritionScore(
  r: Restaurant,
  weekly: WeeklyNutritionDay[]
): number {
  const eaten = weekly.filter((d) => d.calories > 0);
  if (eaten.length === 0) return 50;
  const avgProtein =
    eaten.reduce((s, d) => s + d.protein, 0) / eaten.length;
  const avgFat = eaten.reduce((s, d) => s + d.fat, 0) / eaten.length;
  let score = 50;
  if (avgProtein < 25 && r.protein >= 30) score += 20;
  if (avgFat > 30 && r.fat <= 15) score += 20;
  if (r.calories >= 400 && r.calories <= 700) score += 10;
  return Math.min(score, 100);
}

export function getTeamScore(r: Restaurant, team: TeamMember[]): number {
  const votes = team.filter((t) => t.vote === r.id).length;
  return Math.min(votes * 25 + 25, 100);
}

export function getCompositeScore(
  r: Restaurant,
  weather: WeatherNow,
  nutrition: WeeklyNutritionDay[],
  team: TeamMember[]
): number {
  const d = getDistanceScore(r.distance);
  const w = getWeatherScore(r, weather);
  const n = getNutritionScore(r, nutrition);
  const t = getTeamScore(r, team);
  return Math.round(
    d * SCORE_WEIGHTS.distance +
      w * SCORE_WEIGHTS.weather +
      n * SCORE_WEIGHTS.nutrition +
      t * SCORE_WEIGHTS.team
  );
}
