"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Shuffle, CheckCircle2, RotateCcw, Send, MessageSquare } from "lucide-react";
import type { TeamMember, SlackNotifyResponse } from "@/lib/types";
import { TEAM } from "@/lib/mock";
import {
  useRestaurants,
  useNearbyRestaurants,
  useTeamMembers,
  useChatHistory,
  useVoteStatus,
} from "@/lib/queries";
import { apiFetchLunch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useGeolocation } from "@/lib/useGeolocation";
import { useTeamChat } from "@/lib/useTeamChat";
import VoterGrid from "@/components/vote/VoterGrid";
import VoteResultBanner from "@/components/vote/VoteResultBanner";
import VoteResultsChart, {
  type VoteRow,
} from "@/components/vote/VoteResultsChart";
import VisitHistory from "@/components/vote/VisitHistory";
import TeamChat from "@/components/vote/TeamChat";

export default function VotePage() {
  const currentUser = useAuth();
  const teamId = currentUser?.team_id ?? "team1";

  // 위치 기반 식당 풀 (Discovery 와 동일 패턴) — 좌표 미확보 시 전체 풀로 폴백
  const { position } = useGeolocation();
  const { data: nearby = [] } = useNearbyRestaurants(
    position?.lat,
    position?.lng,
    1500,
    50,
  );
  const { data: fallback = [] } = useRestaurants();
  const restaurants = nearby.length > 0 ? nearby : fallback;

  const { data: teamMembers } = useTeamMembers(teamId);
  const { data: chatHistory = [] } = useChatHistory(teamId);

  // 실시간 투표 현황 — 3초 폴링 (queries.ts useVoteStatus refetchInterval 단축됨)
  const { data: voteStatus, refetch: refetchVoteStatus } = useVoteStatus(teamId);

  // 팀 멤버: API 데이터 우선, 폴백은 목 데이터
  const memberIds = useMemo(() => {
    if (teamMembers && teamMembers.length > 0) {
      return teamMembers.map((m) => m.id).join(",");
    }
    return "";
  }, [teamMembers]);

  const [votes, setVotes] = useState<TeamMember[]>(() =>
    TEAM.map((t) => ({ ...t }))
  );
  const prevMemberIdsRef = useRef("");

  // API 멤버 데이터가 도착하면 votes 갱신 (기존 투표 유지)
  useEffect(() => {
    if (!memberIds || memberIds === prevMemberIdsRef.current) return;
    prevMemberIdsRef.current = memberIds;
    const members = teamMembers!;
    setVotes((prev) => {
      const voteMap = new Map(prev.filter((m) => m.vote != null).map((m) => [m.id, m.vote]));
      return members.map((m) => ({
        ...m,
        vote: voteMap.get(m.id) ?? null,
      }));
    });
  }, [memberIds, teamMembers]);

  const [showResult, setShowResult] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);

  // WebSocket 채팅
  const chat = useTeamChat({
    teamId,
    userId: currentUser?.id ?? "",
    userName: currentUser?.name ?? "",
    avatarEmoji: currentUser?.avatar_emoji ?? "🧑‍💻",
    initialMessages: chatHistory,
  });

  // voteStatus 가 도착하면 다른 팀원의 투표를 병합 (서버 권위)
  // 본인 투표는 옵티미스틱 업데이트가 우선이지만, 폴링 시 서버 값과 동기화
  useEffect(() => {
    const serverVotes = voteStatus?.votes;
    if (!serverVotes || serverVotes.length === 0) return;
    setVotes((prev) =>
      prev.map((m) => {
        const serverVote = serverVotes.find(
          (v) => String(v.user_id) === String(m.id),
        );
        return serverVote
          ? { ...m, vote: Number(serverVote.restaurant_id) }
          : m;
      }),
    );
  }, [voteStatus]);

  const handleVote = useCallback(
    async (memberId: string, restaurantId: number) => {
      // 본인만 투표 가능 검증
      if (currentUser && memberId !== currentUser.id) return;
      // 옵티미스틱 업데이트 — 즉시 UI 반영
      setVotes((prev) =>
        prev.map((m) => (m.id === memberId ? { ...m, vote: restaurantId } : m)),
      );
      // 백엔드 POST → 다른 팀원도 3초 내에 보게 됨
      try {
        await apiFetchLunch("/vote/cast", {
          method: "POST",
          body: JSON.stringify({
            user_id: memberId,
            restaurant_id: String(restaurantId),
          }),
        });
      } catch (e) {
        console.warn("[vote/cast] failed", e);
      } finally {
        // 성공/실패 상관없이 서버 상태로 재동기화
        refetchVoteStatus();
      }
    },
    [currentUser, refetchVoteStatus],
  );

  const randomVote = () => {
    if (restaurants.length === 0) return;
    setVotes((prev) =>
      prev.map((m) => ({
        ...m,
        vote: Number(
          restaurants[Math.floor(Math.random() * restaurants.length)].id
        ),
      }))
    );
  };

  const resetVotes = () => {
    setVotes((prev) => prev.map((m) => ({ ...m, vote: null })));
    setShowResult(false);
  };

  const rows: VoteRow[] = useMemo(() => {
    const counts = new Map<string | number, number>();
    for (const m of votes) {
      if (m.vote != null) {
        counts.set(m.vote, (counts.get(m.vote) ?? 0) + 1);
      }
    }
    return Array.from(counts.entries())
      .map(([id, voteCount]) => {
        const r = restaurants.find((x) => String(x.id) === String(id));
        return r ? { id: Number(id), name: r.name, voteCount } : null;
      })
      .filter((x): x is VoteRow => x !== null)
      .sort((a, b) => b.voteCount - a.voteCount);
  }, [votes, restaurants]);

  const winner =
    showResult && rows.length > 0
      ? restaurants.find((r) => String(r.id) === String(rows[0].id)) ?? null
      : null;
  const winnerVotes = rows[0]?.voteCount ?? 0;

  const [slackStatus, setSlackStatus] = useState<null | "sending" | "sent" | "failed">(null);
  const [slackError, setSlackError] = useState<string | null>(null);

  const notifySlack = async () => {
    if (!winner) return;
    setSlackStatus("sending");
    setSlackError(null);
    try {
      const res = await apiFetchLunch<SlackNotifyResponse>("/notify/slack", {
        method: "POST",
        body: JSON.stringify({
          event: "vote_result",
          title: "Today's Lunch Winner",
          body: `${winner.name} — ${winnerVotes}표 · ${winner.category} · ${winner.distance}m`,
          emoji: "🎉",
        }),
      });
      if (res.sent) {
        setSlackStatus("sent");
      } else {
        setSlackStatus("failed");
        setSlackError(res.error || "unknown error");
      }
    } catch (e) {
      setSlackStatus("failed");
      setSlackError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold text-text-primary uppercase tracking-tight">
            Team Vote
          </h1>
          <p className="text-xs text-text-tertiary uppercase tracking-[0.1em] mt-0.5">
            Democracy for Lunch
          </p>
          <p
            className="text-[11px] text-text-tertiary mt-0.5"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            팀원 투표 · 실시간 집계 · 최근 방문 이력
          </p>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 mb-5 flex-wrap">
        <button
          onClick={randomVote}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary text-background text-xs font-bold uppercase tracking-wider rounded-sm hover:bg-primary-dark transition-colors"
        >
          <Shuffle size={14} />
          Random Simulation
        </button>
        <button
          onClick={() => setShowResult(true)}
          className="flex items-center gap-2 px-4 py-2.5 border border-outline/25 text-xs font-bold uppercase tracking-wider rounded-sm text-text-primary hover:border-success/40 hover:text-success transition-colors"
        >
          <CheckCircle2 size={14} />
          Confirm Result
        </button>
        <button
          onClick={resetVotes}
          className="flex items-center gap-2 px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-text-tertiary hover:text-text-primary transition-colors"
        >
          <RotateCcw size={14} />
          Reset
        </button>
        <button
          onClick={() => setChatOpen((p) => !p)}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold uppercase tracking-wider rounded-sm border transition-colors ${
            chatOpen
              ? "border-primary/30 text-primary bg-primary/5"
              : "border-outline/25 text-text-tertiary hover:text-text-primary"
          }`}
        >
          <MessageSquare size={14} />
          Chat
        </button>
        {winner && (
          <button
            onClick={notifySlack}
            disabled={slackStatus === "sending"}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold uppercase tracking-wider rounded-sm border transition-colors ml-auto ${
              slackStatus === "sent"
                ? "border-success/40 text-success bg-success/10"
                : slackStatus === "failed"
                ? "border-error/40 text-error bg-error/10"
                : "border-outline/25 text-text-secondary hover:text-primary hover:border-primary/40"
            }`}
          >
            <Send size={14} />
            {slackStatus === "sending"
              ? "Sending..."
              : slackStatus === "sent"
              ? "Sent to Slack"
              : slackStatus === "failed"
              ? "Failed"
              : "Share to Slack"}
          </button>
        )}
      </div>
      {slackError && (
        <div className="text-[10px] text-error font-mono mb-3">
          Slack: {slackError}
        </div>
      )}

      {/* Main grid */}
      <div
        className={`grid grid-cols-1 gap-4 ${
          chatOpen ? "lg:grid-cols-7" : "lg:grid-cols-5"
        }`}
      >
        <div className="lg:col-span-3">
          <VoterGrid
            members={votes}
            restaurants={restaurants}
            onVote={handleVote}
            currentUserId={currentUser?.id}
          />
        </div>
        <div className="lg:col-span-2">
          <div className="bg-surface-1 border border-outline/15 rounded-sm p-5">
            <h3 className="text-base font-heading font-bold text-text-primary uppercase tracking-[0.04em] mb-1">
              Vote Results
            </h3>
            <p
              className="text-[11px] text-text-tertiary mb-4"
              style={{ fontFamily: "var(--font-ko)" }}
            >
              투표 결과
            </p>
            <VoteResultBanner winner={winner} voteCount={winnerVotes} />
            <VoteResultsChart rows={rows} />
          </div>
          <VisitHistory restaurants={restaurants} />
        </div>
        {chatOpen && (
          <div className="lg:col-span-2">
            <TeamChat
              messages={chat.messages}
              currentUserId={currentUser?.id ?? ""}
              connected={chat.connected}
              onSend={chat.sendMessage}
            />
          </div>
        )}
      </div>
    </div>
  );
}
