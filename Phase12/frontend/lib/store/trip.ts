/**
 * Trip plan — 사용자 정의 경유지 (waypoints) 영속.
 * 사용처: /map TripConfirmationSheet · WaypointPicker · 길안내 deeplink.
 */
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface TripWaypoint {
  id: string;
  name: string;
  lat: number;
  lng: number;
  category: "food" | "stay" | "tour" | "custom";
}

interface TripState {
  waypoints: TripWaypoint[];
  add: (wp: Omit<TripWaypoint, "id">) => void;
  remove: (id: string) => void;
  clear: () => void;
  reorder: (oldIdx: number, newIdx: number) => void;
  hasWaypoint: (lat: number, lng: number) => boolean;
}

function uid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `wp-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
}

export const useTripStore = create<TripState & { _hasHydrated: boolean }>()(
  persist(
    (set, get) => ({
      waypoints: [],
      _hasHydrated: false,
      add: (wp) =>
        set((s) => ({
          waypoints:
            s.waypoints.length >= 5
              ? s.waypoints // 최대 5개 (OSRM via parameter 성능)
              : [...s.waypoints, { ...wp, id: uid() }],
        })),
      remove: (id) =>
        set((s) => ({ waypoints: s.waypoints.filter((w) => w.id !== id) })),
      clear: () => set({ waypoints: [] }),
      reorder: (oldIdx, newIdx) =>
        set((s) => {
          const list = [...s.waypoints];
          const [moved] = list.splice(oldIdx, 1);
          list.splice(newIdx, 0, moved);
          return { waypoints: list };
        }),
      hasWaypoint: (lat, lng) =>
        get().waypoints.some(
          (w) => Math.abs(w.lat - lat) < 1e-5 && Math.abs(w.lng - lng) < 1e-5,
        ),
    }),
    {
      name: "away-game-trip",
      version: 1,
      partialize: (s) => ({ waypoints: s.waypoints }),
    },
  ),
);
