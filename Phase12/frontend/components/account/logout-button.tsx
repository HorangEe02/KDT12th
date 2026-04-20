"use client";

import { useState, useTransition } from "react";
import { toast } from "sonner";
import { signOut } from "@/lib/firebase/auth";
import { cn } from "@/lib/utils";

/**
 * 로그아웃 버튼 (danger 스타일 · 확인 다이얼로그 포함).
 *
 * 흐름:
 *   1. 탭 → confirm 다이얼로그
 *   2. 확인 → signOut() (세션 쿠키 삭제 + Firebase Auth signOut)
 *   3. /login 으로 전환 (middleware 가 미인증 시 /login 으로 가드하지만 명시적 이동)
 *
 * 모바일에서 쉽게 눌리지 않도록 confirm 추가.
 */
export function LogoutButton() {
  const [pending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState(false);

  async function performLogout() {
    startTransition(async () => {
      try {
        await signOut();
        toast.success("로그아웃 되었습니다.");
        // 즉시 /login 으로 이동 (middleware 로 바로 처리되지만 명시적 네비게이션)
        window.location.assign("/login");
      } catch (err) {
        const msg = err instanceof Error ? err.message : "로그아웃 실패";
        toast.error(msg);
        setConfirming(false);
      }
    });
  }

  if (confirming) {
    return (
      <div
        role="alertdialog"
        aria-labelledby="logout-confirm-title"
        className="rounded-2xl border border-red-200 bg-red-50 p-5"
      >
        <p
          id="logout-confirm-title"
          className="font-display text-base font-bold text-red-900"
        >
          정말 로그아웃 하시겠습니까?
        </p>
        <p className="mt-1.5 text-xs text-red-800/80">
          다시 이용하려면 로그인해야 합니다. 공유 링크(`/share/...`)는 계속
          접근 가능합니다.
        </p>
        <div className="mt-4 flex gap-3">
          <button
            type="button"
            onClick={() => setConfirming(false)}
            disabled={pending}
            className="h-11 flex-1 rounded-full border border-red-300 bg-white px-5 font-display text-sm font-bold text-red-900 active:scale-95 disabled:opacity-50"
          >
            취소
          </button>
          <button
            type="button"
            onClick={performLogout}
            disabled={pending}
            className={cn(
              "h-11 flex-1 rounded-full bg-red-600 px-5 font-display text-sm font-extrabold text-white shadow-[0_4px_12px_rgba(220,38,38,0.25)] active:scale-95",
              pending && "opacity-60",
            )}
          >
            {pending ? "로그아웃 중…" : "로그아웃"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <button
      type="button"
      onClick={() => setConfirming(true)}
      className="flex h-11 w-full items-center justify-center gap-2 rounded-full border border-red-200 bg-white px-5 font-display text-sm font-bold text-red-700 transition-colors hover:border-red-400 hover:bg-red-50 active:scale-95"
    >
      <span className="material-symbols-outlined text-[18px]">logout</span>
      로그아웃
    </button>
  );
}
