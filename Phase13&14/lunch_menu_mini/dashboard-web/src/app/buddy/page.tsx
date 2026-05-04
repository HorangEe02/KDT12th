"use client";

import { useState, useEffect, useCallback } from "react";
import { Plus, RefreshCw, LogIn } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/lib/useAuth";
import {
  useBuddyPosts,
  useCreateBuddyPost,
  useJoinBuddyPost,
  useLeaveBuddyPost,
  useCloseBuddyPost,
  useRestaurants,
} from "@/lib/queries";
import { useTeamChat } from "@/lib/useTeamChat";
import BuddyFeed from "@/components/buddy/BuddyFeed";
import CreateBuddyModal from "@/components/buddy/CreateBuddyModal";

export default function BuddyPage() {
  const currentUser = useAuth();
  const teamId = currentUser?.team_id ?? "team1";
  const qc = useQueryClient();
  const router = useRouter();

  // 데이터
  const { data: posts = [], isLoading } = useBuddyPosts(teamId);
  const { data: restaurants = [] } = useRestaurants();

  // Mutations
  const createPost = useCreateBuddyPost();
  const joinPost = useJoinBuddyPost();
  const leavePost = useLeaveBuddyPost();
  const closePost = useCloseBuddyPost();

  // 모달
  const [showCreate, setShowCreate] = useState(false);

  // WebSocket — buddy_event 감지 (팀 채팅 WS 재활용)
  const chat = useTeamChat({
    teamId,
    userId: currentUser?.id ?? "",
    userName: currentUser?.name ?? "",
    avatarEmoji: currentUser?.avatar_emoji ?? "🧑‍💻",
  });
  useEffect(() => {
    if (!chat.messages.length) return;
    const last = chat.messages[chat.messages.length - 1];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if ((last as any).type === "buddy_event") {
      qc.invalidateQueries({ queryKey: ["buddy", "posts"] });
    }
  }, [chat.messages.length, qc]);

  // 핸들러
  const handleCreate = useCallback(
    (data: {
      restaurant_id?: string | null;
      restaurant_name: string;
      meal_time: string;
      max_buddies?: number;
      message?: string;
    }) => {
      if (!currentUser) return;
      createPost.mutate({
        team_id: teamId,
        author_id: currentUser.id,
        restaurant_id: data.restaurant_id,
        restaurant_name: data.restaurant_name,
        meal_time: data.meal_time,
        max_buddies: data.max_buddies ?? 3,
        message: data.message,
      });
    },
    [currentUser, teamId, createPost]
  );

  const handleJoin = useCallback(
    (postId: number) => {
      if (!currentUser) return;
      joinPost.mutate({ postId, userId: currentUser.id });
    },
    [currentUser, joinPost]
  );

  const handleLeave = useCallback(
    (postId: number) => {
      if (!currentUser) return;
      leavePost.mutate({ postId, userId: currentUser.id });
    },
    [currentUser, leavePost]
  );

  const handleClose = useCallback(
    (postId: number) => {
      if (!currentUser) return;
      closePost.mutate({
        postId,
        authorId: currentUser.id,
        status: "closed",
      });
    },
    [currentUser, closePost]
  );

  return (
    <div>
      {/* 헤더 */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary uppercase tracking-tight">
            Lunch Buddy
          </h1>
          <p className="text-xs text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            Find someone to eat with
          </p>
          <p
            className="text-[11px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            혼밥은 그만! 밥친구를 찾아보세요
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() =>
              qc.invalidateQueries({ queryKey: ["buddy", "posts"] })
            }
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-surface-2 hover:bg-surface-3 text-text-secondary text-xs font-bold transition-colors"
            title="새로고침"
          >
            <RefreshCw size={14} />
          </button>
          <button
            onClick={() => {
              if (!currentUser) {
                router.push("/login?mode=guest&next=/buddy");
                return;
              }
              setShowCreate(true);
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary-dark text-white text-xs font-bold uppercase tracking-wider transition-colors"
          >
            <Plus size={14} />
            <span>모집하기</span>
          </button>
        </div>
      </div>

      {/* 비로그인 안내 — 게스트로 즉시 시작할 수 있는 인라인 CTA */}
      {!currentUser && (
        <div
          className="mb-4 flex items-center gap-3 rounded-lg border border-primary/30 bg-primary/5 p-3"
          role="status"
        >
          <LogIn size={16} className="flex-shrink-0 text-primary" />
          <div className="flex-1 min-w-0">
            <p
              className="text-[12px] font-bold text-text-primary"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              로그인 후 사용 가능
            </p>
            <p
              className="text-[11px] text-text-tertiary"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              모집 글 작성·참여하려면 로그인이 필요합니다 (게스트로 1초 시작 가능).
            </p>
          </div>
          <Link
            href="/login?mode=guest&next=/buddy"
            className="flex-shrink-0 px-3 py-1.5 rounded-md bg-primary text-white text-[11px] font-bold uppercase tracking-wider hover:bg-primary-dark active:scale-95 transition-all"
          >
            게스트 시작
          </Link>
        </div>
      )}

      {/* 로딩 */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="bento-card--flat h-48 animate-pulse bg-surface-1"
            />
          ))}
        </div>
      ) : (
        <BuddyFeed
          posts={posts}
          currentUserId={currentUser?.id}
          onJoin={handleJoin}
          onLeave={handleLeave}
          onClose={handleClose}
        />
      )}

      {/* 모집글 작성 모달 */}
      <CreateBuddyModal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onSubmit={handleCreate}
        restaurants={restaurants}
      />
    </div>
  );
}
