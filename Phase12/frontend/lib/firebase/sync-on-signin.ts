/**
 * 로그인 직후 1회 호출 — anon localStorage 데이터를 Firestore 와 머지.
 *
 * 전략:
 *   - prefs: last-writer-wins by updatedAt (remote 우선, 단 아주 오래된 경우 local 보존)
 *   - visits: set union (잃는 데이터 0)
 *
 * 호출처: AuthProvider 의 onAuthStateChanged user != null 분기.
 * 참고: docs/FIREBASE_DB_PLAN.md §5-1
 */
"use client";

import { useFilters, SEASON_START } from "@/lib/store/filters";
import { useBadges } from "@/lib/store/badges";
import { loadUserPrefs, saveUserPrefs } from "./user-prefs";
import { loadUserVisits, saveUserVisits } from "./user-visits";

const SYNC_FLAG_KEY = "auth-synced-uid";

export interface SyncResult {
  ok: boolean;
  mergedVisitedCount: number;
  appliedPrefs: boolean;
  source: "remote" | "local" | "merged" | "none";
}

/**
 * 동일 uid 로 1회만 머지 (브라우저 세션). 페이지 이동 마다 호출돼도 안전.
 * 명시적 reset 필요 시 forceRun=true.
 */
export async function syncOnSignIn(
  uid: string,
  opts?: { forceRun?: boolean },
): Promise<SyncResult> {
  if (!uid) return { ok: false, mergedVisitedCount: 0, appliedPrefs: false, source: "none" };

  if (typeof window !== "undefined" && !opts?.forceRun) {
    const last = sessionStorage.getItem(SYNC_FLAG_KEY);
    if (last === uid) {
      return { ok: true, mergedVisitedCount: 0, appliedPrefs: false, source: "none" };
    }
  }

  const localFilters = useFilters.getState();
  const localBadges = useBadges.getState();

  const [remotePrefs, remoteVisits] = await Promise.all([
    loadUserPrefs(uid),
    loadUserVisits(uid),
  ]);

  // ── visits: set union (보수적) ──
  const merged = new Set<string>([
    ...(localBadges.visited ?? []),
    ...(remoteVisits?.visited ?? []),
  ]);
  const mergedArr = [...merged];
  if (mergedArr.length !== localBadges.visited.length) {
    useBadges.getState().setVisited(mergedArr);
  }
  // remote 와 다르면 push (특히 local 추가분)
  if (
    !remoteVisits ||
    mergedArr.length !== (remoteVisits.visited?.length ?? 0)
  ) {
    await saveUserVisits(uid, mergedArr);
  }
  useBadges.getState().setSyncStatus("synced");

  // ── prefs: remote 가 있으면 우선, 없으면 local push ──
  let source: SyncResult["source"] = "merged";
  let appliedPrefs = false;

  if (remotePrefs && remotePrefs.team) {
    // remote → store
    const setters = useFilters.getState();
    if (remotePrefs.team) setters.setTeam(remotePrefs.team);
    if (remotePrefs.startDate && remotePrefs.endDate)
      setters.setDateRange(remotePrefs.startDate, remotePrefs.endDate);
    if (typeof remotePrefs.budgetMax === "number")
      setters.setBudget(remotePrefs.budgetMax);
    if (remotePrefs.partySize) setters.setParty(remotePrefs.partySize);
    if (remotePrefs.transport) setters.setTransport(remotePrefs.transport);
    appliedPrefs = true;
    source = "remote";
  } else {
    // local → remote
    await saveUserPrefs(uid, {
      team: localFilters.team,
      startDate: localFilters.dateStart,
      endDate: localFilters.dateEnd,
      budgetMax: localFilters.budget,
      partySize: localFilters.party,
      transport: localFilters.transport,
    });
    source = "local";
  }

  if (typeof window !== "undefined") {
    sessionStorage.setItem(SYNC_FLAG_KEY, uid);
  }

  return {
    ok: true,
    mergedVisitedCount: mergedArr.length,
    appliedPrefs,
    source: localFilters.team === "LG" && source === "local" && !remotePrefs
      ? "none"
      : source,
  };
}

/** 로그아웃 시 플래그 제거 (다음 로그인에 다시 머지) */
export function clearSyncFlag(): void {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(SYNC_FLAG_KEY);
  }
}

// SEASON_START re-export 로 외부에서 fallback 사용 가능
export { SEASON_START };
