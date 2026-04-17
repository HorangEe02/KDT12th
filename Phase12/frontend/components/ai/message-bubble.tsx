"use client";

import type { UIMessage } from "ai";
import { ToolViz } from "./tool-viz";
import { cn } from "@/lib/utils";

function extractText(message: UIMessage): string {
  const parts = message.parts ?? [];
  return parts
    .map((p) =>
      p && typeof p === "object" && "type" in p && p.type === "text"
        ? (p as { text?: string }).text ?? ""
        : "",
    )
    .join("");
}

export function MessageBubble({ message }: { message: UIMessage }) {
  const isUser = message.role === "user";
  const text = extractText(message);

  return (
    <div
      className={cn(
        "flex w-full gap-3",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      {!isUser ? (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-se-primary to-se-primary-container text-white">
          <span className="material-symbols-outlined text-[18px]">
            smart_toy
          </span>
        </div>
      ) : null}
      <div
        className={cn(
          "max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
          isUser
            ? "bg-se-primary text-white"
            : "bg-se-surface-container-lowest text-se-on-surface border border-se-outline-variant",
        )}
      >
        {text || (
          <span className="italic text-se-on-surface-variant">
            (도구 호출 중…)
          </span>
        )}
        {!isUser ? <ToolViz message={message} /> : null}
      </div>
      {isUser ? (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-se-surface-container-low text-se-primary">
          <span className="material-symbols-outlined text-[18px]">person</span>
        </div>
      ) : null}
    </div>
  );
}
