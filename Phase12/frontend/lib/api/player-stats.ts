import "server-only";
import { loadPlayerStats } from "@/lib/data/loaders";
import { TEAM_COLORS } from "@/lib/team-colors";
import type { PlayerStat } from "@/lib/types";

export interface PlayerStatsResult {
  season: number;
  updatedAt: string;
  source: "static" | "crawled";
  count: number;
  players: PlayerStat[];
  note?: string;
}

/**
 * 선수 스탯 조회.
 * 필터:
 *   - team: 특정 팀 소속만 (LG, 삼성 등)
 *   - name: 이름 부분 일치 (이정후, 김도영 등)
 *   - position: "batter" | "pitcher"
 *
 * 데이터 소스: public/data/player-stats.json (10팀 × 5명 · 2026 시즌 더미)
 * 향후: KBO 공식 기록실 크롤링 + Firestore 캐시 교체 예정
 */
export async function getPlayerStats(
  opts: { team?: string; name?: string; position?: "batter" | "pitcher" } = {},
): Promise<PlayerStatsResult> {
  const file = await loadPlayerStats();
  const { team, name, position } = opts;

  let players = file.players;

  if (team) {
    // 약칭(LG) 또는 한국명(LG 트윈스) 모두 허용
    const resolvedCode = team in TEAM_COLORS
      ? team
      : Object.entries(TEAM_COLORS).find(([, v]) => v.nameKo === team)?.[0];
    if (resolvedCode) {
      players = players.filter((p) => p.team === resolvedCode);
    }
  }

  if (name) {
    const q = name.toLowerCase().replace(/\s+/g, "");
    players = players.filter((p) =>
      p.name.toLowerCase().replace(/\s+/g, "").includes(q),
    );
  }

  if (position) {
    players = players.filter((p) => p.position === position);
  }

  return {
    season: file.season,
    updatedAt: file.updated_at,
    source: "static",
    count: players.length,
    players,
    note:
      players.length === 0
        ? "검색 조건에 맞는 선수가 없습니다. 이름 철자·팀명을 확인해 주세요."
        : "선수 스탯은 정적 스냅샷 기준입니다. 향후 KBO 공식 기록실 크롤링으로 고도화 예정.",
  };
}
