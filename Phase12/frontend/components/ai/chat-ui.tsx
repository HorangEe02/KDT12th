"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useFilters } from "@/lib/store/filters";
import { getTeamPalette } from "@/lib/team-colors";
import { AiMobileView } from "./ai-mobile-view";
import { AiDesktopView } from "./ai-desktop-view";

/**
 * AI 챗 상태 컨테이너.
 * - useChat 훅과 입력 상태를 소유.
 * - AiMobileView (md:hidden) + AiDesktopView (hidden md:flex) 에 props 로 주입.
 * - 양쪽 뷰가 동시에 mount 되지만 visibility 토글이므로 하나만 보임.
 *   각 뷰가 자체 scrollRef 를 보유하여 자동 스크롤은 양쪽에 적용 (hidden 뷰는 no-op).
 */
export function ChatUI() {
  const filters = useFilters();
  const [multiAgent, setMultiAgent] = useState(false);
  const mobileScrollRef = useRef<HTMLDivElement>(null);
  const desktopScrollRef = useRef<HTMLDivElement>(null);

  const { messages, sendMessage, status, stop, error } = useChat({
    transport: new DefaultChatTransport({
      api: "/api/chat",
      prepareSendMessagesRequest: ({ messages, id }) => ({
        body: {
          id,
          messages,
          multiAgent,
          filters: {
            team: filters.team,
            dateRange: [filters.dateStart, filters.dateEnd],
            budget: filters.budget,
            party: filters.party,
            transport: filters.transport,
            demoMode: filters.demoMode,
          },
        },
      }),
    }),
  });

  const [input, setInput] = useState("");
  const busy = status === "submitted" || status === "streaming";

  useEffect(() => {
    for (const ref of [mobileScrollRef, desktopScrollRef]) {
      ref.current?.scrollTo({
        top: ref.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages.length, status]);

  function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    sendMessage({ text: trimmed });
    setInput("");
  }

  const palette = getTeamPalette(filters.team);

  const shared = {
    messages,
    busy,
    error,
    stop,
    submit,
    input,
    setInput,
    multiAgent,
    setMultiAgent,
    demoMode: filters.demoMode,
    teamLabel: palette.nameKo,
    teamColor: palette.color,
    dateStart: filters.dateStart,
    dateEnd: filters.dateEnd,
    budget: filters.budget,
  };

  return (
    <>
      <AiMobileView {...shared} scrollRef={mobileScrollRef} />
      <AiDesktopView {...shared} scrollRef={desktopScrollRef} />
    </>
  );
}
