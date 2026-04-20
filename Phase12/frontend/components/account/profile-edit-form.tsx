"use client";

import { useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { useAuthProfile, useAuthUser } from "@/lib/store/auth";
import { useFilters } from "@/lib/store/filters";
import { getTeamPalette } from "@/lib/team-colors";
import { TeamGridSelector } from "./team-grid-selector";
import { cn } from "@/lib/utils";

/**
 * 프로필 편집 폼 — 닉네임 + 응originalValue팀.
 *
 * - 초기값: useAuthProfile() (Firestore 실시간 구독)
 * - 저장 경로: PATCH /api/user/profile
 * - 성공 시: Firestore 리스너가 자동 반영 + filters.team 도 즉시 갱신 (선택한 팀이 현재 응원팀이 됨)
 * - 본인만 수정 가능 (관리자가 타인 편집 시 별도 admin 폼 필요)
 */
export function ProfileEditForm() {
  const user = useAuthUser();
  const profile = useAuthProfile();
  const setFiltersTeam = useFilters((s) => s.setTeam);
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  const [displayName, setDisplayName] = useState("");
  const [favoriteTeam, setFavoriteTeam] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // profile 로드/업데이트 시 폼 초기값 동기화
  useEffect(() => {
    if (profile) {
      setDisplayName(profile.displayName ?? "");
      setFavoriteTeam(profile.favoriteTeam ?? null);
    }
  }, [profile?.uid, profile?.displayName, profile?.favoriteTeam]);

  if (!user) {
    return (
      <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-low px-5 py-8 text-center text-sm text-se-on-surface-variant">
        로그인이 필요합니다.
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-low px-5 py-8 text-center text-sm text-se-on-surface-variant">
        프로필 로딩 중…
      </div>
    );
  }

  const originalName = profile.displayName ?? "";
  const originalTeam = profile.favoriteTeam ?? null;
  const dirty =
    displayName.trim() !== originalName || favoriteTeam !== originalTeam;

  // 로컬 검증 (서버 Zod 와 동일 규칙)
  function validate(): string | null {
    const trimmed = displayName.trim();
    if (trimmed.length < 2) return "닉네임은 2자 이상이어야 합니다.";
    if (trimmed.length > 20) return "닉네임은 20자 이하여야 합니다.";
    if (!/^[\p{L}\p{N}\s._-]+$/u.test(trimmed))
      return "한글·영문·숫자·공백·`._-` 만 허용됩니다.";
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const err = validate();
    if (err) {
      setError(err);
      return;
    }
    setError(null);

    const body: Record<string, string | null> = {};
    const trimmed = displayName.trim();
    if (trimmed !== originalName) body.displayName = trimmed;
    if (favoriteTeam !== originalTeam) body.favoriteTeam = favoriteTeam;

    startTransition(async () => {
      try {
        const res = await fetch("/api/user/profile", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => null);
          const msg =
            (data?.issues?.[0]?.message as string | undefined) ??
            data?.error ??
            `저장 실패 (${res.status})`;
          toast.error(msg);
          setError(msg);
          return;
        }
        // 응원팀이 바뀌었으면 filters.team 에도 즉시 반영
        if (body.favoriteTeam && typeof body.favoriteTeam === "string") {
          setFiltersTeam(body.favoriteTeam);
        }
        toast.success("프로필을 저장했습니다.");
        // Firestore 리스너가 profile 자동 갱신 → useEffect 로 폼 리하이드레이션
      } catch (err) {
        const msg = err instanceof Error ? err.message : "네트워크 오류";
        toast.error(msg);
        setError(msg);
      }
    });
  }

  const teamLabel = favoriteTeam
    ? getTeamPalette(favoriteTeam).nameKo
    : "미설정";

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* 사용자 메타 */}
      <header className="rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest p-5">
        <div className="flex items-center gap-3">
          <div
            aria-hidden
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-se-primary to-se-primary-container text-xl font-extrabold text-white"
          >
            {(profile.displayName ?? profile.email ?? "?").slice(0, 1).toUpperCase()}
          </div>
          <div className="min-w-0">
            <div className="font-display text-base font-extrabold text-se-primary">
              {profile.displayName || "이름 없음"}
            </div>
            <div className="truncate text-xs text-se-on-surface-variant">
              {profile.email} · {profile.role === "admin" ? "관리자" : "일반회원"}
            </div>
          </div>
        </div>
      </header>

      {/* 닉네임 */}
      <section>
        <label
          htmlFor="displayName"
          className="mb-2 block font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant"
        >
          닉네임
        </label>
        <input
          id="displayName"
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          disabled={pending}
          maxLength={20}
          className="h-11 w-full rounded-xl border border-se-outline-variant bg-white px-4 text-sm text-se-on-surface focus:border-se-primary focus:outline-none focus:ring-2 focus:ring-se-primary/20"
          placeholder="2~20자 · 한글/영문/숫자"
          aria-invalid={error ? true : undefined}
          aria-describedby="displayName-help"
        />
        <p
          id="displayName-help"
          className="mt-1.5 text-xs text-se-on-surface-variant"
        >
          {displayName.trim().length}/20 · 한글·영문·숫자·공백·`._-`
        </p>
      </section>

      {/* 응원팀 */}
      <section>
        <label className="mb-2 block font-display text-sm font-extrabold uppercase tracking-[0.12em] text-se-on-surface-variant">
          응원팀 · <span className="normal-case text-se-primary">{teamLabel}</span>
        </label>
        <TeamGridSelector
          value={favoriteTeam}
          onChange={setFavoriteTeam}
          disabled={pending}
        />
        <p className="mt-2 text-xs text-se-on-surface-variant">
          첫 접속 시 자동으로 이 팀 기준의 원정 일정·맛집이 조회됩니다.
        </p>
      </section>

      {/* 에러 */}
      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-900">
          {error}
        </div>
      ) : null}

      {/* 액션 */}
      <div className="sticky bottom-0 -mx-4 flex gap-3 border-t border-se-outline-variant bg-white/95 px-4 py-3 backdrop-blur md:static md:mx-0 md:border-0 md:bg-transparent md:p-0">
        <button
          type="button"
          onClick={() => router.back()}
          disabled={pending}
          className="h-11 flex-1 rounded-full border border-se-outline-variant bg-white px-5 font-display text-sm font-bold text-se-primary transition-colors hover:border-se-primary disabled:opacity-50 md:flex-none"
        >
          취소
        </button>
        <button
          type="submit"
          disabled={!dirty || pending}
          className={cn(
            "h-11 flex-1 rounded-full bg-se-primary px-5 font-display text-sm font-extrabold text-white shadow-[0_6px_18px_rgba(0,25,60,0.2)] transition-opacity md:flex-none",
            (!dirty || pending) && "opacity-40",
          )}
        >
          {pending ? "저장 중…" : dirty ? "저장" : "저장됨"}
        </button>
      </div>
    </form>
  );
}
