import { ChatUI } from "@/components/ai/chat-ui";

export default function AIPage() {
  return (
    <section className="space-y-3">
      <header>
        <h1 className="font-display text-2xl font-extrabold text-se-primary">
          🤖 AI 플래너
        </h1>
        <p className="text-sm text-se-on-surface-variant">
          Gemini 2.5 Flash Lite · 6 tool calling · Multi-Agent · 🎬 Mock 시연 모드
        </p>
      </header>
      <ChatUI />
    </section>
  );
}
