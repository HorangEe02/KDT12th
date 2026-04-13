"""
keyword_extractor.py
사용자 입력에서 핵심 키워드를 추출합니다.

KeyBERT + 다국어 문장 임베딩 모델을 활용합니다.
"""

from dataclasses import dataclass


@dataclass
class KeywordResult:
    """키워드 추출 결과"""
    keywords: list[tuple[str, float]]  # [(키워드, 유사도 점수), ...]
    model_used: str


# ── 한국어 불용어 (피트니스 도메인) ──
KOREAN_STOPWORDS = [
    "저는", "제가", "이고", "입니다", "에요", "이에요", "인데",
    "하고", "싶어요", "싶습니다", "있습니다", "있어요",
    "것", "수", "때", "등", "좀", "약간", "정도",
    "그리고", "하지만", "그래서", "그런데",
]


def extract_keywords(
    text: str,
    top_n: int = 5,
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
) -> KeywordResult:
    """
    KeyBERT로 핵심 키워드를 추출합니다.

    Args:
        text: 사용자 입력 텍스트
        top_n: 추출할 키워드 수
        model_name: 사용할 sentence-transformers 모델

    Returns:
        KeywordResult 데이터클래스

    Examples:
        >>> result = extract_keywords(
        ...     "체지방을 줄이고 근육을 늘리고 싶어요. 주 3회 헬스장 운동 가능합니다."
        ... )
        >>> result.keywords[0][0]  # 첫 번째 키워드
        '체지방'
    """
    try:
        from keybert import KeyBERT

        kw_model = KeyBERT(model_name)

        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words=KOREAN_STOPWORDS,
            top_n=top_n,
            use_mmr=True,       # 다양성 확보 (Maximal Marginal Relevance)
            diversity=0.5,
        )

        return KeywordResult(
            keywords=keywords,
            model_used=model_name,
        )

    except ImportError:
        # KeyBERT 미설치 시 간단한 빈도 기반 추출로 폴백
        return _extract_keywords_fallback(text, top_n)


def _extract_keywords_fallback(text: str, top_n: int = 5) -> KeywordResult:
    """KeyBERT 미설치 시 간단한 키워드 추출 폴백."""
    import re

    # 피트니스 도메인 핵심 키워드
    FITNESS_TERMS = [
        "체지방", "근육", "다이어트", "벌크업", "체력", "유산소", "무산소",
        "단백질", "탄수화물", "칼로리", "운동", "헬스", "웨이트",
        "스쿼트", "데드리프트", "벤치프레스", "러닝", "수영",
        "체중", "감량", "증가", "관리", "건강", "재활",
        "무릎", "허리", "어깨", "당뇨", "고혈압",
    ]

    found = []
    for term in FITNESS_TERMS:
        if term in text:
            # 간단한 점수: 등장 위치가 앞쪽일수록 높은 점수
            pos = text.index(term)
            score = round(1.0 - (pos / max(len(text), 1)), 2)
            found.append((term, score))

    found.sort(key=lambda x: x[1], reverse=True)

    return KeywordResult(
        keywords=found[:top_n],
        model_used="fallback_frequency",
    )
