"use client";

import { useEffect, useMemo, useRef, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import type { Game, Waypoint } from "@/lib/types";
import { cn } from "@/lib/utils";

interface GamePickerDialogProps {
  games: Game[];
  selectedGameId: string;
  currentStadiumShort?: string;
  /** 현재 waypoints — 경기 변경으로 구장이 바뀌면 "멀어진 경유지" 경고 (자동 삭제 안 함 · Decision D) */
  waypoints: Waypoint[];
  onClose: () => void;
}

/** 2026-04-03 → Date 객체 */
function parseDateISO(iso: string): Date {
  return new Date(`${iso}T00:00:00+09:00`);
}
function monthKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}
function fmtDateShort(d: Date): string {
  const wd = ["일", "월", "화", "수", "목", "금", "토"][d.getDay()];
  return `${d.getMonth() + 1}/${d.getDate()} (${wd})`;
}

export function GamePickerDialog({
  games,
  selectedGameId,
  currentStadiumShort,
  waypoints,
  onClose,
}: GamePickerDialogProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();
  const scrollRef = useRef<HTMLDivElement>(null);
  const upcomingAnchorRef = useRef<HTMLDivElement>(null);

  const todayISO = new Date().toISOString().slice(0, 10);

  const grouped = useMemo(() => {
    const upcoming: Game[] = [];
    const past: Game[] = [];
    for (const g of games) {
      if (g.date >= todayISO) upcoming.push(g);
      else past.push(g);
    }
    const byMonth = (list: Game[]) => {
      const map = new Map<string, Game[]>();
      for (const g of list) {
        const d = parseDateISO(g.date);
        const k = monthKey(d);
        if (!map.has(k)) map.set(k, []);
        map.get(k)!.push(g);
      }
      return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
    };
    return {
      upcoming: byMonth(upcoming),
      past: byMonth(past).reverse(), // 과거는 최근부터
    };
  }, [games, todayISO]);

  // 첫 렌더 시 다가오는 첫 경기로 자동 스크롤
  useEffect(() => {
    const el = upcomingAnchorRef.current;
    const container = scrollRef.current;
    if (!el || !container) return;
    container.scrollTop = Math.max(0, el.offsetTop - 16);
  }, []);

  function selectGame(gameId: string, nextStadium: string) {
    const p = new URLSearchParams(searchParams.toString());
    p.set("game", gameId);
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    });
    // Decision 3 D — 구장 변경 + 경유지 존재 시 경고 토스트
    if (waypoints.length > 0 && currentStadiumShort && nextStadium !== currentStadiumShort) {
      toast.warning(
        `구장이 "${nextStadium}" 로 변경됐어요. 기존 경유지 ${waypoints.length}개가 새 구장과 멀어질 수 있어요.`,
        { duration: 4500 },
      );
    }
    onClose();
  }

  const hasUpcoming = grouped.upcoming.length > 0;
  const hasPast = grouped.past.length > 0;

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/55 p-6 backdrop-blur-sm"
      role="dialog"
      aria-modal
      aria-label="경기 선택"
      onClick={onClose}
    >
      <div
        className="relative flex max-h-[80dvh] w-full max-w-lg flex-col overflow-hidden rounded-3xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-se-outline-variant/50 px-5 py-4">
          <div>
            <h3 className="font-display text-base font-bold text-se-primary">
              🎯 경기 선택
            </h3>
            <p className="mt-0.5 text-[11px] text-se-on-surface-variant">
              {games.length} 경기 · 월별 그룹
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-se-surface-container-low"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </header>

        <div ref={scrollRef} className="overflow-y-auto px-5 py-4">
          {games.length === 0 ? (
            <p className="py-10 text-center text-sm text-se-on-surface-variant">
              선택 가능한 원정 경기가 없어요. 기간 필터를 확인해 주세요.
            </p>
          ) : (
            <>
              {hasUpcoming ? (
                <section>
                  <div
                    ref={upcomingAnchorRef}
                    className="sticky top-0 z-10 -mx-5 mb-2 bg-white/95 px-5 py-2 backdrop-blur"
                  >
                    <h4 className="font-display text-xs font-extrabold uppercase tracking-wider text-se-secondary">
                      🔮 다가오는 경기 ({grouped.upcoming.reduce((acc, [, l]) => acc + l.length, 0)})
                    </h4>
                  </div>
                  {grouped.upcoming.map(([monthKey, list]) => (
                    <MonthSection
                      key={`up-${monthKey}`}
                      monthKey={monthKey}
                      list={list}
                      selectedGameId={selectedGameId}
                      onPick={selectGame}
                    />
                  ))}
                </section>
              ) : null}
              {hasPast ? (
                <section className={cn(hasUpcoming && "mt-5")}>
                  <div className="sticky top-0 z-10 -mx-5 mb-2 bg-white/95 px-5 py-2 backdrop-blur">
                    <h4 className="font-display text-xs font-extrabold uppercase tracking-wider text-se-outline">
                      ✅ 지난 경기 ({grouped.past.reduce((acc, [, l]) => acc + l.length, 0)})
                    </h4>
                  </div>
                  {grouped.past.map(([monthKey, list]) => (
                    <MonthSection
                      key={`past-${monthKey}`}
                      monthKey={monthKey}
                      list={list}
                      selectedGameId={selectedGameId}
                      onPick={selectGame}
                      muted
                    />
                  ))}
                </section>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function MonthSection({
  monthKey,
  list,
  selectedGameId,
  onPick,
  muted,
}: {
  monthKey: string;
  list: Game[];
  selectedGameId: string;
  onPick: (gameId: string, nextStadium: string) => void;
  muted?: boolean;
}) {
  const [y, m] = monthKey.split("-");
  return (
    <div className="mb-4">
      <div
        className={cn(
          "mb-1.5 px-1 font-display text-[11px] font-bold",
          muted ? "text-se-outline" : "text-se-on-surface-variant",
        )}
      >
        ── {y}년 {Number(m)}월 ──
      </div>
      <ul className="space-y-1">
        {list.map((g) => {
          const active = g.game_id === selectedGameId;
          const d = new Date(`${g.date}T00:00:00+09:00`);
          const wd = ["일", "월", "화", "수", "목", "금", "토"][d.getDay()];
          return (
            <li key={g.game_id}>
              <button
                type="button"
                onClick={() => onPick(g.game_id, g.stadium)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors",
                  active
                    ? "bg-se-primary/10 ring-1 ring-se-primary"
                    : "hover:bg-se-surface-container-low",
                  muted && !active && "opacity-60",
                )}
              >
                <div className="flex w-12 shrink-0 flex-col items-center rounded-lg bg-se-surface-container-low py-1">
                  <span className="font-display text-[10px] font-bold text-se-outline">
                    {wd}
                  </span>
                  <span className="font-display text-sm font-extrabold leading-none text-se-primary">
                    {d.getDate()}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-display text-sm font-bold text-se-on-surface">
                    vs {g.home_team}
                  </p>
                  <p className="truncate text-[11px] text-se-outline">
                    {g.stadium}
                    {g.start_time || g.time ? ` · ${g.start_time || g.time}` : ""}
                  </p>
                </div>
                {active ? (
                  <span className="rounded-full bg-se-primary px-2 py-0.5 font-display text-[9px] font-extrabold uppercase tracking-wider text-white">
                    현재
                  </span>
                ) : null}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
