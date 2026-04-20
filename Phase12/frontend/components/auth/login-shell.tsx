"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { LoginForm } from "./login-form";
import { SignupForm } from "./signup-form";
import { SocialButtons } from "./social-buttons";

const KAKAO_ERROR_MESSAGES: Record<string, string> = {
  missing_code: "카카오에서 인가 코드를 받지 못했어요.",
  state_mismatch: "보안 검증 실패 — 다시 시도해 주세요.",
  access_denied: "카카오 로그인 동의가 취소됐어요.",
  firebase_admin_unavailable: "서버 설정 오류 — 잠시 후 다시 시도해 주세요.",
};

function KakaoErrorToast() {
  const sp = useSearchParams();
  const err = sp.get("kakao_error");
  useEffect(() => {
    if (!err) return;
    const msg = KAKAO_ERROR_MESSAGES[err] ?? `카카오 로그인 실패: ${err}`;
    toast.error(msg);
  }, [err]);
  return null;
}

interface LoginShellProps {
  mode: "login" | "signup";
  next?: string;
}

const HEADERS = {
  login: {
    title: "다시 만나서 반가워요.",
    subtitle: "로그인하고 다음 원정을 큐레이팅하세요.",
    mobileTitle: "경기를 골라봐요.",
    footer: { text: "처음 오셨나요?", link: "/signup", linkText: "회원가입" },
  },
  signup: {
    title: "원정 응원, 시작해 볼까요.",
    subtitle: "30초면 시작할 수 있어요. 나만의 응원 일정을 만들어 보세요.",
    mobileTitle: "팬으로 함께 해요.",
    footer: { text: "이미 계정이 있나요?", link: "/login", linkText: "로그인" },
  },
} as const;

export function LoginShell({ mode, next }: LoginShellProps) {
  const config = HEADERS[mode];
  const nextQuery = next ? `?next=${encodeURIComponent(next)}` : "";

  return (
    <div className="relative min-h-dvh w-full overflow-hidden bg-se-surface">
      <KakaoErrorToast />
      {/* ─── 공통 배경 (Stadium gradient) ─── */}
      <div
        className="absolute inset-0 z-0"
        aria-hidden
        style={{
          backgroundImage:
            "linear-gradient(135deg, #00193c 0%, #002d62 50%, #1b6d24 100%)",
        }}
      />
      <div
        className="absolute inset-0 z-0 opacity-30 mix-blend-overlay"
        aria-hidden
        style={{
          backgroundImage:
            "radial-gradient(ellipse at top, rgba(255,255,255,0.4), transparent 60%), radial-gradient(ellipse at bottom, rgba(0,25,60,0.5), transparent 70%)",
        }}
      />

      {/* ─── 데스크톱: 좌측 Hero + 우측 Card ─── */}
      <main className="relative z-10 mx-auto hidden min-h-dvh w-full max-w-6xl items-center gap-12 px-12 py-12 md:flex">
        <Hero
          title={config.title}
          subtitle={config.subtitle}
          mode={mode}
        />
        <section className="w-full max-w-md rounded-[2rem] border border-white/30 bg-white/95 p-10 shadow-[0_24px_48px_-12px_rgba(0,25,60,0.5)] backdrop-blur-xl">
          <div className="mb-8 text-center">
            <h2 className="font-display text-2xl font-bold text-se-primary">
              {mode === "login" ? "로그인" : "회원가입"}
            </h2>
            <p className="mt-2 text-sm text-se-on-surface-variant">
              {mode === "login"
                ? "이메일/비밀번호 또는 Google 계정으로 시작하세요."
                : "30초면 가입할 수 있어요."}
            </p>
          </div>
          {mode === "login" ? (
            <LoginForm next={next} />
          ) : (
            <SignupForm next={next} />
          )}
          <Divider />
          <SocialButtons next={next} layout="stack" />
          <FooterRow
            text={config.footer.text}
            href={`${config.footer.link}${nextQuery}`}
            linkText={config.footer.linkText}
          />
        </section>
      </main>

      {/* ─── 모바일: 풀스크린 + 슬라이드업 카드 ─── */}
      <main className="relative z-10 mx-auto flex min-h-dvh w-full max-w-md flex-col justify-end md:hidden">
        <section className="se-slide-up rounded-t-[2.5rem] bg-white/95 px-7 pb-10 pt-8 shadow-[0_-12px_40px_rgba(0,25,60,0.3)] backdrop-blur-xl">
          <header className="mb-6 flex flex-col gap-1.5">
            <span className="font-display text-[10px] font-extrabold uppercase tracking-[0.2em] text-se-secondary">
              원정 응원 플래너
            </span>
            <h1 className="font-display text-3xl font-extrabold tracking-tight text-se-primary">
              {config.mobileTitle}
            </h1>
            <p className="mt-1 text-xs text-se-on-surface-variant">
              {config.subtitle}
            </p>
          </header>
          {mode === "login" ? (
            <LoginForm next={next} />
          ) : (
            <SignupForm next={next} />
          )}
          <div className="my-5">
            <Divider />
            <SocialButtons next={next} layout="row" />
          </div>
          <FooterRow
            text={config.footer.text}
            href={`${config.footer.link}${nextQuery}`}
            linkText={config.footer.linkText}
          />
        </section>
      </main>
    </div>
  );
}

