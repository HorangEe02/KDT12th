import { ChatUI } from "@/components/ai/chat-ui";

export default function AIPage() {
  return (
    <section className="space-y-3">
      {/* 데스크톱 전용 페이지 헤더 — 모바일은 AiMobileView 내부 헤더 사용 */}
      <header className="hidden md:block">
        <h1 className="font-display text-2xl font-extrabold text-se-primary">
          🤖 AI 챗봇
        </h1>
        <p className="text-sm text-se-on-surface-variant">
          Gemini 3.1 Flash Lite (Preview) · 9 tool calling · Multi-Agent · 🎬 Mock 시연 모드
        </p>
      </header>
      <ChatUI />
    </section>
  );
}
