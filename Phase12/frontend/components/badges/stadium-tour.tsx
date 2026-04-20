"use client";

import Image from "next/image";
import { useEffect, useRef } from "react";
import { useBadges } from "@/lib/store/badges";
import { loadUserVisits, saveUserVisits } from "@/lib/firebase/user-visits";
import { useAuthUser } from "@/lib/store/auth";
import { getTeamPalette, getTeamLogoPath } from "@/lib/team-colors";
import type { Stadium } from "@/lib/types";
import { cn } from "@/lib/utils";

interface StadiumTourProps {
  stadiums: Stadium[];
}

function firstTeam(homeTeam: string): string {
  return homeTeam.split(",")[0].replace("(보조)", "").trim();
}

export function StadiumTour({ stadiums }: StadiumTourProps) {
  const { visited, uid: anonUid, syncStatus, toggle, setVisited, setSyncStatus } =
    useBadges();
  const authUser = useAuthUser();
  const hasFirebase = Boolean(process.env.NEXT_PUBLIC_FIREBASE_API_KEY);
  const lastSavedSig = useRef<string>("");

  // 로그인 사용자만 Firestore (user_visits/{uid}). 익명 사용자는 localStorage only.
  // 이유: Firestore Rules 가 익명 (request.auth=null) 차단 + 개인정보 보호.
  const useAuthedCollection = Boolean(authUser?.uid);
  const effectiveUid = authUser?.uid ?? null;

  // 최초 마운트: Firestore → merge with local (인증 사용자만)
  useEffect(() => {
    if (!effectiveUid) {
      // 익명: 로컬만 사용
      if (anonUid) setSyncStatus("local-only");
      return;
    }
    if (!hasFirebase) {
      setSyncStatus("local-only");
      return;
    }
    let cancelled = false;
    (async () => {
      setSyncStatus("syncing");
      const remote = (await loadUserVisits(effectiveUid))?.visited ?? null;
      if (cancelled) return;
      if (remote === null) {
        setSyncStatus("error");
        return;
      }
      const merged = [...new Set([...visited, ...remote])];
      if (merged.length !== visited.length) setVisited(merged);
      setSyncStatus("synced");
      lastSavedSig.current = [...merged].sort().join(",");
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveUid, hasFirebase]);

  // 인증 사용자: visited 변경 시 즉시 backup write (use-firestore-sync 도 debounce 처리하지만
  // 즉각성을 위해 1차 fire-and-forget)
  useEffect(() => {
    if (!effectiveUid || !hasFirebase) return;
    const sig = [...visited].sort().join(",");
    if (sig === lastSavedSig.current) return;
    lastSavedSig.current = sig;
    void saveUserVisits(effectiveUid, visited);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visited.join(",")]);

  const count = visited.length;
  const total = stadiums.length;
  const allDone = count >= total;

  return (
    <div className="space-y-4">
      <header className="flex items-end justify-between">
        <div>
          <h2 className="font-display text-xl font-extrabold text-se-primary">
            🏟️ Stadium Tour
          </h2>
          <p className="mt-1 font-display text-[0.72rem] uppercase tracking-[0.14em] text-se-on-surface-variant">
            KBO 10 Stadiums Challenge
          </p>
        </div>
        <div className="text-right">
          <div className="font-display text-3xl font-extrabold text-se-primary">
            {count}
            <span className="ml-1 text-base font-semibold text-se-outline">
              / {total}
            </span>
          </div>
          <SyncBadge
            status={syncStatus}
            hasFirebase={hasFirebase}
            authed={useAuthedCollection}
          />
        </div>
      </header>

      {allDone ? (
        <div className="rounded-2xl bg-gradient-to-br from-se-secondary to-se-secondary-container px-5 py-4 text-white shadow-[0_8px_18px_rgba(27,109,36,0.3)]">
          <p className="font-display text-lg font-extrabold">
            🏆 All Stadiums Conquered!
          </p>
          <p className="mt-1 text-sm opacity-90">
            모든 KBO 구장을 방문하셨습니다. 진짜 원정러 인증 완료 ⚾
          </p>
        </div>
      ) : null}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
        {stadiums.map((s) => {
          const team = firstTeam(s.home_team);
          const palette = getTeamPalette(team);
          const isVisited = visited.includes(s.short_name);
          return (
            <button
              key={s.short_name}
              onClick={() => toggle(s.short_name)}
              aria-pressed={isVisited}
              className={cn(
                "group relative flex flex-col items-center rounded-2xl border-2 border-transparent bg-se-surface-container-lowest px-3 py-4 text-center transition-[transform,box-shadow,border-color]",
                "hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(0,0,0,0.08)]",
                isVisited
                  ? "border-se-secondary bg-white shadow-[0_4px_14px_rgba(27,109,36,0.15)]"
                  : "opacity-75 grayscale",
              )}
            >
              {isVisited ? (
                <span className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-se-secondary text-white">
                  <span className="material-symbols-outlined text-[16px]">
                    check
                  </span>
                </span>
              ) : null}
              <div
                className="mb-2 flex h-12 w-12 items-center justify-center rounded-full shadow-[0_3px_8px_rgba(0,0,0,0.15)]"
                style={{ background: palette.color }}
              >
                <Image
                  src={getTeamLogoPath(team)}
                  alt=""
                  width={28}
                  height={28}
                  className="object-contain"
                />
              </div>
              <div className="font-display text-sm font-extrabold text-se-primary">
                {s.short_name}
              </div>
              <div className="mt-0.5 truncate text-[0.65rem] text-se-on-surface-variant">
                {s.city}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function SyncBadge({
  status,
  hasFirebase,
  authed,
}: {
  status: string;
  hasFirebase: boolean;
  authed: boolean;
}) {
  if (!hasFirebase) {
    return (
      <span className="mt-1 inline-block rounded-full bg-se-surface-container-low px-2 py-0.5 text-[0.6rem] font-bold text-se-on-surface-variant">
        🏠 로컬 저장
      </span>
    );
  }
  const meta: Record<string, { label: string; tone: string }> = {
    idle: { label: "—", tone: "bg-se-surface-container-low text-se-outline" },
    syncing: { label: "⏳ 동기화 중", tone: "bg-amber-100 text-amber-900" },
    synced: {
      label: authed ? "👤 내 계정 동기화됨" : "☁️ 익명 동기화됨",
      tone: authed
        ? "bg-emerald-100 text-emerald-900"
        : "bg-blue-100 text-blue-900",
    },
    "local-only": {
      label: "🏠 로컬 저장",
      tone: "bg-se-surface-container-low text-se-on-surface-variant",
    },
    error: { label: "⚠️ 동기화 실패", tone: "bg-red-100 text-red-900" },
  };
  const m = meta[status] ?? meta.idle;
  return (
    <span
      className={cn(
        "mt-1 inline-block rounded-full px-2 py-0.5 text-[0.6rem] font-bold",
        m.tone,
      )}
    >
      {m.label}
    </span>
  );
}
