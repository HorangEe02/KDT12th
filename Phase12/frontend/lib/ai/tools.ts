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
    "특정 팀의 원정 경기를 날짜 범위로 검색합니다. 사용자가 '다음 원정', '이번 주말 경기' 같은 질문 시 호출.",
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
  }),
  execute: async ({ team, startDate, endDate }) => {
    const today = new Date().toISOString().slice(0, 10);
    const start = startDate ?? today;
    const end =
      endDate ??
      new Date(new Date(start).getTime() + 7 * 24 * 3600 * 1000)
        .toISOString()
        .slice(0, 10);
    const games = await filterAwayGames(team, start, end);
    return {
      count: games.length,
      games: games.slice(0, 8),
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

/** 모든 도구를 한 번에 주입하기 위한 번들. */
export const ALL_TOOLS = {
  search_game: searchGame,
  predict_win_rate: predictWinRateTool,
  get_weather: getWeather,
  find_places: findPlaces,
  get_route: getRoute,
  search_knowledge: searchKnowledge,
} as const;
