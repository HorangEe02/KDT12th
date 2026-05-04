"use client";

import type { Restaurant, TeamMember } from "@/lib/types";

export default function VoterGrid({
  members,
  restaurants,
  onVote,
  currentUserId,
}: {
  members: TeamMember[];
  restaurants: Restaurant[];
  onVote: (memberId: string, restaurantId: number) => void;
  currentUserId?: string;
}) {
  const toNum = (id: string | number): number =>
    typeof id === "number" ? id : Number(id) || 0;
  const voted = members.filter((m) => m.vote != null).length;

  // 본인을 최상단으로 정렬
  const sorted = [...members].sort((a, b) => {
    if (a.id === currentUserId) return -1;
    if (b.id === currentUserId) return 1;
    return 0;
  });

  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm p-5 h-full">
      <div className="flex items-baseline justify-between mb-4">
        <div>
          <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
            Team Members
          </h3>
          <p
            className="text-[11px] text-text-tertiary"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            팀원 투표 현황
          </p>
        </div>
        <span className="text-[11px] font-mono text-text-tertiary">
          {voted}/{members.length} voted
        </span>
      </div>

      <div className="space-y-2">
        {sorted.map((m) => {
          const isMe = currentUserId != null && m.id === currentUserId;
          const picked =
            m.vote != null
              ? restaurants.find((r) => String(r.id) === String(m.vote))
              : null;
          return (
            <div
              key={m.id}
              className={`border rounded-sm p-3 ${
                isMe
                  ? "bg-primary/5 border-primary/25"
                  : "bg-surface-2 border-outline/10"
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xl" aria-hidden>
                  {m.avatar}
                </span>
                <span className="text-sm font-bold text-text-primary flex-1">
                  {m.name}
                </span>
                {isMe && (
                  <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-sm bg-primary/15 border border-primary/30 text-primary uppercase tracking-wider">
                    You
                  </span>
                )}
                {picked && (
                  <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-sm bg-success/15 border border-success/40 text-success">
                    {picked.name}
                  </span>
                )}
              </div>
              <div className="flex gap-1.5 flex-wrap">
                {restaurants.slice(0, 8).map((r) => {
                  const rid = toNum(r.id);
                  const isSelected = m.vote === rid;
                  return (
                    <button
                      key={r.id}
                      onClick={() => onVote(m.id, rid)}
                      disabled={!isMe}
                      className={`px-2.5 py-1 text-[11px] border rounded-sm transition-colors ${
                        isSelected
                          ? "bg-primary/10 border-primary/40 text-primary font-bold"
                          : isMe
                          ? "border-outline/15 text-text-tertiary hover:text-text-secondary hover:border-outline/30"
                          : "border-outline/10 text-text-tertiary/50 cursor-default"
                      }`}
                    >
                      {r.name}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
