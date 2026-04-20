/**
 * Vercel AI SDK v6 tool 정의 — 6 function calling 도구.
 * 포팅 원본: src/ai/tools.py
 */
import "server-only";
import { tool } from "ai";
import { z } from "zod";
import {
  filterAwayGames,
  loadPOIsByStadium,
  loadStadiums,
} from "@/lib/data/loaders";
import { predictWinRate } from "@/lib/predict";
import { requestRoute } from "@/lib/api/route";
import { getForecast } from "@/lib/api/weather";
import { getTeamRankings } from "@/lib/api/rankings";
import { getPlayerStats } from "@/lib/api/player-stats";
import { getLiveScore } from "@/lib/api/live-score";
import { searchTips } from "@/lib/ai/rag";
import { ORIGIN_PRESETS } from "@/lib/map/origins";

const ORIGIN_PRESET_KEYS = Object.keys(ORIGIN_PRESETS);
function parseOrigin(origin: string): [number, number] | null {
  if (!origin) return null;
  const key = origin.toLowerCase().trim();
  if (key in ORIGIN_PRESETS) return ORIGIN_PRESETS[key];
  const ko: Record<string, string> = {
    서울역: "seoul",
    강남역: "gangnam",
    수원역: "suwon",
    대전역: "daejeon",
  };
  if (origin in ko) return ORIGIN_PRESETS[ko[origin]];
  const parts = origin.split(",").map((s) => s.trim());
  if (parts.length === 2) {
    const a = Number(parts[0]);
    const b = Number(parts[1]);
    if (Number.isFinite(a) && Number.isFinite(b)) return [a, b];
  }
  return null;
}

async function stadiumByShort(short: string) {
  const all = await loadStadiums();
  return all.find((s) => s.short_name === short) ?? null;
}

export const searchGame = tool({
  description:
    "특정 팀의 원정 경기를 날짜 범위로 검색합니다. 2026 시즌 실제 KBO 데이터 (종료 경기는 score/status/pitchers 포함). " +
    "'다음 원정', '이번 주말 경기', '최근 경기 결과', 'KIA 지난주 경기' 같은 질문 시 호출. " +
    "status 파라미터로 과거/미래/전체 필터 가능: 'scheduled'=예정 경기만, 'finished'=종료 경기만 (결과 조회용), 'all'=모두 (기본).",
  inputSchema: z.object({
    team: z
      .string()
      .describe(
        "응원팀 약칭: LG, KT, SSG, 두산, KIA, NC, 삼성, 롯데, 한화, 키움",
      ),
    startDate: z.string().optional().describe("YYYY-MM-DD. 생략 시 오늘"),
    endDate: z
      .string()
      .optional()
      .describe("YYYY-MM-DD. 생략 시 start+7일"),
    status: z
      .enum(["scheduled", "finished", "all"])
      .optional()
      .describe(
        "경기 상태 필터 — scheduled: 예정 경기만 (앞으로 원정 일정 질문), " +
          "finished: 종료 경기만 (최근 결과·지난 경기 질문), all: 모두. 기본 all.",
      ),
  }),
  execute: async ({ team, startDate, endDate, status = "all" }) => {
    const today = new Date().toISOString().slice(0, 10);
    const start = startDate ?? today;
    const end =
      endDate ??
      new Date(new Date(start).getTime() + 7 * 24 * 3600 * 1000)
        .toISOString()
        .slice(0, 10);
    const allGames = await filterAwayGames(team, start, end);
    const games =
      status === "scheduled"
        ? allGames.filter((g) => (g.status ?? "SCHEDULED") === "SCHEDULED")
        : status === "finished"
          ? allGames.filter((g) => g.status === "FINISHED")
          : allGames;
    const recent = games.slice(0, 8).map((g) => ({
      game_id: g.game_id,
      date: g.date,
      day_of_week: g.day_of_week,
      home_team: g.home_team,
      away_team: g.away_team,
      stadium: g.stadium,
      start_time: g.start_time,
      status: g.status ?? "SCHEDULED",
      score: g.score ?? null,
      home_pitcher: g.home_pitcher ?? null,
      away_pitcher: g.away_pitcher ?? null,
      win_pitcher: g.win_pitcher ?? null,
      lose_pitcher: g.lose_pitcher ?? null,
      save_pitcher: g.save_pitcher ?? null,
      current_inning: g.current_inning ?? null,
      broadcast: g.broadcast ?? null,
    }));
    // 응원팀 관점 W/L/D 계산 (종료 경기만)
    const summary = {
      wins: 0,
      losses: 0,
      draws: 0,
      scheduled: 0,
    };
    for (const g of games) {
      if (g.status !== "FINISHED" || !g.score) {
        if (g.status === "SCHEDULED") summary.scheduled++;
        continue;
      }
      const teamIsAway = g.away_team === team;
      const my = teamIsAway ? g.score.away : g.score.home;
      const opp = teamIsAway ? g.score.home : g.score.away;
      if (my > opp) summary.wins++;
      else if (my < opp) summary.losses++;
      else summary.draws++;
    }
    // 0건일 때: AI 가 그대로 전달할 수 있도록 명시적 안내 메시지 포함.
    // (단순 빈 배열보다 자연어 힌트가 있으면 LLM 답변이 일관됨.)
    const statusWord =
      status === "scheduled"
        ? "예정된 원정 경기"
        : status === "finished"
          ? "종료된 원정 경기"
          : "원정 경기";
    const message =
      games.length === 0
        ? `${team} 팀의 ${start} ~ ${end} 기간 ${statusWord}(이)가 없습니다.`
        : undefined;
    return {
      count: games.length,
      summary,
      games: recent,
      message,
    };
  },
});

