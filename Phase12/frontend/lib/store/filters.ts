/**
 * 사용자 원정 설정 필터 (Zustand).
 * 포팅 원본: src/ui/sidebar.py + st.session_state['filters']
 *
 * 저장 전략: localStorage persist (팀·기간·예산·인원·이동수단).
 * URL 동기화: `team` 만 `?team=XX` 와 연동 (Hero/TeamSelector 서버 컴포넌트가 searchParams 로 읽음).
 */
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { PartyType, TransportType } from "@/lib/types";

export const SEASON_START = "2026-03-28";
export const SEASON_END = "2026-09-30";

/**
 * 매 접속 시 today 기준 한 달 (KBO 시즌 범위 cap).
 * - today 가 시즌 안 (3/28 ~ 9/30) 이면 today 부터 +30일
 * - 시즌 끝 가까이면 SEASON_END 로 cap
 * - 시즌 외 (예: 1월, 12월) 이면 SEASON_START 부터 +30일
 */
export function getDefaultDateRange(): { dateStart: string; dateEnd: string } {
  const seasonStart = new Date(SEASON_START);
  const seasonEnd = new Date(SEASON_END);
  const now = new Date();

  const start =
    now >= seasonStart && now <= seasonEnd ? now : seasonStart;
  const endCandidate = new Date(start.getTime() + 30 * 24 * 60 * 60 * 1000);
  const end = endCandidate > seasonEnd ? seasonEnd : endCandidate;

  return {
    dateStart: start.toISOString().slice(0, 10),
    dateEnd: end.toISOString().slice(0, 10),
  };
}

export interface FiltersState {
  team: string;
  dateStart: string;
  dateEnd: string;
  budget: number; // 만원
  party: PartyType;
  transport: TransportType;
  demoMode: boolean;
  generateTrigger: number; // 증가하면 하위 컴포넌트가 "코스 생성" 이벤트로 인식
}

export interface FiltersActions {
  setTeam: (team: string) => void;
  setDateRange: (start: string, end: string) => void;
  setBudget: (budget: number) => void;
  setParty: (party: PartyType) => void;
  setTransport: (transport: TransportType) => void;
  setDemoMode: (demoMode: boolean) => void;
  triggerGenerate: () => void;
  reset: () => void;
  hydrateFromUrl: (params: URLSearchParams) => void;
}

const _defaultRange = getDefaultDateRange();
const INITIAL: FiltersState = {
  team: "LG",
  dateStart: _defaultRange.dateStart,
  dateEnd: _defaultRange.dateEnd,
  budget: 30,
  party: "solo",
  transport: "train",
  demoMode: false,
  generateTrigger: 0,
};

export const useFilters = create<FiltersState & FiltersActions>()(
  persist(
    (set) => ({
      ...INITIAL,
      setTeam: (team) => set({ team }),
      setDateRange: (dateStart, dateEnd) => set({ dateStart, dateEnd }),
      setBudget: (budget) => set({ budget }),
      setParty: (party) => set({ party }),
      setTransport: (transport) => set({ transport }),
      setDemoMode: (demoMode) => set({ demoMode }),
      triggerGenerate: () =>
        set((s) => ({ generateTrigger: s.generateTrigger + 1 })),
      reset: () => set(INITIAL),
      hydrateFromUrl: (params) => {
        const patch: Partial<FiltersState> = {};
        const urlTeam = params.get("team");
        if (urlTeam) patch.team = urlTeam;
        const s = params.get("start");
        const e = params.get("end");
        if (s && e) {
          patch.dateStart = s;
          patch.dateEnd = e;
        }
        if (Object.keys(patch).length) set(patch);
      },
    }),
    {
      name: "away-game-filters",
      version: 2,  // dateStart/dateEnd 제외로 변경 → version bump 으로 구버전 캐시 무시
      // 옵션 A: 날짜는 매 접속 시 today 기준 한 달로 reset (persist 에서 제외)
      partialize: (state) => ({
        team: state.team,
        budget: state.budget,
        party: state.party,
        transport: state.transport,
        demoMode: state.demoMode,
      }),
    },
  ),
);
