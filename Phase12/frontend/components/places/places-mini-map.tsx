"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import type { POI, Stadium } from "@/lib/types";

// Next.js 환경에서 leaflet 기본 마커 이미지 경로 수동 지정 (idempotent)
type LeafletDefaultIconProto = { _getIconUrl?: unknown };
delete (L.Icon.Default.prototype as LeafletDefaultIconProto)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const CAT_COLOR: Record<string, string> = {
  food: "#f97316",
  stay: "#2563eb",
  tour: "#16a34a",
};
const CAT_EMOJI: Record<string, string> = {
  food: "🍽️",
  stay: "🏨",
  tour: "🎡",
};

function makeStadiumIcon(): L.DivIcon {
  return L.divIcon({
    className: "se-leaflet-icon",
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -36],
    html: `<div style="
      background:#dc2626;
      width:40px;height:40px;
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      display:flex;align-items:center;justify-content:center;
      box-shadow:0 4px 12px rgba(0,0,0,0.4);
      border:3px solid #fff;
    "><span style="transform:rotate(45deg);font-size:18px;">⚾</span></div>`,
  });
}

function makePoiIcon(category: string, rank: number, selected: boolean): L.DivIcon {
  const color = CAT_COLOR[category] ?? "#6b7280";
  const emoji = CAT_EMOJI[category] ?? "📍";
  const size = selected ? 36 : 28;
  const ring = selected ? "border:3px solid #00193c;" : "border:2px solid #fff;";
  return L.divIcon({
    className: "se-leaflet-icon",
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size + 4],
    html: `<div style="
      background:${color};
      width:${size}px;height:${size}px;
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      display:flex;align-items:center;justify-content:center;
      box-shadow:0 ${selected ? 6 : 2}px ${selected ? 14 : 6}px rgba(0,0,0,${selected ? 0.5 : 0.3});
      ${ring}
      position:relative;
    ">
      <span style="transform:rotate(45deg);font-size:${selected ? 14 : 12}px;">${emoji}</span>
      <div style="
        position:absolute;top:-4px;right:-4px;
        background:#00193c;color:white;
        font-size:9px;font-weight:800;
        width:16px;height:16px;
        border-radius:50%;
        display:flex;align-items:center;justify-content:center;
        transform:rotate(45deg);
        border:1.5px solid white;
      ">${rank}</div>
    </div>`,
  });
}

interface FitBoundsProps {
  points: Array<[number, number]>;
}
function FitBoundsOnLoad({ points }: FitBoundsProps) {
  const map = useMap();
  useEffect(() => {
    if (points.length >= 2) {
      map.fitBounds(points as L.LatLngBoundsExpression, {
        padding: [40, 40],
        maxZoom: 16,
      });
    } else if (points.length === 1) {
      map.setView(points[0], 15);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points.length, points[0]?.[0], points[0]?.[1]]);
  return null;
}

/** 지도 내부에서 마커 클릭 시 카드 영역으로 스크롤 + URL ?p=... 갱신 */
function useSelectPoi() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  return (contentId: string) => {
    const p = new URLSearchParams(searchParams.toString());
    p.set("p", contentId);
    router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    if (typeof document !== "undefined") {
      const target = document.getElementById(`poi-card-${contentId}`);
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        target.classList.add("ring-2", "ring-se-primary", "ring-offset-2");
        setTimeout(() => {
          target.classList.remove("ring-2", "ring-se-primary", "ring-offset-2");
        }, 2000);
      }
    }
  };
}

interface PlacesMiniMapProps {
  stadium: Stadium;
  pois: POI[];
  category: "food" | "stay" | "tour";
  selectedId?: string;
  height?: number;
}

export function PlacesMiniMap({
  stadium,
  pois,
  category,
  selectedId,
  height = 380,
}: PlacesMiniMapProps) {
  const center: [number, number] = [stadium.lat, stadium.lng];
  const onSelect = useSelectPoi();

  const points = useMemo<Array<[number, number]>>(
    () => [center, ...pois.map((p): [number, number] => [p.lat, p.lng])],
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [stadium.lat, stadium.lng, pois.length],
  );

  return (
    <div
      className="overflow-hidden rounded-2xl border border-se-outline-variant"
      style={{ height }}
    >
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
        <FitBoundsOnLoad points={points} />

        {/* 경기장 반경 500m 원 */}
        <Circle
          center={center}
          radius={500}
          pathOptions={{
            color: "#00193c",
            weight: 1.5,
            opacity: 0.4,
            fillColor: "#abc7ff",
            fillOpacity: 0.08,
            dashArray: "4 6",
          }}
        />

        {/* 경기장 마커 */}
        <Marker position={center} icon={makeStadiumIcon()}>
          <Popup>
            <div style={{ minWidth: 200 }}>
              <div style={{ fontWeight: 800, color: "#00193c", fontSize: 14 }}>
                ⚾ {stadium.stadium_name}
              </div>
              <div style={{ fontSize: 12, marginTop: 4 }}>
                📍 {stadium.address}
              </div>
              <div style={{ fontSize: 12, marginTop: 2 }}>
                🚇 {stadium.subway_station}
              </div>
            </div>
          </Popup>
        </Marker>

        {/* TOP POI 마커 (rank 1~10) */}
        {pois.map((poi, idx) => (
          <Marker
            key={poi.content_id}
            position={[poi.lat, poi.lng]}
            icon={makePoiIcon(category, idx + 1, poi.content_id === selectedId)}
            eventHandlers={{
              click: () => onSelect(poi.content_id),
            }}
          >
            <Popup>
              <div style={{ minWidth: 200 }}>
                <div
                  style={{
                    fontWeight: 700,
                    color: "#00193c",
                    fontSize: 13,
                    marginBottom: 4,
                  }}
                >
                  #{idx + 1} {poi.title}
                </div>
                {poi.addr ? (
                  <div style={{ fontSize: 11, marginTop: 2 }}>
                    📍 {poi.addr}
                  </div>
                ) : null}
                {typeof poi.dist_m === "number" ? (
                  <div
                    style={{ fontSize: 11, marginTop: 2, color: "#6b7280" }}
                  >
                    🏟️ 경기장에서 {poi.dist_m.toLocaleString()}m
                  </div>
                ) : null}
                <button
                  onClick={() => onSelect(poi.content_id)}
                  style={{
                    marginTop: 8,
                    padding: "4px 10px",
                    background: "#00193c",
                    color: "white",
                    fontSize: 11,
                    fontWeight: 700,
                    border: "none",
                    borderRadius: 6,
                    cursor: "pointer",
                  }}
                >
                  카드에서 자세히 보기 →
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
