"use client";

import { useBadges } from "@/lib/store/badges";
import { cn } from "@/lib/utils";
import type { Stadium } from "@/lib/types";

/**
 * 모바일 전용 — 원정 기록 timeline.
 * mockup: uiux/mobile_uiux/my_badges_records_mobile/code.html § Away Timeline
 *
 * MVP 단순화: visited 배열 + stadium 정보 만으로 timeline 표시 (W/L 없음).
 * 향후 Firestore user_visits.perStadium.lastAt 으로 정렬 가능.
 */
interface AwayTimelineProps {
  stadiums: Stadium[];
}

function firstTeam(homeTeam: string): string {
  return homeTeam.split(",")[0].replace("(보조)", "").trim();
}

export function AwayTimeline({ stadiums }: AwayTimelineProps) {
  const visited = useBadges((s) => s.visited);

  if (visited.length === 0) {
    return (
      <section className="px-2">
        <h3 className="mb-4 font-display text-xl font-bold text-se-primary">
          원정 기록
        </h3>
        <div className="rounded-2xl border border-dashed border-se-outline-variant bg-se-surface-container-low px-5 py-10 text-center">
          <span className="material-symbols-outlined block text-3xl text-se-outline">
            timeline
          </span>
          <p className="mt-2 font-display text-sm font-bold text-se-on-surface">
            아직 방문 기록이 없습니다
          </p>
          <p className="mt-1 text-xs text-se-on-surface-variant">
            구장 정복에서 방문한 구장을 체크하면 기록됩니다.
          </p>
        </div>
      </section>
    );
  }

  const visitedStadiums = stadiums.filter((s) =>
    visited.includes(s.short_name),
  );

  return (
    <section className="px-2">
      <h3 className="mb-6 font-display text-xl font-bold text-se-primary">
        원정 기록
      </h3>
      <div className="space-y-4">
        {visitedStadiums.map((s, i) => {
          const team = firstTeam(s.home_team);
          const isLast = i === visitedStadiums.length - 1;
          return (
            <div key={s.short_name} className="flex gap-4">
              <div className="flex flex-col items-center pt-2">
                <div className="h-3 w-3 rounded-full bg-se-secondary-fixed ring-4 ring-se-secondary-container/40" />
                {!isLast ? (
                  <div className="mt-2 h-full w-px bg-gradient-to-b from-se-secondary-fixed/40 to-transparent" />
                ) : null}
              </div>
              <div className="flex-1 rounded-2xl border border-se-surface-container bg-se-surface-container-lowest p-4 shadow-[0_4px_24px_rgba(0,0,0,0.03)]">
                <div className="mb-2 flex items-center justify-between">
                  <span className="rounded bg-se-secondary-container px-2 py-0.5 font-display text-[10px] font-bold uppercase tracking-widest text-se-on-secondary-container">
                    방문
                  </span>
                  <span className="font-body text-xs text-se-on-surface-variant">
                    {team} 홈구장
                  </span>
                </div>
                <h4 className="font-display text-base font-bold text-se-primary">
                  {s.stadium_name}
                </h4>
                <p
                  className={cn(
                    "mt-1 flex items-center gap-1 font-body text-sm text-se-on-surface-variant",
                  )}
                >
                  <span className="material-symbols-outlined text-[14px]">
                    location_on
                  </span>
                  {s.city} · {s.address}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
