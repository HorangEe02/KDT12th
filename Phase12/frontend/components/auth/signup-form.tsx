"use client";

import { type FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { signUpWithEmail } from "@/lib/firebase/auth";
import {
  translateAuthError,
  validateEmail,
  validatePassword,
} from "@/lib/firebase/auth-errors";
import { TEAMS, getTeamPalette } from "@/lib/team-colors";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface SignupFormProps {
  next?: string;
}

export function SignupForm({ next }: SignupFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [favoriteTeam, setFavoriteTeam] = useState<string>("");
  const [showPw, setShowPw] = useState(false);
  const [consentTos, setConsentTos] = useState(false);
  const [consentPrivacy, setConsentPrivacy] = useState(false);
  const [consentMarketing, setConsentMarketing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const emailErr = validateEmail(email);
    if (emailErr) return setError(emailErr);
    const pwErr = validatePassword(password);
    if (pwErr) return setError(pwErr);
    if (password !== passwordConfirm)
      return setError("비밀번호가 일치하지 않습니다.");
    if (!displayName.trim()) return setError("닉네임을 입력해 주세요.");
    if (displayName.length > 30)
      return setError("닉네임은 30자 이하로 입력해 주세요.");
    if (!consentTos || !consentPrivacy)
      return setError("이용약관 + 개인정보 처리방침에 동의해 주세요.");

    setSubmitting(true);
    try {
      await signUpWithEmail({
        email,
        password,
        displayName: displayName.trim(),
        favoriteTeam: favoriteTeam || null,
        consent: {
          tos: consentTos,
          privacy: consentPrivacy,
          marketing: consentMarketing,
        },
      });
      toast.success("가입 완료 — 환영합니다!");
      router.push(next ?? "/?welcome=1");
    } catch (err) {
      const msg = translateAuthError(err);
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <Field
        id="email"
        label="이메일"
        type="email"
        icon="mail"
        autoComplete="email"
        value={email}
        onChange={setEmail}
        placeholder="name@example.com"
        disabled={submitting}
      />

      <Field
        id="displayName"
        label="닉네임"
        type="text"
        icon="badge"
        autoComplete="nickname"
        value={displayName}
        onChange={setDisplayName}
        placeholder="홍길동"
        disabled={submitting}
        helper="사이드바·프로필에 표시됩니다 (최대 30자)"
      />

      <Field
        id="password"
        label="비밀번호"
        type={showPw ? "text" : "password"}
        icon="lock"
        autoComplete="new-password"
        value={password}
        onChange={setPassword}
        placeholder="8자 이상, 영문 소문자 + 숫자"
        disabled={submitting}
        rightAction={
          <button
            type="button"
            onClick={() => setShowPw((v) => !v)}
            tabIndex={-1}
            className="text-se-outline hover:text-se-primary"
            aria-label={showPw ? "비밀번호 숨기기" : "비밀번호 표시"}
          >
            <span className="material-symbols-outlined text-[20px]">
              {showPw ? "visibility" : "visibility_off"}
            </span>
          </button>
        }
      />

      <Field
        id="passwordConfirm"
        label="비밀번호 확인"
        type={showPw ? "text" : "password"}
        icon="lock"
        autoComplete="new-password"
        value={passwordConfirm}
        onChange={setPasswordConfirm}
        placeholder="••••••••"
        disabled={submitting}
      />

      <div>
        <label
          htmlFor="favoriteTeam"
          className="block font-display text-xs font-bold uppercase tracking-widest text-se-on-surface-variant mb-2 ml-1"
        >
          응원팀 (선택)
        </label>
        <select
          id="favoriteTeam"
          value={favoriteTeam}
          onChange={(e) => setFavoriteTeam(e.target.value)}
          disabled={submitting}
          className="w-full rounded-xl border-none bg-se-surface-container-low py-3.5 px-4 text-sm text-se-on-surface ring-1 ring-se-outline-variant/30 focus:bg-white focus:outline-none focus:ring-2 focus:ring-se-primary disabled:opacity-50"
        >
          <option value="">선택 안 함</option>
          {TEAMS.map((code) => {
            const p = getTeamPalette(code);
            return (
              <option key={code} value={code}>
                {code} · {p.nameKo}
              </option>
            );
          })}
        </select>
      </div>

      <div className="space-y-2 rounded-xl border border-se-outline-variant bg-white px-3 py-3 text-xs">
        <ConsentRow
          checked={consentTos}
          onChange={setConsentTos}
          required
          label="이용약관 동의"
        />
        <ConsentRow
          checked={consentPrivacy}
          onChange={setConsentPrivacy}
          required
          label="개인정보 처리방침 동의"
        />
        <ConsentRow
          checked={consentMarketing}
          onChange={setConsentMarketing}
          label="이벤트 / 마케팅 수신 동의 (선택)"
        />
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
        {submitting ? "가입 중..." : "가입하기"}
      </button>
    </form>
  );
}

interface FieldProps {
  id: string;
  label: string;
  type: string;
  icon: string;
  autoComplete?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  disabled?: boolean;
  helper?: string;
  rightAction?: React.ReactNode;
}

function Field({
  id,
  label,
  type,
  icon,
  autoComplete,
  value,
  onChange,
  placeholder,
  disabled,
  helper,
  rightAction,
}: FieldProps) {
  return (
    <div>
      <label
        htmlFor={id}
        className="block font-display text-xs font-bold uppercase tracking-widest text-se-on-surface-variant mb-2 ml-1"
      >
        {label}
      </label>
      <div className="relative">
        <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-se-outline text-[20px]">
          {icon}
        </span>
        <input
          id={id}
          type={type}
          autoComplete={autoComplete}
          required
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "w-full rounded-xl border-none bg-se-surface-container-low py-3.5 pl-12 text-sm text-se-on-surface ring-1 ring-se-outline-variant/30 transition-all focus:bg-white focus:outline-none focus:ring-2 focus:ring-se-primary disabled:opacity-50",
            rightAction ? "pr-12" : "pr-4",
          )}
        />
        {rightAction ? (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            {rightAction}
          </div>
        ) : null}
      </div>
      {helper ? (
        <p className="mt-1 ml-1 text-[0.65rem] text-se-on-surface-variant">
          {helper}
        </p>
      ) : null}
    </div>
  );
}

interface ConsentRowProps {
  checked: boolean;
  onChange: (v: boolean) => void;
  required?: boolean;
  label: string;
}
function ConsentRow({ checked, onChange, required, label }: ConsentRowProps) {
  return (
    <label className="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 accent-se-primary"
      />
      <span className="text-se-on-surface">
        {required ? <span className="text-se-error">*</span> : null} {label}
      </span>
    </label>
  );
}
