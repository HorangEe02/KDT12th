import type { RouteLeg, RouteResult } from "@/lib/types";

const EARTH_R = 6_371_000; // meters

export function haversineM(
  [lat1, lng1]: [number, number],
  [lat2, lng2]: [number, number],
): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dPhi = toRad(lat2 - lat1);
  const dLmb = toRad(lng2 - lng1);
  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const a =
    Math.sin(dPhi / 2) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLmb / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return EARTH_R * c;
}

/**
 * 다구간 Haversine — 연속 직선 연결. duration 은 계산 안 함.
 */
export function haversineRoute(
  points: Array<[number, number]>,
  ms: number = 0,
): RouteResult {
  if (points.length < 2) throw new Error("need >= 2 points");
  const legs: RouteLeg[] = [];
  let total = 0;
  for (let i = 0; i < points.length - 1; i++) {
    const d = haversineM(points[i], points[i + 1]);
    legs.push({ distance_m: d, duration_sec: null });
    total += d;
  }
  return {
    polyline: [...points],
    distance_m: total,
    duration_sec: null,
    toll_fare_krw: null,
    source: "haversine",
    fallback: true,
    attempts: [
      { provider: "haversine", status: "ok", ms, reason: "straight-line" },
    ],
    fetched_at: Date.now(),
    legs,
  };
}
