/**
 * 경유지 ↔ 구장 거리 계산 + 경고 판정.
 * 경기 변경으로 구장이 바뀌면 기존 경유지가 "멀어질" 수 있어 UI 에 경고 표시.
 */
import { haversineM } from "@/lib/api/haversine";
import type { Waypoint } from "@/lib/types";

/** 이 거리 이상이면 "경유지가 현재 구장과 멀어요" 경고 */
export const FAR_WAYPOINT_THRESHOLD_M = 5_000;

export interface WaypointDistance {
  waypoint: Waypoint;
  distance_m: number;
  isFar: boolean;
}

export function annotateWaypointDistances(
  waypoints: Waypoint[],
  stadium: { lat: number; lng: number },
): WaypointDistance[] {
  return waypoints.map((w) => {
    const d = haversineM([w.lat, w.lng], [stadium.lat, stadium.lng]);
    return {
      waypoint: w,
      distance_m: d,
      isFar: d > FAR_WAYPOINT_THRESHOLD_M,
    };
  });
}

export function formatDistanceShort(m: number): string {
  return m >= 1000 ? `${(m / 1000).toFixed(1)}km` : `${Math.round(m)}m`;
}
