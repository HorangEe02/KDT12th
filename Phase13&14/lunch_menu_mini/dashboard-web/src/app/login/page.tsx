"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LogIn, Loader2, UserPlus, User as UserIcon } from "lucide-react";
import {
  login,
  loginGuest,
  pullPreferencesFromBackend,
  register,
} from "@/lib/auth";
import { BRAND } from "@/lib/brand";

const AVATARS = ["🧑‍💻", "👩‍💼", "👨‍🔬", "👩‍🎨", "🧑‍🏫", "🧑‍🍳", "👨‍🎤", "👩‍⚕️"];

type Mode = "signin" | "register" | "guest";

// Only allow same-origin paths to prevent open-redirect.
function safeNext(raw: string | null): string {
  if (!raw) return "/";
  if (!raw.startsWith("/") || raw.startsWith("//")) return "/";
  return raw;
}

// `useSearchParams()` requires a Suspense boundary during static export
// (`NEXT_OUTPUT=export` build path). The form below holds the URL-param logic
// and is rendered inside <Suspense> by the default export at the bottom.
function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Pre-select tab from `?mode=guest|register|signin`. Default = signin.
  const initialMode: Mode =
    searchParams.get("mode") === "guest"
      ? "guest"
      : searchParams.get("mode") === "register"
      ? "register"
      : "signin";
  const nextPath = safeNext(searchParams.get("next"));

  const [mode, setMode] = useState<Mode>(initialMode);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [id, setId] = useState("");
  const [team, setTeam] = useState("team1");
  const [avatar, setAvatar] = useState(AVATARS[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-prefill guest defaults so 1-tap "게스트 시작" works on mobile.
  useEffect(() => {
    if (mode === "guest" && !id && !name) {
      const suffix = Math.random().toString(36).slice(2, 7);
      setId(`guest-${suffix}`);
      setName(`Guest ${suffix.slice(0, 4).toUpperCase()}`);
    }
  }, [mode, id, name]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === "signin") {
        if (!email.trim() || !password) throw new Error("이메일과 비밀번호를 입력하세요.");
        const user = await login({ email: email.trim(), password });
        await pullPreferencesFromBackend(user);
        router.replace(nextPath);
      } else if (mode === "register") {
        if (!email.trim() || !password || !name.trim())
          throw new Error("이메일·비밀번호·이름을 모두 입력하세요.");
        if (password.length < 8) throw new Error("비밀번호는 8자 이상이어야 합니다.");
        const user = await register({
          email: email.trim(),
          password,
          name: name.trim(),
          team_id: team.trim() || "team1",
          avatar_emoji: avatar,
        });
        await pullPreferencesFromBackend(user);
        // Onboarding always wins for new accounts; ?next is honored after onboarding.
        router.replace("/onboarding");
      } else {
        // guest
        if (!id.trim() || !name.trim())
          throw new Error("ID와 이름을 입력하세요.");
        const user = await loginGuest(id.trim(), name.trim(), team.trim() || "team1", avatar);
        await pullPreferencesFromBackend(user);
        router.replace(nextPath);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const tabClass = (m: Mode) =>
    `flex-1 py-2 text-xs font-bold uppercase tracking-wider rounded-sm transition-colors ${
      mode === m
        ? "bg-primary text-background"
        : "bg-surface-2 text-text-secondary hover:text-text-primary"
    }`;

  const inputClass =
    "w-full bg-surface-2 border border-outline/20 px-3 py-2.5 text-sm text-text-primary rounded-sm outline-none focus:border-primary/40";
  const labelClass =
    "block text-[10px] font-bold uppercase tracking-wider text-text-secondary mb-1.5";

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-surface-1 border border-outline/15 rounded-sm p-8">
        <div className="flex items-center gap-3 mb-6">
          <img
            src={BRAND.logoSrc}
            alt={BRAND.logoAlt}
            className="w-12 h-12 rounded-md object-contain select-none"
            draggable={false}
          />
          <div>
            <h1 className="text-2xl font-heading font-bold text-text-primary tracking-tight">
              {mode === "signin" && "Sign in"}
              {mode === "register" && "Create account"}
              {mode === "guest" && "Continue as guest"}
            </h1>
            <p className="text-[11px] text-text-tertiary" style={{ fontFamily: "var(--font-ko)" }}>
              {mode === "signin" && "이메일·비밀번호로 로그인"}
              {mode === "register" && "새 계정 생성 (이메일 인증 없음)"}
              {mode === "guest" && "비밀번호 없이 ID 만으로 시작"}
            </p>
          </div>
        </div>

        <div className="flex gap-1.5 mb-5">
          <button type="button" className={tabClass("signin")} onClick={() => setMode("signin")}>
            <LogIn size={12} className="inline mr-1" />로그인
          </button>
          <button type="button" className={tabClass("register")} onClick={() => setMode("register")}>
            <UserPlus size={12} className="inline mr-1" />회원가입
          </button>
          <button type="button" className={tabClass("guest")} onClick={() => setMode("guest")}>
            <UserIcon size={12} className="inline mr-1" />게스트
          </button>
        </div>

        <form onSubmit={submit} className="space-y-4">
          {(mode === "signin" || mode === "register") && (
            <>
              <div>
                <label className={labelClass}>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  autoFocus
                  className={`${inputClass} font-mono`}
                />
              </div>
              <div>
                <label className={labelClass}>Password (8자 이상)</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={8}
                  className={`${inputClass} font-mono`}
                />
              </div>
            </>
          )}

          {mode === "guest" && (
            <div>
              <label className={labelClass}>User ID</label>
              <input
                type="text"
                value={id}
                onChange={(e) => setId(e.target.value)}
                placeholder="user1"
                required
                autoFocus
                className={`${inputClass} font-mono`}
              />
            </div>
          )}

          {(mode === "register" || mode === "guest") && (
            <>
              <div>
                <label className={labelClass}>Display name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="김민수"
                  required
                  className={inputClass}
                  style={{ fontFamily: "var(--font-ko)" }}
                />
              </div>
              <div>
                <label className={labelClass}>Team</label>
                <input
                  type="text"
                  value={team}
                  onChange={(e) => setTeam(e.target.value)}
                  placeholder="team1"
                  className={`${inputClass} font-mono`}
                />
              </div>
              <div>
                <label className={labelClass}>Avatar</label>
                <div className="flex gap-1.5 flex-wrap">
                  {AVATARS.map((a) => (
                    <button
                      key={a}
                      type="button"
                      onClick={() => setAvatar(a)}
                      className={`w-10 h-10 rounded-full text-xl border-2 transition-all ${
                        avatar === a
                          ? "border-primary bg-primary/10 scale-110"
                          : "border-outline/20 hover:border-outline/40"
                      }`}
                    >
                      {a}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {error && <div className="text-xs text-error font-mono">{error}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3 bg-primary text-background text-sm font-bold uppercase tracking-wider rounded-sm hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                처리 중...
              </>
            ) : mode === "signin" ? (
              <>
                <LogIn size={16} />로그인
              </>
            ) : mode === "register" ? (
              <>
                <UserPlus size={16} />계정 생성
              </>
            ) : (
              <>
                <UserIcon size={16} />게스트로 시작
              </>
            )}
          </button>
        </form>

        <p
          className="text-[10px] text-text-tertiary text-center mt-4"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          {mode === "guest"
            ? "게스트 모드는 백엔드 인증 미적용 — 일부 기능 제한"
            : "JWT 토큰은 브라우저 localStorage 에 24시간 보관"}
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <Loader2 size={20} className="animate-spin text-text-tertiary" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
