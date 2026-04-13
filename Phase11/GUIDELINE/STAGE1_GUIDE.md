# 🏋️ 기(起) — 나를 알자 | 구현 가이드라인

## 📌 개요

이 문서는 **헬창지피티(HelChangGPT)** 프로젝트의 **1단계: 사용자 프로필 분석** 구현을 위한
구현 가이드라인입니다.

사용자가 **인바디(InBody) 측정 결과 이미지**를 업로드하거나 **자연어로 신체 정보를 입력**하면,
NLP 기법을 활용하여 구조화된 프로필을 생성하고, 이후 단계(식단/운동/피드백)로 전달합니다.

---

## 1. 입력 데이터 형태

사용자는 두 가지 방식으로 자신의 정보를 제공할 수 있습니다.

### 1-1. 인바디 이미지 업로드

인바디 용지에서 추출해야 할 핵심 데이터 필드는 다음과 같습니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    InBody 측정 결과지                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [기본 정보]                                                 │
│  ├─ 신장(cm), 연령, 성별, 검사일시                            │
│                                                             │
│  [체성분분석 Body Composition Analysis]                       │
│  ├─ 체수분(L), 단백질(kg), 무기질(kg)                         │
│  ├─ 체지방량(kg), 체중(kg)                                   │
│                                                             │
│  [골격근·지방분석 Muscle-Fat Analysis]                        │
│  ├─ 체중(kg), 골격근량(kg), 체지방량(kg)                      │
│                                                             │
│  [비만분석 Obesity Analysis]                                  │
│  ├─ BMI(kg/m²), 체지방률(%)                                  │
│                                                             │
│  [체중조절 Weight Control]                                   │
│  ├─ 적정체중(kg), 체중조절(kg)                                │
│  ├─ 지방조절(kg), 근육조절(kg)                                │
│                                                             │
│  [연구항목 Research Parameters]                               │
│  ├─ 제지방량(kg), 기초대사량(kcal)                             │
│  ├─ 비만도(%), 권장섭취열량(kcal)                              │
│                                                             │
│  [비만평가 Obesity Evaluation]                                │
│  ├─ BMI 판정, 체지방률 판정                                   │
│  ├─ 복부지방률(WHR), 내장지방레벨                              │
│                                                             │
│  [인바디점수 InBody Score]                                    │
│  ├─ 종합점수 (/100)                                          │
│                                                             │
│  [신체변화 Body Composition History]                          │
│  ├─ 체중/골격근량/체지방률 변화 추이                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 인바디 데이터 예시 (위 이미지 기준)

```json
{
  "basic_info": {
    "name": "Jane Doe",
    "height_cm": 156.9,
    "age": 51,
    "gender": "여성",
    "test_date": "2015-05-04T09:46:00"
  },
  "body_composition": {
    "body_water_L": 27.2,
    "protein_kg": 7.1,
    "minerals_kg": 2.74,
    "body_fat_mass_kg": 22.1,
    "weight_kg": 59.1
  },
  "muscle_fat_analysis": {
    "weight_kg": 59.1,
    "skeletal_muscle_mass_kg": 19.3,
    "body_fat_mass_kg": 22.1
  },
  "obesity_analysis": {
    "bmi": 24.0,
    "body_fat_percent": 37.5
  },
  "weight_control": {
    "ideal_weight_kg": 52.9,
    "weight_adjustment_kg": -6.2,
    "fat_adjustment_kg": -10.0,
    "muscle_adjustment_kg": 3.8
  },
  "research_params": {
    "lean_body_mass_kg": 37.0,
    "bmr_kcal": 1168,
    "obesity_degree_percent": 112,
    "recommended_intake_kcal": 1397
  },
  "obesity_evaluation": {
    "bmi_category": "표준",
    "body_fat_category": "비만",
    "waist_hip_ratio": 0.98,
    "visceral_fat_level": 13
  },
  "inbody_score": 66
}
```

### 1-2. 자연어 텍스트 입력

인바디가 없는 사용자를 위한 자연어 입력도 지원합니다.

```
입력 예시들:

(A) "25세 남성이고 키 178cm에 몸무게 82kg입니다. 
     체지방을 줄이고 근육을 늘리고 싶어요. 주 3회 운동 가능합니다."

(B) "30대 여자, 163cm 58kg이에요. 
     최근에 살이 많이 쪄서 다이어트하고 싶습니다. 
     운동은 처음이라 쉬운 것부터 시작하고 싶어요."

(C) "45세 남성 172cm 90kg 당뇨 전단계 진단받았습니다.
     건강을 위해 체중 감량이 필요합니다.
     무릎이 안 좋아서 달리기는 어렵습니다."
```

---

## 2. 출력 데이터 구조

1단계의 최종 출력은 2~4단계에서 사용할 **구조화된 사용자 프로필 JSON** 입니다.

