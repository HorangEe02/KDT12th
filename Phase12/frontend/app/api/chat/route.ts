/**
 * POST /api/chat — AI 챗봇 스트리밍 엔드포인트.
 *
 * body:
 *   { messages: UIMessage[], filters?: Filters, multiAgent?: boolean }
 *
 * 분기:
 *   - filters.demoMode === true  → lib/ai/mock.ts 시나리오 매칭 시 즉시 텍스트 스트림
 *   - multiAgent === true        → Multi-Agent system prompt 로 단일 streamText
 *   - else                       → 일반 system prompt + 6 tools streamText
 */
import "server-only";
import { convertToModelMessages, streamText, stepCountIs, type UIMessage } from "ai";
import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { ALL_TOOLS } from "@/lib/ai/tools";

const google = createGoogleGenerativeAI({
  apiKey:
    process.env.GEMINI_API_KEY ?? process.env.GOOGLE_GENERATIVE_AI_API_KEY ?? "",
});
import { buildSystemPrompt } from "@/lib/ai/prompts";
import { buildMultiAgentSystemPrompt } from "@/lib/ai/agents";
import { pickMock } from "@/lib/ai/mock";
import type { Filters } from "@/lib/types";

export const runtime = "nodejs";
export const maxDuration = 60;

interface ChatBody {
  messages: UIMessage[];
  filters?: Partial<Filters>;
  multiAgent?: boolean;
}

function lastUserText(messages: UIMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const m = messages[i];
    if (m.role !== "user") continue;
    const parts = m.parts ?? [];
    const text = parts
      .map((p) =>
        p && typeof p === "object" && "type" in p && p.type === "text"
          ? (p as { text?: string }).text ?? ""
          : "",
      )
      .join(" ")
      .trim();
    if (text) return text;
  }
  return "";
}

function encodeTextStream(text: string): Response {
  // UIMessage 프로토콜 없이 순수 텍스트 스트림 (useChat transport 가 text 모드로 파싱)
  const stream = new ReadableStream({
    async start(controller) {
      const enc = new TextEncoder();
      const chunkSize = 16;
      for (let i = 0; i < text.length; i += chunkSize) {
        controller.enqueue(enc.encode(text.slice(i, i + chunkSize)));
        await new Promise((r) => setTimeout(r, 15));
      }
      controller.close();
    },
  });
  return new Response(stream, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}

export async function POST(request: Request) {
  let body: ChatBody;
  try {
    body = (await request.json()) as ChatBody;
  } catch {
    return Response.json({ error: "invalid-json" }, { status: 400 });
  }
  const { messages = [], filters, multiAgent = false } = body;
  const demoMode = filters?.demoMode ?? false;

  // === 시연 모드 (Mock) ===
  if (demoMode) {
    const query = lastUserText(messages);
    const sc = pickMock(query);
    if (sc) {
      return encodeTextStream(
        `[🎬 Mock · ${sc.title}]\n\n${sc.reply}`,
      );
    }
    return encodeTextStream(
      "[🎬 Mock] 매칭되는 시나리오가 없어 일반 안내를 반환합니다.\n시연 모드에선 광주/부산/우천 키워드를 포함해 주세요.",
    );
  }

  if (!process.env.GEMINI_API_KEY) {
    return encodeTextStream(
      "⚠️ GEMINI_API_KEY 가 설정되지 않아 AI 응답을 드릴 수 없어요.\n`.env.local` 에 키를 추가한 뒤 다시 시도해 주세요.",
    );
  }

  const system = multiAgent
    ? buildMultiAgentSystemPrompt(filters)
    : buildSystemPrompt(filters);

  const modelMessages = await convertToModelMessages(messages);
  const result = streamText({
    model: google(
      process.env.GEMINI_CHAT_MODEL ?? "gemini-2.5-flash-lite",
    ),
    system,
    messages: modelMessages,
    tools: ALL_TOOLS,
    stopWhen: stepCountIs(5),
    temperature: multiAgent ? 0.55 : 0.7,
  });

  return result.toUIMessageStreamResponse();
}
