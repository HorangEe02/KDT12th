"use client";

import { useBadges } from "@/lib/store/badges";
import { ACHIEVEMENTS } from "@/lib/badges/achievements";
import { cn } from "@/lib/utils";

/**
 * 데스크톱 전용 — 도전 과제 grid (5 카드).
 * 모바일의 AchievementScroll 과 동일 데이터 (ACHIEVEMENTS) 공유.
 *
 *   - unlocked: 풀컬러 그라디언트 아이콘 + "달성" 배지
 *   - locked:   회색 lock 아이콘 + 진행도 바 (N / threshold)
 */
export function AchievementGrid() {
  const visitedCount = useBadges((s) => s.visited.length);

  return (
    <section className="rounded-3xl border border-se-outline-variant bg-se-surface-container-lowest p-6">
      <header className="mb-5 flex items-end justify-between">
        <div>
          <h2 className="font-display text-lg font-extrabold text-se-primary">
            🏅 도전 과제
          </h2>
          <p className="mt-1 text-xs text-se-on-surface-variant">
            방문 구장 수에 따라 배지가 해제됩니다. 현재{" "}
            <strong className="text-se-primary">{visitedCount}/10</strong> 구장 방문.
          </p>
        </div>
        <div className="hidden items-center gap-2 sm:flex">
          {ACHIEVEMENTS.map((a) => {
            const unlocked = visitedCount >= a.threshold;
            return (
              <span
                key={`pip-${a.id}`}
                aria-hidden
                className={cn(
                  "h-2 w-2 rounded-full transition-colors",
                  unlocked
                    ? `bg-gradient-to-br ${a.gradient}`
                    : "bg-se-outline-variant",
                )}
              />
            );
          })}
        </div>
      </header>

      <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
        {ACHIEVEMENTS.map((a) => {
          const unlocked = visitedCount >= a.threshold;
          const progress = Math.min(1, visitedCount / a.threshold);
          return (
            <li
              key={a.id}
              className={cn(
                "relative flex flex-col items-center overflow-hidden rounded-2xl border bg-white p-4 text-center transition-all",
                unlocked
                  ? "border-se-outline-variant shadow-[0_6px_20px_rgba(0,25,60,0.06)]"
                  : "border-se-outline-variant/50 bg-se-surface-container-low",
              )}
            >
              {unlocked ? (
                <span className="absolute right-2 top-2 rounded-full bg-se-secondary px-2 py-0.5 font-display text-[9px] font-extrabold uppercase tracking-wider text-white">
                  달성
                </span>
              ) : (
                <span className="absolute right-2 top-2 rounded-full bg-se-surface-container px-2 py-0.5 font-display text-[9px] font-extrabold uppercase tracking-wider text-se-outline">
                  {visitedCount}/{a.threshold}
                </span>
              )}

              <div
                className={cn(
                  "mb-3 flex h-20 w-20 items-center justify-center rounded-full p-1 shadow-[0_12px_24px_rgba(0,0,0,0.08)]",
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

              <p className="font-display text-sm font-bold text-se-on-surface">
                {a.label}
              </p>
              <p className="mt-0.5 font-body text-[11px] text-se-on-surface-variant line-clamp-2">
                {a.description}
              </p>

              {/* 진행도 바 */}
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-se-surface-container-high">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    unlocked
                      ? `bg-gradient-to-r ${a.gradient}`
                      : "bg-se-outline-variant",
                  )}
                  style={{ width: `${progress * 100}%` }}
                />
              </div>
              <p
                className={cn(
                  "mt-1.5 font-display text-[10px] font-bold uppercase tracking-widest",
                  unlocked ? "text-se-secondary" : "text-se-outline",
                )}
              >
                {a.threshold}구장
              </p>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
