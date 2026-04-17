"use client";

import { useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { Game } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ORIGIN_PRESETS, ORIGIN_LABEL } from "@/lib/map/origins";

interface MapControlsProps {
  games: Game[];
  selectedGameId?: string;
  origin: string;
}

export function MapControls({
  games,
  selectedGameId,
  origin,
}: MapControlsProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [, startTransition] = useTransition();

  function push(param: Record<string, string>) {
    const p = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(param)) p.set(k, v);
    startTransition(() => {
      router.replace(`${pathname}?${p.toString()}`, { scroll: false });
    });
  }

  return (
    <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2">
      <label className="block">
        <span className="font-display text-[0.65rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
          🎯 경기 선택
        </span>
        <select
          value={selectedGameId ?? ""}
          onChange={(e) => push({ game: e.target.value })}
          className="mt-1 w-full rounded-xl border border-se-outline-variant bg-white px-3 py-2 text-sm"
          disabled={games.length === 0}
        >
          {games.length === 0 ? (
            <option>선택 가능한 원정 경기가 없습니다</option>
          ) : (
            games.map((g) => (
              <option key={g.game_id} value={g.game_id}>
                {g.date} @ {g.stadium} vs {g.home_team}
              </option>
            ))
          )}
        </select>
      </label>

      <div>
        <span className="font-display text-[0.65rem] font-bold uppercase tracking-[0.12em] text-se-on-surface-variant">
          🚗 출발지
        </span>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {Object.keys(ORIGIN_PRESETS).map((key) => (
            <button
              key={key}
              onClick={() => push({ origin: key })}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-bold transition-colors",
                origin === key
                  ? "border-se-primary bg-se-primary text-white"
                  : "border-se-outline-variant bg-white text-se-on-surface",
              )}
            >
              {ORIGIN_LABEL[key]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
