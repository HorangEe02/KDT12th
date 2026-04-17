import Image from "next/image";
import Link from "next/link";
import {
  TEAMS,
  getTeamLogoPath,
  getTeamPalette,
} from "@/lib/team-colors";
import { cn } from "@/lib/utils";
import type { Viewport } from "@/lib/types";

interface TeamSelectorProps {
  selected?: string;
  viewport?: Viewport;
}

/**
 * 팀 카드 그리드 — 웹 5×2 / 모바일 3열.
 * 포팅 원본: src/ui/components/team_selector.py + assets/react/team_selector.html
 *
 * Server Component. Next Link로 `?team=XX` 쿼리 동기화.
 */
export function TeamSelector({
  selected = "LG",
  viewport = "web",
}: TeamSelectorProps) {
  const isMobile = viewport === "mobile";
  return (
    <section
      className={cn(
        "relative mb-6 overflow-hidden rounded-2xl bg-se-surface-container-low px-6 py-5",
      )}
      aria-label="응원팀 선택"
    >
      {/* Secondary fixed blob */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-10 -top-10 h-36 w-36 rounded-full bg-se-secondary-fixed opacity-[0.18] blur-3xl"
      />
      <header className="relative z-10 mb-4 flex items-baseline justify-between">
        <h3 className="font-display text-[1.05rem] font-extrabold uppercase tracking-wide text-se-primary">
          Select Your Team
        </h3>
        <span className="font-display text-[0.72rem] uppercase tracking-[0.12em] text-se-on-surface-variant">
          ⚡ 클릭 → URL 동기화
        </span>
      </header>

      <div
        className={cn(
          "relative z-10 grid gap-3",
          isMobile ? "grid-cols-3" : "grid-cols-5",
        )}
      >
        {TEAMS.map((code) => {
          const palette = getTeamPalette(code);
          const isSelected = code === selected;
          return (
            <Link
              key={code}
              href={{ pathname: "/", query: { team: code } }}
              scroll={false}
              aria-pressed={isSelected}
              title={palette.nameKo}
              className={cn(
                "group flex min-h-[102px] flex-col items-center justify-center rounded-2xl border-2 border-transparent bg-se-surface-container-lowest px-2 py-3.5 no-underline transition-[transform,box-shadow,border-color] duration-200",
                "hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(0,0,0,0.08)]",
                isSelected &&
                  "border-se-primary shadow-[0_10px_22px_rgba(0,25,60,0.18)]",
              )}
            >
              <div
                className={cn(
                  "mb-2 flex h-[46px] w-[46px] items-center justify-center rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.1)]",
                )}
                style={{ background: palette.color }}
              >
                <Image
                  src={getTeamLogoPath(code)}
                  alt=""
                  width={30}
                  height={30}
                  className="object-contain drop-shadow-[0_1px_2px_rgba(0,0,0,0.3)]"
                />
              </div>
              <div className="font-display text-[0.85rem] font-bold text-se-primary">
                {code}
              </div>
              <div className="mt-0.5 text-center text-[0.68rem] text-se-on-surface-variant">
                {palette.nameKo}
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
