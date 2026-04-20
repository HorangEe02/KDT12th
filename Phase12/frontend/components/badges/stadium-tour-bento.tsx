"use client";

import { useBadges } from "@/lib/store/badges";
import { getTeamPalette, getTeamLogoPath } from "@/lib/team-colors";
import Image from "next/image";
import { cn } from "@/lib/utils";
import type { Stadium } from "@/lib/types";

/**
 * 모바일 전용 — Stadium Tour bento (2x2 grid 사진 카드).
 * mockup: uiux/mobile_uiux/my_badges_records_mobile/code.html § Stadium Tour Bento
 */
interface StadiumTourBentoProps {
  stadiums: Stadium[];
}

function firstTeam(homeTeam: string): string {
  return homeTeam.split(",")[0].replace("(보조)", "").trim();
}

export function StadiumTourBento({ stadiums }: StadiumTourBentoProps) {
  const { visited, toggle } = useBadges();
  const visitedCount = visited.length;

  return (
    <section className="-mx-2 rounded-[2rem] bg-se-surface-container-low p-6">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h3 className="font-display text-xl font-bold text-se-primary">
            구장 정복
          </h3>
          <p className="mt-0.5 font-body text-sm text-se-on-surface-variant">
            {stadiums.length}개 중 {visitedCount}개 방문
          </p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-se-secondary-container text-se-on-secondary-container">
          <span
            className="material-symbols-outlined"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            explore
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {stadiums.map((s) => {
          const team = firstTeam(s.home_team);
          const palette = getTeamPalette(team);
          const isVisited = visited.includes(s.short_name);
          return (
            <button
              key={s.short_name}
              onClick={() => toggle(s.short_name)}
              aria-pressed={isVisited}
              className={cn(
                "relative aspect-square overflow-hidden rounded-xl bg-se-surface-container-lowest text-left shadow-[0_8px_24px_rgba(0,0,0,0.04)] transition-transform active:scale-95",
                !isVisited && "opacity-70 grayscale",
              )}
            >
              {/* Background — 팀 컬러 그라디언트 */}
              <div
                className="absolute inset-0"
                style={{
                  background: `linear-gradient(135deg, ${palette.color} 0%, ${palette.subColor} 100%)`,
                }}
              />
              {/* Team logo watermark */}
              <div className="absolute inset-0 flex items-center justify-center opacity-30">
                <Image
                  src={getTeamLogoPath(team)}
                  alt=""
                  width={80}
                  height={80}
                  className="object-contain"
                />
              </div>
              {/* Bottom gradient overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
              {/* Stadium label */}
              <div className="absolute bottom-3 left-3 text-white">
                <p className="font-display text-sm font-bold drop-shadow">
                  {s.short_name}
                </p>
                <p className="font-display text-[10px] uppercase tracking-wider opacity-85">
                  {s.city}
                </p>
              </div>
              {/* Check mark (visited) */}
              {isVisited ? (
                <div className="absolute right-3 top-3 flex h-7 w-7 items-center justify-center rounded-full bg-se-secondary-fixed shadow-md">
                  <span
                    className="material-symbols-outlined text-[16px] text-se-on-secondary-fixed"
                    style={{ fontVariationSettings: "'FILL' 1" }}
                  >
                    check
                  </span>
                </div>
              ) : null}
            </button>
          );
        })}
      </div>
    </section>
  );
}
