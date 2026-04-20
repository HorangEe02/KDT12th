"use client";

import { type FormEvent, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { sendPasswordReset } from "@/lib/firebase/auth";
import { translateAuthError, validateEmail } from "@/lib/firebase/auth-errors";
import { cn } from "@/lib/utils";

export default function ResetPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const emailErr = validateEmail(email);
    if (emailErr) {
      setError(emailErr);
      return;
    }
    setSubmitting(true);
    try {
      await sendPasswordReset(email);
      setDone(true);
      toast.success("재설정 링크를 보냈어요. 메일을 확인해 주세요.");
    } catch (err) {
      const msg = translateAuthError(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-se-surface p-6">
      <div
        className="absolute inset-0 z-0"
        aria-hidden
        style={{
          backgroundImage:
            "linear-gradient(135deg, #00193c 0%, #002d62 50%, #1b6d24 100%)",
        }}
      />
      <section className="relative z-10 w-full max-w-md rounded-[2rem] border border-white/30 bg-white/95 p-8 shadow-[0_24px_48px_-12px_rgba(0,25,60,0.5)] backdrop-blur-xl">
        <div className="mb-6 text-center">
          <h1 className="font-display text-2xl font-bold text-se-primary">
            비밀번호 재설정
          </h1>
          <p className="mt-2 text-sm text-se-on-surface-variant">
            가입한 이메일로 재설정 링크를 보내드립니다.
          </p>
        </div>

        {done ? (
          <div className="space-y-4 text-center">
            <div className="rounded-2xl border border-se-secondary/30 bg-green-50 px-4 py-6 text-sm text-se-secondary">
              <span className="material-symbols-outlined mb-2 block text-[36px]">
                mark_email_read
              </span>
              메일함에서 재설정 링크를 확인해 주세요.
              <br />
              <span className="text-xs">
                받지 못했다면 스팸함을 확인하거나 다시 요청해 보세요.
              </span>
            </div>
            <Link
              href="/login"
              className="inline-block font-display text-sm font-bold text-se-primary underline decoration-2 underline-offset-4"
            >
              로그인으로 돌아가기
            </Link>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="reset-email"
                className="block font-display text-xs font-bold uppercase tracking-widest text-se-on-surface-variant mb-2 ml-1"
              >
                이메일
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-se-outline text-[20px]">
                  mail
                </span>
                <input
                  id="reset-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  disabled={submitting}
                  className="w-full rounded-xl border-none bg-se-surface-container-low py-3.5 pl-12 pr-4 text-sm text-se-on-surface ring-1 ring-se-outline-variant/30 focus:bg-white focus:outline-none focus:ring-2 focus:ring-se-primary disabled:opacity-50"
                />
              </div>
            </div>

            {error ? (
              <div
                role="alert"
                className="rounded-xl border border-se-error/30 bg-red-50 px-3 py-2 text-xs font-semibold text-se-error"
              >
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={submitting}
              className={cn(
                "mt-2 w-full rounded-xl bg-gradient-to-br from-se-primary to-se-primary-container py-4 font-display text-sm font-extrabold uppercase tracking-[0.1em] text-white shadow-[0_8px_24px_rgba(0,25,60,0.25)] transition-all hover:shadow-[0_12px_32px_rgba(0,25,60,0.35)] active:scale-[0.98] disabled:opacity-60",
              )}
            >
              {submitting ? "전송 중..." : "재설정 링크 보내기"}
            </button>

            <p className="text-center text-sm text-se-on-surface-variant">
              <Link
                href="/login"
                className="font-display font-bold text-se-primary hover:text-se-secondary"
              >
                ← 로그인으로 돌아가기
              </Link>
            </p>
          </form>
        )}
      </section>
    </main>
  );
}