```python
# 최종 프로필 스키마
USER_PROFILE_SCHEMA = {
    # ── 기본 신체 정보 ──
    "basic": {
        "name": str,           # 사용자명 (선택)
        "age": int,            # 나이
        "gender": str,         # "남성" | "여성"
        "height_cm": float,    # 키 (cm)
        "weight_kg": float,    # 체중 (kg)
    },
    
    # ── 체성분 데이터 (인바디 있을 때) ──
    "body_composition": {
        "skeletal_muscle_mass_kg": float,  # 골격근량
        "body_fat_mass_kg": float,         # 체지방량
        "body_fat_percent": float,         # 체지방률 (%)
        "bmi": float,                      # BMI
        "bmr_kcal": int,                   # 기초대사량
        "lean_body_mass_kg": float,        # 제지방량
        "visceral_fat_level": int,         # 내장지방레벨
        "waist_hip_ratio": float,          # 복부지방률
        "inbody_score": int,               # 인바디 점수
    },
    
    # ── 자동 계산 지표 ──
    "calculated": {
        "bmi": float,                      # 직접 계산한 BMI
        "bmi_category": str,               # "저체중|표준|과체중|비만"
        "bmr_kcal": int,                   # 해리스-베네딕트 공식 기반
        "tdee_kcal": int,                  # 총 일일 에너지 소비량
        "recommended_intake_kcal": int,    # 목표 기반 권장 섭취량
        "ideal_weight_kg": float,          # 적정 체중
    },
    
    # ── NLP 분석 결과 ──
    "nlp_analysis": {
        "goal_type": str,         # "체지방감소|근력증가|체력향상|체중관리|건강개선"
        "goal_keywords": list,    # 추출된 목표 키워드
        "constraints": list,      # 제약사항 (부상, 질환 등)
        "experience_level": str,  # "입문|초급|중급|고급"
        "exercise_frequency": int, # 주당 운동 가능 횟수
        "preferred_exercises": list, # 선호 운동 (있을 경우)
    },
    
    # ── 인바디 기반 권장사항 ──
    "recommendations": {
        "weight_adjustment_kg": float,   # 체중 조절 목표
        "fat_adjustment_kg": float,      # 지방 조절 목표
        "muscle_adjustment_kg": float,   # 근육 조절 목표
        "priority": str,                 # "지방감량우선|근육증가우선|균형관리"
    },
    
    # ── 메타데이터 ──
    "meta": {
        "input_type": str,       # "inbody_image" | "natural_language" | "both"
        "has_inbody": bool,      # 인바디 데이터 존재 여부
        "created_at": str,       # ISO 8601 타임스탬프
        "model_used": str,       # 사용한 LLM/NLP 모델명
    }
}
```

---

## 3. 구현 모듈 상세

### 3-1. 인바디 이미지 파싱 모듈

인바디 이미지에서 데이터를 추출하는 두 가지 방식을 구현합니다.

#### 방식 A: LLM 비전 기능 활용 (권장)

```python
"""
inbody_parser_llm.py
LLM의 비전(Vision) 기능을 활용하여 인바디 이미지에서 데이터를 추출합니다.
EXAONE과 OpenAI 두 모델의 결과를 비교합니다.
"""

import base64
import json
from openai import OpenAI

# ── 인바디 이미지 파싱 프롬프트 ──
INBODY_PARSE_PROMPT = """
당신은 InBody(인바디) 체성분 분석 결과지를 정확하게 읽는 전문가입니다.

아래 인바디 측정 결과지 이미지에서 다음 정보를 정확히 추출하여 JSON 형식으로 반환해주세요.
숫자는 반드시 이미지에 표시된 그대로 입력하세요. 없는 항목은 null로 표시하세요.

반환 형식:
{
  "basic_info": {
    "height_cm": <키(cm) 숫자>,
    "age": <연령 숫자>,
    "gender": "<성별: 남성 또는 여성>",
    "test_date": "<검사일시 YYYY-MM-DD>"
  },
  "body_composition": {
    "body_water_L": <체수분(L)>,
    "protein_kg": <단백질(kg)>,
    "minerals_kg": <무기질(kg)>,
    "body_fat_mass_kg": <체지방량(kg)>,
    "weight_kg": <체중(kg)>
  },
  "muscle_fat_analysis": {
    "skeletal_muscle_mass_kg": <골격근량(kg)>,
    "body_fat_mass_kg": <체지방량(kg)>
  },
  "obesity_analysis": {
    "bmi": <BMI 숫자>,
    "body_fat_percent": <체지방률(%)>
  },
  "weight_control": {
    "ideal_weight_kg": <적정체중(kg)>,
    "weight_adjustment_kg": <체중조절(kg) 부호 포함>,
    "fat_adjustment_kg": <지방조절(kg) 부호 포함>,
    "muscle_adjustment_kg": <근육조절(kg) 부호 포함>
  },
  "research_params": {
    "lean_body_mass_kg": <제지방량(kg)>,
    "bmr_kcal": <기초대사량(kcal)>,
    "obesity_degree_percent": <비만도(%)>,
    "recommended_intake_kcal": <권장섭취열량(kcal)>
  },
  "obesity_evaluation": {
    "bmi_category": "<BMI 판정: 저체중/표준/과체중/심한과체중>",
    "body_fat_category": "<체지방률 판정: 표준/경도비만/비만>",
    "waist_hip_ratio": <복부지방률 숫자>,
    "visceral_fat_level": <내장지방레벨 숫자>
  },
  "inbody_score": <인바디점수 숫자>
}

JSON만 반환하세요. 다른 설명은 넣지 마세요.
"""


def encode_image_to_base64(image_path: str) -> str:
    """이미지 파일을 base64 문자열로 인코딩합니다."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def parse_inbody_with_openai(image_path: str, api_key: str) -> dict:
    """
    OpenAI GPT-4o Vision으로 인바디 이미지를 파싱합니다.
    
    Args:
        image_path: 인바디 이미지 파일 경로
        api_key: OpenAI API 키
    
    Returns:
        파싱된 인바디 데이터 딕셔너리
    """
    client = OpenAI(api_key=api_key)
    base64_image = encode_image_to_base64(image_path)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": INBODY_PARSE_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        temperature=0.1,  # 정확한 숫자 추출을 위해 낮은 temperature
        max_tokens=2000
    )
    
    result_text = response.choices[0].message.content
    
    # JSON 파싱 (코드블록 제거)
    result_text = result_text.strip()
    if result_text.startswith("```"):
        result_text = result_text.split("\n", 1)[1]
        result_text = result_text.rsplit("```", 1)[0]
    
    return json.loads(result_text)