function Hero({
  title,
  subtitle,
  mode,
}: {
  title: string;
  subtitle: string;
  mode: "login" | "signup";
}) {
  return (
    <div className="flex flex-1 flex-col justify-center gap-5 text-white">
      <div className="font-display text-xs font-extrabold uppercase tracking-[0.3em] text-se-primary-fixed-dim">
        ⚾ The Stadium Editorial · KBO Companion
      </div>
      {/* globals.css 의 h1 default color (se-primary) 를 명시적으로 override */}
      <h1
        className="font-display text-3xl font-extrabold leading-[1.15] tracking-tight !text-white drop-shadow-[0_4px_18px_rgba(0,0,0,0.55)] md:text-4xl lg:text-5xl"
        style={{ color: "#ffffff" }}
      >
        {title}
      </h1>
      <p className="max-w-md font-body text-base font-medium leading-relaxed text-white/90 drop-shadow-[0_2px_10px_rgba(0,0,0,0.4)] md:text-lg">
        {subtitle}
      </p>
      <div className="mt-2 grid max-w-md grid-cols-3 gap-2 text-center">
        <Stat icon="sports_baseball" label="10 구단 전부" />
        <Stat icon="route" label="동선 + 길찾기" />
        <Stat icon="smart_toy" label="AI 코스 추천" />
      </div>
      {mode === "login" ? (
        <div className="mt-2 inline-flex items-center gap-2 self-start rounded-full bg-white/15 px-3 py-1.5 text-xs font-medium text-white backdrop-blur">
          <span className="material-symbols-outlined text-[16px]">savings</span>
          무료로 시작 · 카드 정보 불필요
        </div>
      ) : null}
    </div>
  );
}

function Stat({ icon, label }: { icon: string; label: string }) {
  return (
    <div className="rounded-xl border border-white/20 bg-white/5 px-2 py-3 backdrop-blur">
      <span className="material-symbols-outlined block text-[22px] text-se-primary-fixed">
        {icon}
      </span>
      <div className="mt-1 text-[0.7rem] font-bold uppercase tracking-wider text-white/85">
        {label}
      </div>
    </div>
  );
}

function Divider() {
  return (
    <div className="my-6 flex items-center gap-4">
      <div className="h-px flex-1 bg-se-outline-variant/40" />
      <span className="font-display text-[10px] font-bold uppercase tracking-widest text-se-outline">
        또는
      </span>
      <div className="h-px flex-1 bg-se-outline-variant/40" />
    </div>
  );
}

function FooterRow({
  text,
  href,
  linkText,
}: {
  text: string;
  href: string;
  linkText: string;
}) {
  return (
    <p className="mt-6 text-center text-sm text-se-on-surface-variant">
      {text}{" "}
      <Link
        href={href}
        className="font-display font-bold text-se-primary underline decoration-2 underline-offset-4 hover:text-se-secondary"
      >
        {linkText}
      </Link>
    </p>
  );
}
