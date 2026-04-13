# 🏆 결(結) — 잘 하고 있나? | 구현 가이드라인

## 📌 개요

이 문서는 **헬창지피티(HelChangGPT)** 프로젝트의 **4단계: 감성 분석 & 동기부여 피드백** 구현을 위한
구현 가이드라인입니다.

사용자가 작성한 **운동 일지 텍스트를 감성 분석**(KoBERT/KcBERT)하여 긍정·부정·중립을 판별하고,
**주간 기록을 NLP 모델로 요약**(mT5/BART)한 뒤,
감성 상태에 맞는 **개인화된 동기부여 피드백을 LLM으로 생성**합니다.

이 단계가 기승전결의 **결(結)** 로서, 앞선 3단계(프로필→식단→운동)의 모든 데이터를 종합하여
사용자에게 **"잘 하고 있다"는 확인과 다음 행동 방향**을 제공하는 마무리 역할을 합니다.

---

## 1. 이전 단계로부터 받는 입력

```python
STAGE4_INPUT = {
    # ── 1단계: 프로필 ──
    "goal_type": "체지방감소",
    "weight_kg": 59.1,
    "body_fat_percent": 37.5,
    "experience_level": "입문",
    "constraints": ["무릎 부상"],
    
    # ── 2단계: 식단 ──
    "target_kcal": 1397,
    "meal_plan_summary": "고단백 저탄수화물 식단, 총 1397kcal",
    
    # ── 3단계: 운동 루틴 ──
    "weekly_plan_summary": "주 3회 전신 운동, 유산소 40% + 무산소 60%",
    "planned_exercises": ["레그프레스", "랫풀다운", "푸쉬업", "사이클"],
    "exercise_frequency": 3,
    
    # ── 4단계 자체 입력: 운동 일지 ──
    "diary_entries": [
        {
            "date": "2026-04-07",
            "text": "오늘 레그프레스 4세트 했는데 생각보다 잘 됐다! 무릎도 안 아프고 무게도 조금 올렸다.",
            "exercises_done": ["레그프레스", "사이클"],
            "duration_min": 50,
        },
        {
            "date": "2026-04-09",
            "text": "너무 피곤해서 운동 의욕이 없었다. 겨우 30분 하고 나왔다. 식단도 지키기 힘들었다.",
            "exercises_done": ["트레드밀 걷기"],
            "duration_min": 30,
        },
        {
            "date": "2026-04-11",
            "text": "친구랑 같이 운동했더니 재밌었다. 푸쉬업 15개 연속 성공! 점점 체력이 느는 것 같다.",
            "exercises_done": ["푸쉬업", "랫풀다운", "플랭크"],
            "duration_min": 60,
        },
    ],
}
```

---

## 2. 출력 데이터 구조

```python
FEEDBACK_SCHEMA = {
    # ── 감성 분석 결과 ──
    "sentiment_analysis": {
        "entries": [
            {
                "date": str,
                "text": str,
                "sentiment": str,          # "긍정" | "부정" | "중립"
                "confidence": float,       # 0.0 ~ 1.0
                "emotion_detail": str,     # "성취감|자신감|피로|좌절|평온" 등 (세분류)
                "model_used": str,         # "kobert" | "kcbert" | "llm"
            }
        ],
        "weekly_sentiment": {
            "positive_count": int,
            "negative_count": int,
            "neutral_count": int,
            "dominant_sentiment": str,
            "trend": str,                  # "상승" | "하락" | "유지"
        },
    },
    
    # ── 주간 요약 ──
    "weekly_summary": {
        "text": str,                       # NLP 모델(mT5/BART) 요약 텍스트
        "total_sessions": int,             # 실제 수행 세션 수
        "planned_sessions": int,           # 계획 세션 수
        "completion_rate": float,          # 달성률 (%)
        "total_duration_min": int,
        "exercises_performed": list,       # 실제 수행 운동 목록
        "highlights": list,               # 주요 성과 키워드
        "model_used": str,
    },
    
    # ── AI 동기부여 피드백 ──
    "motivational_feedback": {
        "main_message": str,               # 핵심 피드백 메시지
        "praise_points": list,             # 칭찬 포인트
        "improvement_suggestions": list,   # 개선 제안
        "next_week_tips": list,            # 다음 주 팁
        "encouragement_quote": str,        # 동기부여 문구
        "tone": str,                       # "격려|칭찬|응원|코칭" (감성 기반)
        "model_used": str,
        "temperature": float,
    },
    
    # ── 진행 추적 ──
    "progress_tracking": {
        "goal_type": str,
        "week_number": int,
        "diet_adherence_rate": float,      # 식단 준수율 (사용자 자가 평가)
        "exercise_adherence_rate": float,  # 운동 달성률
        "overall_score": int,              # 종합 점수 (0~100)
    },
    
    "meta": {
        "generated_at": str,
        "models_used": dict,               # 각 모듈별 사용 모델
    },
}
```

---

## 3. 감성 분석 모듈

### 3-1. KoBERT / KcBERT 감성 분석