def parse_inbody_with_exaone(image_path: str, api_key: str) -> dict:
    """
    EXAONE Vision으로 인바디 이미지를 파싱합니다.
    (API 엔드포인트와 모델명은 EXAONE 버전에 따라 조정 필요)
    
    구현 구조는 OpenAI 버전과 동일하며, 
    엔드포인트와 모델명만 변경합니다.
    """
    # EXAONE API 연동 구현
    # base_url, model 등을 EXAONE에 맞게 설정
    pass
```

#### 방식 B: OCR + 정규식 파싱 (보조)

```python
"""
inbody_parser_ocr.py
OCR(Tesseract/EasyOCR)로 텍스트를 추출한 뒤, 정규식으로 파싱합니다.
LLM Vision의 보조 수단 또는 비교 대상으로 사용합니다.
"""

import re
import easyocr

# ── 인바디 필드별 정규식 패턴 ──
INBODY_PATTERNS = {
    "height_cm": r"신장\s*(\d+\.?\d*)\s*cm",
    "age": r"연령\s*(\d+)",
    "gender": r"성별\s*(남성|여성|남|여)",
    "weight_kg": r"체중\s*(?:\(kg\))?\s*(\d+\.?\d*)",
    "skeletal_muscle_mass_kg": r"골격근량\s*(?:\(kg\))?\s*(\d+\.?\d*)",
    "body_fat_mass_kg": r"체지방량\s*(?:\(kg\))?\s*(\d+\.?\d*)",
    "bmi": r"BMI\s*(?:\(kg/m²\))?\s*(\d+\.?\d*)",
    "body_fat_percent": r"체지방률\s*(?:\(%\))?\s*(\d+\.?\d*)",
    "bmr_kcal": r"기초대사량\s*(\d+)\s*kcal",
    "recommended_intake_kcal": r"권장섭취열량\s*(\d+)\s*kcal",
    "inbody_score": r"인바디점수\s*(\d+)",
    "waist_hip_ratio": r"복부지방률\s*(\d+\.?\d*)",
    "visceral_fat_level": r"내장지방레벨\s*(\d+)",
    "ideal_weight_kg": r"적정체중\s*(\d+\.?\d*)\s*kg",
    "weight_adjustment_kg": r"체중조절\s*(-?\+?\d+\.?\d*)\s*kg",
    "fat_adjustment_kg": r"지방조절\s*(-?\+?\d+\.?\d*)\s*kg",
    "muscle_adjustment_kg": r"근육조절\s*(-?\+?\d+\.?\d*)\s*kg",
}


def extract_text_from_image(image_path: str) -> str:
    """EasyOCR로 인바디 이미지에서 텍스트를 추출합니다."""
    reader = easyocr.Reader(["ko", "en"])
    results = reader.readtext(image_path, detail=0)
    return " ".join(results)


def parse_inbody_with_regex(ocr_text: str) -> dict:
    """정규식으로 OCR 텍스트에서 인바디 데이터를 추출합니다."""
    parsed = {}
    for field, pattern in INBODY_PATTERNS.items():
        match = re.search(pattern, ocr_text)
        if match:
            value = match.group(1)
            # 숫자 변환
            try:
                parsed[field] = float(value) if "." in value else int(value)
            except ValueError:
                parsed[field] = value
        else:
            parsed[field] = None
    return parsed
```

### 3-2. 자연어 입력 분석 모듈

#### NER (개체명 인식)

```python
"""
profile_ner.py
사용자의 자연어 입력에서 신체 정보 엔티티를 추출합니다.
"""

import re
from dataclasses import dataclass, field


@dataclass
class ExtractedEntities:
    """자연어에서 추출된 엔티티"""
    age: int = None
    gender: str = None
    height_cm: float = None
    weight_kg: float = None
    exercise_frequency: int = None    # 주당 횟수
    constraints: list = field(default_factory=list)
    preferred_exercises: list = field(default_factory=list)


# ── 정규식 기반 엔티티 추출 (Rule-based NER) ──
# BERT 모델 적용 전 기본 추출기로 사용

ENTITY_PATTERNS = {
    "age": [
        r"(\d{1,2})\s*세",
        r"(\d{1,2})\s*살",
        r"나이\s*(\d{1,2})",
        r"(\d{2})대",  # "30대" → 35로 중간값 처리
    ],
    "gender": [
        r"(남성|여성|남자|여자)",
        r"(남|여)\s",
    ],
    "height_cm": [
        r"(?:키|신장)\s*(\d{2,3}\.?\d*)\s*(?:cm|센티)?",
        r"(\d{3})\s*cm",
        r"(\d{3}\.?\d*)\s*(?:센티|센치)",
    ],
    "weight_kg": [
        r"(?:몸무게|체중)\s*(\d{2,3}\.?\d*)\s*(?:kg|킬로)?",
        r"(\d{2,3}\.?\d*)\s*kg",
        r"(\d{2,3}\.?\d*)\s*(?:킬로)",
    ],
    "exercise_frequency": [
        r"주\s*(\d)\s*회",
        r"주\s*(\d)\s*번",
        r"일주일에?\s*(\d)\s*(?:회|번|일)",
        r"(\d)\s*회.*주",
    ],
}

# ── 제약사항 키워드 사전 ──
CONSTRAINT_KEYWORDS = {
    "무릎 부상": ["무릎", "슬개골", "관절"],
    "허리 부상": ["허리", "디스크", "척추", "요통"],
    "어깨 부상": ["어깨", "회전근개"],
    "당뇨": ["당뇨", "혈당"],
    "고혈압": ["고혈압", "혈압"],
    "심장질환": ["심장", "부정맥"],
    "임산부": ["임신", "임산부"],
}

