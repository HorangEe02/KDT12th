/**
 * 모바일 BottomSheet 상태 store.
 *
 * 모든 모바일 페이지의 tune/menu 버튼이 같은 sheet 를 열도록 글로벌 상태로 관리.
 * MobileFilterSheet 는 (shell)/layout.tsx 에 한 번 mount, 이 store 로 제어.
 *
 * 향후 sub-sheet (game/origin picker) 도 같은 패턴으로 추가.
 */
"use client";

import { create } from "zustand";

export type SheetKind =
  | "filter"
  | "game"
  | "origin"
  | "trip-confirm"
  | "nav-app"
  | "waypoint"
  | null;

export interface MobileSheetState {
  active: SheetKind;
  open: (kind: Exclude<SheetKind, null>) => void;
  close: () => void;
  isOpen: (kind: Exclude<SheetKind, null>) => boolean;
}

export const useMobileSheet = create<MobileSheetState>((set, get) => ({
  active: null,
  open: (kind) => set({ active: kind }),
  close: () => set({ active: null }),
  isOpen: (kind) => get().active === kind,
}));
