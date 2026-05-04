"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage } from "./types";
import { apiFetchLunch } from "./api";

interface UseTeamChatOptions {
  teamId: string;
  userId: string;
  userName: string;
  avatarEmoji: string;
  initialMessages?: ChatMessage[];
}

interface UseTeamChatReturn {
  messages: ChatMessage[];
  sendMessage: (text: string) => Promise<void>;
  connected: boolean;
}

/**
 * REST 폴링 기반 팀 채팅 훅.
 *
 * Cloudflare quick tunnel + Firebase 정적 호스팅 환경에서 WebSocket 핸드셰이크가
 * 불안정해 "Disconnected" 가 지속되는 문제 해결을 위해 REST 폴링 으로 재구현.
 *
 * - GET /api/chat/messages?team_id=&limit=50 으로 2.5초 간격 폴링
 * - POST /api/chat/messages 로 송신
 * - 탭 비활성 시 폴링 일시정지(visibilitychange)
 * - 마지막 polling 이 200 OK 이면 connected = true
 *
 * 백엔드 WS 엔드포인트(`/ws/chat/{team_id}`)와 같은 chat_messages 테이블을
 * 공유하므로 WS 클라이언트와 혼용 가능.
 */

const POLL_INTERVAL_MS = 2_500;

export function useTeamChat({
  teamId,
  userId,
  userName,
  avatarEmoji,
  initialMessages = [],
}: UseTeamChatOptions): UseTeamChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [connected, setConnected] = useState(true);
  const sendingRef = useRef(false);
  const initialAppliedRef = useRef(false);

  // initialMessages (히스토리) 1회 머지
  useEffect(() => {
    if (initialAppliedRef.current) return;
    if (initialMessages.length === 0) return;
    initialAppliedRef.current = true;
    setMessages((prev) => {
      if (prev.length > 0) return prev;
      return initialMessages;
    });
  }, [initialMessages]);

  // 폴링 루프 — 탭 visible 일 때만 동작
  useEffect(() => {
    if (!teamId) return;
    let cancelled = false;

    const fetchOnce = async () => {
      try {
        const list = await apiFetchLunch<ChatMessage[]>(
          `/chat/messages?team_id=${encodeURIComponent(teamId)}&limit=50`,
        );
        if (cancelled) return;
        setConnected(true);
        setMessages((prev) => {
          // 길이가 다르거나 마지막 id 가 다르면 갱신
          if (prev.length !== list.length) return list;
          const lastA = prev[prev.length - 1]?.id;
          const lastB = list[list.length - 1]?.id;
          return lastA === lastB ? prev : list;
        });
      } catch {
        if (!cancelled) setConnected(false);
      }
    };

    let timer: ReturnType<typeof setInterval> | null = null;
    const start = () => {
      if (timer != null) return;
      fetchOnce();
      timer = setInterval(fetchOnce, POLL_INTERVAL_MS);
    };
    const stop = () => {
      if (timer != null) {
        clearInterval(timer);
        timer = null;
      }
    };

    const onVisibility = () => {
      if (typeof document === "undefined") return;
      if (document.visibilityState === "visible") start();
      else stop();
    };

    start();
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", onVisibility);
    }

    return () => {
      cancelled = true;
      stop();
      if (typeof document !== "undefined") {
        document.removeEventListener("visibilitychange", onVisibility);
      }
    };
  }, [teamId]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || !teamId || sendingRef.current) return;
      sendingRef.current = true;
      try {
        const saved = await apiFetchLunch<ChatMessage>("/chat/messages", {
          method: "POST",
          body: JSON.stringify({
            team_id: teamId,
            user_id: userId,
            user_name: userName,
            avatar_emoji: avatarEmoji,
            message: trimmed,
          }),
        });
        setMessages((prev) => {
          // 중복 방지
          if (prev.some((m) => m.id === saved.id)) return prev;
          return [...prev, saved];
        });
        setConnected(true);
      } catch (e) {
        console.warn("[useTeamChat] send failed", e);
        setConnected(false);
      } finally {
        sendingRef.current = false;
      }
    },
    [teamId, userId, userName, avatarEmoji],
  );

  return { messages, sendMessage, connected };
}
