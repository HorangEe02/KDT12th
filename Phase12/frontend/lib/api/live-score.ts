import "server-only";
import { loadSchedule } from "@/lib/data/loaders";
import { TEAM_COLORS } from "@/lib/team-colors";
import type { Game } from "@/lib/types";

export interface LiveScoreGame {
  game_id: string;
  date: string;
  day_of_week: string;
  home_team: string;
  away_team: string;
  stadium: string;
  start_time: string | null;
  status: string;
  score: { home: number; away: number } | null;
  current_inning: number | null;
  broadcast: string[] | string | null;
}

export interface LiveScoreResult {
  date: string;
  count: number;
  source: "static" | "crawled";
  games: LiveScoreGame[];
  summary: {
    scheduled: number;
    in_progress: number;
    finished: number;
    canceled: number;
  };
  note?: string;
}

/**
 * 오늘(또는 지정 날짜) 전 경기 스코어보드 조회.
 *
 * 필터:
 *   - date: "YYYY-MM-DD" (생략 시 오늘)
 *   - team: 특정 팀 포함 경기만 (home_team 또는 away_team 매칭)
 *
 * 데이터 소스: 빌드 타임 static schedule.json
 * 향후: 네이버 스포츠 실시간 크롤링 + 30초 캐시 교체 예정
 */
export async function getLiveScore(
  opts: { date?: string; team?: string } = {},
): Promise<LiveScoreResult> {
  const all = await loadSchedule();
  const today = new Date().toISOString().slice(0, 10);
  const date = opts.date ?? today;

  let games = all.filter((g) => g.date === date);

  if (opts.team) {
    const resolvedCode =
      opts.team in TEAM_COLORS
        ? opts.team
        : Object.entries(TEAM_COLORS).find(([, v]) => v.nameKo === opts.team)?.[0];
    if (resolvedCode) {
      games = games.filter(
        (g) => g.home_team === resolvedCode || g.away_team === resolvedCode,
      );
    }
  }

  const summary = {
    scheduled: 0,
    in_progress: 0,
    finished: 0,
    canceled: 0,
  };
  const enriched: LiveScoreGame[] = games.map((g: Game) => {
    const status = g.status ?? "SCHEDULED";
    if (status === "SCHEDULED") summary.scheduled++;
    else if (status === "IN_PROGRESS") summary.in_progress++;
    else if (status === "FINISHED") summary.finished++;
    else if (status === "CANCELED") summary.canceled++;
    return {
      game_id: g.game_id,
      date: g.date,
      day_of_week: g.day_of_week ?? "",
      home_team: g.home_team,
      away_team: g.away_team,
      stadium: g.stadium,
      start_time: g.start_time ?? g.time ?? null,
      status,
      score: g.score ?? null,
      current_inning: g.current_inning ?? null,
      broadcast: g.broadcast ?? null,
    };
  });

  return {
    date,
    count: enriched.length,
    source: "static",
    games: enriched,
    summary,
    note:
      enriched.length === 0
        ? `${date}에 예정/진행 중/종료된 경기가 없습니다.`
        : "실시간 스코어는 정적 스케줄 기준입니다. 향후 네이버 스포츠 크롤링으로 고도화 예정.",
  };
}
