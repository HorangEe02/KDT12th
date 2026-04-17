import Link from "next/link";
import type { Game, GameStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

interface MatchListProps {
  games: Game[];
  /** 해당 팀 기준 원정/홈 관계를 추론하기 위해 전달 */
  team: string;
  selectedGameId?: string;
  baseQuery: Record<string, string>;
}

const STATUS_META: Record<
  GameStatus,
  { icon: string; label: string; tone: string }
> = {
  SCHEDULED: { icon: "⏱", label: "예정", tone: "text-se-on-surface-variant" },
  IN_PROGRESS: { icon: "🔴", label: "진행", tone: "text-red-700" },
  FINISHED: { icon: "✅", label: "종료", tone: "text-se-on-surface" },
  CANCELED: { icon: "🚫", label: "취소", tone: "text-amber-700" },
};

function outcomeFor(team: string, g: Game): "W" | "L" | "D" | null {
  if (g.status !== "FINISHED" || !g.score) return null;
  const teamIsHome = g.home_team === team;
  const teamIsAway = g.away_team === team;
  if (!teamIsHome && !teamIsAway) return null;
  const teamScore = teamIsHome ? g.score.home : g.score.away;
  const oppScore = teamIsHome ? g.score.away : g.score.home;
  if (teamScore > oppScore) return "W";
  if (teamScore < oppScore) return "L";
  return "D";
}

function renderScoreCell(team: string, g: Game) {
  const meta = STATUS_META[g.status ?? "SCHEDULED"];
  if (g.status === "SCHEDULED") {
    return (
      <span className={cn("font-mono text-xs", meta.tone)}>
        {meta.icon} {g.start_time || g.time || "미정"}
      </span>
    );
  }
  if (g.status === "CANCELED") {
    return (
      <span className={cn("text-xs font-semibold", meta.tone)}>
        {meta.icon} 취소
      </span>
    );
  }
  const sc = g.score;
  if (!sc) {
    return <span className="text-xs text-se-on-surface-variant">—</span>;
  }
  const oc = outcomeFor(team, g);
  const ocColor =
    oc === "W"
      ? "bg-emerald-100 text-emerald-900"
      : oc === "L"
        ? "bg-red-100 text-red-900"
        : oc === "D"
          ? "bg-amber-100 text-amber-900"
          : "bg-se-surface-container-low text-se-on-surface";
  const isAway = g.away_team === team;
  // 응원팀 관점: "내 점수 - 상대 점수"
  const display = isAway
    ? `${sc.away}–${sc.home}`
    : `${sc.home}–${sc.away}`;
  return (
    <span className="flex items-center gap-1.5">
      <span className="font-mono text-sm font-bold tabular-nums">{display}</span>
      {oc ? (
        <span
          className={cn(
            "rounded-full px-1.5 py-0.5 text-[0.65rem] font-extrabold",
            ocColor,
          )}
        >
          {oc}
        </span>
      ) : null}
      {g.status === "IN_PROGRESS" && g.current_inning ? (
        <span className="rounded-full bg-red-50 px-1.5 py-0.5 text-[0.6rem] font-bold text-red-900">
          {g.current_inning}회
        </span>
      ) : null}
    </span>
  );
}

function renderPitcherCell(team: string, g: Game) {
  if (g.status === "SCHEDULED") {
    const isAway = g.away_team === team;
    const myPit = isAway ? g.away_pitcher : g.home_pitcher;
    const oppPit = isAway ? g.home_pitcher : g.away_pitcher;
    if (!myPit && !oppPit) {
      return <span className="text-xs text-se-on-surface-variant">선발 미정</span>;
    }
    return (
      <span className="text-xs text-se-on-surface-variant">
        <span className="font-semibold text-se-primary">{myPit || "?"}</span>
        <span className="mx-1">vs</span>
        <span>{oppPit || "?"}</span>
      </span>
    );
  }
  if (g.status === "FINISHED") {
    const parts: string[] = [];
    if (g.win_pitcher) parts.push(`승:${g.win_pitcher}`);
    if (g.lose_pitcher) parts.push(`패:${g.lose_pitcher}`);
    if (g.save_pitcher) parts.push(`세:${g.save_pitcher}`);
    return (
      <span className="text-xs text-se-on-surface-variant">
        {parts.join(" · ") || "—"}
      </span>
    );
  }
  return <span className="text-xs text-se-on-surface-variant">—</span>;
}

function formatBroadcast(b: Game["broadcast"]): string {
  if (!b) return "";
  if (Array.isArray(b)) return b.join(", ");
  return String(b);
}

export function MatchList({
  games,
  team,
  selectedGameId,
  baseQuery,
}: MatchListProps) {
  if (games.length === 0) {
    return (
      <div className="rounded-2xl border border-se-outline-variant bg-se-surface-container-low px-5 py-8 text-center text-sm text-se-on-surface-variant">
        선택한 기간에 원정 경기가 없습니다. 사이드바에서 기간을 넓혀보세요.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-se-outline-variant bg-se-surface-container-lowest">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="bg-se-surface-container-low">
          <tr className="text-left font-display text-[0.68rem] uppercase tracking-[0.12em] text-se-on-surface-variant">
            <th className="px-4 py-3">날짜</th>
            <th className="px-3 py-3">요일</th>
            <th className="px-4 py-3">vs 홈팀</th>
            <th className="px-3 py-3">구장</th>
            <th className="px-3 py-3">결과 · 시간</th>
            <th className="px-3 py-3">투수</th>
            <th className="px-3 py-3">중계</th>
          </tr>
        </thead>
        <tbody>
          {games.map((g) => {
            const selected = g.game_id === selectedGameId;
            const query = { ...baseQuery, game: g.game_id };
            const status = g.status ?? "SCHEDULED";
            return (
              <tr
                key={g.game_id}
                className={cn(
                  "border-t border-se-outline-variant transition-colors",
                  selected
                    ? "bg-se-secondary-fixed/30"
                    : "hover:bg-se-surface-container-low",
                  status === "CANCELED" && "opacity-50",
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
                <td className="px-3 py-2.5 text-se-on-surface-variant">
                  {g.day_of_week}
                </td>
                <td className="px-4 py-2.5 font-semibold">
                  {g.home_team}
                </td>
                <td className="px-3 py-2.5 text-se-on-surface">{g.stadium}</td>
                <td className="px-3 py-2.5">
                  {renderScoreCell(team, g)}
                </td>
                <td className="px-3 py-2.5">{renderPitcherCell(team, g)}</td>
                <td className="px-3 py-2.5 text-[0.7rem] text-se-on-surface-variant">
                  {formatBroadcast(g.broadcast)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
