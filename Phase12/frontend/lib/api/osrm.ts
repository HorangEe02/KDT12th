/**
 * OSRM (Open Source Routing Machine) Tier-2 fallback.
 * Public demo server: https://router.project-osrm.org
 * 무료 · API 키 불필요 · OpenStreetMap 데이터 기반.
 *
 * 라이선스: 지도 하단에 "© OpenStreetMap contributors · Routing by OSRM" 표시 필요.
 */
import "server-only";
import type { RouteLeg, RouteResult } from "@/lib/types";

const ENDPOINT = "https://router.project-osrm.org/route/v1/driving";
const TIMEOUT_MS = 5000;

interface OSRMResponse {
  code: string;
  routes?: Array<{
    distance: number;
    duration: number;
    geometry: { type: "LineString"; coordinates: [number, number][] };
    legs?: Array<{ distance: number; duration: number }>;
  }>;
  message?: string;
}

/**
 * 다구간 OSRM 호출. points[0] = origin, points[N-1] = destination, 중간은 waypoints.
 */
export async function fetchOSRM(
  points: Array<[number, number]>,
): Promise<RouteResult> {
  if (points.length < 2) throw new Error("need >= 2 points");
  const startedAt = performance.now();
  const path = points.map(([lat, lng]) => `${lng},${lat}`).join(";");
  const url =
    `${ENDPOINT}/${path}` +
    `?overview=full&geometries=geojson&alternatives=false&steps=false`;

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), TIMEOUT_MS);

  try {
    const resp = await fetch(url, {
      signal: ctl.signal,
      headers: { "User-Agent": "away-game-companion/1.0" },
    });
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }
    const data = (await resp.json()) as OSRMResponse;
    if (data.code !== "Ok" || !data.routes?.length) {
      throw new Error(data.message ?? `OSRM code=${data.code}`);
    }
    const r = data.routes[0];
    // GeoJSON coords are [lon, lat]; Leaflet wants [lat, lng]
    const polyline: Array<[number, number]> = r.geometry.coordinates.map(
      ([lon, lat]) => [lat, lon],
    );
    const legs: RouteLeg[] | undefined = r.legs?.map((l) => ({
      distance_m: l.distance,
      duration_sec: l.duration,
    }));
    const ms = Math.round(performance.now() - startedAt);
    return {
      polyline,
      distance_m: r.distance,
      duration_sec: r.duration,
      toll_fare_krw: null,
      source: "osrm",
      fallback: true,
      attempts: [{ provider: "osrm", status: "ok", ms }],
      fetched_at: Date.now(),
      legs,
    };
  } finally {
    clearTimeout(timer);
  }
}
