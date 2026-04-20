"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { signInWithKakaoCustomToken } from "@/lib/firebase/auth";

export function KakaoComplete() {
  const router = useRouter();
  const sp = useSearchParams();
  const [status, setStatus] = useState<"busy" | "error">("busy");
  const [message, setMessage] = useState("카카오 계정 연결 중...");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetch("/api/auth/kakao/consume", {
          credentials: "same-origin",
        });
        if (!res.ok) throw new Error("로그인 토큰을 찾을 수 없어요.");
        const { token } = (await res.json()) as { token: string };
        await signInWithKakaoCustomToken(token);
        if (!mounted) return;
        toast.success("카카오 로그인 완료");
        router.push(sanitizeNext(sp.get("next")));
      } catch (err) {
        if (!mounted) return;
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "로그인에 실패했어요.");
      }
    })();
    return () => {
      mounted = false;
    };
  }, [router, sp]);

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gradient-to-br from-[#00193c] via-[#002d62] to-[#1b6d24] p-6">
      <div className="rounded-3xl bg-white/95 px-8 py-10 shadow-[0_24px_48px_-12px_rgba(0,25,60,0.5)] backdrop-blur-xl">
        <div className="flex flex-col items-center gap-3 text-center">
          <span
            className={`material-symbols-outlined text-[32px] ${
              status === "busy" ? "animate-pulse text-se-primary" : "text-se-error"
            }`}
          >
            {status === "busy" ? "hourglass_top" : "error"}
          </span>
          <p className="font-display text-sm font-bold text-se-primary">
            {message}
          </p>
          {status === "error" ? (
            <a
              href="/login"
              className="mt-2 rounded-full bg-se-primary px-4 py-2 text-xs font-bold text-white"
            >
              로그인 화면으로
            </a>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function sanitizeNext(n: string | null): string {
  if (!n) return "/";
  if (!n.startsWith("/") || n.startsWith("//")) return "/";
  return n;
}
