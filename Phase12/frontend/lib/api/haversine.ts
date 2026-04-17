import type { RouteResult } from "@/lib/types";

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

export function haversineRoute(
  origin: [number, number],
  destination: [number, number],
  ms: number = 0,
): RouteResult {
  return {
    polyline: [origin, destination],
    distance_m: haversineM(origin, destination),
    duration_sec: null,
    toll_fare_krw: null,
    source: "haversine",
    fallback: true,
    attempts: [
      { provider: "haversine", status: "ok", ms, reason: "straight-line" },
    ],
    fetched_at: Date.now(),
  };
}
