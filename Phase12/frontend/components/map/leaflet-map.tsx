"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  LayersControl,
  LayerGroup,
  useMap,
} from "react-leaflet";
import L, { type LatLngBoundsExpression } from "leaflet";
import type { POI, RouteResult, Stadium, Waypoint } from "@/lib/types";

// Next.js 환경에서 leaflet 기본 마커 이미지 경로 수동 지정
type LeafletDefaultIconProto = { _getIconUrl?: unknown };
delete (L.Icon.Default.prototype as LeafletDefaultIconProto)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const CATEGORY_COLOR: Record<string, string> = {
  stadium: "#dc2626",
  food: "#f97316",
  stay: "#2563eb",
  tour: "#16a34a",
};
const CATEGORY_EMOJI: Record<string, string> = {
  stadium: "⚾",
  food: "🍽️",
  stay: "🏨",
  tour: "🎡",
};
const CATEGORY_LABEL: Record<string, string> = {
  stadium: "🏟️ 경기장",
  food: "🍽️ 음식점",
  stay: "🏨 숙박",
  tour: "🎡 관광지",
};

function makeIcon(category: string): L.DivIcon {
  const color = CATEGORY_COLOR[category] ?? "#6b7280";
  const emoji = CATEGORY_EMOJI[category] ?? "📍";
  return L.divIcon({
    className: "se-leaflet-icon",
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -28],
    html: `<div style="
      background:${color};
      width:32px;height:32px;
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      display:flex;align-items:center;justify-content:center;
      box-shadow:0 2px 6px rgba(0,0,0,0.3);
      border:2px solid #fff;
    "><span style="transform:rotate(45deg);font-size:14px;">${emoji}</span></div>`,
  });
}

function makeWaypointIcon(n: number): L.DivIcon {
  return L.divIcon({
    className: "se-leaflet-wp-icon",
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -14],
    html: `<div style="
      background:#1b6d24;
      width:30px;height:30px;
      border-radius:50%;
      display:flex;align-items:center;justify-content:center;
      box-shadow:0 2px 6px rgba(0,0,0,0.35);
      border:3px solid #fff;
      color:#fff;font-weight:800;font-family:system-ui;font-size:13px;
    ">${n}</div>`,
  });
}

