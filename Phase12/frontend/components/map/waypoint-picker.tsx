"use client";

import { useState } from "react";
import { BottomSheet } from "@/components/ui/bottom-sheet";
import { useMobileSheet } from "@/lib/store/mobile-sheet";
import { useTripStore, type TripWaypoint } from "@/lib/store/trip";
import { cn } from "@/lib/utils";
import type { POI } from "@/lib/types";

/**
 * 경유지 추가 BottomSheet — 주변 POI 중 선택.
 * 추가 후 자동 close.
 */
interface WaypointPickerProps {
  pois: { food: POI[]; stay: POI[]; tour: POI[] };
}

const CAT_LABEL: Record<"food" | "stay" | "tour", { label: string; icon: string }> = {
  food: { label: "음식점", icon: "restaurant" },
  stay: { label: "숙박", icon: "hotel" },
  tour: { label: "관광", icon: "landscape" },
};

export function WaypointPicker({ pois }: WaypointPickerProps) {
  const open = useMobileSheet((s) => s.active === "waypoint");
  const close = useMobileSheet((s) => s.close);
  const [tab, setTab] = useState<"food" | "stay" | "tour">("food");
  const { waypoints, add, remove, hasWaypoint } = useTripStore();
  const list = pois[tab].slice(0, 30);

  function toggleAdd(p: POI) {
    if (hasWaypoint(p.lat, p.lng)) {
      const existing = waypoints.find(
        (w) => Math.abs(w.lat - p.lat) < 1e-5 && Math.abs(w.lng - p.lng) < 1e-5,
      );
      if (existing) remove(existing.id);
    } else {
      add({
        name: p.title,
        lat: p.lat,
        lng: p.lng,
        category: tab,
      });
    }
  }

  return (
    <BottomSheet
      open={open}
      onOpenChange={(o) => (o ? null : close())}
      title="🚏 경유지 추가"
      snapPoints={["62%", "92%"]}
    >
      {/* Current waypoints */}
      {waypoints.length > 0 ? (
        <section className="mb-4 rounded-xl bg-se-secondary-fixed/20 px-3 py-2.5">
          <div className="mb-1.5 font-display text-[0.65rem] font-bold uppercase tracking-wider text-se-on-surface-variant">
            추가된 경유지 ({waypoints.length} / 5)
          </div>
          <div className="flex flex-col gap-1.5">
            {waypoints.map((wp, i) => (
              <div
                key={wp.id}
                className="flex items-center gap-2 text-sm"
              >
                <span className="font-display text-xs font-bold text-se-secondary">
                  {i + 1}.
                </span>
                <span className="flex-1 truncate text-se-on-surface">
                  {wp.name}
                </span>
                <button
                  type="button"
                  onClick={() => remove(wp.id)}
                  aria-label="경유지 삭제"
                  className="text-se-outline hover:text-red-500 active:scale-90"
                >
                  <span className="material-symbols-outlined text-[16px]">
                    close
                  </span>
                </button>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {/* Category tabs */}
      <div className="mb-3 flex gap-2">
        {(["food", "stay", "tour"] as const).map((c) => {
          const meta = CAT_LABEL[c];
          const active = tab === c;
          return (
            <button
              key={c}
              type="button"
              onClick={() => setTab(c)}
              className={cn(
                "flex flex-1 items-center justify-center gap-1.5 rounded-full px-3 py-2 font-display text-xs font-bold transition-colors",
                active
                  ? "bg-se-primary text-white"
                  : "bg-se-surface-container-low text-se-on-surface",
              )}
            >
              <span className="material-symbols-outlined text-[16px]">
                {meta.icon}
              </span>
              {meta.label} ({pois[c].length})
            </button>
          );
        })}
      </div>

      {/* POI list */}
      {list.length === 0 ? (
        <div className="rounded-xl border border-dashed border-se-outline-variant bg-se-surface-container-low p-6 text-center text-sm text-se-on-surface-variant">
          이 카테고리의 주변 장소가 없습니다.
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {list.map((p) => {
            const added = hasWaypoint(p.lat, p.lng);
            return (
              <button
                key={p.content_id}
                type="button"
                onClick={() => toggleAdd(p)}
                disabled={!added && waypoints.length >= 5}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition-colors active:scale-[0.98]",
                  added
                    ? "border-se-secondary bg-se-secondary-fixed/30"
                    : "border-se-outline-variant/40 bg-white hover:border-se-primary/40",
                  !added && waypoints.length >= 5 && "cursor-not-allowed opacity-50",
                )}
              >
                <div
                  className={cn(
                    "flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
                    added ? "bg-se-secondary text-white" : "bg-se-surface-container-low text-se-on-surface-variant",
                  )}
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {added ? "check" : CAT_LABEL[tab].icon}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-display text-sm font-bold text-se-on-surface">
                    {p.title}
                  </p>
                  <p className="truncate font-body text-xs text-se-on-surface-variant">
                    {typeof p.dist_m === "number"
                      ? `경기장에서 ${p.dist_m >= 1000 ? `${(p.dist_m / 1000).toFixed(1)}km` : `${Math.round(p.dist_m)}m`}`
                      : p.addr ?? ""}
                  </p>
                </div>
                {added ? (
                  <span className="font-display text-[10px] font-bold text-se-secondary">
                    추가됨
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      )}

      {waypoints.length >= 5 ? (
        <p className="mt-3 text-center text-[0.7rem] font-bold text-se-error">
          최대 5개까지 추가 가능합니다 (OSRM 성능 제한)
        </p>
      ) : null}
    </BottomSheet>
  );
}
