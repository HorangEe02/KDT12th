"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  useAuthUser,
  useAuthProfile,
  useIsAdmin,
  useIsAuthLoading,
} from "@/lib/store/auth";
import { signOut } from "@/lib/firebase/auth";
import { cn } from "@/lib/utils";

/**
 * 사이드바 / 상단 nav 우상단에 들어가는 사용자 배지.
 *
 * Hydration-safe 패턴: SSR 시 항상 skeleton, mount 후 실제 UI 렌더.
 * Navigation 은 window.location.href 사용 — Next.js Link/Router 의
 * client hydration 실패 가능성과 무관하게 항상 동작.
 */
export function UserBadge() {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);

  const user = useAuthUser();
  const profile = useAuthProfile();
  const isAdmin = useIsAdmin();
  const loading = useIsAuthLoading();
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // SSR 또는 hydration 직전 — 빈 skeleton (mismatch 0)
  if (!hydrated || loading) {
    return (
      <div
        className="flex items-center gap-2 rounded-xl border border-se-outline-variant bg-white px-3 py-2"
        suppressHydrationWarning
      >
        <div className="h-7 w-7 animate-pulse rounded-full bg-se-surface-variant" />
        <div className="h-3 w-20 animate-pulse rounded bg-se-surface-variant" />
      </div>
    );
  }

  if (!user) {
    const nextRaw = pathname && pathname !== "/" ? pathname : "/";
    const next = encodeURIComponent(nextRaw);
    const loginHref = `/login?next=${next}`;
    const signupHref = `/signup?next=${next}`;
    return (
      <div className="flex flex-col gap-1.5">
        <a
          href={loginHref}
          data-target="login"
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-se-primary px-3 py-2 font-display text-xs font-bold text-white no-underline transition-transform hover:-translate-y-0.5 active:scale-95"
        >
          <span className="material-symbols-outlined text-[16px]">login</span>
          로그인
        </a>
        <a
          href={signupHref}
          data-target="signup"
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-se-outline-variant bg-white px-3 py-2 text-xs font-bold text-se-on-surface no-underline hover:border-se-primary active:scale-95"
        >
          <span className="material-symbols-outlined text-[16px]">person_add</span>
          회원가입
        </a>
      </div>
    );
  }

  const displayName =
    profile?.displayName ?? user.displayName ?? user.email?.split("@")[0] ?? "사용자";
  const initial = displayName.slice(0, 1).toUpperCase();

  async function onSignOut() {
    setOpen(false);
    try {
      await signOut();
    } catch {
      /* ignore */
    }
    window.location.href = "/";
  }

  const goAccount = () => {
    setOpen(false);
    window.location.assign("/account");
  };
  const goAdmin = () => {
    setOpen(false);
    window.location.assign("/admin");
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex w-full items-center gap-2 rounded-xl border bg-white px-3 py-2 text-left transition-colors",
          isAdmin
            ? "border-se-secondary"
            : "border-se-outline-variant hover:border-se-primary",
        )}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        {user.photoURL ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.photoURL}
            alt={displayName}
            className="h-7 w-7 rounded-full object-cover"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-se-primary text-white font-display text-xs font-bold">
            {initial}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="truncate text-xs font-bold text-se-on-surface">
            {displayName}
          </div>
          <div className="truncate text-[0.65rem] text-se-on-surface-variant">
            {isAdmin ? "관리자" : (user.email ?? "회원")}
          </div>
        </div>
        <span className="material-symbols-outlined text-[16px] text-se-on-surface-variant">
          {open ? "expand_less" : "expand_more"}
        </span>
      </button>

      {open ? (
        <div
          role="menu"
          className="absolute left-0 right-0 top-full z-30 mt-1 overflow-hidden rounded-xl border border-se-outline-variant bg-white shadow-lg"
        >
          <button
            type="button"
            onClick={goAccount}
            className="block w-full px-3 py-2 text-left text-xs font-semibold text-se-on-surface hover:bg-se-surface-container-low"
          >
            <span className="material-symbols-outlined mr-1.5 align-middle text-[14px]">
              person
            </span>
            내 계정
          </button>
          {isAdmin ? (
            <button
              type="button"
              onClick={goAdmin}
              className="block w-full px-3 py-2 text-left text-xs font-semibold text-se-secondary hover:bg-se-surface-container-low"
            >
              <span className="material-symbols-outlined mr-1.5 align-middle text-[14px]">
                admin_panel_settings
              </span>
              관리자 콘솔
            </button>
          ) : null}
          <button
            type="button"
            onClick={onSignOut}
            className="block w-full border-t border-se-outline-variant/60 px-3 py-2 text-left text-xs font-semibold text-se-error hover:bg-se-surface-container-low"
          >
            <span className="material-symbols-outlined mr-1.5 align-middle text-[14px]">
              logout
            </span>
            로그아웃
          </button>
        </div>
      ) : null}
    </div>
  );
}