# ── 운동 경험 레벨 키워드 ──
EXPERIENCE_KEYWORDS = {
    "입문": ["처음", "시작", "입문", "초보", "모르", "경험 없"],
    "초급": ["초급", "초보", "조금", "가끔", "몇 번"],
    "중급": ["중급", "꾸준", "1년", "2년", "정기적"],
    "고급": ["고급", "전문", "선수", "대회", "5년 이상"],
}


def extract_entities_rule_based(text: str) -> ExtractedEntities:
    """정규식 기반으로 엔티티를 추출합니다."""
    entities = ExtractedEntities()
    
    # 나이 추출
    for pattern in ENTITY_PATTERNS["age"]:
        match = re.search(pattern, text)
        if match:
            val = match.group(1)
            if "대" in text[match.end()-1:match.end()+1]:
                entities.age = int(val) + 5  # "30대" → 35
            else:
                entities.age = int(val)
            break
    
    # 성별 추출
    for pattern in ENTITY_PATTERNS["gender"]:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1)
            entities.gender = "남성" if raw in ["남성", "남자", "남"] else "여성"
            break
    
    # 키 추출
    for pattern in ENTITY_PATTERNS["height_cm"]:
        match = re.search(pattern, text)
        if match:
            entities.height_cm = float(match.group(1))
            break
    
    # 몸무게 추출
    for pattern in ENTITY_PATTERNS["weight_kg"]:
        match = re.search(pattern, text)
        if match:
            entities.weight_kg = float(match.group(1))
            break
    
    # 운동 빈도 추출
    for pattern in ENTITY_PATTERNS["exercise_frequency"]:
        match = re.search(pattern, text)
        if match:
            entities.exercise_frequency = int(match.group(1))
            break
    
    # 제약사항 추출
    for constraint_name, keywords in CONSTRAINT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            entities.constraints.append(constraint_name)
    
    return entities
```

#### 텍스트 분류 (운동 목표 분류)

```python
"""
goal_classifier.py
사용자의 텍스트에서 운동 목표 유형을 분류합니다.

방식 1: 키워드 기반 규칙 분류 (baseline)
방식 2: KoBERT/KcBERT Fine-tuning 분류 (고도화)
방식 3: LLM 프롬프트 기반 분류 (비교 대상)
"""

from enum import Enum
from transformers import pipeline


class GoalType(Enum):
    FAT_LOSS = "체지방감소"
    MUSCLE_GAIN = "근력증가"
    FITNESS = "체력향상"
    WEIGHT_MGMT = "체중관리"
    HEALTH = "건강개선"


# ── 방식 1: 키워드 기반 규칙 분류 ──

GOAL_KEYWORDS = {
    GoalType.FAT_LOSS: [
        "체지방", "지방 감소", "지방 줄이", "살 빼", "살빼", "다이어트",
        "체중 감량", "몸무게 줄이", "마른", "날씬", "뱃살", "군살",
    ],
    GoalType.MUSCLE_GAIN: [
        "근육", "근력", "벌크", "벌크업", "헬스", "머슬",
        "팔뚝", "가슴 운동", "어깨 넓", "덩치", "몸 키우",
    ],
    GoalType.FITNESS: [
        "체력", "스태미나", "지구력", "컨디션", "활력",
        "에너지", "운동 능력", "기초 체력",
    ],
    GoalType.WEIGHT_MGMT: [
        "체중 관리", "유지", "현재 체중", "표준 체중",
        "적정 체중", "몸매 유지",
    ],
    GoalType.HEALTH: [
        "건강", "당뇨", "혈압", "혈당", "콜레스테롤",
        "관절", "재활", "회복",
    ],
}


def classify_goal_rule_based(text: str) -> tuple[GoalType, float]:
    """키워드 기반으로 목표를 분류합니다. (baseline)"""
    scores = {}
    for goal_type, keywords in GOAL_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[goal_type] = score
    
    if max(scores.values()) == 0:
        return GoalType.WEIGHT_MGMT, 0.5  # 기본값
    
    best_goal = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = scores[best_goal] / total if total > 0 else 0.5
    
    return best_goal, confidence


# ── 방식 2: BERT 계열 모델 분류 ──

def classify_goal_with_bert(text: str, model_name: str = "beomi/KcBERT-base") -> tuple[GoalType, float]:
    """
    KcBERT로 운동 목표를 분류합니다.
    
    사전 학습 데이터:
    - 운동 커뮤니티(헬창넷, 클리앙 등)에서 수집한 운동 목표 텍스트
    - 5개 클래스로 라벨링한 학습 데이터 필요
    
    학습 데이터 예시:
    | 텍스트                                    | 라벨        |
    |------------------------------------------|------------|
    | "뱃살 빼고 식스팩 만들고 싶어요"              | 체지방감소   |
    | "상체 근육을 키우고 싶습니다"                 | 근력증가    |
    | "계단만 올라가도 숨이 차요"                   | 체력향상    |
    | "지금 체중을 유지하면서 몸매를 다듬고 싶어요"    | 체중관리    |
    | "당뇨 때문에 운동을 시작해야 합니다"            | 건강개선    |
    """
    classifier = pipeline(
        "text-classification",
        model=model_name,
        tokenizer=model_name,
    )
    # Fine-tuned 모델이 있을 경우 사용
    # 없을 경우 rule-based 결과를 반환
    result = classifier(text)
    return GoalType(result[0]["label"]), result[0]["score"]


# ── 방식 3: LLM 프롬프트 기반 분류 ──

