"use client";

/**
 * LeafletMap — OpenStreetMap 타일 + 사용자 위치 + 음식점 마커.
 *
 * 이 파일은 Leaflet 과 react-leaflet 을 직접 import 하므로 `window` 가 필요합니다.
 * Next.js SSR 에서 에러가 나므로 반드시 `LeafletMapClient.tsx` 를 통해
 * dynamic({ ssr: false }) 로 래핑해서 사용하세요.
 */
import { MapContainer, TileLayer, Marker, Popup, Circle } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Restaurant } from "@/lib/types";
import {
  buildGlassMarkerHTML,
  ensureGlassMarkerStylesInjected,
} from "@/components/map/markers/LiquidGlassMarker";

// ────────────────────────────────────────────────────────────
// Liquid Glass DivIcon — 통합 마커 빌더 사용
// ────────────────────────────────────────────────────────────
ensureGlassMarkerStylesInjected();

const foodIcon = L.divIcon({
  html: buildGlassMarkerHTML({ kind: "restaurant" }),
  className: "lg-marker",
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -24],
});

const foodActiveIcon = L.divIcon({
  html: buildGlassMarkerHTML({ kind: "restaurantSelected" }),
  className: "lg-marker",
  iconSize: [34, 34],
  iconAnchor: [17, 34],
  popupAnchor: [0, -28],
});

const userIcon = L.divIcon({
  html: buildGlassMarkerHTML({ kind: "user" }),
  className: "lg-marker",
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -16],
});

// ────────────────────────────────────────────────────────────
// Props
// ────────────────────────────────────────────────────────────
interface LeafletMapProps {
  userLat: number;
  userLng: number;
  restaurants: Restaurant[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  height?: string;
  zoom?: number;
  /** 사용자 위치 기준 반경 원 (미터). 없으면 미표시 */
  showRadius?: number;
  /** 지도 중심을 사용자 위치로 할지 / 선택된 음식점으로 할지 */
  centerOn?: "user" | "selected";
}

export default function LeafletMap({
  userLat,
  userLng,
  restaurants,
  selectedId = null,
  onSelect,
  height = "400px",
  zoom = 15,
  showRadius,
  centerOn = "user",
}: LeafletMapProps) {
  // lat/lng 없는 아이템은 걸러냄 (mock fallback 대응)
  const withCoords = restaurants.filter(
    (r): r is Restaurant & { lat: number; lng: number } =>
      typeof r.lat === "number" && typeof r.lng === "number"
  );

  const selectedRest =
    selectedId != null ? withCoords.find((r) => String(r.id) === String(selectedId)) : null;

  const center: [number, number] =
    centerOn === "selected" && selectedRest
      ? [selectedRest.lat, selectedRest.lng]
      : [userLat, userLng];

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      scrollWheelZoom={false}
      style={{
        height,
        width: "100%",
        borderRadius: "1.25rem",
        zIndex: 0,
      }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
      />

      {showRadius && (
        <Circle
          center={[userLat, userLng]}
          radius={showRadius}
          pathOptions={{
            color: "#e8593c",
            weight: 1.5,
            fillColor: "#e8593c",
            fillOpacity: 0.06,
          }}
        />
      )}

      {/* 사용자 위치 */}
      <Marker position={[userLat, userLng]} icon={userIcon}>
        <Popup>내 위치</Popup>
      </Marker>

      {/* 음식점 마커 */}
      {withCoords.map((r) => {
        const isSelected = String(r.id) === String(selectedId);
        return (
          <Marker
            key={r.id}
            position={[r.lat, r.lng]}
            icon={isSelected ? foodActiveIcon : foodIcon}
            eventHandlers={{
              click: () => onSelect?.(String(r.id)),
            }}
          >
            <Popup>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 2 }}>
                {r.name}
              </div>
              <div style={{ fontSize: 11, opacity: 0.75 }}>
                {r.category ?? "기타"} · {r.distance_m ?? "?"}m
              </div>
              {r.address && (
                <div style={{ fontSize: 10, opacity: 0.6, marginTop: 4 }}>
                  {r.address}
                </div>
              )}
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
