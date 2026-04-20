"use client";

import type { RefObject } from "react";
import type { UIMessage } from "ai";
import { MessageBubble } from "./message-bubble";
import { MobileSettingsButton } from "@/components/nav/mobile-settings-button";
import { cn } from "@/lib/utils";

/**
 * 모바일 전용 AI 챗 뷰.
 * mockup: uiux/mobile_uiux/ai_travel_planner_chat_mobile/code.html
 *
 * 데스크톱 (md+) 에서는 hidden, 모바일 (< md) 에서만 표시.
 * 상태(useChat)는 상위 ChatUI 가 소유하고 props 로 주입.
 *
 * 레이아웃
 *   - header: 페이지 타이틀 + Mock 배지 + MobileSettingsButton (다른 모바일 뷰와 일관)
 *   - messages: 스크롤 영역, ai-glass 스타일 (< md 자동)
 *   - input: sticky glass-pill (BottomNav 공간은 shell 의 pb-28 로 이미 확보)
 */

const SUGGESTIONS = [
  "이번 주말 원정 경기 언제야?",
  "오늘 수원 경기 비 올까?",
  "광주 원정 가족코스 짜줘",
  "LG vs KT 승률은?",
];

export interface AiViewProps {
  messages: UIMessage[];
  busy: boolean;
  error: Error | null | undefined;
  stop: () => void;
  submit: (text: string) => void;
  input: string;
  setInput: (v: string) => void;
  multiAgent: boolean;
  setMultiAgent: (v: boolean) => void;
  demoMode: boolean;
  teamLabel: string;
  teamColor: string;
  dateStart: string;
  dateEnd: string;
  budget: number;
  scrollRef: RefObject<HTMLDivElement | null>;
}

export function AiMobileView(props: AiViewProps) {
  const {
    messages,
    busy,
    error,
    stop,
    submit,
    input,
    setInput,
    multiAgent,
    demoMode,
    teamLabel,
    teamColor,
    dateStart,
    dateEnd,
    scrollRef,
  } = props;

  return (
    <section className="-mx-4 flex h-[calc(100dvh-9rem)] flex-col md:hidden">
      {/* Mobile Header — 다른 MobileView 와 동일 패턴 */}
      <header className="flex items-center justify-between px-4 pt-1 pb-3">
        <div className="min-w-0">
          <h1 className="font-display text-2xl font-black tracking-tight text-se-primary">
            AI 챗봇
          </h1>
          <p className="mt-0.5 flex items-center gap-1.5 text-xs text-se-on-surface-variant">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: teamColor }}
            />
            <span className="truncate">
              {teamLabel} · {dateStart.slice(5)}~{dateEnd.slice(5)}
            </span>
            {demoMode ? (
              <span className="ml-1 shrink-0 rounded-full bg-amber-100 px-1.5 py-0.5 text-[0.6rem] font-bold text-amber-900">
                🎬 Mock
              </span>
            ) : null}
          </p>
        </div>
        <MobileSettingsButton ariaLabel="원정 설정 열기" />
      </header>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 pb-2"
      >
        {messages.length === 0 ? (
          <Greeting onPick={submit} />
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}

        {busy ? (
          <div className="flex items-center gap-2 text-xs text-se-on-surface-variant">
            <span className="h-2 w-2 animate-pulse rounded-full bg-se-primary" />
            {multiAgent ? "Multi-Agent 실행 중…" : "생각 중…"}
            <button
              onClick={stop}
              className="ml-auto h-8 rounded-full border border-se-outline-variant px-3 text-[0.7rem] font-bold text-se-primary"
            >
              중단
            </button>
          </div>
        ) : null}

        {error ? (
          <div className="rounded-xl bg-red-50 px-3 py-2 text-xs text-red-900">
            오류: {error.message}
          </div>
        ) : null}
      </div>

      {/* Glass-pill Input — sticky, BottomNav 위 (shell 의 pb-28 로 공간 확보) */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
        className="sticky bottom-0 px-4 pt-3 pb-2 backdrop-blur supports-[backdrop-filter]:bg-white/75"
      >
        <div className="flex items-center gap-2 rounded-full border border-se-outline-variant/40 bg-white/95 p-1.5 shadow-[0_6px_18px_rgba(0,0,0,0.06)]">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={busy}
            placeholder="컨시어지에게 물어보세요..."
            className="min-w-0 flex-1 border-none bg-transparent px-3 py-2 font-body text-sm text-se-on-surface placeholder:text-se-outline focus:outline-none focus:ring-0"
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            aria-label="전송"
            className={cn(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-se-primary to-se-primary-container text-white shadow-[0_4px_12px_rgba(0,25,60,0.25)] transition-opacity active:scale-90",
              (busy || !input.trim()) && "opacity-40",
            )}
          >
            <span
              className="material-symbols-outlined text-[20px]"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              send
            </span>
          </button>
        </div>
      </form>
    </section>
  );
}

function Greeting({ onPick }: { onPick: (s: string) => void }) {
  return (
    <div className="m-auto flex w-full max-w-sm flex-col items-center gap-3 text-center">
      <div
        className="flex h-12 w-12 items-center justify-center rounded-full bg-se-primary/10"
        aria-hidden
      >
        <span
          className="material-symbols-outlined text-2xl text-se-primary"
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          auto_awesome
        </span>
      </div>
      <p className="font-display text-base font-bold text-se-primary">
        KBO 원정 컨시어지
      </p>
      <p className="px-4 text-xs leading-relaxed text-se-on-surface-variant">
        경기·날씨·맛집·길찾기·팁을 한 번에 물어보세요.
      </p>
      <div className="mt-1 flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="h-10 rounded-full border border-se-outline-variant bg-white px-3 text-xs font-semibold text-se-primary active:scale-95"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
