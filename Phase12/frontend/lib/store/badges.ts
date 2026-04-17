/**
 * 방문 구장 상태 (Stadium Tour).
 * localStorage 영속 + Firebase 옵션 싱크.
 */
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface BadgesState {
  visited: string[]; // short_name 배열 (예: ["잠실", "수원"])
  uid: string; // 브라우저별 UUID (익명)
  syncStatus: "idle" | "syncing" | "synced" | "local-only" | "error";
}

export interface BadgesActions {
  toggle: (short: string) => void;
  setVisited: (list: string[]) => void;
  setSyncStatus: (s: BadgesState["syncStatus"]) => void;
  reset: () => void;
}

function generateUid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `local-${Date.now()}-${Math.floor(Math.random() * 1e9)}`;
}

export const useBadges = create<BadgesState & BadgesActions>()(
  persist(
    (set) => ({
      visited: [],
      uid: "",
      syncStatus: "idle",
      toggle: (short) =>
        set((s) => ({
          visited: s.visited.includes(short)
            ? s.visited.filter((v) => v !== short)
            : [...s.visited, short],
        })),
      setVisited: (list) => set({ visited: [...new Set(list)] }),
      setSyncStatus: (syncStatus) => set({ syncStatus }),
      reset: () => set({ visited: [], syncStatus: "idle" }),
    }),
    {
      name: "away-game-badges",
      version: 1,
      onRehydrateStorage: () => (state) => {
        if (state && !state.uid) {
          state.uid = generateUid();
        }
      },
    },
  ),
);
