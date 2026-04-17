import Link from "next/link";
import type { Game } from "@/lib/types";
import { cn } from "@/lib/utils";

interface MatchListProps {
  games: Game[];
  selectedGameId?: string;
  /** clicking a row navigates to ?game=XXX while preserving other searchParams */
  baseQuery: Record<string, string>;
}

export function MatchList({ games, selectedGameId, baseQuery }: MatchListProps) {
  if (games.length === 0) {
    return (
      <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-low px-5 py-8 text-center text-sm text-se-on-surface-variant">
        선택한 기간에 원정 경기가 없습니다. 사이드바에서 기간을 넓혀보세요.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest">
      <table className="w-full text-sm">
        <thead className="bg-se-surface-container-low">
          <tr className="text-left font-display text-[0.72rem] uppercase tracking-[0.12em] text-se-on-surface-variant">
            <th className="px-4 py-3">날짜</th>
            <th className="px-4 py-3">요일</th>
            <th className="px-4 py-3">홈팀</th>
            <th className="px-4 py-3">구장</th>
            <th className="px-4 py-3">시간</th>
            <th className="px-4 py-3">중계</th>
          </tr>
        </thead>
        <tbody>
          {games.map((g) => {
            const selected = g.game_id === selectedGameId;
            const query = { ...baseQuery, game: g.game_id };
            return (
              <tr
                key={g.game_id}
                className={cn(
                  "border-t border-se-outline-variant transition-colors",
                  selected
                    ? "bg-se-secondary-fixed/30"
                    : "hover:bg-se-surface-container-low",
                )}
              >
                <td className="px-4 py-2.5 font-semibold text-se-primary">
                  <Link
                    href={{ pathname: "/matches", query }}
                    scroll={false}
                    className="no-underline text-se-primary"
                  >
                    {g.date}
                  </Link>
                </td>
                <td className="px-4 py-2.5 text-se-on-surface-variant">
                  {g.day_of_week}
                </td>
                <td className="px-4 py-2.5 font-semibold">{g.home_team}</td>
                <td className="px-4 py-2.5 text-se-on-surface">
                  {g.stadium}
                </td>
                <td className="px-4 py-2.5 tabular-nums">
                  {g.time ?? (g as unknown as { start_time?: string }).start_time ?? ""}
                </td>
                <td className="px-4 py-2.5 text-se-on-surface-variant">
                  {(g as unknown as { broadcast?: string }).broadcast ?? ""}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
