"use client";

import { useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  ORIGIN_PRESETS,
  ORIGIN_LABEL,
  ORIGIN_GROUPS,
  CUSTOM_ORIGIN_KEY,
  findNearestPreset,
} from "@/lib/map/origins";
import { cn } from "@/lib/utils";

interface OriginPickerDialogProps {
  currentOrigin: string;
  onClose: () => void;
}

type GeoState = "idle" | "loading" | "denied" | "ok" | "unsupported";

export function OriginPickerDialog({
  currentOrigin,
  onClose,
}: OriginPickerDialogProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  const [openGroupId, setOpenGroupId] = useState<string>(() => {
    for (const g of ORIGIN_GROUPS) if (g.keys.includes(currentOrigin)) return g.id;
    return "capital";
  });
  const [geoState, setGeoState] = useState<GeoState>("idle");
  const [geoHint, setGeoHint] = useState<string | null>(null);

  function pushParams(param: Record<string, string | null>) {
    const p = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(param)) {
      if (v === null) p.delete(k);
      else p.set(k, v);
    }
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    });
  }

  function selectPreset(key: string) {
    pushParams({ origin: key, lat: null, lng: null });
    onClose();
  }

  function selectMyLocation(highAccuracy = false) {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGeoState("unsupported");
      setGeoHint("이 브라우저는 위치 정보를 지원하지 않습니다.");
      return;
    }
    setGeoState("loading");
    setGeoHint(
      highAccuracy ? "정밀 측위 재시도 중... (최대 20초)" : "위치 확인 중...",
    );
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const nearest = findNearestPreset(lat, lng);
        setGeoState("ok");
        setGeoHint(
          `현재 위치 적용 (가장 가까운 역: ${nearest.label} · ${nearest.distanceKm}km)`,
        );
        pushParams({
          origin: CUSTOM_ORIGIN_KEY,
          lat: lat.toFixed(5),
          lng: lng.toFixed(5),
        });
        setTimeout(onClose, 500);
      },
      (err) => {
        setGeoState("denied");
        const base =
          err.code === 1
            ? "위치 권한이 차단됨 — macOS 시스템 설정 → 개인정보 보호 및 보안 → 위치 서비스 또는 브라우저 주소창 🔒 → 위치 '허용' 으로 변경"
            : err.code === 2
              ? "위치 공급자 응답 없음 — Wi-Fi/GPS 비활성, VPN 연결, 또는 기업 네트워크 차단 가능"
              : err.code === 3
                ? "측위 시간 초과 — 아래 '정밀 재시도' 버튼으로 GPS 기반 재시도"
                : "알 수 없는 오류";
        const detail = err.message ? ` · ${err.message}` : "";
        setGeoHint(`[code ${err.code}] ${base}${detail}`);
      },
      {
        enableHighAccuracy: highAccuracy,
        timeout: highAccuracy ? 20_000 : 15_000,
        maximumAge: 60_000,
      },
    );
  }

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/55 p-6 backdrop-blur-sm"
      role="dialog"
      aria-modal
      aria-label="출발지 선택"
      onClick={onClose}
    >
      <div
        className="relative flex max-h-[80dvh] w-full max-w-lg flex-col overflow-hidden rounded-3xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-se-outline-variant/50 px-5 py-4">
          <h3 className="font-display text-base font-bold text-se-primary">
            🚗 출발지 선택
          </h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-se-surface-container-low"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </header>

        <div className="overflow-y-auto px-5 py-4">
          {/* 📍 내 위치 */}
          <button
            type="button"
            onClick={() => selectMyLocation()}
            disabled={geoState === "loading"}
            className={cn(
              "mb-4 flex w-full items-center justify-between rounded-xl border-2 px-4 py-3 font-display text-sm font-bold transition-colors",
              currentOrigin === CUSTOM_ORIGIN_KEY
                ? "border-se-secondary bg-se-secondary/10 text-se-secondary"
                : "border-se-primary bg-white text-se-primary hover:bg-se-primary/5",
              geoState === "loading" && "opacity-60",
            )}
          >
            <span className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[20px]">
                my_location
              </span>
              {geoState === "loading" ? "📡 측정 중..." : "📍 내 위치 사용"}
            </span>
            {currentOrigin === CUSTOM_ORIGIN_KEY ? (
              <span className="rounded-full bg-se-secondary px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider text-white">
                사용 중
              </span>
            ) : null}
          </button>

          {geoHint ? (
            <div className="mb-4 rounded-xl border border-se-outline-variant/50 bg-se-surface-container-low p-3">
              <p
                className={cn(
                  "text-[0.7rem] leading-snug",
                  geoState === "ok"
                    ? "text-se-secondary"
                    : geoState === "denied" || geoState === "unsupported"
                      ? "text-red-600"
                      : "text-se-on-surface-variant",
                )}
                role="status"
              >
                {geoHint}
              </p>
              {geoState === "denied" ? (
                <button
                  type="button"
                  onClick={() => selectMyLocation(true)}
                  className="mt-2 inline-flex items-center gap-1 rounded-full border border-se-primary bg-white px-2.5 py-0.5 text-[0.65rem] font-bold text-se-primary hover:bg-se-primary/5"
                >
                  🛰️ 정밀 재시도 (GPS)
                </button>
              ) : null}
            </div>
          ) : null}

          {/* 지역별 프리셋 */}
          <div className="rounded-xl border border-se-outline-variant bg-white">
            {ORIGIN_GROUPS.map((group, idx) => {
              const isOpen = openGroupId === group.id;
              const activeInGroup = group.keys.includes(currentOrigin);
              return (
                <div
                  key={group.id}
                  className={cn(
                    "border-se-outline-variant/60",
                    idx > 0 && "border-t",
                  )}
                >
                  <button
                    type="button"
                    onClick={() => setOpenGroupId(isOpen ? "" : group.id)}
                    className={cn(
                      "flex w-full items-center justify-between px-3 py-2 text-left text-xs font-bold transition-colors",
                      activeInGroup
                        ? "text-se-primary"
                        : "text-se-on-surface-variant hover:bg-se-surface-container-low",
                    )}
                    aria-expanded={isOpen}
                  >
                    <span>
                      <span className="mr-1.5">{group.emoji}</span>
                      {group.label}
                      {activeInGroup ? (
                        <span className="ml-2 inline-block h-1.5 w-1.5 rounded-full bg-se-primary align-middle" />
                      ) : null}
                    </span>
                    <span
                      className={cn(
                        "transition-transform",
                        isOpen ? "rotate-180" : "rotate-0",
                      )}
                    >
                      ▾
                    </span>
                  </button>
                  {isOpen ? (
                    <div className="flex flex-wrap gap-1.5 px-3 pb-3">
                      {group.keys.map((key) => (
                        <button
                          key={key}
                          type="button"
                          onClick={() => selectPreset(key)}
                          className={cn(
                            "rounded-full border px-3 py-1 text-xs font-bold transition-colors",
                            currentOrigin === key
                              ? "border-se-primary bg-se-primary text-white shadow-sm"
                              : "border-se-outline-variant bg-white text-se-on-surface hover:border-se-primary",
                          )}
                          title={`${ORIGIN_LABEL[key]} (${ORIGIN_PRESETS[key][0].toFixed(3)}, ${ORIGIN_PRESETS[key][1].toFixed(3)})`}
                        >
                          {ORIGIN_LABEL[key]}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
