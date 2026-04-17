"use client";

import type { UIMessage } from "ai";
import { cn } from "@/lib/utils";

const TOOL_ICON: Record<string, string> = {
  search_game: "sports_baseball",
  predict_win_rate: "insights",
  get_weather: "cloud",
  find_places: "restaurant",
  get_route: "route",
  search_knowledge: "menu_book",
};

const TOOL_LABEL: Record<string, string> = {
  search_game: "경기 조회",
  predict_win_rate: "승률 예측",
  get_weather: "날씨",
  find_places: "장소 검색",
  get_route: "길찾기",
  search_knowledge: "팁 검색",
};

type Part = NonNullable<UIMessage["parts"]>[number];

function isToolPart(p: Part): p is Part & { type: string } {
  return !!p && typeof p === "object" && "type" in p && typeof p.type === "string";
}

/**
 * UIMessage.parts 중 tool invocation 파트만 골라 렌더.
 * AI SDK v6 tool parts: `tool-${toolName}` type · state / input / output 필드.
 */
export function ToolViz({ message }: { message: UIMessage }) {
  const toolParts = (message.parts ?? []).filter((p) => {
    if (!isToolPart(p)) return false;
    return p.type.startsWith("tool-") || p.type === "dynamic-tool";
  });

  if (toolParts.length === 0) return null;

  return (
    <div className="mt-2 flex flex-col gap-1.5">
      {toolParts.map((p, i) => {
        const pt = p as unknown as {
          type: string;
          toolName?: string;
          state?: string;
          input?: unknown;
          output?: unknown;
          errorText?: string;
        };
        const name =
          pt.type.startsWith("tool-") ? pt.type.slice(5) : pt.toolName ?? "tool";
        const icon = TOOL_ICON[name] ?? "build";
        const label = TOOL_LABEL[name] ?? name;
        const state = pt.state ?? "output-available";
        const isDone =
          state === "output-available" || state === "result" || state === "ok";
        const isError = state === "output-error" || !!pt.errorText;

        return (
          <details
            key={i}
            className={cn(
              "rounded-lg border px-3 py-1.5 text-xs",
              isError
                ? "border-red-200 bg-red-50 text-red-900"
                : isDone
                  ? "border-se-outline-variant bg-se-surface-container-low text-se-on-surface"
                  : "border-amber-200 bg-amber-50 text-amber-900",
            )}
          >
            <summary className="flex cursor-pointer items-center gap-2 font-semibold">
              <span className="material-symbols-outlined text-[16px]">
                {icon}
              </span>
              <span>🔧 {label}</span>
              <span className="ml-auto font-mono text-[0.6rem] text-se-outline">
                {state}
              </span>
            </summary>
            <div className="mt-1.5 space-y-1 font-mono text-[0.65rem] leading-snug">
              {pt.input != null ? (
                <div>
                  <span className="font-bold text-se-on-surface-variant">input:</span>{" "}
                  <code>{JSON.stringify(pt.input)}</code>
                </div>
              ) : null}
              {pt.output != null ? (
                <div className="break-all">
                  <span className="font-bold text-se-on-surface-variant">output:</span>{" "}
                  <code>{JSON.stringify(pt.output).slice(0, 400)}</code>
                </div>
              ) : null}
              {pt.errorText ? (
                <div className="text-red-900">error: {pt.errorText}</div>
              ) : null}
            </div>
          </details>
        );
      })}
    </div>
  );
}