```python
"""
sentiment_analyzer.py
운동 일지 텍스트의 감성을 분석합니다.

방식 1: KoBERT 기반 감성 분류 (baseline)
방식 2: KcBERT 기반 감성 분류 (구어체 특화)
방식 3: LLM 프롬프트 기반 감성 분류 (비교 대상)
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """감성 분석 결과"""
    sentiment: str          # "긍정" | "부정" | "중립"
    confidence: float       # 0.0 ~ 1.0
    emotion_detail: str     # 세부 감정
    probabilities: dict     # 클래스별 확률
    model_used: str


# ══════════════════════════════════════
# 방식 1: KoBERT 감성 분류
# ══════════════════════════════════════

class KoBERTSentimentAnalyzer:
    """
    KoBERT 기반 감성 분석기입니다.
    
    사전 학습 모델: monologg/kobert
    Fine-tuning 데이터: 운동 일지 감성 데이터셋 (직접 구축)
    
    Fine-tuning이 안 된 경우, 
    사전 학습된 감성 분류 모델을 사용합니다:
    - jeonghyeon97/koBERT-Senti5 (5가지 감정)
    - monologg/kobert (기본)
    """
    
    def __init__(self, model_name: str = "monologg/kobert"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=3  # 긍정, 부정, 중립
        )
        self.model.eval()
        self.label_map = {0: "부정", 1: "중립", 2: "긍정"}
    
    def analyze(self, text: str) -> SentimentResult:
        """텍스트의 감성을 분석합니다."""
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
        
        pred_idx = probs.argmax().item()
        sentiment = self.label_map[pred_idx]
        confidence = probs[pred_idx].item()
        
        probabilities = {
            self.label_map[i]: round(probs[i].item(), 4)
            for i in range(len(self.label_map))
        }
        
        # 세부 감정 추론
        emotion_detail = self._infer_emotion_detail(text, sentiment)
        
        return SentimentResult(
            sentiment=sentiment,
            confidence=round(confidence, 4),
            emotion_detail=emotion_detail,
            probabilities=probabilities,
            model_used="kobert",
        )
    
    def _infer_emotion_detail(self, text: str, sentiment: str) -> str:
        """키워드 기반으로 세부 감정을 추론합니다."""
        emotion_keywords = {
            "긍정": {
                "성취감": ["성공", "해냈", "올렸", "늘었", "신기록", "달성"],
                "자신감": ["자신감", "뿌듯", "할 수 있", "가능", "잘 됐"],
                "즐거움": ["재밌", "즐거", "좋았", "신났", "같이"],
                "만족감": ["만족", "충분", "괜찮", "무리 없"],
            },
            "부정": {
                "피로": ["피곤", "지쳤", "힘들", "체력", "컨디션"],
                "좌절": ["못 했", "실패", "포기", "안 됐", "늘지 않"],
                "통증": ["아프", "통증", "쑤시", "결림", "부상"],
                "무기력": ["의욕", "귀찮", "하기 싫", "동기"],
            },
            "중립": {
                "평온": ["그냥", "보통", "무난", "평범"],
            },
        }
        
        for emotion, keywords in emotion_keywords.get(sentiment, {}).items():
            if any(kw in text for kw in keywords):
                return emotion
        
        return "기타"


# ══════════════════════════════════════
# 방식 2: KcBERT 감성 분류 (구어체 특화)
# ══════════════════════════════════════

class KcBERTSentimentAnalyzer:
    """
    KcBERT 기반 감성 분석기입니다.
    KcBERT는 온라인 댓글/구어체로 학습되어 운동 일지의
    비격식 표현에 더 강합니다.
    
    사전 학습 모델: beomi/kcbert-base
    """
    
    def __init__(self, model_name: str = "beomi/kcbert-base"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=3
        )
        self.model.eval()
        self.label_map = {0: "부정", 1: "중립", 2: "긍정"}
    
    def analyze(self, text: str) -> SentimentResult:
        """KcBERT로 감성을 분석합니다. (구현 구조는 KoBERT와 동일)"""
        inputs = self.tokenizer(
            text, return_tensors="pt", padding=True,
            truncation=True, max_length=128,
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
        
        pred_idx = probs.argmax().item()
        
        return SentimentResult(
            sentiment=self.label_map[pred_idx],
            confidence=round(probs[pred_idx].item(), 4),
            emotion_detail=self._infer_emotion_detail(text, self.label_map[pred_idx]),
            probabilities={self.label_map[i]: round(probs[i].item(), 4) for i in range(3)},
            model_used="kcbert",
        )
    
    def _infer_emotion_detail(self, text, sentiment):
        # KoBERTSentimentAnalyzer._infer_emotion_detail과 동일 로직 공유
        pass


# ══════════════════════════════════════
# 방식 3: LLM 프롬프트 기반 감성 분류
# ══════════════════════════════════════

SENTIMENT_LLM_PROMPT = """
당신은 운동 심리 전문가입니다.

아래 운동 일지 텍스트의 감성을 분석해주세요.

운동 일지: "{diary_text}"

아래 JSON으로만 응답하세요:
{{
  "sentiment": "<긍정|부정|중립>",
  "confidence": <0.0~1.0>,
  "emotion_detail": "<성취감|자신감|즐거움|만족감|피로|좌절|통증|무기력|평온 중 택1>",
  "reason": "<판단 이유 한 줄>"
}}
"""
```

