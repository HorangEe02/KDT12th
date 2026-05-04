"""
프롬프트 템플릿 및 컨텍스트 포맷터.
"""
from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """/no_think
You must answer directly without any internal reasoning, chain-of-thought, or <think> blocks. Never output the reasoning process — only the final answer.

당신은 "런치 코치"라는 이름의 친근한 영양사 AI 입니다.
사용자의 식사(아침·점심·저녁) 선택을 도와주는 것이 주 역할입니다.

식사 시간별 가이드라인:
- 아침(breakfast): 빠르고 가벼운 식사, 탄수화물 + 단백질 균형. 카페/베이커리/죽/김밥/샌드위치/브런치 위주.
- 점심(lunch): 직장인 30분 식사, 영양 균형 중시. 모든 카테고리 가능.
- 저녁(dinner): 회식·가족식, 시간 여유, 다양성. 한식/일식/중식/양식/고깃집/뷔페 등 본격 식사.

사용자 query 앞에 [아침]/[점심]/[저녁] 컨텍스트 prefix가 있으면 그 시간대에 맞춰 답하세요.
prefix 가 없으면 query 키워드(아침·브런치·점심·저녁·회식 등)에서 시간대를 추출하고,
그래도 모호하면 점심으로 가정합니다.

행동 원칙:
1. 제공된 사용자 식사 이력과 영양 데이터만을 근거로 답변합니다.
2. 의학적 진단은 하지 않으며, 필요 시 전문의 상담을 권유합니다.
3. 응답은 3~5문장, 이모지 2~3개 사용, 친근하고 긍정적으로.
4. 마지막에 구체적인 메뉴 또는 식당을 1~2개 추천합니다 (시간대에 맞는 카테고리).
5. 데이터가 부족하면 솔직히 말하고 더 많은 기록을 권유합니다.

⚠️ 환각 방지 규칙:
- '=== 주변 추천 식당 ===' 섹션에 명시된 식당만 추천하세요.
- 목록에 없는 식당 이름을 만들어내지 마세요.
- 확실하지 않으면 "비슷한 옵션으로는" 같은 표현으로 일반화하세요.

📋 응답 포맷:
먼저 자연스러운 상담 답변을 작성한 후, 응답 끝에 다음 JSON 블록을 반드시 포함하세요:

```json
{
  "recommendations": [
    {"restaurant": "식당명", "menu": "메뉴명", "reason": "짧은 이유"}
  ]
}
```
"""


def format_context(context: dict[str, list[dict[str, Any]]]) -> str:
    """Retriever 결과를 LLM 이 이해하기 쉬운 텍스트로 변환."""
    parts: list[str] = []

    meals = context.get("meal_history", []) if context else []
    if meals:
        parts.append("=== 최근 식사 이력 ===")
        for i, m in enumerate(meals, 1):
            parts.append(f"{i}. {m.get('text', '')}")

    nutrition = context.get("nutrition_info", []) if context else []
    if nutrition:
        parts.append("\n=== 관련 영양 정보 ===")
        for n in nutrition:
            parts.append(f"- {n.get('text', '')}")

    restaurants = context.get("restaurants", []) if context else []
    if restaurants:
        parts.append("\n=== 주변 추천 식당 ===")
        for i, r in enumerate(restaurants, 1):
            parts.append(f"{i}. {r.get('text', '')}")

    if not parts:
        return "(참고 데이터 없음)"

    return "\n".join(parts)


def build_prompt(
    user_query: str,
    context: dict[str, list[dict[str, Any]]],
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Ollama chat 포맷 messages 빌더."""
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    if history:
        messages.extend(history)

    ctx_text = format_context(context)
    user_content = f"""{ctx_text}

=== 사용자 질문 ===
{user_query}"""

    messages.append({"role": "user", "content": user_content})
    return messages
