/**
 * 사용자 store 변경 → 디바운스 → Firestore 쓰기 자동 동기화 훅.
 * AuthProvider 안에서 호출 (uid 가 있을 때만 활성).
 *
 * - filters: 1.5초 debounce (입력 잦음)
 * - visits: 0.4초 debounce (토글성)
 */
"use client";

import { useEffect, useRef } from "react";
import { useFilters } from "@/lib/store/filters";
import { useBadges } from "@/lib/store/badges";
import { saveUserPrefs } from "./user-prefs";
import { saveUserVisits, subscribeUserVisits } from "./user-visits";

interface Options {
  uid: string | null;
}

const FILTER_DEBOUNCE_MS = 1500;
const VISITS_DEBOUNCE_MS = 400;

export function useFirestoreSync({ uid }: Options): void {
  const filterTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const visitsTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastFilterSigRef = useRef<string>("");
  const lastVisitsSigRef = useRef<string>("");

  // ── filters store 구독 (debounced write) ──
  useEffect(() => {
    if (!uid) return;
    const unsub = useFilters.subscribe((s) => {
      const sig = `${s.team}|${s.dateStart}|${s.dateEnd}|${s.budget}|${s.party}|${s.transport}`;
      if (sig === lastFilterSigRef.current) return;
      lastFilterSigRef.current = sig;
      if (filterTimerRef.current) clearTimeout(filterTimerRef.current);
      filterTimerRef.current = setTimeout(() => {
        void saveUserPrefs(uid, {
          team: s.team,
          startDate: s.dateStart,
          endDate: s.dateEnd,
          budgetMax: s.budget,
          partySize: s.party,
          transport: s.transport,
        });
      }, FILTER_DEBOUNCE_MS);
    });
    return () => {
      unsub();
      if (filterTimerRef.current) clearTimeout(filterTimerRef.current);
    };
  }, [uid]);

  // ── badges store 구독 (debounced write) ──
  useEffect(() => {
    if (!uid) return;
    const unsub = useBadges.subscribe((s) => {
      const sig = [...s.visited].sort().join(",");
      if (sig === lastVisitsSigRef.current) return;
      lastVisitsSigRef.current = sig;
      if (visitsTimerRef.current) clearTimeout(visitsTimerRef.current);
      visitsTimerRef.current = setTimeout(() => {
        void saveUserVisits(uid, s.visited);
      }, VISITS_DEBOUNCE_MS);
    });
    return () => {
      unsub();
      if (visitsTimerRef.current) clearTimeout(visitsTimerRef.current);
    };
  }, [uid]);

  // ── visits 실시간 구독 (다른 디바이스 변경 반영 — 단, 안전 모드) ──
  // 이전 버전은 초기 snapshot([] 비어있음)이 로컬 토글을 덮어쓰는 race condition 발생.
  // 수정: remote 가 local 의 strict superset (추가만) 일 때만 반영.
  //   - 초기 로드 시 remote=[] · local=["잠실"] → superset 아님 → skip (로컬 유지)
  //   - 다른 기기에서 추가 시 remote=["잠실","수원"] · local=["잠실"] → superset → 반영
  //   - 삭제 동기화는 희생 (새로고침 시 stadium-tour.tsx 의 초기 merge 가 정리)
  useEffect(() => {
    if (!uid) return;
    const unsub = subscribeUserVisits(uid, (data) => {
      if (!data) return;
      const local = useBadges.getState().visited;
      const remote = data.visited ?? [];
      const remoteSig = [...remote].sort().join(",");
      const localSig = [...local].sort().join(",");
      if (remoteSig === localSig) return;
      // remote 가 local 의 모든 항목을 포함하는가?
      const isSuperset = local.every((v) => remote.includes(v));
      if (isSuperset && remote.length > local.length) {
        useBadges.getState().setVisited(remote);
      }
      // else: 로컬 우선 — 덮어쓰지 않고 debounced save 가 remote 를 맞춤
    });
    return unsub;
  }, [uid]);
}