GOAL_CLASSIFY_PROMPT = """
사용자의 운동 목표를 아래 5가지 유형 중 하나로 분류해주세요.

유형:
1. 체지방감소 - 살을 빼거나 체지방률을 낮추고 싶은 경우
2. 근력증가 - 근육량을 늘리거나 몸을 키우고 싶은 경우
3. 체력향상 - 기초 체력, 지구력, 활력을 높이고 싶은 경우
4. 체중관리 - 현재 체중을 유지하면서 몸매를 관리하고 싶은 경우
5. 건강개선 - 질환 관리나 건강 회복을 위해 운동하는 경우

사용자 입력: "{user_text}"

아래 JSON 형식으로만 응답하세요:
{{"goal_type": "<유형명>", "confidence": <0.0~1.0>, "reason": "<분류 이유 한 줄>"}}
"""
```

#### 키워드 추출

```python
"""
keyword_extractor.py
사용자 입력에서 핵심 키워드를 추출합니다.
"""

from keybert import KeyBERT


def extract_keywords(text: str, top_n: int = 5) -> list[tuple[str, float]]:
    """
    KeyBERT로 핵심 키워드를 추출합니다.
    
    Args:
        text: 사용자 입력 텍스트
        top_n: 추출할 키워드 수
    
    Returns:
        [(키워드, 유사도 점수), ...] 리스트
    
    사용 예시:
        입력: "체지방을 줄이고 근육을 늘리고 싶어요. 주 3회 헬스장 운동 가능합니다."
        출력: [("체지방", 0.82), ("근육", 0.78), ("헬스장", 0.65), ...]
    """
    kw_model = KeyBERT("paraphrase-multilingual-MiniLM-L12-v2")
    
    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words=None,  # 한국어는 별도 불용어 처리
        top_n=top_n,
        use_mmr=True,     # 다양성 확보
        diversity=0.5,
    )
    
    return keywords
```

### 3-3. 신체 지표 자동 계산 모듈

```python
"""
body_calculator.py
신체 정보를 바탕으로 주요 건강 지표를 계산합니다.
인바디 데이터가 없는 사용자를 위한 대체 계산 로직입니다.
"""

from dataclasses import dataclass
from enum import Enum


class BMICategory(Enum):
    UNDERWEIGHT = "저체중"      # < 18.5
    NORMAL = "표준"             # 18.5 ~ 22.9
    OVERWEIGHT = "과체중"       # 23.0 ~ 24.9
    OBESE = "비만"              # >= 25.0


class ActivityLevel(Enum):
    SEDENTARY = 1.2        # 거의 운동 안 함
    LIGHT = 1.375          # 주 1~3회 가벼운 운동
    MODERATE = 1.55        # 주 3~5회 중간 강도
    ACTIVE = 1.725         # 주 6~7회 강한 운동
    VERY_ACTIVE = 1.9      # 매일 고강도 + 육체노동


@dataclass
class BodyMetrics:
    """계산된 신체 지표"""
    bmi: float
    bmi_category: BMICategory
    bmr_kcal: int
    tdee_kcal: int
    recommended_intake_kcal: int
    ideal_weight_kg: float


def calculate_bmi(weight_kg: float, height_cm: float) -> tuple[float, BMICategory]:
    """BMI를 계산하고 카테고리를 판정합니다. (아시아-태평양 기준)"""
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)
    
    if bmi < 18.5:
        category = BMICategory.UNDERWEIGHT
    elif bmi < 23.0:
        category = BMICategory.NORMAL
    elif bmi < 25.0:
        category = BMICategory.OVERWEIGHT
    else:
        category = BMICategory.OBESE
    
    return bmi, category


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> int:
    """
    기초대사량을 해리스-베네딕트 공식(개정판)으로 계산합니다.
    
    남성: BMR = 88.362 + (13.397 × 체중kg) + (4.799 × 키cm) - (5.677 × 나이)
    여성: BMR = 447.593 + (9.247 × 체중kg) + (3.098 × 키cm) - (4.330 × 나이)
    """
    if gender == "남성":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    
    return round(bmr)


def calculate_tdee(bmr: int, exercise_frequency: int) -> int:
    """
    TDEE(총 일일 에너지 소비량)를 계산합니다.
    주당 운동 횟수를 기반으로 활동 수준을 결정합니다.
    """
    if exercise_frequency <= 0:
        multiplier = ActivityLevel.SEDENTARY.value
    elif exercise_frequency <= 2:
        multiplier = ActivityLevel.LIGHT.value
    elif exercise_frequency <= 4:
        multiplier = ActivityLevel.MODERATE.value
    elif exercise_frequency <= 6:
        multiplier = ActivityLevel.ACTIVE.value
    else:
        multiplier = ActivityLevel.VERY_ACTIVE.value
    
    return round(bmr * multiplier)


def calculate_recommended_intake(tdee: int, goal_type: str) -> int:
    """
    목표 유형에 따른 권장 섭취 칼로리를 계산합니다.
    
    - 체지방감소: TDEE - 500 kcal (주당 약 0.5kg 감량)
    - 근력증가:   TDEE + 300 kcal (린매스 증가 목표)
    - 체력향상:   TDEE (유지)
    - 체중관리:   TDEE (유지)
    - 건강개선:   TDEE - 300 kcal (완만한 감량)
    """
    adjustments = {
        "체지방감소": -500,
        "근력증가": +300,
        "체력향상": 0,
        "체중관리": 0,
        "건강개선": -300,
    }
    adjustment = adjustments.get(goal_type, 0)
    recommended = tdee + adjustment
    
    # 최소 섭취량 보장 (남성 1500, 여성 1200)
    return max(recommended, 1200)


