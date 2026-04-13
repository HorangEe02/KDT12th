"""
profile_ner.py
사용자의 자연어 입력에서 신체 정보 엔티티를 추출합니다.

방식 1: 정규식 기반 규칙 NER (baseline, 높은 정확도)
방식 2: KoBERT/KcBERT NER (실험용, 향후 파인튜닝)
"""

import re
from dataclasses import dataclass, field


@dataclass
class ExtractedEntities:
    """자연어에서 추출된 엔티티"""
    age: int | None = None
    gender: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    exercise_frequency: int | None = None
    constraints: list[str] = field(default_factory=list)
    preferred_exercises: list[str] = field(default_factory=list)
    experience_level: str | None = None


# ── 정규식 기반 엔티티 추출 패턴 ──

ENTITY_PATTERNS = {
    "age": [
        r"(\d{1,2})\s*세",
        r"(\d{1,2})\s*살",
        r"나이\s*[:=]?\s*(\d{1,2})",
        r"만\s*(\d{1,2})\s*(?:세|살)",
    ],
    "age_decade": [
        r"(\d{2})대\s*(?:초반|중반|후반)?",
    ],
    "gender": [
        r"(남성|여성|남자|여자)",
        r"(남|여)\b",
    ],
    "height_cm": [
        r"(?:키|신장)\s*[:=]?\s*(\d{2,3}\.?\d*)\s*(?:cm|센티|센치)?",
        r"(\d{3})\s*cm",
        r"(\d{3}\.?\d*)\s*(?:센티|센치)",
    ],
    "weight_kg": [
        r"(?:몸무게|체중)\s*[:=]?\s*(\d{2,3}\.?\d*)\s*(?:kg|킬로)?",
        r"(\d{2,3}\.?\d*)\s*kg",
        r"(\d{2,3}\.?\d*)\s*(?:킬로)",
    ],
    "body_fat_percent": [
        r"체지방률?\s*[:=]?\s*(\d{1,2}\.?\d*)\s*%?",
        r"체지방\s*(\d{1,2}\.?\d*)\s*%",
    ],
    "exercise_frequency": [
        r"주\s*(\d)\s*회",
        r"주\s*(\d)\s*번",
        r"일주일에?\s*(\d)\s*(?:회|번|일)",
        r"(\d)\s*회.*주",
        r"주당\s*(\d)",
    ],
}

# ── 제약사항 키워드 사전 ──
CONSTRAINT_KEYWORDS = {
    "무릎 부상": ["무릎", "슬개골", "관절염", "반월판"],
    "허리 부상": ["허리", "디스크", "척추", "요통", "허리디스크"],
    "어깨 부상": ["어깨", "회전근개", "오십견"],
    "손목 부상": ["손목", "건초염", "손목터널"],
    "발목 부상": ["발목"],
    "당뇨": ["당뇨", "혈당", "인슐린"],
    "고혈압": ["고혈압", "혈압 높"],
    "고지혈증": ["고지혈", "콜레스테롤", "중성지방"],
    "심장질환": ["심장", "부정맥", "협심증"],
    "천식": ["천식", "호흡곤란"],
    "신장질환": ["신장", "콩팥", "투석"],
    "임산부": ["임신", "임산부", "태아"],
    "골다공증": ["골다공", "뼈 약"],
}

# ── 운동 경험 레벨 키워드 ──
EXPERIENCE_KEYWORDS = {
    "입문": ["처음", "시작", "입문", "초보", "모르", "경험 없", "생초보", "운동 안 해"],
    "초급": ["초급", "조금", "가끔", "몇 번", "얼마 안"],
    "중급": ["중급", "꾸준", "1년", "2년", "정기적", "헬스장 다"],
    "고급": ["고급", "전문", "선수", "대회", "5년 이상", "오래"],
}

# ── 선호 운동 키워드 ──
EXERCISE_KEYWORDS = {
    "웨이트트레이닝": ["웨이트", "헬스", "벤치프레스", "데드리프트", "스쿼트"],
    "유산소": ["유산소", "달리기", "러닝", "조깅", "자전거", "사이클"],
    "수영": ["수영", "수중"],
    "요가": ["요가", "필라테스"],
    "홈트레이닝": ["홈트", "홈트레이닝", "맨몸", "집에서"],
    "등산": ["등산", "산"],
    "크로스핏": ["크로스핏"],
    "격투기": ["복싱", "주짓수", "격투기", "무술"],
}


def _extract_age(text: str) -> int | None:
    """나이를 추출합니다."""
    # 정확한 나이 먼저
    for pattern in ENTITY_PATTERNS["age"]:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    # "30대" 등 10대 단위
    for pattern in ENTITY_PATTERNS["age_decade"]:
        match = re.search(pattern, text)
        if match:
            decade = int(match.group(0)[:2])
            suffix = match.group(0)[3:] if len(match.group(0)) > 3 else ""
            if "초반" in suffix:
                return decade + 2
            elif "후반" in suffix:
                return decade + 8
            else:
                return decade + 5  # 중반 또는 미지정 → 중간값
    return None


def _extract_gender(text: str) -> str | None:
    """성별을 추출합니다."""
    for pattern in ENTITY_PATTERNS["gender"]:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1)
            return "남성" if raw in ("남성", "남자", "남") else "여성"
    return None


def _extract_float(text: str, patterns: list[str]) -> float | None:
    """패턴 목록에서 첫 번째 매칭되는 float 값을 추출합니다."""
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    return None


def _extract_int(text: str, patterns: list[str]) -> int | None:
    """패턴 목록에서 첫 번째 매칭되는 int 값을 추출합니다."""
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def _extract_constraints(text: str) -> list[str]:
    """제약사항을 추출합니다."""
    found = []
    for constraint_name, keywords in CONSTRAINT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(constraint_name)
    return found


def _detect_experience_level(text: str) -> str:
    """운동 경험 수준을 파악합니다."""
    for level in ["고급", "중급", "초급", "입문"]:
        if any(kw in text for kw in EXPERIENCE_KEYWORDS[level]):
            return level
    return "입문"


def _detect_preferred_exercises(text: str) -> list[str]:
    """선호하는 운동 종류를 추출합니다."""
    found = []
    for exercise_type, keywords in EXERCISE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(exercise_type)
    return found


def extract_entities_rule_based(text: str) -> ExtractedEntities:
    """
    정규식 기반으로 자연어 텍스트에서 엔티티를 추출합니다.

    Args:
        text: 사용자 입력 자연어 텍스트

    Returns:
        ExtractedEntities 데이터클래스

    Examples:
        >>> result = extract_entities_rule_based(
        ...     "25세 남성이고 키 178cm에 몸무게 82kg입니다. 주 3회 운동 가능합니다."
        ... )
        >>> result.age
        25
        >>> result.gender
        '남성'
        >>> result.height_cm
        178.0
        >>> result.weight_kg
        82.0
        >>> result.exercise_frequency
        3
    """
    return ExtractedEntities(
        age=_extract_age(text),
        gender=_extract_gender(text),
        height_cm=_extract_float(text, ENTITY_PATTERNS["height_cm"]),
        weight_kg=_extract_float(text, ENTITY_PATTERNS["weight_kg"]),
        body_fat_percent=_extract_float(text, ENTITY_PATTERNS["body_fat_percent"]),
        exercise_frequency=_extract_int(text, ENTITY_PATTERNS["exercise_frequency"]),
        constraints=_extract_constraints(text),
        preferred_exercises=_detect_preferred_exercises(text),
        experience_level=_detect_experience_level(text),
    )
