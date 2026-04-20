"use client";

import { useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Game } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  ORIGIN_PRESETS,
  ORIGIN_LABEL,
  ORIGIN_GROUPS,
  CUSTOM_ORIGIN_KEY,
  findNearestPreset,
} from "@/lib/map/origins";

interface MapControlsProps {
  games: Game[];
  selectedGameId?: string;
  origin: string;
}

export function MapControls({
  games,
  selectedGameId,
  origin,
}: MapControlsProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  const [openGroupId, setOpenGroupId] = useState<string>(() => {
    for (const g of ORIGIN_GROUPS) if (g.keys.includes(origin)) return g.id;
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
    <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2">
      <label className="block">
        <span className="font-display text-[0.65rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
          🎯 경기 선택
        </span>
        <select
          value={selectedGameId ?? ""}
          onChange={(e) => pushParams({ game: e.target.value })}
          className="mt-1 w-full rounded-xl border border-se-outline-variant bg-white px-3 py-2 text-sm"
          disabled={games.length === 0}
        >
          {games.length === 0 ? (
            <option>선택 가능한 원정 경기가 없습니다</option>
          ) : (
            games.map((g) => (
              <option key={g.game_id} value={g.game_id}>
                {g.date} @ {g.stadium} vs {g.home_team}
              </option>
            ))
          )}
        </select>
      </label>

      <div>
        <div className="flex items-center justify-between">
          <span className="font-display text-[0.65rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
            🚗 출발지
          </span>
          <button
            type="button"
            onClick={selectMyLocation}
            disabled={geoState === "loading"}
            className={cn(
              "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[0.65rem] font-bold transition-colors",
              origin === CUSTOM_ORIGIN_KEY
                ? "border-se-secondary bg-se-secondary text-white"
                : "border-se-outline-variant bg-white text-se-on-surface hover:border-se-primary",
            )}
            title="브라우저 위치 정보를 사용해 현재 위치를 출발지로 설정합니다."
          >
            {geoState === "loading" ? "📡 측정 중..." : "📍 내 위치"}
          </button>
        </div>

        <div className="mt-1.5 rounded-xl border border-se-outline-variant bg-white">
          {ORIGIN_GROUPS.map((group, idx) => {
            const isOpen = openGroupId === group.id;
            const activeInGroup = group.keys.includes(origin);
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
                          origin === key
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

        {geoHint ? (
          <p
            className={cn(
              "mt-1.5 text-[0.7rem] font-medium",
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
      </div>
    </div>
  );
}
