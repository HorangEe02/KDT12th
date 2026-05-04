"use client";

import type { Restaurant } from "@/lib/types";

export default function VisitHistory({
  restaurants,
}: {
  restaurants: Restaurant[];
}) {
  const recent = [...restaurants]
    .sort(
      (a, b) =>
        new Date(b.lastVisit).getTime() - new Date(a.lastVisit).getTime()
    )
    .slice(0, 5);

  return (
    <div className="mt-5 bg-surface-1 border border-outline/15 rounded-sm p-5">
      <h4 className="text-xs font-bold text-text-primary uppercase tracking-[0.08em] mb-3">
        Recent Visits{" "}
        <span
          className="text-[10px] font-normal normal-case tracking-normal text-text-tertiary"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          최근 방문 기록
        </span>
      </h4>
      <div className="divide-y divide-outline/10">
        {recent.map((r) => (
          <div
            key={r.id}
            className="flex items-center justify-between py-2 text-xs"
          >
            <span className="text-text-primary font-semibold">{r.name}</span>
            <span className="text-text-tertiary font-mono">
              {r.lastVisit} · {r.visits}회
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
