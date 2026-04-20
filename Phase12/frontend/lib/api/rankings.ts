import "server-only";
import { loadTeamStatsAll } from "@/lib/data/loaders";
import { TEAM_COLORS } from "@/lib/team-colors";

/**
 * KBO 팀 순위 조회 — 현재 시즌(가장 최신 year) 기준.
 *
 * 데이터 소스:
 *   현재: public/data/team-stats.json (빌드 타임 정적 데이터, 2015~2026)
 *   향후: Naver 스포츠 크롤링 또는 KBO 공식 API (Cloud Scheduler 매일 자동 수집)
 *
 * 확장 지점:
 *   - `fetchLiveRankings()` 를 추가하면 이 함수에서 우선 시도 → 실패 시 정적 폴백
 *   - Firestore `kbo_rankings/{yyyy-mm-dd}` 캐시 레이어 추가 가능
 */
export interface TeamRanking {
  rank: number;
  team: string;
  teamNameKo: string;
  wins: number;
  losses: number;
  draws: number;
  winRate: number;
  homeWinRate: number;
  awayWinRate: number;
  gamesPlayed: number;
}

export interface RankingResult {
  season: number;
  updatedAt: string;
  source: "static" | "crawled";
  rankings: TeamRanking[];
  note?: string;
}

/** 최신 시즌 순위 반환. team 지정 시 해당 팀만 필터. */
export async function getTeamRankings(team?: string): Promise<RankingResult> {
  const all = await loadTeamStatsAll();
  if (all.length === 0) {
    return {
      season: new Date().getFullYear(),
      updatedAt: new Date().toISOString(),
      source: "static",
      rankings: [],
      note: "팀 통계 데이터가 없습니다.",
    };
  }

  // 가장 최신 시즌 선정
  const latestSeason = Math.max(...all.map((s) => s.year));
  const seasonRows = all.filter((s) => s.year === latestSeason);

  // final_rank 기준 정렬 (없으면 win_rate 내림차순)
  const rankings: TeamRanking[] = seasonRows
    .map((row) => ({
      rank: row.final_rank ?? 0,
      team: row.team,
      teamNameKo: TEAM_COLORS[row.team]?.nameKo ?? row.team,
      wins: row.wins,
      losses: row.losses,
      draws: row.draws,
      winRate: row.win_rate,
      homeWinRate: row.home_win_rate,
      awayWinRate: row.away_win_rate,
      gamesPlayed: row.games_played,
    }))
    .sort((a, b) => {
      if (a.rank && b.rank) return a.rank - b.rank;
      return b.winRate - a.winRate;
    });

  // 팀 필터
  const filtered = team
    ? rankings.filter((r) => r.team === team || r.teamNameKo === team)
    : rankings;

  return {
    season: latestSeason,
    updatedAt: new Date().toISOString(),
    source: "static",
    rankings: filtered,
    note:
      "현재 순위 데이터는 정적 스냅샷 기준입니다. 실시간 업데이트는 향후 Cloud Scheduler + 크롤링 파이프라인으로 고도화 예정.",
  };
}
