"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { signInWithGoogle } from "@/lib/firebase/auth";
import { translateAuthError } from "@/lib/firebase/auth-errors";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface SocialButtonsProps {
  next?: string;
  layout?: "stack" | "row";
}

export function SocialButtons({ next, layout = "stack" }: SocialButtonsProps) {
  const router = useRouter();
  const [busy, setBusy] = useState<"google" | "kakao" | null>(null);

  async function onGoogle() {
    setBusy("google");
    try {
      await signInWithGoogle();
      toast.success("Google 로그인 완료");
      router.push(next ?? "/");
    } catch (err) {
      toast.error(translateAuthError(err));
    } finally {
      setBusy(null);
    }
  }

  function onKakao() {
    setBusy("kakao");
    const qs = next ? `?next=${encodeURIComponent(next)}` : "";
    window.location.href = `/api/auth/kakao/start${qs}`;
  }

  const containerCls =
    layout === "row" ? "flex gap-3" : "flex flex-col gap-3";

  return (
    <div className={containerCls}>
      <button
        type="button"
        onClick={onKakao}
        disabled={busy !== null}
        className={cn(
          "flex flex-1 items-center justify-center gap-2 rounded-2xl px-4 py-3.5 font-body text-sm font-semibold transition-colors disabled:opacity-50",
          layout === "row"
            ? "bg-[var(--color-se-brand-kakao)]/10 ring-1 ring-[var(--color-se-brand-kakao)]/50 hover:bg-[var(--color-se-brand-kakao)]/20"
            : "bg-[var(--color-se-brand-kakao)] text-black hover:bg-[var(--color-se-brand-kakao-hover)]",
        )}
        aria-label="카카오로 계속하기"
      >
        <span
          className={cn(
            "flex items-center justify-center font-display text-[10px] font-extrabold",
            layout === "row"
              ? "h-5 w-5 rounded-full bg-[var(--color-se-brand-kakao)] text-black"
              : "",
          )}
        >
          {layout === "row" ? "K" : (
            <span
              className="material-symbols-outlined text-[20px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              chat
            </span>
          )}
        </span>
        <span className={layout === "row" ? "text-xs font-bold" : ""}>
          Kakao{layout === "stack" ? "로 계속하기" : ""}
        </span>
      </button>

      <button
        type="button"
        onClick={onGoogle}
        disabled={busy !== null}
        className={cn(
          "flex flex-1 items-center justify-center gap-2 rounded-2xl border border-se-outline-variant bg-white px-4 py-3.5 font-body text-sm font-semibold text-se-on-surface transition-colors hover:bg-se-surface-container-low disabled:opacity-50",
        )}
        aria-label="Google로 계속하기"
      >
        <GoogleLogo className="h-5 w-5" />
        <span className={layout === "row" ? "text-xs font-bold" : ""}>
          {busy === "google" ? "이동 중..." : `Google${layout === "stack" ? "로 계속하기" : ""}`}
        </span>
      </button>
    </div>
  );
}

function GoogleLogo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden>
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.1A6.6 6.6 0 0 1 5.5 12c0-.73.13-1.43.35-2.1V7.07H2.18a11 11 0 0 0 0 9.86l3.66-2.84z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1A11 11 0 0 0 2.18 7.07l3.66 2.83C6.71 7.31 9.14 5.38 12 5.38z"
      />
    </svg>
  );
}
