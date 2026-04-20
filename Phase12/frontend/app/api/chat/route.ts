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
import {
  convertToModelMessages,
  generateText,
  streamText,
  stepCountIs,
  type UIMessage,
} from "ai";
import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { ALL_TOOLS } from "@/lib/ai/tools";

const google = createGoogleGenerativeAI({
  apiKey:
    process.env.GEMINI_API_KEY ?? process.env.GOOGLE_GENERATIVE_AI_API_KEY ?? "",
});

/**
 * Pre-flight 가용성 체크 — primary 모델이 preview 등 불안정 track 일 때만 실행.
 *
 * 동작:
 *   1. primary 에 1토큰 ping → 3초 timeout
 *   2. 성공 → primary 사용
 *   3. 실패 (429 high demand · timeout · 503 등) → fallback 모델로 자동 전환
 *
 * 비용:
 *   - primary 가 GA 모델 (이름에 "preview" 없음) 이면 **skip** (오버헤드 0)
 *   - preview 모델일 때만 매 요청 ~500ms 추가 (대신 전체 스트리밍 실패 방지)
 *
 * 향후 개선:
 *   - 모듈 스코프 캐시 (최근 60초 내 preview 상태 기억) → 반복 ping 최소화
 *   - Firestore 에 "last_fallback_at" 기록 → Cloud Run 인스턴스 간 공유
 */
async function selectWorkingModel(
  primary: string,
  fallback: string,
): Promise<{ model: string; switched: boolean; reason?: string }> {
  if (primary === fallback) return { model: primary, switched: false };
  if (!primary.toLowerCase().includes("preview")) {
    return { model: primary, switched: false };
  }
  try {
    await generateText({
      model: google(primary),
      prompt: "ping",
      maxRetries: 0,
      abortSignal: AbortSignal.timeout(3000),
    });
    return { model: primary, switched: false };
  } catch (err) {
    const reason = err instanceof Error ? err.message : "unknown";
    console.warn(
      `[chat] pre-flight failed on primary=${primary}, fallback=${fallback}: ${reason}`,
    );
    return { model: fallback, switched: true, reason };
  }
}
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

  const primaryModel =
    process.env.GEMINI_CHAT_MODEL ?? "gemini-2.5-flash-lite";
  const fallbackModel =
    process.env.GEMINI_FALLBACK_MODEL ?? "gemini-flash-lite-latest";
  const { model: selectedModel, switched } = await selectWorkingModel(
    primaryModel,
    fallbackModel,
  );
  if (switched) {
    console.log(
      `[chat] 🔄 auto-fallback: ${primaryModel} → ${selectedModel}`,
    );
  }

  const modelMessages = await convertToModelMessages(messages);
  const result = streamText({
    model: google(selectedModel),
    system,
    messages: modelMessages,
    tools: ALL_TOOLS,
    stopWhen: stepCountIs(5),
    temperature: multiAgent ? 0.55 : 0.7,
    // maxRetries 를 1 로 낮춰 preview 스로틀링 시 지연 누적 방지 (기본 2 → 최대 45s 대기).
    // 실패 시 pre-flight 가 이미 fallback 으로 전환했기 때문에 추가 재시도 불필요.
    maxRetries: 1,
  });

  return result.toUIMessageStreamResponse({
    onError: (err) => {
      const raw = err instanceof Error ? err.message : String(err);
      console.error("[chat] stream error:", raw);

      // "Please retry in X.Ys" 형태가 있으면 대기 시간 파싱
      const retryMatch = raw.match(/retry in ([\d.]+)s/i);
      const retrySec = retryMatch ? Math.ceil(parseFloat(retryMatch[1])) : null;

      // 무료 티어 quota 초과 (일당·분당)
      if (raw.includes("exceeded your current quota") || raw.includes("free_tier_requests")) {
        const wait = retrySec ? `약 ${retrySec}초` : "잠시";
        return `⏱️ AI 호출 한도 초과 — ${wait} 후 다시 시도해 주세요.\n\n💡 Multi-Agent 모드를 끄면 한 질문당 호출 수가 줄어 한도 여유가 생깁니다.`;
      }
      // Preview 모델 일시 스로틀링
      if (raw.includes("high demand") || raw.includes("temporarily")) {
        return "⚠️ 현재 AI 모델이 일시적으로 혼잡합니다. 잠시 후 다시 시도해 주세요.";
      }
      // 429 일반
      if (raw.includes("429")) {
        const wait = retrySec ? `약 ${retrySec}초` : "잠시";
        return `⚠️ 호출 빈도 제한에 걸렸습니다. ${wait} 후 다시 시도해 주세요.`;
      }
      // Timeout / abort
      if (raw.includes("timeout") || raw.includes("abort")) {
        return "⚠️ 응답 시간 초과. 질문을 다시 입력해 주세요.";
      }
      // 일반 — 원본에 "오류:" 이미 포함돼 있으면 중복 prefix 제거
      const clean = raw.replace(/^오류[:：]\s*/i, "").trim();
      return `오류: ${clean}`;
    },
  });
}