### 3-2. Fine-tuning용 운동 일지 감성 데이터셋

```python
"""
diary_sentiment_dataset.py
운동 일지 감성 분석용 학습 데이터셋입니다.
실제 프로젝트에서는 이 샘플을 확장하여 100~500개 수준으로 구축합니다.
"""

DIARY_SENTIMENT_DATASET = [
    # ── 긍정 (성취감) ──
    {"text": "스쿼트 무게를 5kg 올렸다! 드디어 60kg 달성!", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "벤치프레스 10회 3세트 완료. 한 달 전엔 5회도 힘들었는데.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "체중이 2kg 줄었다. 식단 관리가 효과가 있는 것 같다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "런닝 5km 논스톱 완주 성공! 기록도 30분대로 줄었다.", "sentiment": "긍정", "emotion": "성취감"},
    {"text": "인바디 찍었는데 근육량이 0.5kg 늘었다!! 눈물날 뻔 ㅠㅠ", "sentiment": "긍정", "emotion": "성취감"},
    
    # ── 긍정 (즐거움) ──
    {"text": "오늘 친구랑 같이 운동해서 넘 재밌었다ㅋㅋ 시간 가는 줄 몰랐음", "sentiment": "긍정", "emotion": "즐거움"},
    {"text": "새로운 운동 배웠는데 신기하고 재밌었다. 내일도 하고 싶다.", "sentiment": "긍정", "emotion": "즐거움"},
    {"text": "운동 끝나고 샤워하니까 개운하다~ 오운완!", "sentiment": "긍정", "emotion": "만족감"},
    
    # ── 부정 (피로) ──
    {"text": "회사에서 야근하고 와서 너무 피곤했다. 겨우 30분 하고 나옴.", "sentiment": "부정", "emotion": "피로"},
    {"text": "어제 잠을 못 자서 그런지 운동할 때 힘이 하나도 안 났다.", "sentiment": "부정", "emotion": "피로"},
    {"text": "컨디션이 바닥이라 그냥 스트레칭만 하고 왔다.", "sentiment": "부정", "emotion": "피로"},
    
    # ── 부정 (좌절) ──
    {"text": "2주째 체중이 안 줄어든다. 뭘 해도 안 되는 것 같다.", "sentiment": "부정", "emotion": "좌절"},
    {"text": "다른 사람들은 금방 근육이 붙던데 나는 왜 이렇게 안 늘지.", "sentiment": "부정", "emotion": "좌절"},
    {"text": "식단을 또 못 지켰다. 의지가 너무 약한 것 같아서 자괴감 든다.", "sentiment": "부정", "emotion": "좌절"},
    {"text": "운동 가기 싫어서 결국 빠졌다. 작심삼일인 나 자신이 싫다.", "sentiment": "부정", "emotion": "무기력"},
    
    # ── 부정 (통증) ──
    {"text": "레그프레스 하다가 무릎이 좀 아팠다. 내일은 하체 쉬어야 할 듯.", "sentiment": "부정", "emotion": "통증"},
    {"text": "어깨가 결리는 게 좀 신경 쓰인다. 자세가 잘못된 건지 모르겠다.", "sentiment": "부정", "emotion": "통증"},
    
    # ── 중립 ──
    {"text": "계획대로 루틴 소화했다. 특별한 건 없었음.", "sentiment": "중립", "emotion": "평온"},
    {"text": "오늘도 평소처럼 운동하고 왔다. 보통이었다.", "sentiment": "중립", "emotion": "평온"},
    {"text": "가슴 운동 3종 + 유산소 20분. 무난했다.", "sentiment": "중립", "emotion": "평온"},
]
```

---

## 4. 주간 운동 기록 요약 모듈

