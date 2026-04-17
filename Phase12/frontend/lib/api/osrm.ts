/**
 * OSRM (Open Source Routing Machine) Tier-2 fallback.
 * Public demo server: https://router.project-osrm.org
 * 무료 · API 키 불필요 · OpenStreetMap 데이터 기반.
 *
 * 라이선스: 지도 하단에 "© OpenStreetMap contributors · Routing by OSRM" 표시 필요.
 */
import "server-only";
import type { RouteResult } from "@/lib/types";

const ENDPOINT = "https://router.project-osrm.org/route/v1/driving";
const TIMEOUT_MS = 5000;

interface OSRMResponse {
  code: string;
  routes?: Array<{
    distance: number;
    duration: number;
    geometry: { type: "LineString"; coordinates: [number, number][] };
  }>;
  message?: string;
}

export async function fetchOSRM(
  origin: [number, number],
  destination: [number, number],
): Promise<RouteResult> {
  const startedAt = performance.now();
  const url =
    `${ENDPOINT}/${origin[1]},${origin[0]};${destination[1]},${destination[0]}` +
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
    };
  } finally {
    clearTimeout(timer);
  }
}
