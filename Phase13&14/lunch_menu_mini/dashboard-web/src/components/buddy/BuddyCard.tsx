"use client";

import { memo } from "react";
import { Clock, MapPin, X } from "lucide-react";
import type { BuddyPostOut } from "@/lib/types";
import BuddyStatusBadge from "./BuddyStatusBadge";
import BuddyJoinerList from "./BuddyJoinerList";

interface Props {
  post: BuddyPostOut;
  currentUserId: string | undefined;
  onJoin: (postId: number) => void;
  onLeave: (postId: number) => void;
  onClose: (postId: number) => void;
}

/** 카테고리별 이모지 매핑 */
const CAT_EMOJI: Record<string, string> = {
  한식: "🍚",
  중식: "🍜",
  일식: "🍣",
  양식: "🍝",
  분식: "🍱",
  카페: "☕",
  패스트푸드: "🍔",
};

function BuddyCard({ post, currentUserId, onJoin, onLeave, onClose }: Props) {
  const isAuthor = currentUserId === post.author_id;
  const hasJoined = post.joiners.some((j) => j.user_id === currentUserId);
  const isOpen = post.status === "open";
  const isFull = post.status === "full";
  const isActive = isOpen || isFull;

  // 진행률
  const progress =
    post.max_buddies > 0
      ? Math.round((post.current_buddies / post.max_buddies) * 100)
      : 0;

  const emoji = CAT_EMOJI[post.restaurant_name?.split(" ")[0]] ?? "🍽️";

  return (
    <div
      className={`bento-card p-4 transition-all ${
        !isActive ? "opacity-60" : ""
      }`}
    >
      {/* 상단: 식당 + 시간 + 상태 */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xl flex-shrink-0">{emoji}</span>
          <div className="min-w-0">
            <h3 className="text-sm font-bold text-text-primary truncate">
              {post.restaurant_name}
            </h3>
            <div className="flex items-center gap-2 text-[11px] text-text-tertiary mt-0.5">
              <span className="flex items-center gap-0.5">
                <Clock size={11} />
                {post.meal_time}
              </span>
              {post.restaurant_id && (
                <span className="flex items-center gap-0.5">
                  <MapPin size={11} />
                  식당
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <BuddyStatusBadge status={post.status} />
          {isAuthor && isActive && (
            <button
              onClick={() => onClose(post.id)}
              className="p-1 rounded hover:bg-error/10 text-text-tertiary hover:text-error transition-colors"
              title="모집 마감"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* 메시지 */}
      {post.message && (
        <p
          className="text-xs text-text-secondary mb-3 leading-relaxed"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          &ldquo;{post.message}&rdquo;
        </p>
      )}

      {/* 참여자 */}
      <div className="mb-3">
        <BuddyJoinerList
          joiners={post.joiners}
          maxBuddies={post.max_buddies}
          authorAvatar={post.author_avatar ?? "🧑‍💻"}
          authorName={post.author_name ?? post.author_id}
        />
      </div>

      {/* 진행률 바 */}
      <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden mb-3">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isFull ? "bg-warning" : "bg-primary"
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 액션 버튼 */}
      {!isAuthor && isOpen && !hasJoined && (
        <button
          onClick={() => onJoin(post.id)}
          className="w-full py-2 rounded-lg bg-primary hover:bg-primary-dark text-white text-xs font-bold uppercase tracking-wider transition-colors"
        >
          함께 가기
        </button>
      )}
      {!isAuthor && hasJoined && isActive && (
        <button
          onClick={() => onLeave(post.id)}
          className="w-full py-2 rounded-lg bg-surface-2 hover:bg-surface-3 text-text-secondary text-xs font-bold uppercase tracking-wider transition-colors"
        >
          참여 취소
        </button>
      )}
      {isAuthor && isActive && (
        <div
          className="text-center text-[10px] text-text-tertiary uppercase tracking-wider"
          style={{ fontFamily: "var(--font-ko)" }}
        >
          내가 만든 모집글
        </div>
      )}
    </div>
  );
}

export default memo(BuddyCard);