```python
"""
weekly_summarizer.py
주간 운동 일지를 NLP 모델로 요약합니다.
mT5, BART, LLM 세 가지 방식을 비교합니다.
"""

from transformers import pipeline


def prepare_weekly_text(diary_entries: list[dict], plan_info: dict) -> str:
    """
    주간 일지 데이터를 요약용 텍스트로 변환합니다.
    
    출력 예시:
        "이번 주 운동 기록 (계획: 주 3회)
         4/7(월): 레그프레스, 사이클 50분 수행. '무게 올려서 뿌듯했다'
         4/9(수): 트레드밀 걷기 30분. '피곤해서 짧게 끝냈다'
         4/11(금): 푸쉬업, 랫풀다운, 플랭크 60분. '친구와 함께해서 즐거웠다'
         총 3회/3회 달성(100%), 총 140분 운동"
    """
    lines = [f"이번 주 운동 기록 (계획: 주 {plan_info.get('exercise_frequency', 3)}회)"]
    
    total_min = 0
    for entry in diary_entries:
        exercises = ", ".join(entry.get("exercises_done", []))
        duration = entry.get("duration_min", 0)
        total_min += duration
        text_preview = entry["text"][:40] + "..." if len(entry["text"]) > 40 else entry["text"]
        lines.append(f"{entry['date']}: {exercises} {duration}분. '{text_preview}'")
    
    planned = plan_info.get("exercise_frequency", 3)
    actual = len(diary_entries)
    rate = round(actual / planned * 100) if planned > 0 else 0
    lines.append(f"총 {actual}회/{planned}회 달성({rate}%), 총 {total_min}분 운동")
    
    return "\n".join(lines)


# ── 방식 1: mT5 요약 ──

def summarize_with_mt5(weekly_text: str) -> str:
    """mT5로 주간 기록을 요약합니다."""
    summarizer = pipeline(
        "summarization",
        model="google/mt5-base",
        tokenizer="google/mt5-base",
    )
    result = summarizer(weekly_text, max_length=120, min_length=30, do_sample=False)
    return result[0]["summary_text"]


# ── 방식 2: BART 요약 ──

def summarize_with_bart(weekly_text: str) -> str:
    """BART로 주간 기록을 요약합니다."""
    summarizer = pipeline(
        "summarization",
        model="facebook/mbart-large-cc25",
        tokenizer="facebook/mbart-large-cc25",
    )
    result = summarizer(weekly_text, max_length=120, min_length=30, do_sample=False)
    return result[0]["summary_text"]


# ── 방식 3: LLM 요약 ──

WEEKLY_SUMMARY_PROMPT = """
아래 주간 운동 기록을 3~4문장으로 요약해주세요.
달성률, 주요 성과, 아쉬운 점, 전반적인 컨디션 흐름을 포함하세요.

{weekly_text}

요약:
"""


# ── 성과 키워드 추출 ──

def extract_highlights(diary_entries: list[dict]) -> list[str]:
    """운동 일지에서 주요 성과를 키워드로 추출합니다."""
    highlight_patterns = {
        "무게 증가": ["올렸", "늘렸", "무게", "중량"],
        "기록 갱신": ["신기록", "최고", "처음으로", "성공"],
        "체중 변화": ["체중", "몸무게", "줄었", "빠졌"],
        "꾸준한 출석": ["연속", "매일", "빠짐없이"],
        "새 운동 도전": ["새로운", "처음", "배웠"],
        "운동 시간 증가": ["오래", "시간 늘", "추가"],
    }
    
    highlights = []
    all_text = " ".join(entry["text"] for entry in diary_entries)
    
    for highlight_name, keywords in highlight_patterns.items():
        if any(kw in all_text for kw in keywords):
            highlights.append(highlight_name)
    
    return highlights
```

---

## 5. AI 동기부여 피드백 생성

### 5-1. 감성 기반 피드백 전략

```python
"""
feedback_strategy.py
감성 분석 결과에 따라 피드백 전략(톤, 내용)을 결정합니다.
"""

FEEDBACK_STRATEGIES = {
    # ── 긍정 감성이 지배적일 때 ──
    "positive_dominant": {
        "tone": "칭찬",
        "approach": "성취를 인정하고 다음 목표를 제시",
        "structure": [
            "이번 주 성과 칭찬 (구체적 수치 언급)",
            "특히 잘한 점 강조",
            "다음 주 도전 목표 제시 (난이도 살짝 올림)",
            "격려 문구",
        ],
    },
    
    # ── 부정 감성이 지배적일 때 ──
    "negative_dominant": {
        "tone": "격려",
        "approach": "감정을 공감하고 작은 성공을 발견하며 대안을 제시",
        "structure": [
            "감정 공감 (힘들었겠다는 인정)",
            "그럼에도 한 것들에 대한 인정 (운동장에 간 것 자체가 대단함)",
            "부정 원인에 대한 구체적 대안 제시",
            "부담을 줄이는 제안 (강도 낮추기, 짧게라도 하기 등)",
            "따뜻한 격려 문구",
        ],
    },
    
    # ── 혼합 감성일 때 ──
    "mixed": {
        "tone": "코칭",
        "approach": "객관적으로 분석하고 일관성의 가치를 강조",
        "structure": [
            "이번 주 전체 요약",
            "좋았던 날과 힘들었던 날의 차이 분석",
            "패턴에서 배울 점 제시",
            "다음 주 일관성 유지 팁",
            "균형 잡힌 응원 문구",
        ],
    },
    
    # ── 중립 감성일 때 ──
    "neutral_dominant": {
        "tone": "응원",
        "approach": "꾸준함의 가치를 인정하고 새로운 자극을 제안",
        "structure": [
            "꾸준함 인정 및 칭찬",
            "루틴의 안정성 강조",
            "새로운 도전 요소 제안 (슬럼프 방지)",
            "동기부여 문구",
        ],
    },
}


def determine_feedback_strategy(sentiment_results: list[dict]) -> dict:
    """주간 감성 분석 결과로 피드백 전략을 결정합니다."""
    pos = sum(1 for r in sentiment_results if r["sentiment"] == "긍정")
    neg = sum(1 for r in sentiment_results if r["sentiment"] == "부정")
    neu = sum(1 for r in sentiment_results if r["sentiment"] == "중립")
    total = len(sentiment_results)
    
    if total == 0:
        return FEEDBACK_STRATEGIES["neutral_dominant"]
    
    pos_ratio = pos / total
    neg_ratio = neg / total
    
    if pos_ratio >= 0.6:
        return FEEDBACK_STRATEGIES["positive_dominant"]
    elif neg_ratio >= 0.6:
        return FEEDBACK_STRATEGIES["negative_dominant"]
    elif neu / total >= 0.6:
        return FEEDBACK_STRATEGIES["neutral_dominant"]
    else:
        return FEEDBACK_STRATEGIES["mixed"]
```

