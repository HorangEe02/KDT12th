/**
 * 승률 예측 (Phase 4 포팅).
 * 포팅 원본: src/ai/predict.py
 *
 * 모델: StandardScaler + 로지스틱 회귀, 5-피처.
 * 수식:  z = (x - mean) / scale
 *        logit = dot(z, coef) + intercept
 *        prob = 1 / (1 + exp(-logit))
 */
import "server-only";
import fs from "node:fs/promises";
import path from "node:path";
import type { TeamStat, WinRateModel, PredictResponse } from "@/lib/types";

const NEUTRAL = 0.45;

let _model: WinRateModel | null = null;
let _stats: TeamStat[] | null = null;

async function readPublicJson<T>(rel: string): Promise<T> {
  const abs = path.join(process.cwd(), "public", rel);
  const raw = await fs.readFile(abs, "utf-8");
  return JSON.parse(raw) as T;
}

export async function loadModel(): Promise<WinRateModel> {
  if (_model) return _model;
  _model = await readPublicJson<WinRateModel>("data/model.json");
  return _model;
}

export async function loadTeamStats(): Promise<TeamStat[]> {
  if (_stats) return _stats;
  _stats = await readPublicJson<TeamStat[]>("data/team-stats.json");
  return _stats;
}

function sigmoid(z: number): number {
  return 1 / (1 + Math.exp(-z));
}

function dot(a: number[], b: number[]): number {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}

function scale(x: number[], mean: number[], scaleArr: number[]): number[] {
  return x.map((v, i) => (v - mean[i]) / scaleArr[i]);
}

/** 최신 연도 기준 팀의 스탯 row 반환. */
export function latestStatFor(
  team: string,
  stats: TeamStat[],
): TeamStat | null {
  const maxYear = stats.reduce((m, r) => (r.year > m ? r.year : m), 0);
  return stats.find((r) => r.team === team && r.year === maxYear) ?? null;
}

/**
 * `team` 이 `opponent` 원정 경기에서 이길 확률 (0~1).
 * 데이터/모델 누락 시 NEUTRAL(0.45) 반환.
 */
export async function predictWinRate(
  team: string,
  opponent: string,
): Promise<PredictResponse> {
  if (team === opponent) {
    return {
      team,
      opponent,
      prob: NEUTRAL,
      source: "neutral-fallback",
      detail: "동일 팀",
    };
  }

  try {
    const [model, stats] = await Promise.all([loadModel(), loadTeamStats()]);

    const a = latestStatFor(team, stats);
    const b = latestStatFor(opponent, stats);
    if (!a || !b) {
      return {
        team,
        opponent,
        prob: NEUTRAL,
        source: "neutral-fallback",
        detail: `기록 없음: ${!a ? team : opponent}`,
      };
    }

    const x = [
      a.away_win_rate,
      b.home_win_rate,
      a.final_rank,
      b.final_rank,
      b.final_rank - a.final_rank,
    ];
    const z = scale(x, model.scaler.mean, model.scaler.scale);
    const logit = dot(z, model.logreg.coef) + model.logreg.intercept;
    const prob = Math.round(sigmoid(logit) * 10000) / 10000;

    return { team, opponent, prob, source: "logreg" };
  } catch (err) {
    return {
      team,
      opponent,
      prob: NEUTRAL,
      source: "error",
      detail: err instanceof Error ? err.message : String(err),
    };
  }
}

/** 게임 ID 기반 재현 가능한 더미값 (모델 불가 시 fallback). */
export function dummyWinProb(gameId: string): number {
  let h = 0;
  for (let i = 0; i < gameId.length; i++) {
    h = (h * 31 + gameId.charCodeAt(i)) | 0;
  }
  const pseudo = (Math.abs(h) % 10000) / 10000; // 0~1
  const prob = 0.35 + pseudo * 0.3; // [0.35, 0.65)
  return Math.round(prob * 100) / 100;
}