export const predictWinRateTool = tool({
  description:
    "특정 팀이 상대팀 원정에서 이길 확률을 로지스틱 회귀로 예측. 'LG vs KT 승률', '원정 가면 이길까?' 질문 시 호출.",
  inputSchema: z.object({
    team: z.string().describe("원정 팀 약칭"),
    opponent: z.string().describe("홈 팀 약칭"),
  }),
  execute: async ({ team, opponent }) => {
    const r = await predictWinRate(team, opponent);
    return {
      team: r.team,
      opponent: r.opponent,
      win_probability: r.prob,
      win_percentage: `${(r.prob * 100).toFixed(1)}%`,
      source: r.source,
    };
  },
});

export const getWeather = tool({
  description:
    "구장 좌표의 특정 날짜 날씨 예보 (기상청 단기예보). '비 올까?', '날씨 어때?' 질문 시 호출.",
  inputSchema: z.object({
    stadium: z
      .string()
      .describe(
        "구장 short_name: 잠실, 수원, 광주, 부산, 대구, 창원, 대전, 문학, 고척, 사직",
      ),
    targetDate: z.string().optional().describe("YYYY-MM-DD. 기본 오늘"),
  }),
  execute: async ({ stadium, targetDate }) => {
    const s = await stadiumByShort(stadium);
    if (!s) return { error: `알 수 없는 구장: ${stadium}` };
    const date = targetDate ?? new Date().toISOString().slice(0, 10);
    const f = await getForecast(s.lat, s.lng, date);
    return f;
  },
});

export const findPlaces = tool({
  description:
    "구장 주변 맛집/숙소/관광지 POI 리스트. '광주 맛집', '수원 숙소' 질문 시 호출.",
  inputSchema: z.object({
    stadium: z.string().describe("구장 short_name"),
    category: z
      .enum(["food", "stay", "tour"])
      .describe("food=음식점, stay=숙박, tour=관광지"),
    limit: z.number().int().min(1).max(10).default(5).optional(),
  }),
  execute: async ({ stadium, category, limit }) => {
    const items = await loadPOIsByStadium(`${stadium}_${category}`);
    const lim = Math.max(1, Math.min(10, limit ?? 5));
    const sorted = [...items]
      .sort((a, b) => (a.dist_m ?? Infinity) - (b.dist_m ?? Infinity))
      .slice(0, lim);
    return {
      stadium,
      category,
      count: sorted.length,
      places: sorted.map((p) => ({
        title: p.title,
        addr: p.addr,
        dist_m: p.dist_m ?? 0,
        tel: p.tel ?? "",
      })),
    };
  },
});

export const getRoute = tool({
  description:
    "출발지 → 경기장 자동차 경로 거리/시간/통행료. '거리 얼마나?', '몇 시간?' 질문 시 호출.",
  inputSchema: z.object({
    origin: z
      .string()
      .describe(
        `출발지: ${ORIGIN_PRESET_KEYS.join("/")} 또는 "서울역/강남역/수원역/대전역" 또는 "위도,경도"`,
      ),
    destinationStadium: z.string().describe("목적지 구장 short_name"),
  }),
  execute: async ({ origin, destinationStadium }) => {
    const o = parseOrigin(origin);
    if (!o) return { error: `알 수 없는 출발지: ${origin}` };
    const s = await stadiumByShort(destinationStadium);
    if (!s) return { error: `알 수 없는 구장: ${destinationStadium}` };
    const r = await requestRoute(o, [s.lat, s.lng]);
    return {
      origin,
      destinationStadium,
      distance_km:
        r.distance_m != null ? Math.round(r.distance_m / 100) / 10 : null,
      duration_min:
        r.duration_sec != null ? Math.round(r.duration_sec / 60) : null,
      toll_fare_krw: r.toll_fare_krw,
      source: r.source,
      fallback: r.fallback,
    };
  },
});

