"use client";

import { memo } from "react";
import { User, Bot, Zap, CheckCircle2, XCircle } from "lucide-react";
import type {
  ChatRecommendation,
  ToolCallRecord,
  ToolResultRecord,
} from "@/lib/types";
import RecommendationCards from "./RecommendationCards";

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  recommendations?: ChatRecommendation[];
  latencyMs?: number;
  streaming?: boolean;
  error?: string;
  // Phase 7 tool calling meta
  toolCalls?: ToolCallRecord[];
  toolResults?: ToolResultRecord[];
  iterations?: number;
  fallbackUsed?: boolean;
}

function MessageBubbleImpl({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const hasRecs = message.recommendations && message.recommendations.length > 0;

  return (
    <div
      className={`flex items-start gap-3 ${
        isUser ? "flex-row-reverse" : ""
      }`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center border ${
          isUser
            ? "bg-primary/10 border-primary/30 text-primary"
            : "bg-surface-2 border-outline/20 text-text-secondary"
        }`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Bubble */}
      <div className={`flex-1 max-w-[82%] ${isUser ? "text-right" : ""}`}>
        <div
          className={`inline-block px-4 py-3 rounded-sm text-sm leading-relaxed text-left whitespace-pre-wrap ${
            isUser
              ? "bg-primary text-background"
              : "bg-surface-1 border border-outline/15 text-text-primary"
          }`}
          style={{
            fontFamily: "var(--font-ko)",
            borderTopRightRadius: isUser ? 2 : undefined,
            borderTopLeftRadius: !isUser ? 2 : undefined,
          }}
        >
          {message.text || (message.streaming ? "…" : "")}
          {message.streaming && (
            <span className="inline-block w-2 h-4 ml-0.5 bg-text-tertiary/60 align-middle animate-pulse" />
          )}
        </div>

        {/* Recommendations */}
        {hasRecs && (
          <div className="mt-3">
            <RecommendationCards items={message.recommendations!} />
          </div>
        )}

        {/* Tool calls trace (Phase 7) */}
        {!isUser && message.toolResults && message.toolResults.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.toolResults.map((r, i) => (
              <span
                key={i}
                title={r.error || "ok"}
                className={`inline-flex items-center gap-1 px-2 py-0.5 border rounded-full text-[10px] font-mono ${
                  r.ok
                    ? "border-success/40 bg-success/10 text-success"
                    : "border-error/40 bg-error/10 text-error"
                }`}
              >
                {r.ok ? <CheckCircle2 size={9} /> : <XCircle size={9} />}
                {r.tool}
              </span>
            ))}
            {message.fallbackUsed && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 border border-warning/40 bg-warning/10 text-warning rounded-full text-[10px] font-mono">
                <Zap size={9} />
                heuristic
              </span>
            )}
          </div>
        )}

        {/* Meta footer */}
        {!isUser && (message.latencyMs != null || message.error) && (
          <div className="text-[10px] font-mono text-text-tertiary mt-1.5">
            {message.error ? (
              <span className="text-error">⚠️ {message.error}</span>
            ) : (
              <>
                latency {message.latencyMs}ms
                {message.iterations != null && message.iterations > 0 && (
                  <> · {message.iterations} iter{message.iterations > 1 ? "s" : ""}</>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Memoized — prevents every past bubble from re-rendering on each streamed
 * token. The current streaming bubble still updates because `text` and
 * `streaming` change; settled bubbles compare equal and bail out.
 */
const MessageBubble = memo(MessageBubbleImpl, (prev, next) => {
  const a = prev.message;
  const b = next.message;
  return (
    a.id === b.id &&
    a.text === b.text &&
    a.streaming === b.streaming &&
    a.latencyMs === b.latencyMs &&
    a.error === b.error &&
    a.recommendations === b.recommendations &&
    a.toolResults === b.toolResults
  );
});

export default MessageBubble;
