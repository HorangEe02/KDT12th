"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { useMobileSheet } from "@/lib/store/mobile-sheet";
import type { RouteResult, Stadium } from "@/lib/types";

const COLLAPSE_KEY = "map-card-collapsed";

/**
 * 모바일 전용 — 풀스크린 지도 하단 floating Journey Summary Card.
 * mockup: uiux/mobile_uiux/itinerary_route_map_mobile/code.html § Journey Summary
 *
 * BottomNav (88px) 위에 위치 (bottom-[100px]).
 */
interface JourneySummaryCardProps {
  origin: { label: string; time?: string };
  stadium: Stadium;
  route: RouteResult;
  midStop?: { label: string; time?: string; icon?: string };
  isToday?: boolean;
  gameTime?: string;
}

const SOURCE_BADGE: Record<RouteResult["source"], { label: string; tone: string }> = {
  kakao: { label: "정밀", tone: "bg-se-primary text-white" },
  osrm: { label: "최적", tone: "bg-se-secondary-container text-se-on-secondary-container" },
  haversine: { label: "직선", tone: "bg-se-surface-container text-se-on-surface-variant" },
};

function formatDuration(sec: number | null): string {
  if (!sec) return "—";
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}분`;
  const h = Math.floor(min / 60);
  return `${h}시간 ${min % 60}분`;
}
function formatDistance(m: number | null): string {
  if (!m) return "—";
  return m >= 1000 ? `${(m / 1000).toFixed(1)}km` : `${Math.round(m)}m`;
}

export function JourneySummaryCard({
  origin,
  stadium,
  route,
  midStop,
  isToday,
  gameTime,
}: JourneySummaryCardProps) {
  const stops = midStop ? 3 : 2;
  const badge = SOURCE_BADGE[route.source];
  const openSheet = useMobileSheet((s) => s.open);

  // Collapse 상태 (localStorage persist)
  const [collapsed, setCollapsed] = useState<boolean>(false);
  useEffect(() => {
    if (typeof localStorage === "undefined") return;
    setCollapsed(localStorage.getItem(COLLAPSE_KEY) === "1");
  }, []);
  function toggleCollapsed() {
    setCollapsed((c) => {
      const next = !c;
      if (typeof localStorage !== "undefined") {
        localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
      }
      return next;
    });
  }

  // Collapsed 상태 — 80px chip
  if (collapsed) {
    return (
      <div className="pointer-events-none fixed bottom-[100px] left-0 right-0 z-40 px-4 md:hidden">
        <button
          type="button"
          onClick={toggleCollapsed}
          className="pointer-events-auto flex w-full items-center justify-between rounded-full bg-white/95 px-5 py-3 shadow-[0_8px_32px_rgba(0,25,60,0.12)] backdrop-blur-xl active:scale-[0.98]"
          aria-label="동선 카드 펼치기"
        >
          <div className="flex items-center gap-3">
            <span
              className="material-symbols-outlined text-[20px] text-se-primary"
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              route
            </span>
            <span className="font-display text-sm font-bold text-se-primary">
              {stops} stops · {formatDuration(route.duration_sec)} ·{" "}
              {formatDistance(route.distance_m)}
            </span>
          </div>
          <span className="material-symbols-outlined text-[20px] text-se-on-surface-variant">
            expand_less
          </span>
        </button>
      </div>
    );
  }

  return (
    <div className="pointer-events-none fixed bottom-[100px] left-0 right-0 z-40 px-4 md:hidden">
      <div className="pointer-events-auto relative overflow-hidden rounded-[2rem] bg-white/95 p-5 shadow-[0_8px_32px_rgba(0,25,60,0.12)] backdrop-blur-xl">
        {/* Decorative gradient */}
        <div className="pointer-events-none absolute right-0 top-0 h-32 w-32 rounded-bl-full bg-gradient-to-br from-se-primary/10 to-se-primary-container/10" />

        {/* Collapse toggle (우상단) */}
        <button
          type="button"
          onClick={toggleCollapsed}
          className="absolute right-2 top-2 z-20 flex h-11 w-11 items-center justify-center rounded-full text-se-on-surface-variant transition-colors hover:bg-se-surface-container-low active:scale-90"
          aria-label="동선 카드 접기"
        >
          <span className="material-symbols-outlined text-[20px]">
            expand_more
          </span>
        </button>

        {/* Header */}
        <div className="relative z-10 mb-4 flex items-start justify-between pr-9">
          <div>
            <h2 className="font-display text-lg font-extrabold tracking-tight text-se-primary">
              경기일 동선
            </h2>
            <p className="mt-0.5 font-body text-xs text-se-on-surface-variant">
              {stops} stops · 총 {formatDuration(route.duration_sec)} · {formatDistance(route.distance_m)}
            </p>
          </div>
          <div
            className={cn(
              "flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 shadow-sm",
              badge.tone,
            )}
          >
            <span className="material-symbols-outlined text-sm">
              directions_bus
            </span>
            <span className="font-display text-[10px] font-bold uppercase tracking-wider">
              {badge.label}
            </span>
          </div>
        </div>

        {/* Stops list */}
        <div className="relative z-10 flex flex-col gap-3">
          {/* Origin (출발지) — 클릭 가능: 출발지 변경 sheet */}
          <button
            type="button"
            onClick={() => openSheet("origin")}
            className="flex items-center gap-3 rounded-xl border border-dashed border-se-outline-variant/40 p-1 text-left transition-colors hover:border-se-primary hover:bg-se-surface-container-low active:scale-[0.98]"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-se-surface-container-low text-se-on-surface-variant">
              <span className="material-symbols-outlined text-[18px]">
                my_location
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1">
                <p className="truncate font-display text-sm font-bold text-se-on-surface">
                  {origin.label}
                </p>
                <span className="material-symbols-outlined text-[14px] text-se-outline">
                  edit
                </span>
              </div>
              <p className="font-body text-xs text-se-outline">
                출발{origin.time ? ` · ${origin.time}` : ""} · 탭하여 변경
              </p>
            </div>
          </button>
          {midStop ? (
            <Stop
              icon={midStop.icon ?? "restaurant"}
              label={midStop.label}
              sub={`경유${midStop.time ? ` · ${midStop.time}` : ""} · 탭하여 변경`}
              primary={false}
              accent="secondary"
              onClick={() => openSheet("waypoint")}
            />
          ) : null}
          <Stop
            icon="sports_baseball"
            label={stadium.stadium_name}
            sub={`도착${gameTime ? ` · ${gameTime} 경기 시작` : ""} · 탭하여 경기 변경`}
            primary
            live={isToday}
            onClick={() => openSheet("game")}
          />
        </div>

        {/* CTA — Trip Confirmation 트리거 */}
        <button
          type="button"
          onClick={() => openSheet("trip-confirm")}
          className="relative z-10 mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-br from-se-primary to-se-primary-container py-4 font-display text-sm font-bold text-white shadow-[0_4px_16px_rgba(0,25,60,0.18)] transition-all hover:opacity-95 active:scale-[0.98]"
        >
          <span>길 안내 시작</span>
          <span className="material-symbols-outlined text-[18px]">
            navigation
          </span>
        </button>
      </div>
    </div>
  );
}

function Stop({
  icon,
  label,
  sub,
  primary,
  live,
  accent,
  onClick,
}: {
  icon: string;
  label: string;
  sub: string;
  primary?: boolean;
  live?: boolean;
  accent?: "secondary";
  /** 있으면 button 렌더 + edit 아이콘 노출 → 시트 열기용 */
  onClick?: () => void;
}) {
  const iconBoxCls = primary
    ? "h-10 w-10 bg-gradient-to-br from-se-primary to-se-primary-container text-white shadow-[0_4px_12px_rgba(0,25,60,0.2)]"
    : accent === "secondary"
      ? "h-9 w-9 bg-se-secondary-fixed/30 text-se-secondary"
      : "h-9 w-9 bg-se-surface-container-low text-se-on-surface-variant";

  const inner = (
    <>
      <div
        className={cn(
          "flex shrink-0 items-center justify-center rounded-full",
          iconBoxCls,
        )}
      >
        <span
          className="material-symbols-outlined text-[18px]"
          style={primary ? { fontVariationSettings: "'FILL' 1" } : undefined}
        >
          {icon}
        </span>
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1">
          <p
            className={cn(
              "truncate font-display font-bold",
              primary ? "text-base text-se-primary" : "text-sm text-se-on-surface",
            )}
          >
            {label}
          </p>
          {live ? (
            <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
          ) : null}
          {onClick ? (
            <span
              aria-hidden
              className={cn(
                "material-symbols-outlined text-[14px]",
                primary ? "text-se-primary/70" : "text-se-outline",
              )}
            >
              edit
            </span>
          ) : null}
        </div>
        <p
          className={cn(
            "font-body text-xs",
            primary ? "font-semibold text-se-primary/80" : "text-se-outline",
          )}
        >
          {sub}
        </p>
      </div>
    </>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="flex items-center gap-3 rounded-xl border border-dashed border-se-outline-variant/40 p-1 text-left transition-colors hover:border-se-primary hover:bg-se-surface-container-low active:scale-[0.98]"
        aria-label={`${label} 변경`}
      >
        {inner}
      </button>
    );
  }

  return <div className="flex items-center gap-3">{inner}</div>;
}
