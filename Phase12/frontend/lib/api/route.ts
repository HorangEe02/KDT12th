/**
 * 길찾기 Orchestrator — 3-tier fallback.
 * 상세 설계: docs/OSM_FALLBACK_PLAN.md
 *
 *   Tier 1: Kakao 모빌리티 (키 있을 때만)
 *   Tier 2: OSRM public demo (키 불필요)
 *   Tier 3: Haversine 직선 (항상 성공)
 */
import "server-only";
import type { RouteAttempt, RouteResult } from "@/lib/types";
import { fetchKakaoRoute, isKakaoEnabled } from "@/lib/api/kakao";
import { fetchOSRM } from "@/lib/api/osrm";
import { haversineRoute } from "@/lib/api/haversine";

const cache = new Map<string, RouteResult>();

function cacheKey(
  origin: [number, number],
  destination: [number, number],
): string {
  const round = (n: number) => n.toFixed(5);
  return [
    round(origin[0]),
    round(origin[1]),
    round(destination[0]),
    round(destination[1]),
  ].join(":");
}

export async function requestRoute(
  origin: [number, number],
  destination: [number, number],
  opts: { bypassCache?: boolean } = {},
): Promise<RouteResult> {
  const key = cacheKey(origin, destination);
  if (!opts.bypassCache && cache.has(key)) return cache.get(key)!;

  const attempts: RouteAttempt[] = [];

  // Tier 1 — Kakao
  if (isKakaoEnabled()) {
    const t0 = performance.now();
    try {
      const out = await fetchKakaoRoute(origin, destination);
      const result = { ...out, attempts: [...attempts, ...out.attempts] };
      cache.set(key, result);
      return result;
    } catch (err) {
      attempts.push({
        provider: "kakao",
        status: "error",
        ms: Math.round(performance.now() - t0),
        reason: err instanceof Error ? err.message : String(err),
      });
    }
  } else {
    attempts.push({
      provider: "kakao",
      status: "skipped",
      ms: 0,
      reason: "no-key",
    });
  }

  // Tier 2 — OSRM
  const t1 = performance.now();
  try {
    const out = await fetchOSRM(origin, destination);
    const result = { ...out, attempts: [...attempts, ...out.attempts] };
    cache.set(key, result);
    return result;
  } catch (err) {
    attempts.push({
      provider: "osrm",
      status: "error",
      ms: Math.round(performance.now() - t1),
      reason: err instanceof Error ? err.message : String(err),
    });
  }

  // Tier 3 — Haversine
  const t2 = performance.now();
  const h = haversineRoute(
    origin,
    destination,
    Math.round(performance.now() - t2),
  );
  const result = { ...h, attempts: [...attempts, ...h.attempts] };
  cache.set(key, result);
  return result;
}
