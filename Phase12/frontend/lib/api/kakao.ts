/**
 * Kakao 모빌리티 길찾기 클라이언트 (Tier 1).
 * 포팅 원본: src/api/kakao_map.py
 *
 * 키 없거나 401/5xx 시 throw → orchestrator 가 Tier 2 (OSRM) 로 fall through.
 */
import "server-only";
import type { RouteResult } from "@/lib/types";

const ENDPOINT = "https://apis-navi.kakaomobility.com/v1/directions";
const TIMEOUT_MS = 5000;

interface KakaoResponse {
  routes?: Array<{
    result_code?: number;
    summary?: {
      distance?: number;
      duration?: number;
      fare?: { toll?: number; taxi?: number };
    };
    sections?: Array<{
      roads?: Array<{ vertexes?: number[] }>;
    }>;
  }>;
}

function resolveKey(): string | null {
  return (
    process.env.KAKAO_MOBILITY_API_KEY ||
    process.env.KAKAO_REST_API_KEY ||
    null
  );
}

export function isKakaoEnabled(): boolean {
  return Boolean(resolveKey());
}

export async function fetchKakaoRoute(
  origin: [number, number],
  destination: [number, number],
): Promise<RouteResult> {
  const startedAt = performance.now();
  const key = resolveKey();
  if (!key) throw new Error("no-key");

  const params = new URLSearchParams({
    origin: `${origin[1]},${origin[0]}`,
    destination: `${destination[1]},${destination[0]}`,
    priority: "RECOMMEND",
  });
  const url = `${ENDPOINT}?${params.toString()}`;

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);

  try {
    const resp = await fetch(url, {
      headers: {
        Authorization: `KakaoAK ${key}`,
        "Content-Type": "application/json",
      },
      signal: ctl.signal,
    });
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }
    const data = (await resp.json()) as KakaoResponse;
    const route = data.routes?.[0];
    if (!route || route.result_code !== undefined && route.result_code !== 0) {
      throw new Error(`kakao result_code=${route?.result_code}`);
    }

    const pairs: Array<[number, number]> = [];
    for (const sec of route.sections ?? []) {
      for (const road of sec.roads ?? []) {
        const flat = road.vertexes ?? [];
        for (let i = 0; i < flat.length - 1; i += 2) {
          const lng = flat[i];
          const lat = flat[i + 1];
          pairs.push([lat, lng]);
        }
      }
    }
    if (pairs.length < 2) throw new Error("no-vertices");

    const ms = Math.round(performance.now() - startedAt);
    return {
      polyline: pairs,
      distance_m: route.summary?.distance ?? null,
      duration_sec: route.summary?.duration ?? null,
      toll_fare_krw: route.summary?.fare?.toll ?? null,
      source: "kakao",
      fallback: false,
      attempts: [{ provider: "kakao", status: "ok", ms }],
      fetched_at: Date.now(),
    };
  } finally {
    clearTimeout(timer);
  }
}