### 5-2. LLM 피드백 생성 프롬프트

```python
"""
feedback_prompts.py
감성 분석 결과와 주간 요약을 기반으로 동기부여 피드백을 생성합니다.
"""

FEEDBACK_GENERATION_PROMPT = """
당신은 따뜻하고 전문적인 피트니스 코치입니다.
사용자의 운동 일지 분석 결과를 바탕으로 동기부여 피드백을 작성해주세요.

[사용자 정보]
- 운동 목표: {goal_type}
- 운동 경험: {experience_level}
- 제약사항: {constraints}

[이번 주 분석 결과]
- 운동 달성률: {completion_rate}% ({actual_sessions}/{planned_sessions}회)
- 총 운동 시간: {total_duration_min}분
- 감성 분석: 긍정 {pos_count}회, 부정 {neg_count}회, 중립 {neu_count}회
- 주요 감정: {dominant_emotion}
- 주간 요약: {weekly_summary}
- 주요 성과: {highlights}

[피드백 전략]
- 톤: {feedback_tone}
- 접근법: {feedback_approach}
- 구조: {feedback_structure}

[세부 일지 감성]
{diary_sentiments}

[작성 규칙]
1. 반드시 위 피드백 전략의 톤과 구조를 따르세요.
2. 구체적인 수치와 사실을 인용하여 피드백하세요 (예: "레그프레스 무게를 올리셨네요!").
3. 제약사항이 있을 경우 관련 주의사항을 한 줄 포함하세요.
4. 부정 감성이 많을 때 절대 비난하거나 압박하지 마세요. 공감 먼저!
5. 부정 감정 중 '통증' 감정이 감지되면 반드시 휴식을 권고하세요.
6. 마지막에 한 줄 격려 문구를 반드시 포함하세요.
7. 전체 길이는 200~300자 내외로 작성하세요.

아래 JSON 형식으로만 응답하세요:
{{
  "main_message": "<핵심 피드백 메시지 2~3문장>",
  "praise_points": ["<칭찬 포인트 1>", "<칭찬 포인트 2>"],
  "improvement_suggestions": ["<개선 제안 1>", "<개선 제안 2>"],
  "next_week_tips": ["<다음 주 팁 1>", "<다음 주 팁 2>"],
  "encouragement_quote": "<동기부여 격려 문구 한 줄>"
}}
"""

# ── 감성별 격려 문구 풀 (LLM 생성 실패 시 fallback) ──

ENCOURAGEMENT_QUOTES = {
    "긍정": [
        "꾸준함이 최고의 재능입니다. 이번 주도 멋지게 해내셨어요! 💪",
        "오늘의 땀이 내일의 자신감이 됩니다. 계속 이대로! 🔥",
        "변하고 있는 자신을 느끼고 계시죠? 그게 바로 성장입니다! ⭐",
    ],
    "부정": [
        "쉬어가는 것도 운동의 일부입니다. 내일의 나를 위해 오늘 충전하세요 🌱",
        "완벽하지 않아도 괜찮아요. 포기하지 않은 것 자체가 승리입니다 👊",
        "힘든 날에도 운동을 떠올린 당신, 이미 충분히 대단합니다 🌟",
    ],
    "중립": [
        "꾸준함은 화려하지 않지만, 가장 강력한 무기입니다 🛡️",
        "매일 조금씩, 그게 바로 진짜 실력이 쌓이는 방법이에요 📈",
        "오늘도 운동한 나 자신에게 박수! 👏",
    ],
}
```

### 5-3. 피드백 생성 통합 모듈