interface FitBoundsProps {
  polyline?: Array<[number, number]>;
  center: [number, number];
}
function FitBoundsOnLoad({ polyline, center }: FitBoundsProps) {
  const map = useMap();
  useEffect(() => {
    if (polyline && polyline.length >= 2) {
      const bounds: LatLngBoundsExpression = polyline as LatLngBoundsExpression;
      map.fitBounds(bounds, { padding: [40, 40] });
    } else {
      map.setView(center, 14);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [polyline?.length, center[0], center[1]]);
  return null;
}

interface LeafletMapProps {
  stadium: Stadium;
  places: { food: POI[]; stay: POI[]; tour: POI[] };
  route: RouteResult | null;
  waypoints?: Waypoint[];
  /**
   * 지도 높이. 숫자 → px, 문자열 → CSS (e.g. "100%", "calc(100dvh - 4rem)").
   * 모바일 풀스크린은 부모 컨테이너가 크기를 잡고 `"100%"` 를 넘기는 패턴을 권장.
   */
  height?: number | string;
  fill?: boolean;
}

export function LeafletMap({
  stadium,
  places,
  route,
  waypoints = [],
  height = 560,
  fill = false,
}: LeafletMapProps) {
  const center: [number, number] = [stadium.lat, stadium.lng];
  const routeColor =
    route?.source === "kakao"
      ? "#2563eb"
      : route?.source === "osrm"
        ? "#7c3aed"
        : "#9ca3af";
  const routeDash = route?.source === "haversine" ? "8 8" : undefined;

  const poiEntries = useMemo(
    () => [
      { key: "food" as const, list: places.food },
      { key: "stay" as const, list: places.stay },
      { key: "tour" as const, list: places.tour },
    ],
    [places.food, places.stay, places.tour],
  );

  const wrapperClass = fill
    ? "h-full w-full overflow-hidden"
    : "overflow-hidden rounded-2xl border border-se-outline-variant";
  const wrapperStyle = fill ? undefined : { height };

  return (
    <div className={wrapperClass} style={wrapperStyle}>
      <MapContainer
        center={center}
        zoom={14}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />
        <FitBoundsOnLoad polyline={route?.polyline} center={center} />

        <LayersControl position="topright" collapsed={false}>
          <LayersControl.Overlay checked name={CATEGORY_LABEL.stadium}>
            <LayerGroup>
              <Marker
                position={center}
                icon={makeIcon("stadium")}
                title={stadium.stadium_name}
              >
                <Popup>
                  <div style={{ minWidth: 200 }}>
                    <div
                      style={{
                        fontWeight: 800,
                        color: "#00193c",
                        fontSize: 14,
                      }}
                    >
                      ⚾ {stadium.stadium_name}
                    </div>
                    <div style={{ fontSize: 12, marginTop: 4 }}>
                      📍 {stadium.address}
                    </div>
                    <div style={{ fontSize: 12, marginTop: 2 }}>
                      🚇 {stadium.subway_station}
                    </div>
                    <div style={{ fontSize: 12, marginTop: 2 }}>
                      👥 수용: {stadium.capacity.toLocaleString()}명
                    </div>
                  </div>
                </Popup>
              </Marker>
            </LayerGroup>
          </LayersControl.Overlay>

          {poiEntries.map(({ key, list }) => (
            <LayersControl.Overlay
              key={key}
              checked={list.length < 40}
              name={`${CATEGORY_LABEL[key]} (${list.length})`}
            >
              <LayerGroup>
                {list.map((p) => (
                  <Marker
                    key={p.content_id}
                    position={[p.lat, p.lng]}
                    icon={makeIcon(key)}
                    title={p.title}
                  >
                    <Popup>
                      <div style={{ minWidth: 180 }}>
                        <div
                          style={{
                            fontWeight: 700,
                            color: "#00193c",
                            fontSize: 13,
                          }}
                        >
                          {p.title}
                        </div>
                        {p.addr ? (
                          <div style={{ fontSize: 11, marginTop: 3 }}>
                            📍 {p.addr}
                          </div>
                        ) : null}
                        {p.tel ? (
                          <div style={{ fontSize: 11, marginTop: 2 }}>
                            ☎️ {p.tel}
                          </div>
                        ) : null}
                        {typeof p.dist_m === "number" ? (
                          <div
                            style={{
                              fontSize: 11,
                              marginTop: 2,
                              color: "#6b7280",
                            }}
                          >
                            🏟️ 경기장에서 {p.dist_m.toLocaleString()}m
                          </div>
                        ) : null}
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </LayerGroup>
            </LayersControl.Overlay>
          ))}
        </LayersControl>

        {route && route.polyline.length >= 2 ? (
          <Polyline
            positions={route.polyline}
            pathOptions={{
              color: routeColor,
              weight: 4,
              opacity: 0.8,
              dashArray: routeDash,
            }}
          />
        ) : null}

        {waypoints.map((wp, i) => (
          <Marker
            key={`wp-${i}-${wp.lat}-${wp.lng}`}
            position={[wp.lat, wp.lng]}
            icon={makeWaypointIcon(i + 1)}
            title={wp.name ?? `경유지 ${i + 1}`}
          >
            <Popup>
              <div style={{ minWidth: 160 }}>
                <div
                  style={{
                    fontWeight: 800,
                    color: "#1b6d24",
                    fontSize: 13,
                  }}
                >
                  경유지 {i + 1}
                </div>
                {wp.name ? (
                  <div style={{ fontSize: 12, marginTop: 3 }}>{wp.name}</div>
                ) : null}
                <div
                  style={{ fontSize: 11, marginTop: 2, color: "#6b7280" }}
                >
                  {wp.lat.toFixed(4)}, {wp.lng.toFixed(4)}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
