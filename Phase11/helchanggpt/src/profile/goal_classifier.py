"""
goal_classifier.py
사용자의 텍스트에서 운동 목표 유형을 분류합니다.

방식 1: 키워드 기반 규칙 분류 (baseline)
방식 2: KcBERT Fine-tuning 분류 → goal_classifier_bert.py
방식 3: LLM 프롬프트 기반 분류 (비교 대상)
"""

from enum import Enum
from dataclasses import dataclass


class GoalType(Enum):
    FAT_LOSS = "체지방감소"
    MUSCLE_GAIN = "근력증가"
    FITNESS = "체력향상"
    WEIGHT_MGMT = "체중관리"
    HEALTH = "건강개선"


@dataclass
class GoalClassificationResult:
    """목표 분류 결과"""
    goal_type: GoalType
    confidence: float
    method: str       # "rule_based" | "kcbert" | "llm_openai" | "llm_exaone"
    reason: str = ""


# ═══════════════════════════════════════
# 방식 1: 키워드 기반 규칙 분류
# ═══════════════════════════════════════

GOAL_KEYWORDS: dict[GoalType, list[str]] = {
    GoalType.FAT_LOSS: [
        "체지방", "지방 감소", "지방 줄이", "살 빼", "살빼", "다이어트",
        "체중 감량", "몸무게 줄이", "마른", "날씬", "뱃살", "군살",
        "체중 감소", "몸무게 감소", "살 좀 빼", "체지방률 낮",
        "식스팩", "복근", "린", "커팅", "디파이닝",
    ],
    GoalType.MUSCLE_GAIN: [
        "근육", "근력", "벌크", "벌크업", "머슬",
        "팔뚝", "가슴 운동", "어깨 넓", "덩치", "몸 키우",
        "근비대", "무게 올리", "중량", "스트렝스",
        "벤치프레스", "데드리프트", "스쿼트",
    ],
    GoalType.FITNESS: [
        "체력", "스태미나", "지구력", "컨디션", "활력",
        "에너지", "운동 능력", "기초 체력",
        "마라톤", "달리기", "러닝", "숨이 차",
    ],
    GoalType.WEIGHT_MGMT: [
        "체중 관리", "유지", "현재 체중", "표준 체중",
        "적정 체중", "몸매 유지", "요요 방지",
        "몸매 관리", "건강하게 유지",
    ],
    GoalType.HEALTH: [
        "건강", "당뇨", "혈압", "혈당", "콜레스테롤",
        "관절", "재활", "회복", "수술 후",
        "건강 개선", "건강 관리", "만성질환",
    ],
}


def classify_goal_rule_based(text: str) -> GoalClassificationResult:
    """
    키워드 기반으로 운동 목표를 분류합니다.

    Args:
        text: 사용자 입력 텍스트

    Returns:
        GoalClassificationResult

    Examples:
        >>> result = classify_goal_rule_based("뱃살 빼고 식스팩 만들고 싶어요")
        >>> result.goal_type
        <GoalType.FAT_LOSS: '체지방감소'>
    """
    scores: dict[GoalType, int] = {}
    matched_keywords: dict[GoalType, list[str]] = {}

    for goal_type, keywords in GOAL_KEYWORDS.items():
        matches = [kw for kw in keywords if kw in text]
        scores[goal_type] = len(matches)
        matched_keywords[goal_type] = matches

    total = sum(scores.values())

    if total == 0:
        return GoalClassificationResult(
            goal_type=GoalType.WEIGHT_MGMT,
            confidence=0.3,
            method="rule_based",
            reason="매칭되는 키워드 없음, 기본값 적용",
        )

    best_goal = max(scores, key=scores.get)
    confidence = round(scores[best_goal] / total, 2)

    return GoalClassificationResult(
        goal_type=best_goal,
        confidence=confidence,
        method="rule_based",
        reason=f"매칭 키워드: {matched_keywords[best_goal]}",
    )


# ═══════════════════════════════════════
# 방식 3: LLM 프롬프트 기반 분류
# ═══════════════════════════════════════

GOAL_CLASSIFY_PROMPT = """당신은 피트니스 전문가입니다. 사용자의 운동 목표를 아래 5가지 유형 중 하나로 분류해주세요.

유형:
1. 체지방감소 - 살을 빼거나 체지방률을 낮추고 싶은 경우
2. 근력증가 - 근육량을 늘리거나 몸을 키우고 싶은 경우
3. 체력향상 - 기초 체력, 지구력, 활력을 높이고 싶은 경우
4. 체중관리 - 현재 체중을 유지하면서 몸매를 관리하고 싶은 경우
5. 건강개선 - 질환 관리나 건강 회복을 위해 운동하는 경우

사용자 입력: "{user_text}"

아래 JSON 형식으로만 응답하세요:
{{"goal_type": "<유형명>", "confidence": <0.0~1.0>, "reason": "<분류 이유 한 줄>"}}"""


def get_goal_classify_prompt(user_text: str) -> str:
    """LLM 분류용 프롬프트를 생성합니다."""
    return GOAL_CLASSIFY_PROMPT.format(user_text=user_text)


def classify_goal_with_ollama(
    text: str,
    model: str = "exaone3.5",
    temperature: float = 0.3,
) -> GoalClassificationResult:
    """
    Ollama LLM으로 운동 목표를 분류합니다.

    Args:
        text: 사용자 입력 텍스트
        model: Ollama 모델명 (exaone3.5, qwen3.5:9b 등)
        temperature: 생성 온도

    Returns:
        GoalClassificationResult

    Examples:
        >>> result = classify_goal_with_ollama("뱃살 빼고 싶어요", model="exaone3.5")
        >>> result.goal_type
        <GoalType.FAT_LOSS: '체지방감소'>
    """
    import json
    from ..utils.llm_client import LLMClient

    client = LLMClient()
    prompt = get_goal_classify_prompt(text)

    try:
        response = client.chat(
            model=model,
            message=prompt,
            temperature=temperature,
            max_tokens=200,
        )

        # JSON 파싱
        resp_text = response.strip()
        if resp_text.startswith("```"):
            resp_text = resp_text.split("\n", 1)[1]
            resp_text = resp_text.rsplit("```", 1)[0]

        data = json.loads(resp_text)

        goal_str = data.get("goal_type", "체중관리")
        confidence = float(data.get("confidence", 0.5))
        reason = data.get("reason", "")

        # GoalType enum 매핑
        goal_type = GoalType.WEIGHT_MGMT
        for gt in GoalType:
            if gt.value == goal_str:
                goal_type = gt
                break

        return GoalClassificationResult(
            goal_type=goal_type,
            confidence=round(confidence, 2),
            method=f"ollama_{model}",
            reason=reason,
        )

    except Exception as e:
        # LLM 실패 시 규칙 기반으로 폴백
        result = classify_goal_rule_based(text)
        result.reason = f"LLM 폴백 (에러: {str(e)[:50]}). " + result.reason
        return result
