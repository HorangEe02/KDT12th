"use client";

import { useEffect, useRef } from "react";
import { useAuthProfile } from "@/lib/store/auth";
import { useFilters } from "@/lib/store/filters";
import { TEAM_COLORS } from "@/lib/team-colors";

/**
 * 로그인 후 첫 마운트 시 1회 — profile.favoriteTeam 으로 filters.team hydrate.
 *
 * 우선순위 (높음 → 낮음):
 *   1. URL `?team=XX`        — 명시적 공유 의도
 *   2. localStorage (Zustand persist) — 이전 세션 사용자 선택 (이 훅은 건드리지 않음)
 *   3. profile.favoriteTeam  — 이 훅이 주입
 *   4. "LG" 하드 기본        — filters 기본값
 *
 * 동작 규칙:
 *   - 훅은 세션 당 최대 1회만 적용 (appliedRef 로 가드).
 *   - URL 에 `?team=` 있으면 적용하지 않고 바로 lock.
 *   - 이후 /account 에서 팀 변경 시에는 폼이 직접 filters.setTeam 호출 (이 훅은 재실행 안 함).
 */
export function useFavoriteTeamSync(): void {
  const profile = useAuthProfile();
  const setTeam = useFilters((s) => s.setTeam);
  const appliedRef = useRef(false);

  useEffect(() => {
    if (appliedRef.current) return;
    if (!profile?.favoriteTeam) return;
    if (!(profile.favoriteTeam in TEAM_COLORS)) return;

    const urlTeam =
      typeof window !== "undefined"
        ? new URLSearchParams(window.location.search).get("team")
        : null;
    if (urlTeam && urlTeam in TEAM_COLORS) {
      appliedRef.current = true;
      return;
    }

    setTeam(profile.favoriteTeam);
    appliedRef.current = true;
  }, [profile, setTeam]);
}
