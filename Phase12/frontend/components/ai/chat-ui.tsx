"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useFilters } from "@/lib/store/filters";
import { getTeamPalette } from "@/lib/team-colors";
import { MessageBubble } from "./message-bubble";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "이번 주말 원정 경기 언제야?",
  "오늘 수원 경기 비 올까?",
  "광주 원정 가족끼리 맛집 추천해줘",
  "서울역에서 부산 사직구장까지 얼마나 걸려?",
  "LG vs KT 이번 경기 승률은?",
];

export function ChatUI() {
  const filters = useFilters();
  const [multiAgent, setMultiAgent] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { messages, sendMessage, status, stop, error } = useChat({
    transport: new DefaultChatTransport({
      api: "/api/chat",
      prepareSendMessagesRequest: ({ messages, id }) => ({
        body: {
          id,
          messages,
          multiAgent,
          filters: {
            team: filters.team,
            dateRange: [filters.dateStart, filters.dateEnd],
            budget: filters.budget,
            party: filters.party,
            transport: filters.transport,
            demoMode: filters.demoMode,
          },
        },
      }),
    }),
  });

  const [input, setInput] = useState("");
  const busy = status === "submitted" || status === "streaming";

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length, status]);

  function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    sendMessage({ text: trimmed });
    setInput("");
  }

  const palette = getTeamPalette(filters.team);

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col overflow-hidden rounded-3xl border border-se-outline-variant bg-se-surface-container-lowest">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-se-outline-variant bg-se-surface-container-low px-5 py-3">
        <div className="flex items-center gap-2">
          <span
            className="h-3 w-3 rounded-full"
            style={{ background: palette.color }}
          />
          <span className="font-display text-sm font-bold text-se-primary">
            {palette.nameKo} · {filters.dateStart.slice(5)}~{filters.dateEnd.slice(5)} · 예산 {filters.budget}만
          </span>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex cursor-pointer items-center gap-1.5 text-xs font-semibold text-se-on-surface">
            <input
              type="checkbox"
              checked={multiAgent}
              onChange={(e) => setMultiAgent(e.target.checked)}
              className="accent-se-primary"
            />
            Multi-Agent
          </label>
          {filters.demoMode ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[0.65rem] font-bold text-amber-900">
              🎬 Mock
            </span>
          ) : null}
        </div>
      </header>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex flex-1 flex-col gap-4 overflow-y-auto px-5 py-4"
      >
        {messages.length === 0 ? (
          <div className="m-auto flex flex-col items-center gap-3 text-center">
            <span className="material-symbols-outlined text-5xl text-se-outline">
              smart_toy
            </span>
            <p className="max-w-md text-sm text-se-on-surface-variant">
              Gemini 기반 원정 AI 어시스턴트. 경기·날씨·맛집·길찾기·팁을 한 번에 물어보세요.
            </p>
            <div className="mt-2 flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="rounded-full border border-se-outline-variant bg-white px-3 py-1 text-xs font-semibold text-se-primary hover:border-se-primary"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}
        {busy ? (
          <div className="flex items-center gap-2 text-xs text-se-on-surface-variant">
            <span className="h-2 w-2 animate-pulse rounded-full bg-se-primary" />
            {multiAgent ? "Multi-Agent 실행 중…" : "생각 중…"}
            <button
              onClick={stop}
              className="ml-auto rounded-full border border-se-outline-variant px-2 py-0.5 text-[0.65rem] font-bold text-se-primary"
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

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
        className="border-t border-se-outline-variant bg-se-surface-container-low p-3"
      >
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit(input);
              }
            }}
            rows={2}
            disabled={busy}
            placeholder="예: 광주 원정 가족코스 추천해줘"
            className="max-h-32 min-h-[42px] flex-1 resize-none rounded-2xl border border-se-outline-variant bg-white px-4 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className={cn(
              "flex h-10 items-center justify-center gap-1 rounded-full bg-se-primary px-4 font-display text-sm font-extrabold text-white shadow-[0_4px_12px_rgba(0,25,60,0.2)] transition-opacity",
              (busy || !input.trim()) && "opacity-40",
            )}
          >
            <span className="material-symbols-outlined text-[18px]">send</span>
            전송
          </button>
        </div>
        <p className="mt-1.5 text-[0.65rem] text-se-on-surface-variant">
          ⏎ 전송 · Shift+⏎ 줄바꿈 · 도구 호출 최대 5단계
        </p>
      </form>
    </div>
  );
}