def calculate_ideal_weight(height_cm: float, gender: str) -> float:
    """적정 체중을 계산합니다. (BMI 22 기준)"""
    height_m = height_cm / 100
    return round(22.0 * (height_m ** 2), 1)


def calculate_all_metrics(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    exercise_frequency: int,
    goal_type: str,
) -> BodyMetrics:
    """모든 신체 지표를 한 번에 계산합니다."""
    bmi, bmi_category = calculate_bmi(weight_kg, height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, exercise_frequency)
    recommended = calculate_recommended_intake(tdee, goal_type)
    ideal_weight = calculate_ideal_weight(height_cm, gender)
    
    return BodyMetrics(
        bmi=bmi,
        bmi_category=bmi_category,
        bmr_kcal=bmr,
        tdee_kcal=tdee,
        recommended_intake_kcal=recommended,
        ideal_weight_kg=ideal_weight,
    )
```

### 3-4. 프로필 생성 통합 모듈

```python
"""
profile_builder.py
모든 분석 결과를 통합하여 최종 사용자 프로필을 생성합니다.
"""

import json
from datetime import datetime


def build_user_profile(
    inbody_data: dict = None,
    natural_text: str = None,
    model_used: str = "rule_based",
) -> dict:
    """
    인바디 데이터와/또는 자연어 입력을 통합하여 최종 프로필을 생성합니다.
    
    우선순위:
    1. 인바디 데이터가 있으면 인바디 수치를 우선 사용
    2. 자연어에서 추출한 목표/제약사항을 추가
    3. 인바디 없으면 자연어 데이터 + 자동계산으로 대체
    """
    profile = {
        "basic": {},
        "body_composition": {},
        "calculated": {},
        "nlp_analysis": {},
        "recommendations": {},
        "meta": {
            "input_type": "unknown",
            "has_inbody": False,
            "created_at": datetime.now().isoformat(),
            "model_used": model_used,
        },
    }
    
    # ── Step 1: 인바디 데이터 적용 ──
    if inbody_data:
        profile["meta"]["has_inbody"] = True
        profile["meta"]["input_type"] = "inbody_image"
        
        basic = inbody_data.get("basic_info", {})
        profile["basic"] = {
            "age": basic.get("age"),
            "gender": basic.get("gender"),
            "height_cm": basic.get("height_cm"),
            "weight_kg": inbody_data.get("body_composition", {}).get("weight_kg"),
        }
        
        profile["body_composition"] = {
            "skeletal_muscle_mass_kg": inbody_data.get("muscle_fat_analysis", {}).get("skeletal_muscle_mass_kg"),
            "body_fat_mass_kg": inbody_data.get("muscle_fat_analysis", {}).get("body_fat_mass_kg"),
            "body_fat_percent": inbody_data.get("obesity_analysis", {}).get("body_fat_percent"),
            "bmi": inbody_data.get("obesity_analysis", {}).get("bmi"),
            "bmr_kcal": inbody_data.get("research_params", {}).get("bmr_kcal"),
            "lean_body_mass_kg": inbody_data.get("research_params", {}).get("lean_body_mass_kg"),
            "visceral_fat_level": inbody_data.get("obesity_evaluation", {}).get("visceral_fat_level"),
            "waist_hip_ratio": inbody_data.get("obesity_evaluation", {}).get("waist_hip_ratio"),
            "inbody_score": inbody_data.get("inbody_score"),
        }
        
        wc = inbody_data.get("weight_control", {})
        profile["recommendations"] = {
            "weight_adjustment_kg": wc.get("weight_adjustment_kg"),
            "fat_adjustment_kg": wc.get("fat_adjustment_kg"),
            "muscle_adjustment_kg": wc.get("muscle_adjustment_kg"),
            "priority": determine_priority(wc),
        }
    
    # ── Step 2: 자연어 분석 적용 ──
    if natural_text:
        if not inbody_data:
            profile["meta"]["input_type"] = "natural_language"
        else:
            profile["meta"]["input_type"] = "both"
        
        # NER 추출
        entities = extract_entities_rule_based(natural_text)
        
        # 인바디 없을 때 기본 정보 자연어에서 채우기
        if not inbody_data:
            profile["basic"] = {
                "age": entities.age,
                "gender": entities.gender,
                "height_cm": entities.height_cm,
                "weight_kg": entities.weight_kg,
            }
        
        # 목표 분류
        goal_type, confidence = classify_goal_rule_based(natural_text)
        
        # 키워드 추출
        keywords = extract_keywords(natural_text, top_n=5)
        
        profile["nlp_analysis"] = {
            "goal_type": goal_type.value,
            "goal_confidence": round(confidence, 2),
            "goal_keywords": [kw for kw, _ in keywords],
            "constraints": entities.constraints,
            "experience_level": detect_experience_level(natural_text),
            "exercise_frequency": entities.exercise_frequency or 3,
            "preferred_exercises": entities.preferred_exercises,
        }
    
    # ── Step 3: 자동 계산 ──
    b = profile["basic"]
    if b.get("weight_kg") and b.get("height_cm"):
        goal = profile.get("nlp_analysis", {}).get("goal_type", "체중관리")
        freq = profile.get("nlp_analysis", {}).get("exercise_frequency", 3)
        
        metrics = calculate_all_metrics(
            weight_kg=b["weight_kg"],
            height_cm=b["height_cm"],
            age=b.get("age", 30),
            gender=b.get("gender", "남성"),
            exercise_frequency=freq,
            goal_type=goal,
        )
        
        profile["calculated"] = {
            "bmi": metrics.bmi,
            "bmi_category": metrics.bmi_category.value,
            "bmr_kcal": metrics.bmr_kcal,
            "tdee_kcal": metrics.tdee_kcal,
            "recommended_intake_kcal": metrics.recommended_intake_kcal,
            "ideal_weight_kg": metrics.ideal_weight_kg,
        }
    
    return profile


