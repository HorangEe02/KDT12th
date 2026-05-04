"""
LLM 프롬프트 빌더.
"""
from __future__ import annotations

from nlp_mvp.nlg_report.fact_extractor import WeeklyFacts

REPORT_SYSTEM_PROMPT = """당신은 친근한 영양 코치 "런치 코치"입니다.
직장인의 주간 식사 데이터를 바탕으로 격려와 인사이트가 담긴 리포트를 작성합니다.

작성 규칙:
1. **길이**: 3~5문장, 총 150~300자
2. **어투**: 존댓말 + 친근함 + 긍정적 격려
3. **이모지**: 2~3개 사용 (🍱 💪 😊 🥗 ✨ 🎉 등)
4. **구조**:
   - 첫 문장: 이번 주 전체에 대한 긍정적 코멘트
   - 중간: 잘한 점 1개 + 개선 포인트 1개
   - 마지막: 내일 추천 메뉴 1개 + 짧은 이유
5. **금기 사항**:
   - ❌ 의학적 단정 ("~병에 걸릴 수 있습니다")
   - ❌ 비판적 표현 ("나쁩니다", "잘못되었습니다")
   - ❌ 과도한 통계 나열 (3개 이상 숫자 금지)
   - ❌ 존재하지 않는 데이터 창작
6. **개선 제안 표현**:
   - ✅ "조금 더 채우면 좋을 것 같아요"
   - ✅ "내일은 ○○을 시도해볼까요?"
   - ❌ "단백질이 부족합니다"

데이터가 부족하면 솔직히 말하고 더 많은 기록을 권유하세요.
"""


def format_facts_for_user(facts: WeeklyFacts) -> str:
    """facts 를 LLM 에게 전달할 user content 로 변환."""
    if facts.is_empty():
        return (
            f"{facts.user_name}님의 {facts.week_label} 리포트를 작성해주세요.\n\n"
            "⚠️ 이번 주 식사 기록이 없습니다. "
            "기록을 독려하는 짧은 메시지를 작성해주세요."
        )

    if facts.is_sparse():
        return (
            f"{facts.user_name}님의 {facts.week_label} 리포트를 작성해주세요.\n\n"
            f"⚠️ 이번 주 식사 기록이 {facts.meal_count}건뿐이에요.\n"
            "데이터가 적다는 점을 자연스럽게 언급하면서, 격려의 메시지와 "
            "더 많은 기록을 권유하는 내용을 포함해주세요."
        )

    lack_str = ", ".join(facts.lack) if facts.lack else "없음"
    excess_str = ", ".join(facts.excess) if facts.excess else "없음"
    top_cats = ", ".join(f"{c}({n}회)" for c, n in facts.top_categories[:2]) or "없음"

    best_day_str = ""
    if facts.best_day:
        best_day_str = f"- 최고의 날: {facts.best_day['date']} ({facts.best_day['menu']})\n"

    worst_day_str = ""
    if facts.worst_day:
        worst_day_str = f"- 아쉬운 날: {facts.worst_day['date']} ({facts.worst_day['menu']})\n"

    sat_str = ""
    if facts.avg_satisfaction is not None:
        sat_str = f"- 평균 만족도: {facts.avg_satisfaction:.1f}/5\n"

    return (
        f"{facts.user_name}님의 {facts.week_label} 식사 요약입니다.\n\n"
        f"- 식사 수: {facts.meal_count}회\n"
        f"- 총 칼로리: {facts.total_calories:.0f} kcal\n"
        f"- 평균 단백질: {facts.avg_protein:.0f}g (일일 목표 {facts.target_protein:.0f}g)\n"
        f"- 부족: {lack_str}\n"
        f"- 과다: {excess_str}\n"
        f"{best_day_str}"
        f"{worst_day_str}"
        f"{sat_str}"
        f"- 자주 먹은 카테고리: {top_cats}\n\n"
        "위 정보를 바탕으로 3~5문장의 친근한 리포트를 작성해주세요."
    )


def build_report_prompt(facts: WeeklyFacts) -> list[dict[str, str]]:
    """Ollama chat messages 형식."""
    return [
        {"role": "system", "content": REPORT_SYSTEM_PROMPT},
        {"role": "user", "content": format_facts_for_user(facts)},
    ]
