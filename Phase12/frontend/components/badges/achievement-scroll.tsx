"use client";

import { useBadges } from "@/lib/store/badges";
import { ACHIEVEMENTS } from "@/lib/badges/achievements";
import { cn } from "@/lib/utils";

/**
 * 모바일 전용 — 도전 과제 (Achievement Badges) horizontal scroll.
 * mockup: uiux/mobile_uiux/my_badges_records_mobile/code.html § Achievement Badges
 *
 * 클라이언트 계산 — visited.length 기준으로 unlocked 결정.
 * 데이터 공유: lib/badges/achievements.ts (데스크톱 AchievementGrid 와 동일 정의).
 */

export function AchievementScroll() {
  const visitedCount = useBadges((s) => s.visited.length);

  return (
    <section>
      <h3 className="mb-4 px-2 font-display text-xl font-bold text-se-primary">
        도전 과제
      </h3>
      <div className="-mx-4 flex snap-x gap-4 overflow-x-auto px-4 pb-4 [&::-webkit-scrollbar]:hidden">
        {ACHIEVEMENTS.map((a) => {
          const unlocked = visitedCount >= a.threshold;
          return (
            <div
              key={a.id}
              className={cn(
                "flex w-24 shrink-0 snap-start flex-col items-center",
                !unlocked && "opacity-40 grayscale",
              )}
            >
              <div
                className={cn(
                  "mb-2 h-20 w-20 rounded-full p-1 shadow-[0_12px_24px_rgba(0,0,0,0.08)]",
                  unlocked
                    ? `bg-gradient-to-br ${a.gradient}`
                    : "bg-se-surface-container-high",
                )}
              >
                <div className="flex h-full w-full items-center justify-center rounded-full border-2 border-white/30 bg-white/10 backdrop-blur-sm">
                  <span
                    className={cn(
                      "material-symbols-outlined text-3xl",
                      unlocked ? "text-white" : "text-se-outline",
                    )}
                    style={
                      unlocked ? { fontVariationSettings: "'FILL' 1" } : undefined
                    }
                  >
                    {unlocked ? a.icon : "lock"}
                  </span>
                </div>
              </div>
              <p className="text-center font-display text-xs font-bold leading-tight text-se-on-surface">
                {a.label}
              </p>
              <p
                className={cn(
                  "mt-1 font-display text-[9px] uppercase tracking-widest",
                  unlocked ? "text-se-secondary" : "text-se-outline",
                )}
              >
                {unlocked ? "달성" : `${a.threshold}구장`}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
