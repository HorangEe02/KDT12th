"use client";

import Image from "next/image";
import { TEAMS, getTeamLogoPath, getTeamPalette } from "@/lib/team-colors";
import { cn } from "@/lib/utils";

/**
 * Staged team picker — 저장 전까지 URL/Zustand 건드리지 않음.
 * 시각 스타일은 TeamSelector 와 유사하지만 Link 가 아닌 button 기반 controlled component.
 *
 * 반응형: 모바일 3열 · md+ 5열 (TeamSelector 와 동일 패턴)
 */
interface TeamGridSelectorProps {
  value: string | null;
  onChange: (team: string) => void;
  disabled?: boolean;
}

export function TeamGridSelector({
  value,
  onChange,
  disabled = false,
}: TeamGridSelectorProps) {
  return (
    <div
      role="radiogroup"
      aria-label="응원팀 선택"
      className="grid grid-cols-3 gap-3 md:grid-cols-5"
    >
      {TEAMS.map((code) => {
        const palette = getTeamPalette(code);
        const selected = code === value;
        return (
          <button
            key={code}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={disabled}
            onClick={() => onChange(code)}
            title={palette.nameKo}
            className={cn(
              "group flex min-h-[102px] flex-col items-center justify-center rounded-2xl border-2 border-transparent bg-se-surface-container-lowest px-2 py-3.5 transition-[transform,box-shadow,border-color] duration-200 active:scale-95",
              !disabled &&
                "hover:-translate-y-0.5 hover:shadow-[0_12px_24px_rgba(0,0,0,0.08)]",
              selected &&
                "border-se-primary shadow-[0_10px_22px_rgba(0,25,60,0.18)]",
              disabled && "cursor-not-allowed opacity-50",
            )}
          >
            <div
              className="mb-2 flex h-[46px] w-[46px] items-center justify-center rounded-full shadow-[0_4px_10px_rgba(0,0,0,0.1)]"
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
          </button>
        );
      })}
    </div>
  );
}
