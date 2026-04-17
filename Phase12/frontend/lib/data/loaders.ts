/**
 * 서버 측 정적 JSON 로더.
 * 빌드 시점 캐시를 위해 모듈 스코프에 결과 저장.
 * public/data/ 는 dev/prod 공통 경로.
 */
import "server-only";
import fs from "node:fs/promises";
import path from "node:path";
import type { Game, POI, Stadium, TeamStat, Tip } from "@/lib/types";

const cache = new Map<string, unknown>();

async function load<T>(rel: string): Promise<T> {
  if (cache.has(rel)) return cache.get(rel) as T;
  const abs = path.join(process.cwd(), "public", rel);
  const raw = await fs.readFile(abs, "utf-8");
  const parsed = JSON.parse(raw) as T;
  cache.set(rel, parsed);
  return parsed;
}

export const loadSchedule = () => load<Game[]>("data/schedule.json");
export const loadStadiums = () => load<Stadium[]>("data/stadiums.json");
export const loadTeamStatsAll = () => load<TeamStat[]>("data/team-stats.json");
export const loadTips = () => load<Tip[]>("data/tips.json");

export async function loadPOIsByStadium(stadiumShort: string): Promise<POI[]> {
  try {
    return await load<POI[]>(`data/poi/${stadiumShort}.json`);
  } catch {
    return [];
  }
}

/** 특정 팀이 away 인 경기 + 날짜 범위 필터. */
export async function filterAwayGames(
  team: string,
  dateStart?: string,
  dateEnd?: string,
): Promise<Game[]> {
  const all = await loadSchedule();
  return all
    .filter((g) => g.away_team === team)
    .filter((g) => (dateStart ? g.date >= dateStart : true))
    .filter((g) => (dateEnd ? g.date <= dateEnd : true))
    .sort((a, b) => a.date.localeCompare(b.date));
}

/** 최근 N년 평균 원정 승률 → 구단별 정렬 내림차순. */
export async function awayWinRateRanking(
  lastNYears = 3,
): Promise<Array<{ team: string; away_win_rate: number }>> {
  const stats = await loadTeamStatsAll();
  const maxYear = stats.reduce((m, r) => (r.year > m ? r.year : m), 0);
  const cutoff = maxYear - (lastNYears - 1);
  const recent = stats.filter((r) => r.year >= cutoff);

  const bucket = new Map<string, number[]>();
  for (const r of recent) {
    if (!bucket.has(r.team)) bucket.set(r.team, []);
    bucket.get(r.team)!.push(r.away_win_rate);
  }
  const rows = [...bucket.entries()].map(([team, arr]) => ({
    team,
    away_win_rate: arr.reduce((s, v) => s + v, 0) / arr.length,
  }));
  rows.sort((a, b) => b.away_win_rate - a.away_win_rate);
  return rows;
}
