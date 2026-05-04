"use client";

import { useState } from "react";

export interface LocationOption {
  label: string;
  lat: number;
  lng: number;
}

const PRESETS: LocationOption[] = [
  { label: "대구 중구", lat: 35.8714, lng: 128.6014 },
  { label: "대구 동성로", lat: 35.8687, lng: 128.5938 },
  { label: "대구 수성구", lat: 35.8582, lng: 128.6315 },
  { label: "대구 달서구", lat: 35.8299, lng: 128.5329 },
  { label: "서울시청", lat: 37.5665, lng: 126.978 },
  { label: "강남역", lat: 37.4979, lng: 127.0276 },
  { label: "판교", lat: 37.3948, lng: 127.1112 },
];

interface Props {
  current: { lat: number; lng: number; label: string };
  onSelect: (loc: LocationOption) => void;
  geoSource: "gps" | "ip" | "default" | "manual";
  geoError?: string | null;
  loading?: boolean;
}

export default function LocationSelector({
  current,
  onSelect,
  geoSource,
  geoError,
  loading,
}: Props) {
  const [open, setOpen] = useState(false);

  const sourceLabel =
    geoSource === "gps"
      ? "GPS"
      : geoSource === "ip"
      ? "IP 위치"
      : geoSource === "manual"
      ? "직접 선택"
      : "기본 위치";

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-[11px] text-text-tertiary hover:text-primary transition-colors cursor-pointer"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        <span>📍</span>
        {loading ? (
          "위치 확인 중..."
        ) : (
          <>
            <span className={geoSource === "gps" ? "text-success" : ""}>
              {current.label}
            </span>
            <span className="text-[9px] opacity-60">({sourceLabel})</span>
            {geoError && geoSource === "default" && (
              <span className="text-warning text-[9px] ml-1">
                GPS 사용 불가
              </span>
            )}
            <span className="text-[9px] opacity-40">▼</span>
          </>
        )}
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 z-50 bg-surface-1 border border-outline/30 rounded-sm shadow-lg min-w-[200px]">
          <div
            className="px-3 py-1.5 text-[10px] text-text-tertiary border-b border-outline/20"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            위치 선택
          </div>
          {PRESETS.map((loc) => {
            const isActive =
              Math.abs(current.lat - loc.lat) < 0.005 &&
              Math.abs(current.lng - loc.lng) < 0.005;
            return (
              <button
                key={loc.label}
                onClick={() => {
                  onSelect(loc);
                  setOpen(false);
                }}
                className={`w-full text-left px-3 py-2 text-xs hover:bg-primary/5 transition-colors cursor-pointer ${
                  isActive
                    ? "text-primary font-bold bg-primary/5"
                    : "text-text-primary"
                }`}
                style={{ fontFamily: "var(--font-ko)" }}
              >
                {loc.label}
                {isActive && (
                  <span className="ml-1 text-[9px] text-success">현재</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