```python
"""
feedback_generator.py
감성 분석 → 전략 결정 → LLM 피드백 생성을 통합하는 메인 모듈입니다.
"""

import json
from datetime import datetime
from openai import OpenAI


def generate_full_feedback(
    diary_entries: list[dict],
    user_profile: dict,
    plan_info: dict,
    model: str = "gpt-4o",
    temperature: float = 0.7,
    sentiment_model: str = "kobert",
    summary_model: str = "llm",
    api_key: str = None,
) -> dict:
    """
    4단계 전체 파이프라인을 실행합니다.
    
    파이프라인:
    1. 각 일지 → 감성 분석
    2. 주간 감성 집계
    3. 주간 요약 생성
    4. 피드백 전략 결정
    5. LLM 동기부여 피드백 생성
    6. 결과 통합
    """
    
    # ── Step 1: 감성 분석 ──
    if sentiment_model == "kobert":
        analyzer = KoBERTSentimentAnalyzer()
    elif sentiment_model == "kcbert":
        analyzer = KcBERTSentimentAnalyzer()
    else:
        analyzer = None  # LLM 방식
    
    sentiment_results = []
    for entry in diary_entries:
        if analyzer:
            result = analyzer.analyze(entry["text"])
        else:
            result = analyze_sentiment_with_llm(entry["text"], api_key, model)
        
        sentiment_results.append({
            "date": entry["date"],
            "text": entry["text"],
            "sentiment": result.sentiment,
            "confidence": result.confidence,
            "emotion_detail": result.emotion_detail,
            "model_used": result.model_used,
        })
    
    # ── Step 2: 주간 감성 집계 ──
    pos = sum(1 for r in sentiment_results if r["sentiment"] == "긍정")
    neg = sum(1 for r in sentiment_results if r["sentiment"] == "부정")
    neu = sum(1 for r in sentiment_results if r["sentiment"] == "중립")
    
    weekly_sentiment = {
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu,
        "dominant_sentiment": max(["긍정", "부정", "중립"], key=[pos, neg, neu].__getitem__),
        "trend": _calculate_trend(sentiment_results),
    }
    
    # ── Step 3: 주간 요약 ──
    weekly_text = prepare_weekly_text(diary_entries, plan_info)
    
    if summary_model == "mt5":
        summary_text = summarize_with_mt5(weekly_text)
    elif summary_model == "bart":
        summary_text = summarize_with_bart(weekly_text)
    else:
        summary_text = summarize_with_llm(weekly_text, api_key, model)
    
    planned = plan_info.get("exercise_frequency", 3)
    actual = len(diary_entries)
    total_min = sum(e.get("duration_min", 0) for e in diary_entries)
    highlights = extract_highlights(diary_entries)
    
    # ── Step 4: 피드백 전략 결정 ──
    strategy = determine_feedback_strategy(sentiment_results)
    
    # ── Step 5: LLM 피드백 생성 ──
    diary_sentiments_str = "\n".join(
        f"- {r['date']}: [{r['sentiment']}({r['confidence']:.0%})] {r['emotion_detail']} - \"{r['text'][:50]}...\""
        for r in sentiment_results
    )
    
    prompt = FEEDBACK_GENERATION_PROMPT.format(
        goal_type=user_profile.get("goal_type", "체중관리"),
        experience_level=user_profile.get("experience_level", "입문"),
        constraints=", ".join(user_profile.get("constraints", [])) or "없음",
        completion_rate=round(actual / planned * 100) if planned else 0,
        actual_sessions=actual,
        planned_sessions=planned,
        total_duration_min=total_min,
        pos_count=pos, neg_count=neg, neu_count=neu,
        dominant_emotion=weekly_sentiment["dominant_sentiment"],
        weekly_summary=summary_text,
        highlights=", ".join(highlights) or "특이사항 없음",
        feedback_tone=strategy["tone"],
        feedback_approach=strategy["approach"],
        feedback_structure=" → ".join(strategy["structure"]),
        diary_sentiments=diary_sentiments_str,
    )
    
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=1000,
    )
    
    feedback_json = _extract_json(response.choices[0].message.content)
    feedback_json["tone"] = strategy["tone"]
    feedback_json["model_used"] = model
    feedback_json["temperature"] = temperature
    
    # ── Step 6: 결과 통합 ──
    return {
        "sentiment_analysis": {
            "entries": sentiment_results,
            "weekly_sentiment": weekly_sentiment,
        },
        "weekly_summary": {
            "text": summary_text,
            "total_sessions": actual,
            "planned_sessions": planned,
            "completion_rate": round(actual / planned * 100) if planned else 0,
            "total_duration_min": total_min,
            "exercises_performed": list(set(
                ex for entry in diary_entries
                for ex in entry.get("exercises_done", [])
            )),
            "highlights": highlights,
            "model_used": summary_model,
        },
        "motivational_feedback": feedback_json,
        "progress_tracking": {
            "goal_type": user_profile.get("goal_type"),
            "exercise_adherence_rate": round(actual / planned * 100) if planned else 0,
            "overall_score": _calculate_overall_score(actual, planned, weekly_sentiment),
        },
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "models_used": {
                "sentiment": sentiment_model,
                "summary": summary_model,
                "feedback": model,
            },
        },
    }


def _calculate_trend(results: list[dict]) -> str:
    """일지 순서대로 감성 추이를 계산합니다."""
    if len(results) < 2:
        return "유지"
    
    score_map = {"긍정": 1, "중립": 0, "부정": -1}
    scores = [score_map.get(r["sentiment"], 0) for r in results]
    
    first_half = sum(scores[:len(scores)//2])
    second_half = sum(scores[len(scores)//2:])
    
    if second_half > first_half:
        return "상승"
    elif second_half < first_half:
        return "하락"
    return "유지"


def _calculate_overall_score(actual: int, planned: int, sentiment: dict) -> int:
    """종합 점수를 계산합니다. (0~100)"""
    score = 50  # 기본 점수
    
    # 운동 달성률 반영 (최대 ±30)
    if planned > 0:
        adherence = actual / planned
        score += min(30, int(adherence * 30))
    
    # 감성 비율 반영 (최대 ±20)
    total = sentiment["positive_count"] + sentiment["negative_count"] + sentiment["neutral_count"]
    if total > 0:
        pos_ratio = sentiment["positive_count"] / total
        neg_ratio = sentiment["negative_count"] / total
        score += int((pos_ratio - neg_ratio) * 20)
    
    return max(0, min(100, score))


def _extract_json(text: str) -> dict:
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    return json.loads(text.strip())
```

