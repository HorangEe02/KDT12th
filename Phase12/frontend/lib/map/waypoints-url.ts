/**
 * 경유지 URL 직렬화. Format:
 *   wps=<lat>,<lng>[,<name>]|<lat>,<lng>[,<name>]...
 * 이름에 `,` / `|` 포함 시 URL 인코딩.
 */
import type { Waypoint } from "@/lib/types";

export const MAX_WAYPOINTS = 5;

export function parseWaypointsParam(raw: string | null | undefined): Waypoint[] {
  if (!raw) return [];
  const parts = raw.split("|").slice(0, MAX_WAYPOINTS);
  const out: Waypoint[] = [];
  for (const part of parts) {
    const [latStr, lngStr, ...nameParts] = part.split(",");
    const lat = Number.parseFloat(latStr);
    const lng = Number.parseFloat(lngStr);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) continue;
    const nameRaw = nameParts.join(",").trim();
    const name = nameRaw ? safeDecode(nameRaw) : undefined;
    out.push({ lat, lng, name });
  }
  return out;
}

export function serializeWaypoints(waypoints: Waypoint[]): string {
  return waypoints
    .slice(0, MAX_WAYPOINTS)
    .map((w) => {
      const coord = `${w.lat.toFixed(5)},${w.lng.toFixed(5)}`;
      if (!w.name) return coord;
      return `${coord},${encodeURIComponent(w.name)}`;
    })
    .join("|");
}

function safeDecode(s: string): string {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}
