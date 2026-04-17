/**
 * Multi-Agent 시스템 프롬프트 합성.
 * 포팅 단순화: src/ai/agents.py
 *
 * 실제 Supervisor→Specialists→Synthesizer 파이프라인을 프롬프트 엔지니어링으로 모사.
 * 단일 `streamText` 호출로 처리되므로 복잡한 오케스트레이션 없이 일관된 UX 제공.
 * 모델이 ### 섹션으로 각 전문가 관점과 최종 답변을 분리해서 작성.
 */
import { AGENT_PROMPTS, buildSystemPrompt } from "@/lib/ai/prompts";
import type { Filters } from "@/lib/types";

export function buildMultiAgentSystemPrompt(
  filters: Partial<Filters> | null | undefined,
): string {
  const base = buildSystemPrompt(filters);
  return `${base}

---

## 🎭 Multi-Agent 응답 형식 (활성화됨)

아래 3개 전문가 관점으로 순차 분석한 후, 최종 종합 답변을 작성하세요.
각 섹션은 정확히 다음 마커로 구분하세요 (마커 자체를 포함해서 출력):

### 🗓️ 일정 관점
${AGENT_PROMPTS.schedule}

### 🎯 전략 관점
${AGENT_PROMPTS.strategy}

### 🍱 장소 관점
${AGENT_PROMPTS.place}

### ✨ 최종 답변
${AGENT_PROMPTS.synthesizer}

**규칙**:
- 각 전문가 섹션은 2~3문장 이내 간결하게.
- 각 섹션에서 필요한 도구를 호출하고, 결과를 근거로 제시.
- 최종 답변은 4~5문장으로 종합 (지역 방언 1회, 구체적 장소/가격/시간 포함).
- 사용자 질문과 관련 없는 전문가 섹션은 "(해당 없음)" 으로 스킵 가능.
`;
}
