"use client";

import { useState } from "react";
import { BottomSheet } from "@/components/ui/bottom-sheet";
import { useMobileSheet } from "@/lib/store/mobile-sheet";
import { useFilters } from "@/lib/store/filters";
import { NavAppPicker } from "./nav-app-picker";
import { cn } from "@/lib/utils";
import type { TravelMode } from "@/lib/nav-deeplink";
import type { Stadium, Game, RouteResult, TransportType } from "@/lib/types";

/**
 * 길 안내 시작 클릭 시 표시되는 확인 sheet.
 * 출발/도착/날짜/이동수단 미리보기 + 변경 트리거 + NavAppPicker.
 */
interface TripConfirmationSheetProps {
  origin: { label: string; coords: [number, number] };
  stadium: Stadium;
  selectedGame: Game;
  route: RouteResult;
  waypoints?: Array<{ lat: number; lng: number; name: string }>;
}

const MODE_LABEL: Record<TransportType, { label: string; icon: string; nav: "transit" | "car" }> = {
  train: { label: "대중교통", icon: "directions_subway", nav: "transit" },
  bus: { label: "고속버스", icon: "directions_bus", nav: "transit" },
  car: { label: "자차", icon: "directions_car", nav: "car" },
};

export function TripConfirmationSheet({
  origin,
  stadium,
  selectedGame,
  route,
  waypoints,
}: TripConfirmationSheetProps) {
  const open = useMobileSheet((s) => s.active === "trip-confirm");
  const close = useMobileSheet((s) => s.close);
  const openSheet = useMobileSheet((s) => s.open);
  const transport = useFilters((s) => s.transport);
  const [navMode, setNavMode] = useState<TravelMode>(
    MODE_LABEL[transport]?.nav ?? "transit",
  );

  return (
    <BottomSheet
      open={open}
      onOpenChange={(o) => (o ? null : close())}
      title="🧭 길 안내 시작"
      snapPoints={["75%", "92%"]}
    >
      {/* Trip summary */}
      <div className="mb-5 space-y-3">
        <Row
          icon="my_location"
          iconBg="bg-se-surface-container-low"
          iconColor="text-se-on-surface-variant"
          label="출발"
          value={origin.label}
          onChangeClick={() => openSheet("origin")}
        />
        <Row
          icon="sports_baseball"
          iconBg="bg-gradient-to-br from-se-primary to-se-primary-container"
          iconColor="text-white"
          label="도착"
          value={stadium.stadium_name}
          subValue={`vs ${selectedGame.home_team}`}
          onChangeClick={() => openSheet("game")}
        />
        <Row
          icon="event"
          iconBg="bg-se-secondary-fixed/30"
          iconColor="text-se-secondary"
          label="날짜"
          value={`${selectedGame.date}${selectedGame.day_of_week ? ` (${selectedGame.day_of_week})` : ""}`}
          subValue={
            selectedGame.start_time
              ? `${selectedGame.start_time} 경기 시작`
              : undefined
          }
          onChangeClick={() => openSheet("game")}
        />

        {/* 경유지 (있을 때만) */}
        {waypoints && waypoints.length > 0 ? (
          <div className="rounded-xl border border-dashed border-se-outline-variant/60 px-3 py-2">
            <div className="mb-1 font-display text-[0.65rem] font-bold uppercase tracking-wider text-se-on-surface-variant">
              경유지 {waypoints.length}곳
            </div>
            {waypoints.map((wp, i) => (
              <div
                key={i}
                className="flex items-center gap-2 py-0.5 text-sm text-se-on-surface"
              >
                <span className="text-se-outline">{i + 1}.</span>
                <span className="truncate">{wp.name}</span>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      {/* Transit mode toggle */}
      <div className="mb-5">
        <div className="mb-2 font-display text-[0.65rem] font-bold uppercase tracking-wider text-se-on-surface-variant">
          이동수단
        </div>
        <div className="grid grid-cols-3 gap-2">
          {(["transit", "car", "walk"] as const).map((m) => {
            const active = navMode === m;
            const icon = m === "transit" ? "directions_bus" : m === "car" ? "directions_car" : "directions_walk";
            const label = m === "transit" ? "대중교통" : m === "car" ? "자차" : "도보";
            return (
              <button
                key={m}
                type="button"
                onClick={() => setNavMode(m)}
                className={cn(
                  "flex flex-col items-center gap-0.5 rounded-xl border px-2 py-2 transition-colors",
                  active
                    ? "border-se-primary bg-se-primary text-white"
                    : "border-se-outline-variant bg-white text-se-on-surface",
                )}
              >
                <span className="material-symbols-outlined text-[20px]">{icon}</span>
                <span className="font-display text-[10px] font-bold">{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Route preview chip */}
      <div className="mb-5 rounded-xl bg-se-surface-container-low px-4 py-3">
        <div className="flex items-center justify-between">
          <span className="font-display text-xs font-bold text-se-on-surface-variant">
            예상 경로 ({route.source.toUpperCase()})
          </span>
          <span className="font-display text-sm font-extrabold text-se-primary">
            {route.duration_sec ? `${Math.round(route.duration_sec / 60)}분` : "—"} ·{" "}
            {route.distance_m ? `${(route.distance_m / 1000).toFixed(1)}km` : "—"}
          </span>
        </div>
      </div>

      {/* Nav app picker */}
      <NavAppPicker
        origin={origin.coords}
        destination={[stadium.lat, stadium.lng]}
        destinationName={stadium.stadium_name}
        mode={navMode}
        waypoints={waypoints}
        onLaunched={() => {
          // 1초 후 sheet close
          setTimeout(() => close(), 800);
        }}
      />
    </BottomSheet>
  );
}

function Row({
  icon,
  iconBg,
  iconColor,
  label,
  value,
  subValue,
  onChangeClick,
}: {
  icon: string;
  iconBg: string;
  iconColor: string;
  label: string;
  value: string;
  subValue?: string;
  onChangeClick: () => void;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-se-outline-variant/40 px-3 py-3">
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
          iconBg,
        )}
      >
        <span
          className={cn("material-symbols-outlined text-[20px]", iconColor)}
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          {icon}
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="font-display text-[10px] font-bold uppercase tracking-wider text-se-on-surface-variant">
          {label}
        </div>
        <div className="truncate font-display text-sm font-bold text-se-on-surface">
          {value}
        </div>
        {subValue ? (
          <div className="truncate font-body text-xs text-se-on-surface-variant">
            {subValue}
          </div>
        ) : null}
      </div>
      <button
        type="button"
        onClick={onChangeClick}
        className="rounded-full border border-se-outline-variant bg-white px-3 py-1.5 font-display text-xs font-bold text-se-primary hover:border-se-primary active:scale-95"
      >
        변경
      </button>
    </div>
  );
}
