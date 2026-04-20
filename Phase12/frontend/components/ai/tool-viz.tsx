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
  get_team_ranking: "leaderboard",
  get_player_stats: "person",
  get_live_score: "scoreboard",
};

const TOOL_LABEL: Record<string, string> = {
  search_game: "경기 조회",
  predict_win_rate: "승률 예측",
  get_weather: "날씨",
  find_places: "장소 검색",
  get_route: "길찾기",
  search_knowledge: "팁 검색",
  get_team_ranking: "순위 조회",
  get_player_stats: "선수 스탯",
  get_live_score: "실시간 스코어",
};

type Part = NonNullable<UIMessage["parts"]>[number];

function isToolPart(p: Part): p is Part & { type: string } {
  return !!p && typeof p === "object" && "type" in p && typeof p.type === "string";
}

/**
 * UIMessage.parts 중 tool invocation 파트만 골라 렌더.
 * AI SDK v6 tool parts: `tool-${toolName}` type · state / input / output 필드.
 *
 * UX 방침 (2026-04-19 업데이트):
 *   - 일반 사용자에게 raw JSON (input/output) 은 노출하지 않는다.
 *   - 대신 "🔧 경기 조회 ✅" 같은 compact 배지로 "어떤 도구가 실행됐는지" 만 보여줌.
 *   - 투명성(어떤 도구가 호출되었나)은 유지하되, 기술 디테일은 숨겨 혼란 방지.
 *   - 에러는 title 툴팁으로 간단히 확인 가능.
 */
export function ToolViz({ message }: { message: UIMessage }) {
  const toolParts = (message.parts ?? []).filter((p) => {
    if (!isToolPart(p)) return false;
    return p.type.startsWith("tool-") || p.type === "dynamic-tool";
  });

  if (toolParts.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {toolParts.map((p, i) => {
        const pt = p as unknown as {
          type: string;
          toolName?: string;
          state?: string;
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
        const tooltip = isError
          ? `오류: ${pt.errorText ?? "도구 실행 실패"}`
          : isDone
            ? `${label} 도구 실행 완료`
            : `${label} 도구 실행 중…`;

        return (
          <span
            key={i}
            title={tooltip}
            aria-label={tooltip}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.7rem] font-semibold",
              isError
                ? "border-red-200 bg-red-50 text-red-900"
                : isDone
                  ? "border-se-outline-variant bg-se-surface-container-low text-se-on-surface"
                  : "border-amber-200 bg-amber-50 text-amber-900",
            )}
          >
            <span className="material-symbols-outlined text-[14px]">
              {icon}
            </span>
            <span>{label}</span>
            {isError ? (
              <span className="material-symbols-outlined text-[13px] text-red-600">
                error
              </span>
            ) : isDone ? (
              <span className="material-symbols-outlined text-[13px] text-emerald-600">
                check_circle
              </span>
            ) : (
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
            )}
          </span>
        );
      })}
    </div>
  );
}