def determine_priority(weight_control: dict) -> str:
    """인바디 체중조절 데이터에서 우선순위를 결정합니다."""
    fat_adj = abs(weight_control.get("fat_adjustment_kg", 0))
    muscle_adj = abs(weight_control.get("muscle_adjustment_kg", 0))
    
    if fat_adj > muscle_adj * 2:
        return "지방감량우선"
    elif muscle_adj > fat_adj * 2:
        return "근육증가우선"
    else:
        return "균형관리"


def detect_experience_level(text: str) -> str:
    """텍스트에서 운동 경험 수준을 파악합니다."""
    for level, keywords in EXPERIENCE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return level
    return "입문"  # 기본값
```

---

## 4. LLM 비교 실험 설계

### 4-1. 비교 대상

| 비교 항목 | 모델 A | 모델 B |
|----------|--------|--------|
| 인바디 이미지 파싱 | OpenAI GPT-4o Vision | EXAONE Vision |
| 목표 분류 | 규칙 기반 (baseline) | KcBERT Fine-tuned |
| 목표 분류 | LLM 프롬프트 (OpenAI) | LLM 프롬프트 (EXAONE) |
| NER | 규칙 기반 (baseline) | KoBERT NER |

### 4-2. 평가 지표

```python
"""
evaluation.py
1단계 모듈의 성능을 평가합니다.
"""

# ── 인바디 파싱 정확도 ──
# 직접 입력한 정답 데이터와 비교

INBODY_GROUND_TRUTH = {
    "test_image_01.png": {
        "weight_kg": 59.1,
        "skeletal_muscle_mass_kg": 19.3,
        "body_fat_mass_kg": 22.1,
        "bmi": 24.0,
        "body_fat_percent": 37.5,
        "bmr_kcal": 1168,
        "inbody_score": 66,
    }
}


def evaluate_inbody_parsing(parsed: dict, ground_truth: dict) -> dict:
    """인바디 파싱 정확도를 평가합니다."""
    results = {}
    for field, true_value in ground_truth.items():
        parsed_value = parsed.get(field)
        if parsed_value is not None and true_value is not None:
            error = abs(parsed_value - true_value)
            accuracy = 1 - (error / true_value) if true_value != 0 else 0
            results[field] = {
                "parsed": parsed_value,
                "truth": true_value,
                "error": round(error, 2),
                "accuracy": round(accuracy * 100, 1),
            }
    
    avg_accuracy = sum(r["accuracy"] for r in results.values()) / len(results)
    results["average_accuracy"] = round(avg_accuracy, 1)
    return results


# ── 목표 분류 정확도 ──
# 테스트 세트로 F1 스코어 측정

GOAL_CLASSIFICATION_TEST_SET = [
    ("뱃살 빼고 식스팩 만들고 싶어요", "체지방감소"),
    ("상체 근육을 키우고 싶습니다", "근력증가"),
    ("계단만 올라가도 숨이 차요", "체력향상"),
    ("지금 체중을 유지하면서 몸매 관리하고 싶어요", "체중관리"),
    ("당뇨 전단계라서 운동 시작해야 합니다", "건강개선"),
    ("살 좀 빼서 옷이 잘 맞았으면 좋겠어요", "체지방감소"),
    ("헬스장에서 벤치프레스 무게를 올리고 싶어요", "근력증가"),
    ("마라톤 완주가 목표입니다", "체력향상"),
    ("요요 없이 건강하게 관리하고 싶어요", "체중관리"),
    ("고혈압 약을 줄이려고 운동 시작합니다", "건강개선"),
]
```

### 4-3. 파라미터 튜닝 실험

```python
# ── 인바디 이미지 파싱 시 temperature 실험 ──
TEMPERATURE_EXPERIMENTS = {
    "inbody_parsing": {
        "temperatures": [0.0, 0.1, 0.3],
        "hypothesis": "인바디 숫자 추출은 temperature 0에 가까울수록 정확",
        "metric": "필드별 정확도",
    },
    "goal_classification": {
        "temperatures": [0.0, 0.3, 0.7],
        "hypothesis": "목표 분류는 약간의 temperature가 문맥 이해에 도움",
        "metric": "분류 정확도 (F1)",
    },
}
```

---

## 5. React 프론트엔드 가이드

### 5-1. 온보딩 페이지 컴포넌트 구조

```
OnboardingPage/
├── InBodyUploader         ← 인바디 이미지 업로드 (드래그앤드롭)
├── NaturalLanguageInput   ← 자연어 텍스트 입력 필드
├── ProfileForm            ← 직접 입력 폼 (대체 수단)
│   ├── BasicInfoForm      ← 나이, 성별, 키, 몸무게
│   ├── GoalSelector       ← 운동 목표 선택 (라디오)
│   └── ConstraintChecker  ← 제약사항 체크박스
├── ProfilePreview         ← 분석 결과 미리보기 카드
│   ├── BodyMetricsCard    ← BMI, BMR, TDEE 시각화
│   ├── InBodyScoreGauge   ← 인바디 점수 게이지
│   └── GoalSummary        ← 목표 요약 + 추천사항
└── ModelComparisonToggle  ← LLM 모델 비교 ON/OFF
```

### 5-2. API 엔드포인트 설계

```
POST /api/v1/profile/analyze-inbody
  - Body: multipart/form-data (image file)
  - Response: InBodyData JSON

