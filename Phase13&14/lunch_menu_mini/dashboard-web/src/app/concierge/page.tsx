"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RotateCcw, Zap, MessageSquare } from "lucide-react";
import { apiStreamSSENLP, apiFetchNLP, DEFAULT_USER_ID } from "@/lib/api";
import { isWarmingUp } from "@/lib/errors";
import { useNLPHealth } from "@/lib/queries";
import type { ChatRecommendation, ToolChatOut, MealType } from "@/lib/types";
import MessageBubble, {
  type Message,
} from "@/components/concierge/MessageBubble";
import InputBar from "@/components/concierge/InputBar";
import HallucinationBanner from "@/components/concierge/HallucinationBanner";
import ErrorBanner from "@/components/common/ErrorBanner";
import MealTimeSelector, {
  loadStoredMealType,
} from "@/components/concierge/MealTimeSelector";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

const MEAL_GREETINGS: Record<MealType, string> = {
  breakfast: "좋은 아침이에요! ☀️ 가벼운 아침 메뉴, 오늘 영양 균형, 카페·베이커리 추천 등 무엇이든 물어보세요.",
  lunch: "안녕하세요! 오늘 뭐 드실지, 이번 주 영양 균형, 또는 특정 식당에 대한 질문 등 무엇이든 물어보세요. 🍱",
  dinner: "수고 많으셨어요! 🌙 저녁 메뉴, 회식 장소, 가족 식사 추천 등 무엇이든 물어보세요.",
  any: "안녕하세요! 어느 식사 시간이든, 영양·메뉴·식당 무엇이든 편하게 물어보세요. 🍽️",
  snack: "간식 추천이 필요하신가요? 🍪 가볍고 적당한 메뉴를 찾아드릴게요.",
  unknown: "안녕하세요! 어떤 식사를 도와드릴까요?",
};

function initialGreeting(mealType: MealType = "any"): Message {
  return {
    id: "greeting",
    role: "assistant",
    text: MEAL_GREETINGS[mealType],
  };
}

type ChatMode = "stream" | "tools";

