# 🔹 Step 4 — D5 NLG 주간 영양 리포트 상세 구현 가이드

> **Mini NLP MVP 의 4주차 전용 심화 가이드**
>
> 본 문서는 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §8 의
> Step 4 섹션을 **4주차 단일 독립 체크리스트** 로 확장한 문서입니다.
> 브레인스토밍 · 팩트 추출 전략 · 프롬프트 설계 · 템플릿/LLM 하이브리드 ·
> 평가 루브릭 · Mini 통합을 한 문서에 집약합니다.

---

## 📋 목차

1. [문서 목적 및 위치](#1-문서-목적-및-위치)
2. [Step 4 전체 조감](#2-step-4-전체-조감)
3. [브레인스토밍 — 기술 선택 의사결정](#3-브레인스토밍--기술-선택-의사결정)
4. [확장 아키텍처 다이어그램](#4-확장-아키텍처-다이어그램)
5. [파일 목록 및 의존성 그래프](#5-파일-목록-및-의존성-그래프)
6. [파일별 상세 명세](#6-파일별-상세-명세)
7. [구현 순서 (5일 체크리스트)](#7-구현-순서-5일-체크리스트)
8. [KPI 및 검증 기준](#8-kpi-및-검증-기준)
9. [트러블슈팅 (Step 4 한정)](#9-트러블슈팅-step-4-한정)
10. [재사용 가능한 기존 파일](#10-재사용-가능한-기존-파일)
11. [외부 의존성 확인](#11-외부-의존성-확인)
12. [리포트 문체 가이드 (Tone of Voice)](#12-리포트-문체-가이드-tone-of-voice)
13. [Mini 통합 및 마무리](#13-mini-통합-및-마무리)
14. [부록](#14-부록)
15. [1페이지 체크리스트 요약](#15-1페이지-체크리스트-요약)

---

## 1. 문서 목적 및 위치

### 1.1 왜 별도 가이드인가

상위 가이드 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §8 은
Claude Code 요약 프롬프트입니다. 4주차 D5 NLG 구현에는 다음이 추가로 필요합니다:

- **NLG 접근 방식의 근거** — 순수 템플릿 · 순수 LLM · **하이브리드** 트레이드오프
- **팩트 추출 로직** — SQL 집계·기준값·영양 판정 규칙
- **프롬프트 엔지니어링** — 친근한 어투·이모지·"훈계하지 않기"
- **엣지 케이스** — 이력 부족·편식·목표 미설정
- **평가 루브릭** — 자연스러움·유용성·정확성 3축
- **Mini 통합** — React 대시보드 AI 코멘트 카드 연결

### 1.2 상위 문서와의 관계

```
Mini/NLP/
├── README.md
├── GUIDE_NLP_MVP_SCENARIO3.md
│   └── §8 Step 4                         # → 본 문서가 확장
├── GUIDE_NLP_MVP_STEP1_SENTIMENT.md      # 1주차 A1
├── GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md # 2주차 B1
├── GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md    # 3주차 D3
├── GUIDE_NLP_MVP_STEP4_NLG_REPORT.md     # 🆕 본 문서 (4주차 D5)
└── GUIDE_NLP_RESEARCH_SCENARIO2.md
```

### 1.3 선행 조건

- [x] `nlp_mvp/` 스켈레톤 · `.env`
- [x] **Step 0** 공용 유틸 (`shared/db.py`, `shared/logger.py`, `shared/ollama_client.py`)
- [x] **Step 3** 완료 — `OllamaClient` 동작, `LunchCoachBot` 프롬프트 패턴 이해
- [x] **Step 2** 권장 — `meal_history.normalized_menu_id` 가 있으면 영양 조인 정확
- [x] Mini `meal_history`, `nutrition_info`, `users` 시드 데이터
- [x] Ollama 모델 가동 (Step 3 와 동일: `qwen2.5:7b-instruct`)

---

## 2. Step 4 전체 조감

### 2.1 한 줄 목표

> **숫자 덩어리인 주간 영양 이력 → 친근하고 격려하는 한국어 리포트로 자동 변환**

### 2.2 4주차 5일 일정

| Day | 테마 | 산출물 | 누적 |
|-----|------|--------|------|
| **Day 1** | 팩트 추출기 + `nutrition_reports` 스키마 | `fact_extractor.py`, `ensure_schema()` | 20% |
| **Day 2** | 프롬프트 빌더 + 문체 가이드 | `prompt.py`, 10개 수동 프롬프트 테스트 | 40% |
| **Day 3** | Generator + 템플릿 fallback | `generator.py`, `ReportGenerator` 클래스 | 60% |
| **Day 4** | 10건 샘플 생성 + 블라인드 평가 | `samples/sample_reports.md` | 80% |
| **Day 5** | FastAPI · React · 전체 통합 | `integration/scoring_patch.py`, 최종 데모 | 100% |

### 2.3 완료 기준

| 기준 | 목표 |
|------|-----|
| ✅ 팩트 추출 정확도 | 수동 10건 비교 100% |
| ✅ LLM 생성 성공률 | ≥ 95% |
| ✅ 자연스러움 평가 | 블라인드 평균 ≥ 4.0 / 5.0 |
| ✅ 유용성 평가 | ≥ 4.0 / 5.0 |
| ✅ 정확성 평가 | 팩트 오류 0건 / 10건 |
| ✅ 리포트 생성 속도 | ≤ 5초 |
| ✅ 엣지 케이스 처리 | 이력 0/3/7 건 모두 정상 |
| ✅ React 통합 | AI 코멘트 카드 렌더링 |

---

## 3. 브레인스토밍 — 기술 선택 의사결정

### 3.1 NLG 접근 방식 선택

**후보 비교표:**

| 방식 | 일관성 | 자연스러움 | 개인화 | 리스크 | MVP 적합성 |
|------|-------|---------|-------|------|-----------|
| **순수 템플릿** (f-string) | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | 없음 | ⭐⭐ |
| **순수 LLM** (팩트 없이 DB 직접 주입) | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | **환각 · 수치 오류** | ⭐⭐ |
| **하이브리드: 규칙 팩트 추출 + LLM 생성** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 낮음 | ⭐⭐⭐⭐⭐ |
| **LLM + Function Calling** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Ollama SDK 제약 | ⭐⭐⭐ |
| **Fine-tuned T5/KoBART** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 학습 필요 | ⭐⭐ (시나리오 2) |

**의사결정:** **하이브리드** (규칙 팩트 추출 → LLM 생성)

**근거:**
- 수치 정확도는 **규칙 기반 팩트 추출**이 담당 (환각 방지)
- 자연어 표현은 **LLM** 이 담당 (문체 자연스러움)
- 실패 시 **템플릿 fallback** 으로 최소 출력 보장

**코드 구조:**
```python
facts = extract_weekly_facts(user_id)    # 규칙 기반, 100% 정확
prompt = build_report_prompt(facts)       # 사실만 포함된 프롬프트
report_text = ollama.chat(prompt)         # LLM 자연어 변환
# 실패 시: report_text = render_template(facts)  # fallback
```

### 3.2 팩트 추출 SQL 전략

**질문:** meal_history 집계를 어떻게 쿼리할지?

**후보:**

| 방식 | 장점 | 단점 |
|------|------|------|
| **원시 SQL + pandas** | 유연, 디버깅 쉬움 | SQL 코드 관리 |
| **SQLAlchemy ORM** | 타입 안전 | reflect 필요, 보일러플레이트 |
| **pandas.read_sql + groupby** | 가장 간결 | 메모리 사용 |

**결정:** `pandas.read_sql` + SQLAlchemy engine (`shared/db.py` 재사용)

```python
import pandas as pd
from nlp_mvp.shared.db import get_engine

def extract_weekly_facts(user_id, week_start):
    engine = get_engine()
    query = """
        SELECT mh.meal_date, mh.menu, mh.satisfaction,
               COALESCE(ni.calories, 0) AS calories,
               COALESCE(ni.protein, 0) AS protein,
               COALESCE(ni.carbs, 0) AS carbs,
               COALESCE(ni.fat, 0) AS fat,
               COALESCE(ni.sodium, 0) AS sodium,
               r.category
        FROM meal_history mh
        LEFT JOIN nutrition_info ni ON mh.normalized_menu_id = ni.id
        LEFT JOIN restaurants r ON mh.restaurant_id = r.id
        WHERE mh.user_id = :uid
          AND mh.meal_date >= :start
          AND mh.meal_date < date(:start, '+7 days')
    """
    df = pd.read_sql(text(query), engine, params={"uid": user_id, "start": week_start})
    # 집계 로직
    ...
```

### 3.3 영양 기준값 설정

**출처:** 한국영양학회 권장 섭취량 (성인 기준)

| 영양소 | 일일 권장 | 주간 환산 (5 영업일) |
|-------|---------|----------------|
| 칼로리 | 2,000 kcal | 10,000 kcal |
| 단백질 | 60 g | 300 g |
| 탄수화물 | 300 g | 1,500 g |
| 지방 | 55 g | 275 g |
| 나트륨 (상한) | 2,000 mg | 10,000 mg |
| 식이섬유 | 25 g | 125 g |

**개인화:**
- `users.target_calories`, `users.target_protein` 컬럼 존재 시 그 값 사용
- 없으면 기본값

**판정 로직:**
```python
LACK_THRESHOLD = 0.8   # 권장의 80% 미만 = 부족
EXCESS_THRESHOLD = 1.2 # 권장의 120% 이상 = 과다

if avg_protein < target_protein * LACK_THRESHOLD:
    lack.append("단백질")
if avg_sodium > target_sodium * EXCESS_THRESHOLD:
    excess.append("나트륨")
```

### 3.4 "Best Day" / "Worst Day" 판정

**후보 지표:**

| 지표 | 공식 | 특성 |
|------|-----|-----|
| 총 칼로리 근접도 | `1 - abs(total - target) / target` | 목표 달성도 |
| 영양 균형 점수 | 4대 영양소 편차 합 | 균형 |
| **만족도 × 균형** | `satisfaction × balance` | **감정 + 객관** |
| 순수 만족도 | `satisfaction` | 주관만 |

**결정:** **영양 균형 점수** (일일 단위)

```python
def day_balance_score(day_row) -> float:
    """4대 영양소의 목표 대비 균형도 (0~1)."""
    target = {
        "calories": 2000, "protein": 60, "carbs": 300, "fat": 55
    }
    deviations = [
        abs(day_row[k] - target[k]) / target[k]
        for k in target
    ]
    return max(0, 1 - sum(deviations) / len(deviations))
```

### 3.5 리포트 문체 (Tone) 선택

**후보 비교:**

| 어투 | 예시 | 느낌 | MVP 선택 |
|------|-----|-----|--------|
| **격식체 + 전문** | "귀하의 주간 단백질 섭취량은 48g 으로..." | 병원 같음 | ❌ |
| **구어체 + 친근** | "이번 주 단백질이 살짝 부족했어요 😊" | 친구 같음 | ✅ |
| 존댓말 + 격려 | "잘하고 계세요! 조금만 더 추가해볼까요?" | 코치 같음 | ✅ (혼합) |
| 반말 + 발랄 | "이번 주 탄단지 밸런스 굿! 🎉" | 친구 같음 | ❌ (부적절) |

**결정:** **존댓말 + 친근 + 격려 혼합**
- 기본: 존댓말
- 이모지 2~3개
- 부정적 표현보다 긍정 치환 ("부족" → "조금 더 채우면 좋을 것 같아요")

§12 에 상세 가이드.

### 3.6 엣지 케이스 처리

**시나리오:**

| 케이스 | 처리 방식 |
|-------|---------|
| 이력 0건 | 리포트 생성 스킵, "기록이 아직 없어요" 메시지 |
| 이력 1~2건 | 경고 + 간단 요약 ("아직 데이터가 적어서 정확한 분석이 어려워요") |
| 이력 3~4건 | 정상 생성 + "더 많은 기록이 있으면 좋아요" |
| 이력 5건+ | 정상 생성 + 풍부한 분석 |
| 영양 DB 조인 실패 | calories/protein 등 NULL → "영양 정보 미확인" 으로 처리 |
| 극단 편식 (1 카테고리만) | "다양성 제안" 섹션 추가 |
| target 값 없음 | 기본값 (2,000 kcal / 60g protein) 사용 |

### 3.7 재생성 정책

**질문:** 주간 리포트를 매일 재생성? 주 1회? 요청 시?

**후보:**

| 방식 | 장단점 |
|------|------|
| 매일 자동 생성 | 최신 데이터 반영, LLM 호출 많음 |
| 주 1회 (월요일) 배치 | 일관성, 요청 시 과거 주 조회만 |
| **요청 시 생성 + 캐싱** | **유연, 사용자 경험 좋음** |

**결정:** **요청 시 생성 + `nutrition_reports` 캐싱**

```python
def get_or_generate_report(user_id, week_start):
    # 1. DB 조회
    existing = fetch_from_db(user_id, week_start)
    if existing and not is_stale(existing):
        return existing

    # 2. 생성 + 저장
    report = generator.generate(user_id, week_start)
    save_to_db(report)
    return report
```

**Stale 판정:** 주 진행 중이면 4시간 캐시, 완료된 주는 영구 캐시

### 3.8 LLM Fallback 전략

**실패 케이스:**
- Ollama 서버 다운
- 타임아웃
- 응답 품질 이상 (너무 짧거나 JSON 오염)

**3단계 Fallback:**

```
Primary:    Ollama + 프롬프트
    ↓ 실패
Secondary:  경량 템플릿 (f-string)
    ↓ 실패
Tertiary:   "이번 주 N회 식사하셨어요" 최소 메시지
```

```python
def generate_report_with_fallback(facts):
    try:
        return llm_generate(facts)
    except Exception as e:
        logger.warning(f"LLM failed, using template: {e}")
        try:
            return render_template(facts)
        except Exception as e2:
            logger.error(f"Template failed: {e2}")
            return minimal_message(facts)
```

---

## 4. 확장 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────────┐
│                 사용자 요청 (React 대시보드 / CLI / API)             │
│                 "이번 주 영양 리포트 보여줘"                         │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│          ReportGenerator.generate(user_id, week_start)           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ① 캐시 조회: nutrition_reports 에 기존 리포트 있는가?      │  │
│  │    YES & 최신 → 반환                                      │  │
│  │    NO  → 다음 단계                                        │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ② fact_extractor.extract_weekly_facts()                  │  │
│  │                                                          │  │
│  │    SQL 집계 (meal_history ⨝ nutrition_info ⨝ users)     │  │
│  │    → facts dict {                                        │  │
│  │         week_label, meal_count,                           │  │
│  │         total_calories, avg_protein, ...,                 │  │
│  │         lack, excess,                                     │  │
│  │         best_day, worst_day,                              │  │
│  │         top_categories                                    │  │
│  │       }                                                   │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ③ 엣지 케이스 체크                                        │  │
│  │    meal_count == 0 → "기록 없음" 메시지                   │  │
│  │    meal_count < 3  → 경고 + 간단 리포트                   │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ④ prompt.build_report_prompt(facts)                      │  │
│  │                                                          │  │
│  │    messages = [                                          │  │
│  │      {system: REPORT_SYSTEM_PROMPT},                     │  │
│  │      {user: facts 를 자연어로 정리 + 요청}                │  │
│  │    ]                                                     │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ⑤ OllamaClient.chat(messages, temperature=0.5)           │  │
│  │    → nlg_text                                             │  │
│  │                                                          │  │
│  │    실패 시 → render_template(facts) (fallback)           │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ⑥ 품질 검증                                               │  │
│  │    · 길이 (50~500 자)                                      │  │
│  │    · 금칙어 (의학적 단정, 비판적 표현)                     │  │
│  │    · 이모지 개수 (1~5개)                                   │  │
│  │    실패 시 재시도 (최대 2회)                               │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ⑦ DB 저장 (nutrition_reports UPSERT)                      │  │
│  └───────────────────────┬──────────────────────────────────┘  │
└──────────────────────────┼───────────────────────────────────────┘
                           ▼
           {
             "report_id": 42,
             "week_label": "2026년 4월 1주차",
             "facts": {...},
             "nlg_text": "이번 주 수고하셨어요! 💪 ...",
             "generated_at": "2026-04-07T10:30:00"
           }
```

---

## 5. 파일 목록 및 의존성 그래프

```
┌─────────────────────────────────────┐
│ Step 0 (선행)                        │
├─────────────────────────────────────┤
│ shared/db.py                        │
│ shared/logger.py                    │
│ shared/ollama_client.py             │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ Step 4 — D5 NLG 리포트                │
├─────────────────────────────────────┤
│                                     │
│  nlg_report/                        │
│  ├─ fact_extractor.py   ◄── Day 1  │
│  │   ├─ extract_weekly_facts()     │
│  │   ├─ day_balance_score()        │
│  │   ├─ detect_lack_excess()       │
│  │   └─ DEFAULT_TARGETS            │
│  │                                  │
│  ├─ prompt.py           ◄── Day 2  │
│  │   ├─ REPORT_SYSTEM_PROMPT       │
│  │   ├─ build_report_prompt()      │
│  │   └─ format_facts_for_user()    │
│  │                                  │
│  ├─ templates/                      │
│  │   ├─ fallback.txt (f-string)    │
│  │   └─ minimal.txt                │
│  │                                  │
│  ├─ generator.py        ◄── Day 3  │
│  │   ├─ ReportGenerator            │
│  │   ├─ generate()                 │
│  │   ├─ get_or_generate()          │
│  │   ├─ render_template()          │
│  │   ├─ validate_report()          │
│  │   └─ ensure_schema()            │
│  │                                  │
│  ├─ samples/                        │
│  │   └─ sample_reports.md          │
│  │                                  │
│  └─ tests/                          │
│      ├─ test_fact_extractor.py     │
│      ├─ test_prompt.py             │
│      └─ test_generator.py          │
│                                     │
│  integration/                       │
│  └─ scoring_patch.py    ◄── Day 5  │
│      (Step 1/3 통합)                │
│                                     │
│  api/                               │
│  └─ routers/reports.py  ◄── Day 5  │
│      (GET /nlp/reports/weekly)     │
│                                     │
│  notebooks/04_nlg_samples.ipynb ◄── Day 4 │
└─────────────────────────────────────┘
```

---

## 6. 파일별 상세 명세

### 6.1 `nlg_report/fact_extractor.py`

```python
"""
주간 meal_history 집계 → facts dict.
규칙 기반, 100% 정확한 수치만 담당.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from typing import Any, Optional

import pandas as pd
from sqlalchemy import text

from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 기준값 (성인 기본)
# =============================================================================
DEFAULT_TARGETS = {
    "calories_per_day": 2000,
    "protein_per_day": 60,
    "carbs_per_day": 300,
    "fat_per_day": 55,
    "sodium_per_day": 2000,  # 상한
    "fiber_per_day": 25,
}

LACK_THRESHOLD = 0.8   # 권장의 80% 미만
EXCESS_THRESHOLD = 1.2 # 권장의 120% 이상


# =============================================================================
# 데이터 클래스
# =============================================================================
@dataclass
class WeeklyFacts:
    week_label: str
    week_start: str
    week_end: str
    user_id: int
    user_name: str
    meal_count: int
    total_calories: float
    avg_calories_per_meal: float
    avg_protein: float
    avg_carbs: float
    avg_fat: float
    avg_sodium: float
    target_calories: float
    target_protein: float
    lack: list[str] = field(default_factory=list)
    excess: list[str] = field(default_factory=list)
    best_day: Optional[dict] = None
    worst_day: Optional[dict] = None
    top_categories: list[tuple[str, int]] = field(default_factory=list)
    avg_satisfaction: Optional[float] = None
    has_nutrition_data: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_empty(self) -> bool:
        return self.meal_count == 0

    def is_sparse(self) -> bool:
        return 0 < self.meal_count < 3


# =============================================================================
# 주차 유틸
# =============================================================================
def get_week_start(d: Optional[date] = None) -> date:
    """해당 날짜가 속한 주의 월요일."""
    d = d or date.today()
    return d - timedelta(days=d.weekday())


def format_week_label(week_start: date) -> str:
    """'2026년 4월 1주차' 형식."""
    year = week_start.year
    month = week_start.month
    week_of_month = (week_start.day - 1) // 7 + 1
    return f"{year}년 {month}월 {week_of_month}주차"


# =============================================================================
# 집계 로직
# =============================================================================
def _load_user_profile(user_id: int) -> dict[str, Any]:
    engine = get_engine()
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT name, target_calories, target_protein FROM users WHERE id = :uid"),
                {"uid": user_id},
            ).fetchone()
        if row:
            return {
                "name": row[0] or f"사용자{user_id}",
                "target_calories": row[1] or DEFAULT_TARGETS["calories_per_day"],
                "target_protein": row[2] or DEFAULT_TARGETS["protein_per_day"],
            }
    except Exception as e:
        logger.warning(f"_load_user_profile failed: {e}")

    return {
        "name": f"사용자{user_id}",
        "target_calories": DEFAULT_TARGETS["calories_per_day"],
        "target_protein": DEFAULT_TARGETS["protein_per_day"],
    }


def _load_meals_df(user_id: int, week_start: date) -> pd.DataFrame:
    engine = get_engine()
    week_end = week_start + timedelta(days=7)
    query = """
        SELECT mh.meal_date,
               mh.menu,
               mh.satisfaction,
               COALESCE(ni.calories, 0) AS calories,
               COALESCE(ni.protein, 0)  AS protein,
               COALESCE(ni.carbs, 0)    AS carbs,
               COALESCE(ni.fat, 0)      AS fat,
               COALESCE(ni.sodium, 0)   AS sodium,
               r.category
        FROM meal_history mh
        LEFT JOIN nutrition_info ni ON mh.normalized_menu_id = ni.id
        LEFT JOIN restaurants r ON mh.restaurant_id = r.id
        WHERE mh.user_id = :uid
          AND mh.meal_date >= :start
          AND mh.meal_date < :end
        ORDER BY mh.meal_date
    """
    try:
        return pd.read_sql(
            text(query), engine,
            params={"uid": user_id, "start": week_start, "end": week_end},
        )
    except Exception as e:
        logger.warning(f"_load_meals_df failed: {e}")
        return pd.DataFrame()


def day_balance_score(row: pd.Series) -> float:
    """일일 영양 균형 점수 (0~1)."""
    target = DEFAULT_TARGETS
    values = {
        "calories": row.get("calories", 0),
        "protein": row.get("protein", 0),
        "carbs": row.get("carbs", 0),
        "fat": row.get("fat", 0),
    }
    deviations = []
    for k, v in values.items():
        t = target[f"{k}_per_day"]
        if t > 0 and v > 0:
            deviations.append(abs(v - t) / t)
    if not deviations:
        return 0.0
    return max(0.0, 1.0 - sum(deviations) / len(deviations))


def detect_lack_excess(
    avg: dict[str, float],
    targets: dict[str, float],
) -> tuple[list[str], list[str]]:
    lack, excess = [], []

    if avg["protein"] < targets["target_protein"] * LACK_THRESHOLD:
        lack.append("단백질")

    if avg["calories"] < targets["target_calories"] * LACK_THRESHOLD:
        lack.append("칼로리")
    elif avg["calories"] > targets["target_calories"] * EXCESS_THRESHOLD:
        excess.append("칼로리")

    if avg["sodium"] > DEFAULT_TARGETS["sodium_per_day"] * EXCESS_THRESHOLD:
        excess.append("나트륨")

    if avg["fat"] > DEFAULT_TARGETS["fat_per_day"] * EXCESS_THRESHOLD:
        excess.append("지방")

    return lack, excess


def extract_weekly_facts(
    user_id: int,
    week_start: Optional[date] = None,
) -> WeeklyFacts:
    """
    주간 meal_history 집계 → WeeklyFacts.
    """
    week_start = week_start or get_week_start()
    week_end = week_start + timedelta(days=7)

    profile = _load_user_profile(user_id)
    df = _load_meals_df(user_id, week_start)

    facts = WeeklyFacts(
        week_label=format_week_label(week_start),
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        user_id=user_id,
        user_name=profile["name"],
        meal_count=len(df),
        total_calories=0,
        avg_calories_per_meal=0,
        avg_protein=0,
        avg_carbs=0,
        avg_fat=0,
        avg_sodium=0,
        target_calories=profile["target_calories"],
        target_protein=profile["target_protein"],
        has_nutrition_data=False,
    )

    if facts.is_empty():
        return facts

    # 영양 데이터 유효성 (0 만 있으면 DB join 실패)
    facts.has_nutrition_data = df["calories"].sum() > 0

    # 집계
    facts.total_calories = float(df["calories"].sum())
    facts.avg_calories_per_meal = float(df["calories"].mean())
    facts.avg_protein = float(df["protein"].mean())
    facts.avg_carbs = float(df["carbs"].mean())
    facts.avg_fat = float(df["fat"].mean())
    facts.avg_sodium = float(df["sodium"].mean())

    if "satisfaction" in df.columns:
        sat = df["satisfaction"].dropna()
        if len(sat) > 0:
            facts.avg_satisfaction = float(sat.mean())

    # 부족/과다 판정
    avg = {
        "calories": facts.avg_calories_per_meal,
        "protein": facts.avg_protein,
        "sodium": facts.avg_sodium,
        "fat": facts.avg_fat,
    }
    targets = {
        "target_calories": facts.target_calories / 3,  # 끼당
        "target_protein": facts.target_protein / 3,
    }
    facts.lack, facts.excess = detect_lack_excess(avg, targets)

    # Best/Worst day
    if facts.has_nutrition_data:
        df["balance_score"] = df.apply(day_balance_score, axis=1)
        best_idx = df["balance_score"].idxmax()
        worst_idx = df["balance_score"].idxmin()
        facts.best_day = {
            "date": str(df.loc[best_idx, "meal_date"]),
            "menu": str(df.loc[best_idx, "menu"] or ""),
            "balance_score": float(df.loc[best_idx, "balance_score"]),
            "reason": "가장 균형 잡힌 하루",
        }
        facts.worst_day = {
            "date": str(df.loc[worst_idx, "meal_date"]),
            "menu": str(df.loc[worst_idx, "menu"] or ""),
            "balance_score": float(df.loc[worst_idx, "balance_score"]),
            "reason": "균형이 아쉬웠던 날",
        }

    # Top categories
    if "category" in df.columns:
        cat_counter = Counter(df["category"].dropna().tolist())
        facts.top_categories = cat_counter.most_common(3)

    logger.info(
        f"extract_weekly_facts(user={user_id}, week={facts.week_label}): "
        f"meals={facts.meal_count}, lack={facts.lack}, excess={facts.excess}"
    )
    return facts
```

### 6.2 `nlg_report/prompt.py`

```python
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
    """
    facts 를 LLM 에게 전달할 user content 로 변환.
    """
    if facts.is_empty():
        return f"""
{facts.user_name}님의 {facts.week_label} 리포트를 작성해주세요.

⚠️ 이번 주 식사 기록이 없습니다. 기록을 독려하는 짧은 메시지를 작성해주세요.
"""

    if facts.is_sparse():
        return f"""
{facts.user_name}님의 {facts.week_label} 리포트를 작성해주세요.

⚠️ 이번 주 식사 기록이 {facts.meal_count}건뿐이에요.
데이터가 적다는 점을 자연스럽게 언급하면서, 격려의 메시지와
더 많은 기록을 권유하는 내용을 포함해주세요.
"""

    # 정상 케이스
    lack_str = ", ".join(facts.lack) if facts.lack else "없음"
    excess_str = ", ".join(facts.excess) if facts.excess else "없음"

    top_cats = ", ".join(f"{c}({n}회)" for c, n in facts.top_categories[:2]) or "없음"

    best_day_str = ""
    if facts.best_day:
        best_day_str = f"- 최고의 날: {facts.best_day['date']} ({facts.best_day['menu']})"

    worst_day_str = ""
    if facts.worst_day:
        worst_day_str = f"- 아쉬운 날: {facts.worst_day['date']} ({facts.worst_day['menu']})"

    sat_str = ""
    if facts.avg_satisfaction is not None:
        sat_str = f"- 평균 만족도: {facts.avg_satisfaction:.1f}/5"

    return f"""
{facts.user_name}님의 {facts.week_label} 식사 요약입니다.

- 식사 수: {facts.meal_count}회
- 총 칼로리: {facts.total_calories:.0f} kcal
- 평균 단백질: {facts.avg_protein:.0f}g (일일 목표 {facts.target_protein:.0f}g)
- 부족: {lack_str}
- 과다: {excess_str}
{best_day_str}
{worst_day_str}
{sat_str}
- 자주 먹은 카테고리: {top_cats}

위 정보를 바탕으로 3~5문장의 친근한 리포트를 작성해주세요.
"""


def build_report_prompt(facts: WeeklyFacts) -> list[dict[str, str]]:
    """
    Ollama chat messages 형식.
    """
    return [
        {"role": "system", "content": REPORT_SYSTEM_PROMPT},
        {"role": "user", "content": format_facts_for_user(facts)},
    ]
```

### 6.3 `nlg_report/templates/fallback.txt`

```text
{user_name}님의 {week_label} 리포트예요 🍱

이번 주 총 {meal_count}회 식사하셨고, 평균 단백질 {avg_protein:.0f}g 섭취하셨어요.
{lack_message}
내일은 균형 잡힌 한 끼로 새로운 한 주를 시작해볼까요? ✨
```

### 6.4 `nlg_report/generator.py`

```python
"""
리포트 생성기 (LLM + 템플릿 fallback + DB).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import text

from nlp_mvp.nlg_report.fact_extractor import (
    WeeklyFacts, extract_weekly_facts, get_week_start
)
from nlp_mvp.nlg_report.prompt import build_report_prompt
from nlp_mvp.shared.db import get_engine, get_session
from nlp_mvp.shared.logger import get_logger
from nlp_mvp.shared.ollama_client import OllamaClient

logger = get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"

# =============================================================================
# 스키마
# =============================================================================
REPORTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS nutrition_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    week_start DATE NOT NULL,
    facts JSON NOT NULL,
    nlg_text TEXT NOT NULL,
    generation_method TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, week_start)
);
CREATE INDEX IF NOT EXISTS idx_reports_user ON nutrition_reports(user_id);
"""


def ensure_schema() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for stmt in REPORTS_TABLE_SQL.strip().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
    logger.info("nutrition_reports schema ensured")


# =============================================================================
# 품질 검증
# =============================================================================
FORBIDDEN_WORDS = [
    "병", "질병", "진단", "처방", "의사", "약",
    "나쁩니다", "잘못", "위험", "금지",
]

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F9FF\U00002600-\U000027BF]"
)


def validate_report(text: str) -> dict[str, Any]:
    """
    생성된 리포트의 품질 검증.

    Returns:
        {"valid": bool, "issues": list[str], ...}
    """
    issues = []

    # 길이
    length = len(text)
    if length < 50:
        issues.append(f"too_short: {length}")
    if length > 600:
        issues.append(f"too_long: {length}")

    # 이모지 개수
    emoji_count = len(_EMOJI_RE.findall(text))
    if emoji_count == 0:
        issues.append("no_emoji")
    if emoji_count > 6:
        issues.append(f"too_many_emoji: {emoji_count}")

    # 금칙어
    found = [w for w in FORBIDDEN_WORDS if w in text]
    if found:
        issues.append(f"forbidden: {found}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "length": length,
        "emoji_count": emoji_count,
    }


# =============================================================================
# 템플릿 fallback
# =============================================================================
def render_template(facts: WeeklyFacts) -> str:
    """LLM 실패 시 f-string 기반 최소 리포트."""
    if facts.is_empty():
        return (
            f"{facts.user_name}님, 이번 주 식사 기록이 아직 없어요 🍱\n"
            "식사를 기록하시면 더 맞춤 리포트를 드릴 수 있어요 😊"
        )

    lack_message = ""
    if facts.lack:
        lack_message = f"{facts.lack[0]}이(가) 조금 부족했어요. 내일은 더 채워보세요! 💪"
    else:
        lack_message = "영양 균형이 꽤 괜찮았어요! 👍"

    template_path = TEMPLATES_DIR / "fallback.txt"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = (
            "{user_name}님의 {week_label} 리포트예요 🍱\n\n"
            "이번 주 총 {meal_count}회 식사하셨고, "
            "평균 단백질 {avg_protein:.0f}g 섭취하셨어요.\n"
            "{lack_message}\n"
            "내일은 균형 잡힌 한 끼로 새로운 한 주를 시작해볼까요? ✨"
        )

    return template.format(
        user_name=facts.user_name,
        week_label=facts.week_label,
        meal_count=facts.meal_count,
        avg_protein=facts.avg_protein,
        lack_message=lack_message,
    )


def minimal_message(facts: WeeklyFacts) -> str:
    """최후 fallback."""
    return (
        f"{facts.user_name}님, 이번 주 {facts.meal_count}회 식사하셨어요. "
        "다음 주도 건강한 한 끼 되세요 🍱"
    )


# =============================================================================
# 리포트 생성 클래스
# =============================================================================
@dataclass
class ReportResult:
    report_id: Optional[int]
    user_id: int
    week_start: str
    week_label: str
    facts: dict[str, Any]
    nlg_text: str
    generation_method: str  # "llm" | "template" | "minimal"
    generated_at: str
    validation: dict[str, Any] = None


class ReportGenerator:
    """
    주간 영양 리포트 생성기.
    """

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        max_retries: int = 2,
        temperature: float = 0.5,
    ):
        self.ollama = ollama_client or OllamaClient()
        self.max_retries = max_retries
        self.temperature = temperature
        logger.info("ReportGenerator initialized")

    # -------------------------------------------------------------------------
    # 메인 진입점
    # -------------------------------------------------------------------------
    def generate(
        self,
        user_id: int,
        week_start: Optional[date] = None,
        save: bool = True,
    ) -> ReportResult:
        ensure_schema()
        week_start = week_start or get_week_start()

        # 1. 팩트 추출
        facts = extract_weekly_facts(user_id, week_start)

        # 2. LLM 생성 (재시도 포함)
        nlg_text, method, validation = self._generate_with_fallback(facts)

        # 3. DB 저장
        report_id = None
        if save:
            report_id = self._save(facts, nlg_text, method)

        return ReportResult(
            report_id=report_id,
            user_id=user_id,
            week_start=facts.week_start,
            week_label=facts.week_label,
            facts=facts.to_dict(),
            nlg_text=nlg_text,
            generation_method=method,
            generated_at=datetime.utcnow().isoformat(),
            validation=validation,
        )

    def get_or_generate(
        self,
        user_id: int,
        week_start: Optional[date] = None,
    ) -> ReportResult:
        """캐시 우선, 없으면 생성."""
        week_start = week_start or get_week_start()
        existing = self._fetch_existing(user_id, week_start)
        if existing is not None:
            logger.info(f"Cached report hit: user={user_id}, week={week_start}")
            return existing
        return self.generate(user_id, week_start, save=True)

    # -------------------------------------------------------------------------
    # 3단계 fallback
    # -------------------------------------------------------------------------
    def _generate_with_fallback(
        self,
        facts: WeeklyFacts,
    ) -> tuple[str, str, dict[str, Any]]:
        # 1. LLM 시도
        for attempt in range(1, self.max_retries + 2):
            try:
                messages = build_report_prompt(facts)
                text_out = self.ollama.chat(
                    messages=messages,
                    options={"temperature": self.temperature, "num_predict": 400},
                )
                validation = validate_report(text_out)
                if validation["valid"]:
                    logger.info(f"LLM generate OK (attempt={attempt})")
                    return text_out, "llm", validation
                logger.warning(f"LLM validation failed (attempt={attempt}): {validation['issues']}")
            except Exception as e:
                logger.warning(f"LLM generate failed (attempt={attempt}): {e}")

        # 2. 템플릿 fallback
        try:
            text_out = render_template(facts)
            return text_out, "template", {"valid": True, "issues": [], "fallback": True}
        except Exception as e:
            logger.error(f"Template render failed: {e}")

        # 3. 최소 메시지
        return minimal_message(facts), "minimal", {"valid": True, "issues": [], "fallback": True}

    # -------------------------------------------------------------------------
    # DB 접근
    # -------------------------------------------------------------------------
    def _save(
        self,
        facts: WeeklyFacts,
        nlg_text: str,
        method: str,
    ) -> int:
        with get_session() as session:
            result = session.execute(
                text("""
                    INSERT INTO nutrition_reports
                        (user_id, week_start, facts, nlg_text, generation_method)
                    VALUES (:uid, :ws, :facts, :nlg, :method)
                    ON CONFLICT (user_id, week_start) DO UPDATE SET
                        facts = excluded.facts,
                        nlg_text = excluded.nlg_text,
                        generation_method = excluded.generation_method,
                        created_at = CURRENT_TIMESTAMP
                    RETURNING id
                """),
                {
                    "uid": facts.user_id,
                    "ws": facts.week_start,
                    "facts": json.dumps(facts.to_dict(), ensure_ascii=False),
                    "nlg": nlg_text,
                    "method": method,
                },
            )
            row = result.fetchone()
            session.commit()
            return int(row[0]) if row else -1

    def _fetch_existing(
        self,
        user_id: int,
        week_start: date,
    ) -> Optional[ReportResult]:
        try:
            with get_session() as session:
                row = session.execute(
                    text("""
                        SELECT id, facts, nlg_text, generation_method, created_at
                        FROM nutrition_reports
                        WHERE user_id = :uid AND week_start = :ws
                    """),
                    {"uid": user_id, "ws": week_start.isoformat()},
                ).fetchone()
            if not row:
                return None
            facts_dict = json.loads(row[1])
            return ReportResult(
                report_id=int(row[0]),
                user_id=user_id,
                week_start=week_start.isoformat(),
                week_label=facts_dict.get("week_label", ""),
                facts=facts_dict,
                nlg_text=row[2],
                generation_method=row[3],
                generated_at=str(row[4]),
                validation={"valid": True, "cached": True},
            )
        except Exception as e:
            logger.warning(f"_fetch_existing failed: {e}")
            return None


# =============================================================================
# CLI
# =============================================================================
def main():
    import argparse
    import logging

    parser = argparse.ArgumentParser(description="NLG 리포트 생성기")
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--week-start", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--force", action="store_true", help="캐시 무시")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    ws = date.fromisoformat(args.week_start) if args.week_start else None
    gen = ReportGenerator()
    if args.force:
        result = gen.generate(args.user_id, ws, save=not args.no_save)
    else:
        result = gen.get_or_generate(args.user_id, ws)

    print("\n" + "=" * 60)
    print(f"📊 {result.week_label} - {result.facts.get('user_name', '')}")
    print("=" * 60)
    print(result.nlg_text)
    print("=" * 60)
    print(f"method: {result.generation_method}")
    print(f"report_id: {result.report_id}")


if __name__ == "__main__":
    main()
```

### 6.5 `api/routers/reports.py` (Step 5 통합)

```python
"""
FastAPI 엔드포인트.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from nlp_mvp.nlg_report.generator import ReportGenerator

router = APIRouter(prefix="/nlp/reports", tags=["reports"])
_generator = ReportGenerator()


class ReportResponse(BaseModel):
    report_id: int | None
    user_id: int
    week_label: str
    nlg_text: str
    generation_method: str
    facts: dict


@router.get("/weekly/{user_id}", response_model=ReportResponse)
def get_weekly_report(user_id: int):
    """사용자의 이번 주 리포트 조회 (없으면 생성)."""
    try:
        result = _generator.get_or_generate(user_id)
        return ReportResponse(
            report_id=result.report_id,
            user_id=result.user_id,
            week_label=result.week_label,
            nlg_text=result.nlg_text,
            generation_method=result.generation_method,
            facts=result.facts,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weekly/{user_id}/regenerate", response_model=ReportResponse)
def regenerate_weekly_report(user_id: int):
    """강제 재생성."""
    try:
        result = _generator.generate(user_id, save=True)
        return ReportResponse(
            report_id=result.report_id,
            user_id=result.user_id,
            week_label=result.week_label,
            nlg_text=result.nlg_text,
            generation_method=result.generation_method,
            facts=result.facts,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 6.6 테스트

**test_fact_extractor.py:**
```python
from datetime import date
import pytest
from sqlalchemy import create_engine, text

from nlp_mvp.nlg_report.fact_extractor import (
    extract_weekly_facts, day_balance_score, detect_lack_excess,
    format_week_label, get_week_start, DEFAULT_TARGETS
)
from nlp_mvp.shared.db import override_engine, reset_engine


@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, target_calories REAL, target_protein REAL)"))
        conn.execute(text("INSERT INTO users VALUES (1, 'Test', 2000, 60)"))
        conn.execute(text("""
            CREATE TABLE meal_history (
                id INTEGER PRIMARY KEY, user_id INTEGER, restaurant_id INTEGER,
                meal_date DATE, menu TEXT, normalized_menu_id TEXT, satisfaction INTEGER
            )
        """))
        conn.execute(text("CREATE TABLE nutrition_info (id TEXT PRIMARY KEY, food_name TEXT, calories REAL, protein REAL, carbs REAL, fat REAL, sodium REAL)"))
        conn.execute(text("CREATE TABLE restaurants (id INTEGER PRIMARY KEY, category TEXT)"))
    return engine


@pytest.fixture(autouse=True)
def _reset(test_engine):
    override_engine(test_engine)
    yield
    reset_engine()


class TestWeekUtils:
    def test_format_label(self):
        assert "2026" in format_week_label(date(2026, 4, 6))

    def test_get_week_start_monday(self):
        # 2026-04-08 is Wednesday
        ws = get_week_start(date(2026, 4, 8))
        assert ws.weekday() == 0  # Monday
        assert ws == date(2026, 4, 6)


class TestBalanceScore:
    def test_perfect(self):
        import pandas as pd
        row = pd.Series({
            "calories": 2000, "protein": 60, "carbs": 300, "fat": 55
        })
        assert day_balance_score(row) > 0.95

    def test_poor(self):
        import pandas as pd
        row = pd.Series({"calories": 500, "protein": 10, "carbs": 50, "fat": 5})
        assert day_balance_score(row) < 0.5


class TestDetectLackExcess:
    def test_low_protein(self):
        avg = {"calories": 650, "protein": 10, "sodium": 500, "fat": 20}
        targets = {"target_calories": 650, "target_protein": 20}
        lack, excess = detect_lack_excess(avg, targets)
        assert "단백질" in lack

    def test_high_sodium(self):
        avg = {"calories": 650, "protein": 30, "sodium": 3000, "fat": 20}
        targets = {"target_calories": 650, "target_protein": 20}
        lack, excess = detect_lack_excess(avg, targets)
        assert "나트륨" in excess


class TestExtractWeeklyFacts:
    def test_empty_week(self):
        facts = extract_weekly_facts(user_id=1, week_start=date(2026, 4, 6))
        assert facts.is_empty()
        assert facts.meal_count == 0

    def test_with_meals(self, test_engine):
        with test_engine.begin() as conn:
            conn.execute(text("INSERT INTO nutrition_info VALUES ('kimchi', '김치찌개', 650, 22, 80, 25, 1300)"))
            conn.execute(text("""
                INSERT INTO meal_history (id, user_id, meal_date, menu, normalized_menu_id, satisfaction)
                VALUES (1, 1, '2026-04-06', '김치찌개', 'kimchi', 5),
                       (2, 1, '2026-04-07', '김치찌개', 'kimchi', 4)
            """))
        facts = extract_weekly_facts(user_id=1, week_start=date(2026, 4, 6))
        assert facts.meal_count == 2
        assert facts.avg_protein == 22.0
```

**test_generator.py:**
```python
from unittest.mock import MagicMock
import pytest

from nlp_mvp.nlg_report.fact_extractor import WeeklyFacts
from nlp_mvp.nlg_report.generator import (
    ReportGenerator, validate_report, render_template, minimal_message
)


class TestValidate:
    def test_valid(self):
        r = validate_report("이번 주 수고하셨어요 💪 잘 챙겨드셨네요 😊 내일도 힘내요 ✨")
        assert r["valid"] is True

    def test_too_short(self):
        r = validate_report("짧음")
        assert not r["valid"]
        assert any("too_short" in i for i in r["issues"])

    def test_no_emoji(self):
        r = validate_report("이번 주 50자 이상 충분한 길이의 리포트입니다 아주 길게 작성해봅니다")
        assert not r["valid"]
        assert "no_emoji" in r["issues"]

    def test_forbidden_word(self):
        r = validate_report("이번 주 잘못되었습니다 💪 😊 ✨")
        assert not r["valid"]


class TestRenderTemplate:
    def test_empty_facts(self):
        facts = WeeklyFacts(
            week_label="4월 1주차", week_start="2026-04-06", week_end="2026-04-13",
            user_id=1, user_name="Test", meal_count=0,
            total_calories=0, avg_calories_per_meal=0,
            avg_protein=0, avg_carbs=0, avg_fat=0, avg_sodium=0,
            target_calories=2000, target_protein=60,
        )
        text = render_template(facts)
        assert "기록" in text
        assert "Test" in text

    def test_with_meals(self):
        facts = WeeklyFacts(
            week_label="4월 1주차", week_start="2026-04-06", week_end="2026-04-13",
            user_id=1, user_name="Test", meal_count=5,
            total_calories=3500, avg_calories_per_meal=700,
            avg_protein=25, avg_carbs=90, avg_fat=30, avg_sodium=1500,
            target_calories=2000, target_protein=60,
            lack=["단백질"],
        )
        text = render_template(facts)
        assert "단백질" in text


class TestReportGenerator:
    def test_llm_success(self):
        mock_ollama = MagicMock()
        mock_ollama.chat.return_value = (
            "이번 주 수고하셨어요 💪 단백질이 조금 부족했지만 내일은 닭가슴살을 드셔보세요 🍗 화이팅! ✨"
        )
        gen = ReportGenerator(ollama_client=mock_ollama)
        # Skip save (no DB)
        # 이 테스트는 실제 DB 없이는 save 를 건너뜀 → 수동 검증
```

---

## 7. 구현 순서 (5일 체크리스트)

### Day 1 — 팩트 추출기
- [ ] `fact_extractor.py` 의 `WeeklyFacts` 데이터 클래스
- [ ] `extract_weekly_facts()` SQL + 집계
- [ ] `day_balance_score()`, `detect_lack_excess()`
- [ ] `ensure_schema()` (`nutrition_reports`)
- [ ] `test_fact_extractor.py` 통과

### Day 2 — 프롬프트
- [ ] `prompt.py` 의 `REPORT_SYSTEM_PROMPT`
- [ ] `format_facts_for_user()` 3개 케이스 (정상·sparse·empty)
- [ ] `build_report_prompt()`
- [ ] 10개 수동 프롬프트 테스트 (다양한 facts)

### Day 3 — Generator
- [ ] `generator.py` 의 `ReportGenerator`
- [ ] `generate()`, `get_or_generate()`
- [ ] `_generate_with_fallback()` 3단계
- [ ] `validate_report()` 품질 검증
- [ ] `render_template()` fallback
- [ ] `templates/fallback.txt` 작성
- [ ] DB UPSERT 동작
- [ ] `test_generator.py` 통과

### Day 4 — 샘플 + 평가
- [ ] 10명 더미 사용자 facts 수동 생성
- [ ] `ReportGenerator.generate()` 10회 실행
- [ ] `samples/sample_reports.md` 저장
- [ ] 블라인드 평가 (3축 × 5점)
- [ ] `04_nlg_samples.ipynb` 실행

### Day 5 — 통합
- [ ] `api/routers/reports.py` FastAPI 라우터
- [ ] `integration/scoring_patch.py` 보강 (선택)
- [ ] React 대시보드 "AI 코멘트" 카드
- [ ] end-to-end 시연 (사용자 클릭 → 리포트 생성 → 카드 표시)
- [ ] `nlp_mvp/README.md` 100% 체크

---

## 8. KPI 및 검증 기준

| # | 지표 | 측정 | 목표 | 필수 |
|---|------|-----|-----|-----|
| 1 | 팩트 추출 정확도 | 수동 10건 | 100% | ✅ |
| 2 | LLM 생성 성공률 | 50회 호출 | ≥ 95% | ✅ |
| 3 | 자연스러움 평가 | 블라인드 5점 | ≥ 4.0 | ✅ |
| 4 | 유용성 평가 | 블라인드 5점 | ≥ 4.0 | ✅ |
| 5 | 정확성 (팩트 오류) | 10건 검증 | 0건 | ✅ |
| 6 | 리포트 생성 속도 | 평균 | ≤ 5초 | ✅ |
| 7 | 캐시 hit 속도 | 평균 | ≤ 50ms | ⭐ |
| 8 | 엣지 케이스 | 0/3/7건 테스트 | 정상 출력 | ✅ |
| 9 | Template fallback | LLM 강제 실패 | 정상 출력 | ✅ |
| 10 | React 통합 | 카드 렌더링 | ✓ | ✅ |

---

## 9. 트러블슈팅 (Step 4 한정)

### 9.1 팩트 추출 시 JOIN 결과 NULL

**원인:** `meal_history.normalized_menu_id` 미설정 (Step 2 미완료)

**해결:**
- Step 2 먼저 실행
- 또는 COALESCE(영양값, 0) 후 `has_nutrition_data` 플래그로 분기

### 9.2 LLM 응답에 수치 오류

**예시:** 단백질 48g → "단백질 480g 섭취"

**해결:**
- 프롬프트에 "숫자를 변형하지 마세요" 명시
- `validate_report()` 에 수치 추출 후 facts 와 비교 (고급)

### 9.3 생성 리포트가 너무 길어짐

**해결:**
- `num_predict=400` → `256`
- 프롬프트에 "3~5문장" 강조
- 후처리 truncate (마지막 마침표 기준)

### 9.4 금칙어 빈번

**원인:** LLM 이 "질병 예방" 같은 단어 선호

**해결:**
- FORBIDDEN_WORDS 에 추가
- 프롬프트의 "금기 사항" 섹션 강화
- 재시도 로직

### 9.5 이모지 0개

**원인:** 일부 모델이 이모지 생략

**해결:**
- 프롬프트에 "반드시 2~3개 이모지" 명시
- 시스템 프롬프트에 이모지 예시 포함

### 9.6 캐시 충돌

**증상:** 같은 주에 두 번 생성되면 UNIQUE 제약 위반

**해결:** SQL 을 `ON CONFLICT DO UPDATE` 로 UPSERT (본 가이드 §6.4 참고)

### 9.7 `week_start` 로컬 vs UTC

**증상:** 자정 근처에 주차 경계 밀림

**해결:** `get_week_start()` 에서 로컬 date 사용, DB 저장 시 ISO 문자열

---

## 10. 재사용 가능한 기존 파일

### 10.1 채울 스켈레톤
| 파일 | 상태 |
|------|------|
| `nlg_report/fact_extractor.py` | 빈 → §6.1 |
| `nlg_report/prompt.py` | 빈 → §6.2 |
| `nlg_report/generator.py` | 빈 → §6.4 |
| `nlg_report/tests/test_fact_extractor.py` | 빈 → §6.6 |
| `api/routers/reports.py` | 빈 → §6.5 |
| `notebooks/04_nlg_samples.ipynb` | 스켈레톤 |

### 10.2 신규 생성
- `nlg_report/templates/fallback.txt` (§6.3)
- `nlg_report/tests/test_prompt.py` (§6.6)
- `nlg_report/tests/test_generator.py` (§6.6)

### 10.3 재사용 (shared/)
- `shared/db.py`, `shared/logger.py`, **`shared/ollama_client.py`**

---

## 11. 외부 의존성 확인

| 패키지 | 용도 |
|--------|-----|
| `pandas` 2.2.2 | SQL 집계 |
| `sqlalchemy` 2.0.32 | DB |
| `ollama` 0.3.0 | LLM |
| `fastapi` 0.112.0 | API |
| `pydantic` 2.8.2 | 스키마 |

**모두 `requirements.txt` 존재.** 추가 없음.

---

## 12. 리포트 문체 가이드 (Tone of Voice)

### 12.1 원칙 5개

1. **친근함 > 권위** — 영양학 박사 ❌, 친한 코치 ✅
2. **격려 > 경고** — "주의하세요" ❌, "조금만 더 채우면 좋아요" ✅
3. **행동 유도** — 모호한 조언보다 구체적 메뉴
4. **짧게** — 3~5문장, 300자 이내
5. **긍정 시작 + 긍정 마무리** — 샌드위치 구조

### 12.2 좋은 예 / 나쁜 예

| ❌ 나쁜 예 | ✅ 좋은 예 |
|---------|---------|
| "단백질이 부족합니다. 보충하세요." | "단백질이 살짝 아쉬웠어요. 내일은 닭가슴살 샐러드 어때요? 💪" |
| "나트륨 과다 섭취로 건강 위험 증가" | "이번 주 나트륨이 조금 많았어요. 내일은 담백한 한 끼로! 🥗" |
| "일주일간 총 12,450 kcal" | "이번 주도 열심히 달리셨네요! 💪" |
| "[경고] 편식 패턴 감지" | "한식을 많이 드셨네요 😊 내일은 새로운 도전을 해볼까요?" |

### 12.3 이모지 선택

| 카테고리 | 추천 |
|---------|-----|
| 격려 | 💪 ✨ 🎉 👏 🔥 |
| 음식 | 🍱 🥗 🍜 🍚 🍽️ |
| 감정 | 😊 🤗 💕 |
| 건강 | 🌱 💚 🥦 |
| 시간 | 🌅 ☀️ (아침/점심) |

**개수:** 2~3개 (최소 1, 최대 5)

### 12.4 금기

- 의학 단정 ("병", "진단", "처방")
- 비판 ("나쁘다", "잘못")
- 강제 ("하세요", "해야 합니다")
- 과도한 통계 (숫자 3개 이상)
- 비교 ("평균보다 낮습니다")

---

## 13. Mini 통합 및 마무리

### 13.1 FastAPI 서버 구동

```bash
cd Mini/NLP
uvicorn nlp_mvp.api.main:app --reload --port 8001
```

엔드포인트:
- `GET /nlp/reports/weekly/{user_id}` — 현재 주 리포트 조회 (없으면 생성)
- `POST /nlp/reports/weekly/{user_id}/regenerate` — 강제 재생성

### 13.2 React 대시보드 통합

`lunch-optimizer-dashboard.jsx` 의 영양 리포트 탭에 **"AI 코멘트"** 카드 추가:

```jsx
const [aiComment, setAiComment] = useState(null);

useEffect(() => {
  fetch(`${API_BASE}/nlp/reports/weekly/${userId}`)
    .then(r => r.json())
    .then(data => setAiComment(data));
}, [userId]);

return (
  <Card>
    <CardHeader>🧠 AI 코멘트</CardHeader>
    <CardContent>
      <p>{aiComment?.nlg_text}</p>
      <small>{aiComment?.week_label}</small>
      <button onClick={regenerate}>🔄 다시 생성</button>
    </CardContent>
  </Card>
);
```

### 13.3 4주차 MVP v1.0 완료 기준

- [x] Step 1 (A1 감성분석) ✓
- [x] Step 2 (B1 메뉴 정규화) ✓
- [x] Step 3 (D3 RAG 챗봇) ✓
- [x] **Step 4 (D5 NLG 리포트) ✓**
- [ ] 통합 데모 영상 / 스크린샷
- [ ] `nlp_mvp/README.md` 진행률 100%
- [ ] v1.0 git 태그

### 13.4 다음 단계 (선택)

1. **시나리오 2 착수** — `GUIDE_NLP_RESEARCH_SCENARIO2.md` 로 진행
2. **사용자 실증 테스트** — 실제 직장인 10명 대상 1주 사용
3. **배포** — ChatBOT/Phase4 의 Docker 가이드 참고

---

## 14. 부록

### 14.A 10개 샘플 사용자 facts (Day 4 평가용)

| # | 프로필 | 특징 | 예상 리포트 톤 |
|---|-------|------|-------------|
| 1 | 균형식 5일 | 모든 영양소 적정 | 칭찬 위주 |
| 2 | 고탄수 편식 | 탄수화물 과다, 단백질 부족 | 부드러운 제안 |
| 3 | 짠 음식 매일 | 나트륨 과다 | 저염 제안 |
| 4 | 한식만 5일 | 다양성 낮음 | 다양성 제안 |
| 5 | 야식 자주 | 칼로리 과다 | 균형 제안 |
| 6 | 샐러드만 | 칼로리 부족 | 균형 제안 |
| 7 | 2건만 기록 | Sparse | 기록 독려 |
| 8 | 0건 | Empty | 시작 독려 |
| 9 | 영양 DB 없음 | has_nutrition_data=False | 일반 격려 |
| 10 | 평균 + 만족도 높음 | 이상적 | 축하 |

**실제 facts dict 예시 (샘플 1):**
```python
facts = WeeklyFacts(
    week_label="2026년 4월 1주차",
    week_start="2026-04-06",
    week_end="2026-04-13",
    user_id=1,
    user_name="김민수",
    meal_count=5,
    total_calories=3250,
    avg_calories_per_meal=650,
    avg_protein=28,
    avg_carbs=85,
    avg_fat=22,
    avg_sodium=1800,
    target_calories=2000,
    target_protein=60,
    lack=[],
    excess=[],
    best_day={"date": "2026-04-08", "menu": "닭가슴살 샐러드", "balance_score": 0.92, "reason": "균형 최고"},
    worst_day=None,
    top_categories=[("한식", 3), ("양식", 2)],
    avg_satisfaction=4.2,
    has_nutrition_data=True,
)
```

### 14.B 평가 루브릭 (블라인드)

**3축 × 5점:**

| 항목 | 5점 | 3점 | 1점 |
|------|-----|-----|-----|
| **자연스러움** | 사람이 쓴 듯 | 약간 어색 | 기계적 |
| **유용성** | 구체 조언·행동 유도 | 모호 | 무의미 |
| **정확성** | 팩트 일치 | 일부 의심 | 오류 |

**종합 = 평균**

### 14.C 프롬프트 버전 관리

**v1 (Day 2):** 기본 SYSTEM_PROMPT
**v2 (Day 4 튜닝):** 이모지 강제, 금기어 추가
**v3 (필요 시):** Few-shot 예시 2개 추가

각 버전을 `nlg_report/prompts/v{N}.txt` 로 저장하여 A/B 비교.

### 14.D CLI 실행 예시

```bash
cd Mini/NLP

# 단일 사용자 이번 주 리포트
python -m nlp_mvp.nlg_report.generator --user-id 1

# 과거 주 조회
python -m nlp_mvp.nlg_report.generator --user-id 1 --week-start 2026-03-30

# 강제 재생성
python -m nlp_mvp.nlg_report.generator --user-id 1 --force

# 저장 없이 테스트
python -m nlp_mvp.nlg_report.generator --user-id 1 --no-save
```

### 14.E 참고 자료

1. **NLG 기본 개념:** https://en.wikipedia.org/wiki/Natural_language_generation
2. **한국영양학회 권장 섭취량:** https://www.kns.or.kr/
3. **프롬프트 엔지니어링 패턴:** https://www.promptingguide.ai/
4. **Ollama 옵션:** https://github.com/ollama/ollama/blob/main/docs/modelfile.md
5. **f-string 템플릿:** https://docs.python.org/3/library/string.html

---

## 15. 1페이지 체크리스트 요약

### ✅ Step 4 (D5 NLG 리포트) 4주차 체크리스트

**Day 1 — 팩트 추출**
- [ ] `WeeklyFacts` 데이터 클래스
- [ ] `extract_weekly_facts()` SQL 집계
- [ ] `day_balance_score()`, `detect_lack_excess()`
- [ ] `ensure_schema()`
- [ ] 테스트 통과

**Day 2 — 프롬프트**
- [ ] `REPORT_SYSTEM_PROMPT`
- [ ] `format_facts_for_user()` 3 케이스
- [ ] `build_report_prompt()`
- [ ] 10건 수동 테스트

**Day 3 — Generator**
- [ ] `ReportGenerator` 클래스
- [ ] 3단계 fallback (LLM → 템플릿 → 최소)
- [ ] `validate_report()` 품질 검증
- [ ] `fallback.txt` 템플릿
- [ ] DB UPSERT
- [ ] 테스트 통과

**Day 4 — 샘플 평가**
- [ ] 10개 샘플 생성
- [ ] `sample_reports.md` 저장
- [ ] 블라인드 평가 3축
- [ ] 노트북 실행

**Day 5 — 통합**
- [ ] FastAPI 라우터
- [ ] React AI 코멘트 카드
- [ ] end-to-end 시연

### 🎯 KPI
- [ ] 자연스러움 ≥ 4.0
- [ ] 유용성 ≥ 4.0
- [ ] 팩트 오류 0건
- [ ] 속도 ≤ 5초

### 📦 산출물
- [ ] `nlg_report/` 4개 파일 + templates/ + tests/
- [ ] `nutrition_reports` 테이블
- [ ] `sample_reports.md` 10건
- [ ] FastAPI 엔드포인트 2개
- [ ] React 카드

### 🏁 MVP v1.0 완성
- [ ] Step 1~4 모두 완료
- [ ] `nlp_mvp/README.md` 100%
- [ ] git 태그 `v1.0-mvp`

### 📎 다음 단계
- [ ] 시나리오 2 (GUIDE_NLP_RESEARCH_SCENARIO2.md) 착수
- [ ] 실증 테스트

---

**문서 버전:** v1.0
**작성일:** 2026-04-07
**대상:** Mini NLP MVP 4주차 구현자
**상위 문서:** [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §8
**선행 문서:**
- [`GUIDE_NLP_MVP_STEP1_SENTIMENT.md`](./GUIDE_NLP_MVP_STEP1_SENTIMENT.md)
- [`GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md`](./GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md)
- [`GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md`](./GUIDE_NLP_MVP_STEP3_RAG_CHATBOT.md)
**관련 문서:**
- [`README.md`](./README.md) — NLP 진입점
- [`GUIDE_NLP_RESEARCH_SCENARIO2.md`](./GUIDE_NLP_RESEARCH_SCENARIO2.md) — 다음 단계

---

<div align="center">

**🔹 Step 4 — 숫자를 이야기로, 데이터를 응원으로.**

*Mini NLP MVP — The Final Step. MVP Complete.*

</div>
