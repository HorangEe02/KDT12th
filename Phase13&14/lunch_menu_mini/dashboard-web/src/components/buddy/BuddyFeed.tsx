"use client";

import { useState } from "react";
import { Users } from "lucide-react";
import type { BuddyPostOut } from "@/lib/types";
import BuddyCard from "./BuddyCard";

interface Props {
  posts: BuddyPostOut[];
  currentUserId: string | undefined;
  onJoin: (postId: number) => void;
  onLeave: (postId: number) => void;
  onClose: (postId: number) => void;
}

type Filter = "all" | "open";

export default function BuddyFeed({
  posts,
  currentUserId,
  onJoin,
  onLeave,
  onClose,
}: Props) {
  const [filter, setFilter] = useState<Filter>("open");

  const filtered =
    filter === "open"
      ? posts.filter((p) => p.status === "open" || p.status === "full")
      : posts;

  return (
    <div>
      {/* 필터 탭 */}
      <div className="flex items-center gap-2 mb-4">
        {(["open", "all"] as Filter[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-colors ${
              filter === f
                ? "bg-primary text-white"
                : "bg-surface-2 text-text-secondary hover:bg-surface-3"
            }`}
          >
            {f === "open" ? "모집중" : "전체"}
          </button>
        ))}
        <span className="text-xs text-text-tertiary ml-auto">
          {filtered.length}건
        </span>
      </div>

      {/* 카드 그리드 */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((post) => (
            <BuddyCard
              key={post.id}
              post={post}
              currentUserId={currentUserId}
              onJoin={onJoin}
              onLeave={onLeave}
              onClose={onClose}
            />
          ))}
        </div>
      ) : (
        <div className="bento-card--flat flex flex-col items-center justify-center py-16 text-center">
          <Users size={48} className="text-text-tertiary/30 mb-4" />
          <p className="text-sm text-text-tertiary font-bold uppercase tracking-wider">
            No buddy posts yet
          </p>
          <p
            className="text-xs text-text-tertiary mt-1"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            {filter === "open"
              ? "아직 모집중인 밥친구가 없어요. 첫 번째로 만들어보세요!"
              : "오늘 등록된 모집글이 없습니다."}
          </p>
        </div>
      )}
    </div>
  );
}
