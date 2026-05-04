"use client";

import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import type { ChatMessage } from "@/lib/types";

export default function TeamChat({
  messages,
  currentUserId,
  connected,
  onSend,
}: {
  messages: ChatMessage[];
  currentUserId: string;
  connected: boolean;
  onSend: (text: string) => void;
}) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // 새 메시지 시 스크롤 하단 이동
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSend(input);
    setInput("");
  };

  const formatTime = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  };

  return (
    <div className="bg-surface-1 border border-outline/15 rounded-sm flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-outline/10">
        <div>
          <h3 className="text-sm font-heading font-bold text-text-primary uppercase tracking-[0.04em]">
            Team Chat
          </h3>
          <p
            className="text-[10px] text-text-tertiary"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            팀 채팅
          </p>
        </div>
        <span
          className={`flex items-center gap-1 text-[10px] font-mono ${
            connected ? "text-success" : "text-error"
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              connected ? "bg-success" : "bg-error"
            }`}
          />
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-[200px] max-h-[400px]"
      >
        {messages.length === 0 && (
          <p
            className="text-[11px] text-text-tertiary text-center py-8"
            style={{ fontFamily: "var(--font-ko)" }}
          >
            아직 메시지가 없습니다
            <br />
            팀원들과 대화를 시작해보세요!
          </p>
        )}

        {messages.map((msg) => {
          const isMe = msg.user_id === currentUserId;
          return (
            <div
              key={msg.id}
              className={`flex gap-2 ${isMe ? "flex-row-reverse" : ""}`}
            >
              {!isMe && (
                <span className="text-lg flex-shrink-0" aria-hidden>
                  {msg.avatar_emoji}
                </span>
              )}
              <div
                className={`max-w-[75%] ${isMe ? "text-right" : "text-left"}`}
              >
                {!isMe && (
                  <p className="text-[10px] text-text-tertiary font-bold mb-0.5">
                    {msg.user_name}
                  </p>
                )}
                <div
                  className={`inline-block px-3 py-1.5 rounded-lg text-[12px] leading-relaxed ${
                    isMe
                      ? "bg-primary/15 text-primary border border-primary/20"
                      : "bg-surface-2 text-text-primary border border-outline/10"
                  }`}
                  style={{ fontFamily: "var(--font-ko)" }}
                >
                  {msg.message}
                </div>
                <p className="text-[9px] text-text-tertiary mt-0.5 font-mono">
                  {formatTime(msg.created_at)}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Input */}
      <form
        onSubmit={submit}
        className="flex items-center gap-2 px-3 py-2.5 border-t border-outline/10"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="메시지 입력..."
          className="flex-1 bg-surface-2 border border-outline/15 rounded-sm px-3 py-2 text-[12px] text-text-primary outline-none focus:border-primary/40"
          style={{ fontFamily: "var(--font-ko)" }}
          disabled={!connected}
        />
        <button
          type="submit"
          disabled={!connected || !input.trim()}
          className="p-2 rounded-sm bg-primary text-background hover:bg-primary-dark transition-colors disabled:opacity-40"
        >
          <Send size={14} />
        </button>
      </form>
    </div>
  );
}
