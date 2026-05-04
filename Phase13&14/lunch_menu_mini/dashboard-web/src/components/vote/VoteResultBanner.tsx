"use client";

import type { Restaurant } from "@/lib/types";

export default function VoteResultBanner({
  winner,
  voteCount,
}: {
  winner: Restaurant | null;
  voteCount: number;
}) {
  if (!winner) return null;
  return (
    <div className="bg-success/10 border-2 border-success/40 rounded-sm p-5 text-center mb-4">
      <div className="text-4xl mb-1" aria-hidden>🎉</div>
      <div className="text-[11px] font-bold text-success uppercase tracking-[0.1em]">
        Today&apos;s Lunch
      </div>
      <p
        className="text-[10px] text-success/80"
        style={{ fontFamily: "var(--font-ko)" }}
      >
        오늘의 점심
      </p>
      <div className="text-2xl font-heading font-bold text-text-primary mt-2">
        {winner.name}
      </div>
      <div className="text-[12px] text-text-secondary mt-1 font-mono">
        {voteCount}표 · {winner.category} · {winner.distance}m
      </div>
    </div>
  );
}