export default function ConciergePage() {
  const [userId, setUserId] = useState(DEFAULT_USER_ID);
  const [mode, setMode] = useState<ChatMode>("stream");
  const [mealType, setMealType] = useState<MealType>("any");
  const [messages, setMessages] = useState<Message[]>(() => [initialGreeting()]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [showHallucinationWarning, setShowHallucinationWarning] = useState(false);
  const [contextSummary, setContextSummary] = useState<{
    meal_history: number;
    nutrition_info: number;
    restaurants: number;
  } | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const { error: healthError } = useNLPHealth();
  const isWarming = isWarmingUp(healthError);

  // Sync user id from SettingsPanel
  useEffect(() => {
    const saved = localStorage.getItem("p11_user_id");
    const n = saved ? Number(saved) : NaN;
    if (Number.isFinite(n) && n > 0) setUserId(n);
  }, []);

  // 시작 시 저장된 meal_type 복원 (또는 시각 기반 추정)
  useEffect(() => {
    setMealType(loadStoredMealType());
  }, []);

  // mealType 변경 시 — 아직 대화 시작 전이면 (그리팅만 있는 상태) 그리팅 갱신
  // 이미 대화가 진행 중이면 건드리지 않음
  useEffect(() => {
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].id === "greeting") {
        return [initialGreeting(mealType)];
      }
      return prev;
    });
  }, [mealType]);

  // Auto-scroll to bottom on new content
  useEffect(() => {
    listRef.current?.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, streaming]);

  const updateAssistant = useCallback(
    (id: string, patch: Partial<Message>) => {
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? { ...m, ...patch } : m))
      );
    },
    []
  );

  const send = useCallback(async () => {
    const query = input.trim();
    if (!query || streaming) return;

    setInput("");
    setShowHallucinationWarning(false);

    const userMsg: Message = { id: uid(), role: "user", text: query };
    const assistantId = uid();
    const assistantMsg: Message = {
      id: assistantId,
      role: "assistant",
      text: "",
      streaming: true,
    };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStreaming(true);

    if (mode === "tools") {
      // ── Phase 7: Tool Calling mode (non-streaming) ──
      try {
        const out = await apiFetchNLP<ToolChatOut>("/nlp/chatbot/chat/tools", {
          method: "POST",
          body: JSON.stringify({
            user_id: String(userId),
            query,
            temperature: 0.2,
            max_iterations: 3,
            meal_type: mealType,
          }),
        });
        updateAssistant(assistantId, {
          text: out.response,
          latencyMs: out.latency_ms,
          streaming: false,
          toolCalls: out.tool_calls,
          toolResults: out.tool_results,
          iterations: out.iterations,
          fallbackUsed: out.fallback_used,
        });
      } catch (e) {
        updateAssistant(assistantId, {
          text: "",
          streaming: false,
          error: e instanceof Error ? e.message : String(e),
        });
      } finally {
        setStreaming(false);
      }
      return;
    }

    // ── Default: SSE streaming RAG mode ──
    let accum = "";
    const controller = new AbortController();
    abortRef.current = controller;
    await apiStreamSSENLP(
      "/nlp/chatbot/chat/stream",
      { user_id: userId, query, meal_type: mealType },
      {
        onMeta: (meta) => {
          const cs = meta.context_summary as typeof contextSummary;
          if (cs) setContextSummary(cs);
        },
        onToken: (token) => {
          accum += token;
          updateAssistant(assistantId, { text: accum, streaming: true });
        },
        onFinal: (meta) => {
          const recs = (meta.recommendations as ChatRecommendation[]) || [];
          const validation = meta.validation as Record<string, unknown> | undefined;
          const latency = (meta.latency_ms as number) || 0;
          const displayText =
            (meta.display_text as string | undefined) || accum;

          updateAssistant(assistantId, {
            text: displayText,
            recommendations: recs,
            latencyMs: latency,
            streaming: false,
          });

          if (
            validation &&
            (validation.mentioned_count as number) === 0 &&
            recs.length > 0
          ) {
            setShowHallucinationWarning(true);
          }
        },
        onError: (err) => {
          updateAssistant(assistantId, {
            text: accum,
            streaming: false,
            error: err,
          });
        },
        onDone: () => {
          setStreaming(false);
          abortRef.current = null;
        },
      },
      controller.signal,
    );
  }, [input, streaming, userId, updateAssistant, mode, mealType]);

  const stopStream = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStreaming(false);
  }, []);

  const resetConversation = useCallback(async () => {
    try {
      await apiFetchNLP("/nlp/chatbot/reset", {
        method: "POST",
        body: JSON.stringify({ user_id: userId }),
      });
    } catch {
      /* non-fatal */
    }
    setMessages([initialGreeting(mealType)]);
    setContextSummary(null);
    setShowHallucinationWarning(false);
  }, [userId, mealType]);

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      {/* Mobile header — App Store Today 스타일 */}
      <header className="md:hidden mb-4 flex-shrink-0">
        <p className="appstore-eyebrow">AI CONCIERGE</p>
        <h1 className="appstore-title mt-1">AI 상담</h1>
        <p className="text-[12px] text-text-tertiary mt-1.5"
           style={{ fontFamily: "var(--font-ko)" }}>
          ChromaDB RAG + Ollama · 토큰 스트리밍
        </p>
      </header>

      {/* Header (desktop + mobile controls row) */}
      <div className="flex items-start justify-between mb-4 flex-shrink-0 flex-wrap gap-2">
        <div className="hidden md:block">
          <h1 className="text-2xl font-heading font-bold text-text-primary uppercase tracking-tight">
            AI Concierge
          </h1>
          <p className="text-xs text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            RAG Nutrition Advisor &amp; Menu Recommender
          </p>
          <p
            className="text-[11px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            ChromaDB RAG + Ollama · 토큰 스트리밍
          </p>
        </div>
        <div className="flex items-center gap-3">
          {contextSummary && (
            <div className="text-right">
              <p className="text-[10px] text-text-tertiary uppercase tracking-[0.08em]">
                RAG Context
              </p>
              <p className="text-xs font-mono text-text-secondary">
                식사 {contextSummary.meal_history} · 영양{" "}
                {contextSummary.nutrition_info} · 식당{" "}
                {contextSummary.restaurants}
              </p>
            </div>
          )}
          <div className="text-right">
            <p className="text-[10px] text-text-tertiary uppercase tracking-[0.08em]">
              User
            </p>
            <p className="text-lg font-heading font-bold text-text-primary tracking-tight font-mono">
              #{userId}
            </p>
          </div>
          {/* Mode toggle (Phase 7) */}
          <div className="flex items-center border border-outline/25 rounded-sm overflow-hidden">
            <button
              onClick={() => setMode("stream")}
              disabled={streaming}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-[10px] font-bold uppercase transition-colors ${
                mode === "stream"
                  ? "bg-primary/10 text-primary"
                  : "text-text-tertiary hover:text-text-secondary"
              }`}
              title="ChromaDB RAG + SSE token streaming"
            >
              <MessageSquare size={11} />
              RAG
            </button>
            <button
              onClick={() => setMode("tools")}
              disabled={streaming}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-[10px] font-bold uppercase transition-colors border-l border-outline/25 ${
                mode === "tools"
                  ? "bg-tertiary/10 text-tertiary"
                  : "text-text-tertiary hover:text-text-secondary"
              }`}
              title="8 Tool Functions via lunch-optimizer API"
            >
              <Zap size={11} />
              Tools
            </button>
          </div>
          <button
            onClick={resetConversation}
            disabled={streaming}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold uppercase border border-outline/25 rounded-sm hover:border-primary/40 hover:text-primary transition-colors disabled:opacity-40"
          >
            <RotateCcw size={12} />
            Reset
          </button>
        </div>
      </div>

      {/* 식사 시간 칩 — 헤비 옵션 (다중 식사 시간) */}
      <div className="mb-3">
        <MealTimeSelector value={mealType} onChange={setMealType} />
      </div>

      {isWarming && (
        <ErrorBanner
          variant="warming"
          className="mb-3"
          retryAfter={(healthError as { retryAfter?: number })?.retryAfter}
        />
      )}
      {showHallucinationWarning && (
        <HallucinationBanner
          onDismiss={() => setShowHallucinationWarning(false)}
        />
      )}

      {/* Messages */}
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto bg-surface-1 border border-outline/15 rounded-sm p-5 mb-3 space-y-5"
      >
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {messages.length === 1 && (
          <div className="text-center text-[11px] text-text-tertiary mt-8">
            <p style={{ fontFamily: "var(--font-ko)" }}>
              예시 질문:
            </p>
            <ul className="space-y-1 mt-2 text-text-secondary">
              <li>&quot;비 오는 아침 따뜻한 한 그릇&quot;</li>
              <li>&quot;단백질 부족 — 가벼운 점심 추천해줘&quot;</li>
              <li>&quot;회식 가능한 한식 저녁&quot;</li>
            </ul>
          </div>
        )}
      </div>

      {/* Input — sticky to bottom with iOS safe-area padding */}
      <div
        className="flex-shrink-0 sticky bottom-0"
        style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
      >
        <InputBar
          value={input}
          onChange={setInput}
          onSend={send}
          onStop={stopStream}
          disabled={streaming || isWarming}
          streaming={streaming}
        />
      </div>
    </div>
  );
}
