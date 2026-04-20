"use client";

import { useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { BottomSheet } from "@/components/ui/bottom-sheet";
import { useMobileSheet } from "@/lib/store/mobile-sheet";
import {
  ORIGIN_GROUPS,
  ORIGIN_LABEL,
  CUSTOM_ORIGIN_KEY,
  findNearestPreset,
} from "@/lib/map/origins";
import { cn } from "@/lib/utils";

/**
 * 모바일 전용 — 출발지 선택 BottomSheet (sub-sheet).
 * 데스크톱 MapControls 의 origin accordion + geolocation 재사용.
 */
interface MobileOriginPickerProps {
  currentOrigin: string;
}

export function MobileOriginPicker({ currentOrigin }: MobileOriginPickerProps) {
  const open = useMobileSheet((s) => s.active === "origin");
  const close = useMobileSheet((s) => s.close);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  const [openGroupId, setOpenGroupId] = useState<string>(() => {
    for (const g of ORIGIN_GROUPS)
      if (g.keys.includes(currentOrigin)) return g.id;
    return "capital";
  });
  const [geoState, setGeoState] = useState<
    "idle" | "loading" | "denied" | "ok" | "unsupported"
  >("idle");
  const [geoHint, setGeoHint] = useState<string | null>(null);

  function pushParams(param: Record<string, string | null>) {
    const p = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(param)) {
      if (v === null) p.delete(k);
      else p.set(k, v);
    }
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
      close();
    });
  }

  function selectPreset(key: string) {
    pushParams({ origin: key, lat: null, lng: null });
  }

  function selectMyLocation() {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGeoState("unsupported");
      setGeoHint("이 브라우저는 위치 정보를 지원하지 않습니다.");
      return;
    }
    setGeoState("loading");
    setGeoHint("위치 확인 중...");
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
      },
      (err) => {
        setGeoState("denied");
        setGeoHint(
          err.code === 1
            ? "위치 권한이 차단되어 있습니다. 브라우저 설정에서 허용해 주세요."
            : "위치를 가져오지 못했습니다.",
        );
      },
      { enableHighAccuracy: false, timeout: 6000, maximumAge: 60_000 },
    );
  }

  return (
    <BottomSheet
      open={open}
      onOpenChange={(o) => (o ? null : close())}
      title="🚗 출발지 선택"
      snapPoints={["62%", "92%"]}
    >
      {/* 내 위치 */}
      <button
        type="button"
        onClick={selectMyLocation}
        disabled={geoState === "loading"}
        className={cn(
          "mb-4 flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-3 font-display text-sm font-bold transition-colors",
          currentOrigin === CUSTOM_ORIGIN_KEY
            ? "border-se-secondary bg-se-secondary text-white"
            : "border-se-outline-variant bg-white text-se-on-surface hover:border-se-secondary",
          geoState === "loading" && "opacity-60",
        )}
      >
        <span className="material-symbols-outlined text-[18px]">
          {geoState === "loading" ? "progress_activity" : "my_location"}
        </span>
        {geoState === "loading" ? "위치 측정 중..." : "📍 내 위치 사용"}
      </button>
      {geoHint ? (
        <p
          className={cn(
            "mb-4 text-[0.7rem] font-medium",
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
      ) : null}

      {/* 지역 그룹 accordion */}
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
                  "flex w-full items-center justify-between px-4 py-3 text-left text-sm font-bold transition-colors",
                  activeInGroup
                    ? "text-se-primary"
                    : "text-se-on-surface-variant hover:bg-se-surface-container-low",
                )}
                aria-expanded={isOpen}
              >
                <span>
                  <span className="mr-2 text-base">{group.emoji}</span>
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
                <div className="grid grid-cols-2 gap-2 px-3 pb-3">
                  {group.keys.map((key) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => selectPreset(key)}
                      className={cn(
                        "rounded-xl border px-3 py-2.5 text-sm font-bold transition-colors",
                        currentOrigin === key
                          ? "border-se-primary bg-se-primary text-white shadow-sm"
                          : "border-se-outline-variant bg-white text-se-on-surface hover:border-se-primary",
                      )}
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
    </BottomSheet>
  );
}
