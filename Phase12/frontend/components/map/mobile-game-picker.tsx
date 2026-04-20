"use client";

import { useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { BottomSheet } from "@/components/ui/bottom-sheet";
import { useMobileSheet } from "@/lib/store/mobile-sheet";
import { cn } from "@/lib/utils";
import type { Game } from "@/lib/types";

/**
 * 모바일 전용 — 경기 선택 BottomSheet (sub-sheet).
 * /map 페이지의 floating top bar 에서 트리거.
 */
interface MobileGamePickerProps {
  games: Game[];
  selectedGameId?: string;
}

export function MobileGamePicker({ games, selectedGameId }: MobileGamePickerProps) {
  const open = useMobileSheet((s) => s.active === "game");
  const close = useMobileSheet((s) => s.close);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  function selectGame(gameId: string) {
    const p = new URLSearchParams(searchParams.toString());
    p.set("game", gameId);
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
      close();
    });
  }

  return (
    <BottomSheet
      open={open}
      onOpenChange={(o) => (o ? null : close())}
      title="🎯 경기 선택"
      snapPoints={["55%", "92%"]}
    >
      {games.length === 0 ? (
        <div className="rounded-xl border border-dashed border-se-outline-variant bg-se-surface-container-low p-6 text-center text-sm text-se-on-surface-variant">
          선택 가능한 원정 경기가 없습니다.
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {games.map((g) => {
            const active = g.game_id === selectedGameId;
            return (
              <button
                key={g.game_id}
                type="button"
                onClick={() => selectGame(g.game_id)}
                className={cn(
                  "flex w-full items-start gap-3 rounded-xl border px-4 py-3 text-left transition-colors active:scale-[0.98]",
                  active
                    ? "border-se-primary bg-se-primary/5"
                    : "border-se-outline-variant/40 bg-white hover:border-se-primary/40",
                )}
              >
                <div
                  className={cn(
                    "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
                    active
                      ? "bg-se-primary text-white"
                      : "bg-se-surface-container-low text-se-primary",
                  )}
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {active ? "radio_button_checked" : "sports_baseball"}
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-display text-sm font-bold text-se-on-surface">
                      {g.date}
                      {g.day_of_week ? ` · ${g.day_of_week}` : ""}
                    </p>
                    {g.start_time ? (
                      <span className="rounded-full bg-se-surface-container-high px-2 py-0.5 font-display text-[10px] font-bold text-se-on-surface">
                        {g.start_time}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-0.5 font-body text-xs text-se-on-surface-variant">
                    @ {g.stadium} · vs {g.home_team}
                  </p>
                </div>
                {active ? (
                  <span
                    className="material-symbols-outlined text-[20px] text-se-primary"
                    style={{ fontVariationSettings: "'FILL' 1" }}
                  >
                    check_circle
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
      )}
    </BottomSheet>
  );
}
