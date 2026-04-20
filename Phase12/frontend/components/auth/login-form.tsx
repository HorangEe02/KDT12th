"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signInWithEmail } from "@/lib/firebase/auth";
import { translateAuthError, validateEmail } from "@/lib/firebase/auth-errors";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface LoginFormProps {
  next?: string;
}

export function LoginForm({ next }: LoginFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const emailErr = validateEmail(email);
    if (emailErr) {
      setError(emailErr);
      return;
    }
    if (!password) {
      setError("비밀번호를 입력해 주세요.");
      return;
    }
    setSubmitting(true);
    try {
      await signInWithEmail(email, password);
      toast.success("로그인 완료");
      router.push(next ?? "/");
    } catch (err) {
      const msg = translateAuthError(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <label
          htmlFor="email"
          className="block font-display text-xs font-bold uppercase tracking-widest text-se-on-surface-variant mb-2 ml-1"
        >
          이메일
        </label>
        <div className="relative">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-se-outline text-[20px]">
            mail
          </span>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            disabled={submitting}
            className="w-full rounded-xl border-none bg-se-surface-container-low py-3.5 pl-12 pr-4 text-sm text-se-on-surface ring-1 ring-se-outline-variant/30 transition-all focus:bg-white focus:outline-none focus:ring-2 focus:ring-se-primary disabled:opacity-50"
          />
        </div>
      </div>

      <div>
        <div className="flex items-end justify-between mb-2 ml-1">
          <label
            htmlFor="password"
            className="block font-display text-xs font-bold uppercase tracking-widest text-se-on-surface-variant"
          >
            비밀번호
          </label>
          <Link
            href="/reset-password"
            className="font-body text-xs font-semibold text-se-primary hover:text-se-secondary"
          >
            비밀번호 재설정
          </Link>
        </div>
        <div className="relative">
          <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-se-outline text-[20px]">
            lock
          </span>
          <input
            id="password"
            type={showPw ? "text" : "password"}
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            disabled={submitting}
            className="w-full rounded-xl border-none bg-se-surface-container-low py-3.5 pl-12 pr-12 text-sm text-se-on-surface ring-1 ring-se-outline-variant/30 transition-all focus:bg-white focus:outline-none focus:ring-2 focus:ring-se-primary disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => setShowPw((v) => !v)}
            tabIndex={-1}
            aria-label={showPw ? "비밀번호 숨기기" : "비밀번호 표시"}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-se-outline transition-colors hover:text-se-primary"
          >
            <span className="material-symbols-outlined text-[20px]">
              {showPw ? "visibility" : "visibility_off"}
            </span>
          </button>
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
        {submitting ? "로그인 중..." : "로그인"}
      </button>
    </form>
  );
}