---

## 6. React 프론트엔드 가이드

### 6-1. 운동 일지 & 피드백 페이지 컴포넌트 구조

```
FeedbackPage/
├── DiarySection                  ← 운동 일지 작성 영역
│   ├── DiaryEntryForm            ← 일지 작성 폼
│   │   ├── DatePicker            ← 날짜 선택
│   │   ├── TextArea              ← 자유 텍스트 입력
│   │   ├── ExerciseCheckList     ← 수행 운동 체크 (3단계 계획 기반)
│   │   └── DurationInput         ← 운동 시간 입력
│   └── DiaryEntryList            ← 이번 주 일지 목록
│       └── DiaryCard             ← 개별 일지 카드 + 감성 배지
│
├── SentimentDashboard            ← 감성 분석 대시보드
│   ├── SentimentTimeline         ← 일별 감성 추이 차트 (Line)
│   ├── EmotionPieChart           ← 감정 분포 도넛 차트
│   └── SentimentTrend            ← 상승/하락/유지 인디케이터
│
├── WeeklySummaryCard             ← 주간 요약 카드
│   ├── CompletionRate            ← 달성률 프로그레스 바
│   ├── SummaryText               ← NLP 요약 텍스트
│   └── HighlightTags             ← 주요 성과 태그
│
├── MotivationalFeedback          ← AI 피드백 카드 (메인)
│   ├── MainMessage               ← 핵심 피드백 메시지
│   ├── PraiseList                ← 칭찬 포인트 리스트
│   ├── SuggestionList            ← 개선 제안 리스트
│   ├── NextWeekTips              ← 다음 주 팁
│   └── EncouragementQuote        ← 격려 문구 (강조 표시)
│
├── OverallScoreGauge             ← 종합 점수 게이지 (0~100)
│
└── ModelComparisonPanel          ← 모델 비교 패널
    ├── SentimentModelToggle      ← KoBERT / KcBERT / LLM 전환
    ├── SummaryModelToggle        ← mT5 / BART / LLM 전환
    └── SideBySideComparison      ← 결과 나란히 비교
```

### 6-2. API 엔드포인트

```
POST /api/v1/feedback/analyze-diary
  - Body: { "text": "오늘 운동 일지...", "model": "kobert" }
  - Response: SentimentResult JSON

POST /api/v1/feedback/generate
  - Body: {
      "diary_entries": [...],
      "user_profile": {...},
      "plan_info": {...},
      "sentiment_model": "kobert",
      "summary_model": "mt5",
      "feedback_model": "gpt-4o",
      "temperature": 0.7
    }
  - Response: FullFeedback JSON

POST /api/v1/feedback/compare
  - Body: { "diary_entries": [...], "models": ["kobert", "kcbert", "llm"] }
  - Response: [SentimentResult × 3] 비교 결과

GET  /api/v1/feedback/history?weeks=4
  - Response: 주간 피드백 히스토리 (추이 분석용)
```

---

## 7. 비교 실험 설계

| 실험 축 | 비교 대상 | 평가 지표 |
|---------|---------|---------|
| **감성 분석** | KoBERT vs KcBERT vs LLM | 정확도, F1, 응답속도 |
| **요약 모델** | mT5 vs BART vs LLM | ROUGE, 핵심정보 포함률 |
| **피드백 생성** | OpenAI vs EXAONE | 공감도, 실용성, 톤 적절성 |
| **temperature** | 0.3 vs 0.7 vs 1.0 | 피드백 다양성, 공감 수준 |

```python
# ── 감성 분석 테스트 데이터셋 ──
SENTIMENT_TEST_SET = [
    ("스쿼트 무게 5kg 올렸다! 드디어!", "긍정"),
    ("너무 피곤해서 30분 하고 나왔다", "부정"),
    ("평소처럼 루틴 소화함", "중립"),
    ("2주째 체중이 안 줄어서 의욕이 없다", "부정"),
    ("친구랑 같이 하니까 넘 재밌었다ㅋㅋ", "긍정"),
    ("무릎이 좀 아팠다 내일은 쉬어야겠다", "부정"),
    ("오운완! 개운하다~", "긍정"),
    ("그냥 갔다 왔다. 특별한 건 없었음", "중립"),
    ("식단을 또 못 지켰다 자괴감 든다", "부정"),
    ("인바디 근육량 0.5kg 늘었다!!", "긍정"),
]


def evaluate_sentiment_models(test_set: list) -> dict:
    """감성 분석 모델들을 테스트 세트로 평가합니다."""
    models = {
        "kobert": KoBERTSentimentAnalyzer(),
        "kcbert": KcBERTSentimentAnalyzer(),
    }
    
    results = {}
    for model_name, analyzer in models.items():
        correct = 0
        for text, true_label in test_set:
            pred = analyzer.analyze(text)
            if pred.sentiment == true_label:
                correct += 1
        
        accuracy = correct / len(test_set) * 100
        results[model_name] = {
            "accuracy": round(accuracy, 1),
            "total": len(test_set),
            "correct": correct,
        }
    
    return results
```

