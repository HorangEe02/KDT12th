"""
sentiment_analyzer.py
운동 일지 텍스트의 감성을 분석합니다.

방식 1: 규칙 기반 (키워드 매칭) — baseline, 즉시 사용 가능
방식 2: LLM 프롬프트 기반 (Ollama) — 정확도 높음
방식 3: KoBERT/KcBERT (향후 파인튜닝)
"""

import json
import re
from dataclasses import dataclass, field


@dataclass
class SentimentResult:
    """감성 분석 결과"""
    sentiment: str          # "긍정" | "부정" | "중립"
    confidence: float       # 0.0 ~ 1.0
    emotion_detail: str     # 세부 감정
    reason: str = ""        # 판단 이유
    model_used: str = ""


# ═══════════════════════════════════════
# 감정 키워드 사전
# ═══════════════════════════════════════

EMOTION_KEYWORDS = {
    "긍정": {
        "성취감": ["성공", "해냈", "올렸", "늘었", "달성", "신기록", "기록", "완주", "늘고"],
        "자신감": ["자신감", "뿌듯", "할 수 있", "대견", "잘 됐", "잘됐", "좋아진"],
        "즐거움": ["재밌", "즐거", "재미있", "같이", "함께", "신났", "웃", "ㅋㅋ"],
        "만족감": ["만족", "충분", "괜찮", "무리 없", "개운", "상쾌", "오운완"],
        "활력": ["에너지", "활력", "컨디션 좋", "힘이 나", "기분 좋"],
    },
    "부정": {
        "피로": ["피곤", "지쳤", "힘들", "체력 부족", "컨디션 안", "녹초", "기운 없"],
        "좌절": ["못 했", "실패", "포기", "안 됐", "늘지 않", "자괴감", "작심삼일", "안 빠"],
        "통증": ["아프", "통증", "쑤시", "결림", "부상", "저림", "뻐근"],
        "무기력": ["의욕 없", "귀찮", "하기 싫", "동기 없", "빠졌", "가기 싫"],
        "스트레스": ["스트레스", "짜증", "답답", "화나", "못 지켰"],
        "비교": ["다른 사람", "남들은", "나만", "왜 이렇게"],
    },
    "중립": {
        "일상": ["그냥", "보통", "무난", "평범", "루틴대로", "계획대로"],
        "기록": ["했다", "수행", "완료", "마무리"],
    },
}

# 강조 부사 (감성 강도 배율)
INTENSITY_BOOSTERS = {
    "너무": 1.3, "정말": 1.2, "매우": 1.2, "엄청": 1.3,
    "진짜": 1.2, "완전": 1.3, "겁나": 1.3, "개": 1.3,
}

INTENSITY_REDUCERS = {
    "조금": 0.7, "약간": 0.7, "살짝": 0.8, "좀": 0.8,
}


def analyze_sentiment_rule_based(text: str) -> SentimentResult:
    """
    규칙 기반으로 운동 일지 감성을 분석합니다.

    Args:
        text: 운동 일지 텍스트

    Returns:
        SentimentResult
    """
    scores = {"긍정": 0.0, "부정": 0.0, "중립": 0.0}
    matched_emotions = {}

    # 강도 배율 계산
    intensity = 1.0
    for word, mult in INTENSITY_BOOSTERS.items():
        if word in text:
            intensity = max(intensity, mult)
    for word, mult in INTENSITY_REDUCERS.items():
        if word in text:
            intensity = min(intensity, mult)

    # 키워드 매칭
    for sentiment, emotions in EMOTION_KEYWORDS.items():
        for emotion, keywords in emotions.items():
            for kw in keywords:
                if kw in text:
                    scores[sentiment] += intensity
                    matched_emotions.setdefault(sentiment, []).append(emotion)

    # 최종 감성 결정
    if max(scores.values()) == 0:
        return SentimentResult(
            sentiment="중립", confidence=0.5, emotion_detail="일상",
            reason="감성 키워드 미감지", model_used="rule_based",
        )

    best = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    confidence = round(scores[best] / total, 2)

    # 세부 감정 (가장 많이 매칭된 감정)
    emotions_list = matched_emotions.get(best, ["기타"])
    from collections import Counter
    most_common = Counter(emotions_list).most_common(1)[0][0]

    return SentimentResult(
        sentiment=best,
        confidence=min(confidence, 0.99),
        emotion_detail=most_common,
        reason=f"매칭: {dict(Counter(emotions_list))}",
        model_used="rule_based",
    )


def analyze_sentiment_with_llm(
    text: str,
    model: str = "exaone3.5",
    ollama_base_url: str = "http://localhost:11434/v1",
) -> SentimentResult:
    """
    LLM으로 운동 일지 감성을 분석합니다.
    """
    from openai import OpenAI

    prompt = f"""당신은 운동 심리 전문가입니다.

아래 운동 일지 텍스트의 감성을 분석해주세요.

운동 일지: "{text}"

아래 JSON으로만 응답하세요:
{{"sentiment": "<긍정|부정|중립>", "confidence": <0.0~1.0>, "emotion_detail": "<성취감|자신감|즐거움|만족감|활력|피로|좌절|통증|무기력|스트레스|일상 중 택1>", "reason": "<판단 이유 한 줄>"}}"""

    try:
        client = OpenAI(base_url=ollama_base_url, api_key="ollama")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()
        if "```" in content:
            content = content.split("```json")[-1].split("```")[0] if "```json" in content else content.split("```")[1].split("```")[0]

        data = json.loads(content.strip())

        return SentimentResult(
            sentiment=data.get("sentiment", "중립"),
            confidence=round(float(data.get("confidence", 0.5)), 2),
            emotion_detail=data.get("emotion_detail", "기타"),
            reason=data.get("reason", ""),
            model_used=f"llm_{model}",
        )

    except Exception as e:
        # LLM 실패 시 규칙 기반 폴백
        result = analyze_sentiment_rule_based(text)
        result.reason = f"LLM 폴백 ({str(e)[:30]}). " + result.reason
        return result


def analyze_weekly_sentiment(entries: list[dict], use_llm: bool = False) -> dict:
    """
    주간 일지 전체의 감성을 분석합니다.

    Args:
        entries: [{"date": "...", "text": "..."}, ...]
        use_llm: LLM 사용 여부

    Returns:
        {entries: [...], weekly_sentiment: {...}}
    """
    analyzer = analyze_sentiment_with_llm if use_llm else analyze_sentiment_rule_based
    results = []

    for entry in entries:
        result = analyzer(entry["text"])
        results.append({
            "date": entry.get("date", ""),
            "text": entry["text"],
            "sentiment": result.sentiment,
            "confidence": result.confidence,
            "emotion_detail": result.emotion_detail,
            "reason": result.reason,
            "model_used": result.model_used,
        })

    # 주간 통계
    sentiments = [r["sentiment"] for r in results]
    pos = sentiments.count("긍정")
    neg = sentiments.count("부정")
    neu = sentiments.count("중립")

    dominant = max(["긍정", "부정", "중립"], key=lambda s: sentiments.count(s))

    # 추세 (첫 절반 vs 후 절반)
    if len(sentiments) >= 2:
        mid = len(sentiments) // 2
        first_pos = sentiments[:mid].count("긍정")
        second_pos = sentiments[mid:].count("긍정")
        if second_pos > first_pos:
            trend = "상승"
        elif second_pos < first_pos:
            trend = "하락"
        else:
            trend = "유지"
    else:
        trend = "유지"

    return {
        "entries": results,
        "weekly_sentiment": {
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "dominant_sentiment": dominant,
            "trend": trend,
        },
    }