POST /api/v1/profile/analyze-text
  - Body: { "text": "자연어 입력 문자열" }
  - Response: NLPAnalysis JSON

POST /api/v1/profile/build
  - Body: { "inbody_data": {...}, "natural_text": "...", "model": "openai|exaone" }
  - Response: UserProfile JSON

GET  /api/v1/profile/{user_id}
  - Response: 저장된 UserProfile JSON
```

### 5-3. 상태 관리 (React Context)

```typescript
// ProfileContext.tsx — 1단계 결과를 전역 상태로 관리

interface UserProfile {
  basic: {
    age: number;
    gender: "남성" | "여성";
    height_cm: number;
    weight_kg: number;
  };
  body_composition: {
    skeletal_muscle_mass_kg?: number;
    body_fat_percent?: number;
    bmi?: number;
    bmr_kcal?: number;
    inbody_score?: number;
  };
  calculated: {
    bmi: number;
    bmi_category: string;
    bmr_kcal: number;
    tdee_kcal: number;
    recommended_intake_kcal: number;
  };
  nlp_analysis: {
    goal_type: string;
    goal_keywords: string[];
    constraints: string[];
    experience_level: string;
    exercise_frequency: number;
  };
  recommendations: {
    priority: string;
    fat_adjustment_kg?: number;
    muscle_adjustment_kg?: number;
  };
  meta: {
    has_inbody: boolean;
    input_type: string;
  };
}

// 이 프로필은 2단계(식단), 3단계(운동), 4단계(피드백)에서 참조합니다.
// 예: recommended_intake_kcal → 식단 생성의 기준 칼로리
// 예: goal_type + constraints → 운동 루틴 생성의 조건
// 예: exercise_frequency → 주간 운동 계획 설계
```

---

## 6. 다음 단계 연결

1단계에서 생성된 프로필은 다음과 같이 후속 단계로 전달됩니다.

```
기(起) 프로필 출력
    │
    ├──▶ 승(承) 식단 생성
    │    └─ 사용: recommended_intake_kcal, goal_type, constraints
    │
    ├──▶ 전(轉) 운동 루틴
    │    └─ 사용: goal_type, exercise_frequency, constraints, experience_level
    │
    └──▶ 결(結) 피드백
         └─ 사용: goal_type, body_composition (변화 추적용)
```

---

## 7. 체크리스트 (v1.1 현황)

### 필수 구현

- [x] 인바디 이미지 → JSON 파싱 (LLM Vision — Gemma 4 E4B) ✅
- [x] 인바디 CSV/PDF/Word/Excel 다중 포맷 파싱 ✅ `inbody_parser.py`
- [x] 자연어 텍스트 → 엔티티 추출 (NER) ✅ 정확도 100% (21/21) `profile_ner.py`
- [x] 운동 목표 텍스트 분류 (규칙 기반 baseline) ✅ F1=0.849 `goal_classifier.py`
- [x] KeyBERT 키워드 추출 ✅ `keyword_extractor.py`
- [x] BMI(KSSO 6단계) / BMR(Mifflin-St Jeor) / TDEE / 권장 칼로리 자동 계산 ✅ `body_calculator.py`
- [x] 통합 프로필 JSON 생성 ✅ `profile_builder.py`
- [x] React 온보딩 페이지 UI ✅ 4탭 (직접입력/인바디업로드/AI채팅/프로필보기+수정)
- [x] 인바디 건강 분석 (체형C/I/D, 내장지방, 근감소증SMI, ECW) ✅ `inbody_analyzer.py`
- [x] 대사증후군 스크리닝 + 신뢰도 점수 ✅ `health_analyzer.py`
- [x] 사용자별 인바디 측정 이력 관리 ✅ `user_history.py`
- [x] PDF/Word/Excel/CSV/JSON 리포트 내보내기 ✅ `report_generator.py`

### 비교 분석

- [x] 목표 분류: 규칙 기반 vs LLM 정확도 비교 ✅ `evaluation.py`
- [x] BMR 공식 비교: Mifflin-St Jeor vs Harris-Benedict ✅ 평균 -91kcal 차이
- [x] 인바디 파싱 temperature (0.3) 비교 ✅ 낮은 temp가 수치 파싱에 최적
- [ ] KcBERT 파인튜닝 비교 (데이터 500개 확보 후)

### 고도화 (선택)

- [x] BMI 6단계 세분화 (KSSO 대한비만학회 기준) ✅
- [x] 프로필 수정 모드 (프로필 보기 탭에서 인라인 편집) ✅
- [ ] KcBERT Fine-tuning (목표 분류 전용 모델) — 학습 데이터 100개 → 500개 확보 필요
- [ ] 인바디 신체변화 히스토리 시각화 (차트)

---

## 8. 의존성

```txt
# requirements.txt (1단계 관련)

# LLM API
openai>=1.0.0

# NLP 모델
transformers>=4.30.0
torch>=2.0.0
keybert>=0.8.0
sentence-transformers>=2.2.0

# OCR (보조)
easyocr>=1.7.0

# 웹 프레임워크
fastapi>=0.100.0
uvicorn>=0.23.0
python-multipart>=0.0.6

# 데이터 처리
pandas>=2.0.0
numpy>=1.24.0
pydantic>=2.0.0
```

---

> **💡 핵심 원칙**: 인바디 데이터가 있으면 **정확한 수치를 최대한 활용**하고,
> 없으면 **자연어 + 자동계산으로 합리적 대안을 제공**하는 것이 1단계의 목표입니다.
> 
> 모든 경로가 동일한 `UserProfile` 스키마를 출력하므로,
> 2~4단계는 입력 방식에 관계없이 동일하게 동작합니다.