---

## 8. 전체 파이프라인 순환 연결

4단계는 기승전결의 마무리이면서, 동시에 **다음 주기의 시작점**이 됩니다.

```
결(結) 피드백 출력
    │
    ├──▶ 다음 주 기(起) 프로필 갱신
    │    └─ 체중 변화, 새로운 목표 반영
    │
    ├──▶ 다음 주 승(承) 식단 조정
    │    └─ 식단 준수율 기반 난이도 조정
    │
    └──▶ 다음 주 전(轉) 운동 루틴 조정
         └─ 달성률 + 감성에 따라 강도 조정
             - 긍정 + 100% 달성 → 강도 UP
             - 부정 + 낮은 달성률 → 강도 DOWN
             - 통증 감지 → 해당 부위 휴식
```

---

## 9. 체크리스트 (v1.1 현황)

### 필수 구현

- [x] 키워드 기반 감성 분석 (긍정/부정/중립) ✅ 정확도 70% `sentiment_analyzer.py`
- [x] LLM 프롬프트 감성 분석 (병행) ✅ `sentiment_analyzer.py`
- [x] 세부 감정 분류 (성취감/피로/좌절/통증/즐거움/...) ✅ 6개 세분류
- [x] 주간 운동 기록 요약 ✅ `weekly_summarizer.py`
- [x] 감성 기반 피드백 전략 결정 로직 ✅ 달성률 + 감성 + 추세 기반
- [x] LLM 동기부여 피드백 생성 (EXAONE) ✅ `feedback_generator.py`
- [x] 규칙 기반 피드백 (LLM 없이 즉시) ✅ 모드별 템플릿
- [x] 5종 피드백 모드 ✅ 코치/친구/교관/매미킴/해병문학 `feedback_modes.py`
- [x] 해병문학 구호 수정 ("충성"→"필승") ✅ 해병대 정확 경례구호
- [x] 운동 달성률 / 종합 점수 / 연속 운동일 계산 ✅ `/api/v1/diary/{user_id}/growth`
- [x] React 운동 일지 & 피드백 페이지 UI ✅ 3탭 (오늘의일기 + 성장기록 + 목표달성률)
- [x] 일기 저장/이력 조회 API ✅ `/api/v1/diary/save`, `history`
- [x] 주별 달성률 통계 + 스트릭(연속 운동일) ✅

### 비교 분석

- [x] 규칙 기반 vs LLM 감성 분석 비교 ✅ 규칙 70% → LLM 병행 85%+ 기대
- [x] 5종 피드백 모드 톤/스타일 비교 ✅ 동일 결과 → 모드별 다른 표현
- [ ] KcBERT 파인튜닝 감성 분석 (데이터 200개 확보 후)
- [ ] temperature별 피드백 톤/다양성 비교

### 고도화 (선택)

- [x] 매미킴(김동현) 스타일 피드백 ✅ "운동 많이 된다" 긍정 마인드
- [x] 해병문학 스타일 피드백 ✅ "필승!" + 과장된 감성 표현
- [ ] 운동 일지 감성 데이터셋 Fine-tuning (현재 40개 → 200개 확보 필요)
- [ ] 주간 → 월간 장기 추이 분석
- [ ] 감성 추이 시계열 시각화 (차트)
- [ ] 알림/리마인더 시스템 연동

---

## 10. 의존성

```txt
# requirements.txt (4단계 관련)

# 감성 분석
transformers>=4.30.0
torch>=2.0.0
sentencepiece>=0.1.91

# 요약 모델
# (transformers에 포함)

# LLM API
openai>=1.0.0

# 데이터 처리
pandas>=2.0.0
numpy>=1.24.0

# 평가
scikit-learn>=1.3.0     # F1, accuracy 등

# 웹 프레임워크
fastapi>=0.100.0
uvicorn>=0.23.0
```

---

> **💡 핵심 원칙**: 4단계의 존재 이유는 **"운동을 지속하게 만드는 것"** 입니다.
> 가장 중요한 것은 기술적 정확도가 아니라,
> 사용자가 피드백을 읽고 **"다음에도 해봐야지"** 라고 느끼게 만드는 것입니다.
> 부정 감성일 때 절대 비난하지 않고, 긍정 감성일 때 구체적으로 칭찬하며,
> **통증이 감지되면 반드시 휴식을 권고**하는 안전 원칙을 지켜야 합니다.