export const searchKnowledge = tool({
  description:
    "구장별 원정 응원 팁/노하우를 의미 검색으로 조회 (RAG). '어느 자리가 좋아?', '팁 알려줘' 질문 시 호출.",
  inputSchema: z.object({
    query: z.string().describe("검색 의도 한국어 문장"),
    stadium: z.string().optional().describe("구장 필터 (선택)"),
  }),
  execute: async ({ query, stadium }) => {
    const tips = await searchTips(query, { stadium, topK: 3 });
    return { count: tips.length, tips };
  },
});

export const getTeamRankingTool = tool({
  description:
    "현재 KBO 시즌 팀 순위 조회. '지금 순위', '1위 팀 누구', '우리 팀 몇 위', " +
    "'LG 순위' 같은 질문 시 호출. team 생략 시 10팀 전체 순위, 지정 시 해당 팀만 반환. " +
    "반환 데이터는 최신 시즌(year) 기준 최종 순위·승패·승률·홈/원정 승률 포함.",
  inputSchema: z.object({
    team: z
      .string()
      .optional()
      .describe(
        "특정 팀만 조회 시 약칭 (LG, KT, SSG, 두산, KIA, NC, 삼성, 롯데, 한화, 키움). 생략 시 전체 10팀.",
      ),
  }),
  execute: async ({ team }) => {
    const result = await getTeamRankings(team);
    return {
      season: result.season,
      source: result.source,
      count: result.rankings.length,
      rankings: result.rankings,
      note: result.note,
    };
  },
});

export const getPlayerStatsTool = tool({
  description:
    "KBO 선수 시즌 스탯 조회. '이정후 타율', '김도영 홈런', '삼성 타자 순위', " +
    "'LG 선발 투수 방어율' 같은 질문 시 호출. " +
    "필터: team(약칭 또는 한국명), name(이름 부분 일치), position(batter/pitcher). " +
    "타자는 avg/hits/hr/rbi/sb/ops, 투수는 era/wins/losses/so/whip/ip 반환. " +
    "2026 시즌 기준 샘플 데이터 (10팀 × 5명 = 50인).",
  inputSchema: z.object({
    team: z
      .string()
      .optional()
      .describe("팀 약칭(LG, 삼성 등) 또는 한국명. 생략 시 전체 팀."),
    name: z
      .string()
      .optional()
      .describe("선수 이름 부분 일치 검색 (예: '이정후', '김도영')."),
    position: z
      .enum(["batter", "pitcher"])
      .optional()
      .describe("포지션 필터 — batter: 타자, pitcher: 투수."),
  }),
  execute: async ({ team, name, position }) => {
    const result = await getPlayerStats({ team, name, position });
    return {
      season: result.season,
      count: result.count,
      players: result.players,
      note: result.note,
    };
  },
});

export const getLiveScoreTool = tool({
  description:
    "오늘(또는 지정 날짜) 전 KBO 경기 스코어보드 조회. " +
    "'오늘 경기 어떻게 됐어?', '지금 삼성 경기 점수?', '어제 KBO 결과' 같은 질문 시 호출. " +
    "반환: 날짜별 전 경기 + 상태(SCHEDULED/IN_PROGRESS/FINISHED) + 스코어 + 현재 이닝. " +
    "search_game 은 팀 기준 원정 경기만, 이 도구는 리그 전체 일일 현황이 핵심.",
  inputSchema: z.object({
    date: z
      .string()
      .optional()
      .describe("YYYY-MM-DD 형식. 생략 시 오늘."),
    team: z
      .string()
      .optional()
      .describe(
        "특정 팀 참여 경기만 (home/away 양쪽 모두). 약칭·한국명 모두 허용.",
      ),
  }),
  execute: async ({ date, team }) => {
    const result = await getLiveScore({ date, team });
    return {
      date: result.date,
      count: result.count,
      summary: result.summary,
      games: result.games,
      note: result.note,
    };
  },
});

/** 모든 도구를 한 번에 주입하기 위한 번들. */
export const ALL_TOOLS = {
  search_game: searchGame,
  predict_win_rate: predictWinRateTool,
  get_weather: getWeather,
  find_places: findPlaces,
  get_route: getRoute,
  search_knowledge: searchKnowledge,
  get_team_ranking: getTeamRankingTool,
  get_player_stats: getPlayerStatsTool,
  get_live_score: getLiveScoreTool,
} as const;
