/**
 * Phase 6 공통 타입 정의.
 * 포팅 원본: src/data_loader.py + public/data/*.json 스키마
 */

export type TeamCode =
  | "LG"
  | "KT"
  | "SSG"
  | "두산"
  | "KIA"
  | "NC"
  | "삼성"
  | "롯데"
  | "한화"
  | "키움";

export type PartyType = "solo" | "couple" | "family" | "friends";
export type TransportType = "train" | "car" | "bus";
export type Viewport = "web" | "mobile";

export interface Stadium {
  stadium_name: string;
  short_name: string;
  home_team: string;
  city: string;
  address: string;
  lat: number;
  lng: number;
  capacity: number;
  subway_station: string;
}

export type GameStatus =
  | "SCHEDULED"
  | "IN_PROGRESS"
  | "FINISHED"
  | "CANCELED";

export interface GameScore {
  home: number;
  away: number;
}

/**
 * KBO 경기 — kbo-game@0.0.2 + 자체 확장.
 * 포팅 원본 스키마: scripts/fetch_kbo_schedule.mjs normalizeGame()
 */
export interface Game {
  game_id: string;
  date: string;           // YYYY-MM-DD
  day_of_week?: string;   // "일"~"토"
  home_team: string;
  away_team: string;
  stadium: string;        // short name (잠실, 수원 …)
  start_time: string;     // "HH:MM"
  /** @deprecated use start_time */
  time?: string;
  stadium_short?: string;
  week?: number;

  // kbo-game 실데이터 필드 (2026 시즌 교체 후 추가)
  home_pitcher?: string | null;
  away_pitcher?: string | null;
  win_pitcher?: string | null;
  lose_pitcher?: string | null;
  save_pitcher?: string | null;
  score?: GameScore | null;
  status?: GameStatus;
  current_inning?: number | null;
  broadcast?: string[] | string | null;
  season?: number;
}

export interface TeamStat {
  year: number;
  team: string;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  home_win_rate: number;
  away_win_rate: number;
  final_rank: number;
}

/** public/data/poi/*.json 의 원본 스키마. */
export interface POI {
  content_id: string;
  title: string;
  category: "food" | "stay" | "tour" | string;
  addr: string;
  lat: number;
  lng: number;
  tel?: string;
  first_image?: string;
  dist_m?: number;
  stadium?: string;
  rating?: number; // synthesized at view-time
}

export interface Tip {
  id: string;
  stadium: string;
  team: string;
  category: string;
  tip: string;
  source?: string;
}

/** Phase 4 로지스틱 회귀 모델 직렬화 포맷 (public/data/model.json). */
export interface WinRateModel {
  feature_names: string[];
  scaler: {
    mean: number[];
    scale: number[];
  };
  logreg: {
    coef: number[];
    intercept: number;
    classes: [number, number];
  };
}

export interface PredictResponse {
  team: string;
  opponent: string;
  prob: number;
  source: "logreg" | "neutral-fallback" | "error";
  detail?: string;
}

/** 3-tier 길찾기 결과. 자세한 설계: docs/OSM_FALLBACK_PLAN.md */
export type RouteSource = "kakao" | "osrm" | "haversine";
export type RouteMode = "driving";

export interface RouteAttempt {
  provider: "kakao" | "osrm" | "haversine";
  status: "ok" | "error" | "skipped";
  ms: number;
  reason?: string;
}

export interface RouteResult {
  polyline: Array<[number, number]>; // [lat, lng] — Leaflet 친화
  distance_m: number | null;
  duration_sec: number | null;
  toll_fare_krw: number | null;
  source: RouteSource;
  fallback: boolean; // source !== "kakao"
  attempts: RouteAttempt[];
  fetched_at: number;
}

export interface Filters {
  team: TeamCode | string;
  dateRange?: [string, string];
  budget?: number;
  party?: PartyType;
  transport?: TransportType;
  demoMode?: boolean;
}

export interface SharedPlan {
  planId: string;
  filters: Filters;
  createdAt: number;
  title?: string;
}
