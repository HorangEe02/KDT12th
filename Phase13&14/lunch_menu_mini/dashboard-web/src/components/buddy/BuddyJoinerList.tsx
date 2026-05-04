"use client";

import type { BuddyJoiner } from "@/lib/types";

interface Props {
  joiners: BuddyJoiner[];
  maxBuddies: number;
  authorAvatar: string;
  authorName: string;
}

export default function BuddyJoinerList({
  joiners,
  maxBuddies,
  authorAvatar,
  authorName,
}: Props) {
  const emptySlots = Math.max(0, maxBuddies - joiners.length);

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {/* 작성자 (항상 첫 번째) */}
      <div className="relative group" title={authorName}>
        <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/20 text-sm ring-2 ring-primary/40">
          {authorAvatar}
        </span>
        <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-primary rounded-full border border-surface-1" />
      </div>

      <span className="text-text-tertiary text-xs mx-0.5">+</span>

      {/* 참여자들 */}
      {joiners.map((j) => (
        <div key={j.user_id} className="relative group" title={j.user_name}>
          <span className="flex items-center justify-center w-8 h-8 rounded-full bg-secondary/20 text-sm ring-2 ring-secondary/40">
            {j.avatar_emoji}
          </span>
        </div>
      ))}

      {/* 빈 슬롯 */}
      {Array.from({ length: emptySlots }).map((_, i) => (
        <span
          key={`empty-${i}`}
          className="flex items-center justify-center w-8 h-8 rounded-full border-2 border-dashed border-outline/25 text-text-tertiary text-xs"
        >
          ?
        </span>
      ))}

      {/* 카운트 */}
      <span className="text-xs text-text-secondary ml-1">
        {joiners.length}/{maxBuddies}명
      </span>
    </div>
  );
}
