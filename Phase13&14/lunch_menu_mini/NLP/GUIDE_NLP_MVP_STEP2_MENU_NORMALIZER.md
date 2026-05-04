# 🔹 Step 2 — B1 메뉴명 정규화 파이프라인 상세 구현 가이드

> **Mini NLP MVP 의 2주차 전용 심화 가이드**
>
> 본 문서는 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §6 의
> Step 2 섹션을 **2주차 단일 독립 체크리스트** 로 확장한 문서입니다.
> 브레인스토밍 · 대안 비교 · 파일별 상세 명세 · 동의어 사전 확장 전략 ·
> 평가 방법을 한 문서에 집약하여, **이 문서만으로 Step 2 를 완수할 수 있도록** 설계되었습니다.

---

## 📋 목차

1. [문서 목적 및 위치](#1-문서-목적-및-위치)
2. [Step 2 전체 조감](#2-step-2-전체-조감)
3. [브레인스토밍 — 기술 선택 의사결정](#3-브레인스토밍--기술-선택-의사결정)
4. [확장 아키텍처 다이어그램](#4-확장-아키텍처-다이어그램)
5. [파일 목록 및 의존성 그래프](#5-파일-목록-및-의존성-그래프)
6. [파일별 상세 명세](#6-파일별-상세-명세)
7. [구현 순서 (5일 체크리스트)](#7-구현-순서-5일-체크리스트)
8. [KPI 및 검증 기준](#8-kpi-및-검증-기준)
9. [트러블슈팅 (Step 2 한정)](#9-트러블슈팅-step-2-한정)
10. [재사용 가능한 기존 파일](#10-재사용-가능한-기존-파일)
11. [외부 의존성 확인](#11-외부-의존성-확인)
12. [표준 메뉴 ID 체계 설계](#12-표준-메뉴-id-체계-설계)
13. [다음 Step 과의 연결점](#13-다음-step-과의-연결점)
14. [부록](#14-부록)
15. [1페이지 체크리스트 요약](#15-1페이지-체크리스트-요약)

---

## 1. 문서 목적 및 위치

### 1.1 왜 별도 가이드인가

상위 가이드 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §6 은 4주 전체
로드맵을 개괄하는 **요약형 Claude Code 프롬프트 묶음**입니다. 2주차 B1 메뉴 정규화를
실제로 구현하기 위해서는 다음이 추가로 필요합니다:

- **매칭 전략의 근거** — 왜 3단계 하이브리드(규칙→편집거리→임베딩)인지, 임계값은 어떻게 정했는지
- **동의어 사전 운영 방법** — 언제 · 어떻게 · 누가 확장하는지
- **표준 메뉴 ID 체계** — 식약처 DB 와 어떻게 매핑할지, ID 명명 규칙
- **평가 방법론** — 정확도 · 재현율 · 실패 케이스 분류
- **5일 단위 체크리스트** — 하루 단위로 무엇을 완료해야 하는지

본 문서는 이 모든 것을 한 파일에 집약합니다.

### 1.2 상위 문서와의 관계

```
Mini/NLP/
├── README.md                        # NLP 레이어 진입점
├── GUIDE_NLP_MVP_SCENARIO3.md       # 4주 전체 요약 가이드 (상위)
│   └── §6 Step 2                    #   → 본 문서가 확장
├── GUIDE_NLP_MVP_STEP1_SENTIMENT.md # 1주차 A1 감성분석 상세
├── GUIDE_NLP_MVP_STEP2_MENU_NORMALIZER.md  # 🆕 본 문서
└── GUIDE_NLP_RESEARCH_SCENARIO2.md  # 10주 연구 가이드
```

**독자 권장 순서:**
1. Step 1 (A1) 완료 — 감성분석 파이프라인 동작
2. **본 문서** 로 2주차 착수
3. (3주차부터는 Step 3/4 상세 가이드 또는 상위 가이드 §7~§8 참조)

### 1.3 선행 조건

본 문서를 시작하기 전 다음이 완료되어 있어야 합니다:

- [x] `Mini/NLP/nlp_mvp/` 스켈레톤 생성 완료
- [x] `Mini/NLP/.env` 파일 작성
- [x] **Step 0 공용 유틸 완료** — `shared/db.py`, `shared/logger.py`
- [x] **Step 1 (A1) 완료** — 파이프라인 동작 검증 완료
- [x] `nlp_mvp/menu_normalizer/synonym_dict.json` 존재 (스켈레톤에 포함)
- [x] `nlp_mvp/data/menu_test_set.csv` 존재 (90건, 스켈레톤에 포함)
- [ ] Mini SQLite DB 에 `nutrition_info` 테이블 또는 시드 데이터 존재
  (또는 합성 표준 메뉴 사용 가능 — §6.3 참고)

> 💡 **Step 1 이 미완료라면** `GUIDE_NLP_MVP_STEP1_SENTIMENT.md` 를 먼저 완수하세요.

---

## 2. Step 2 전체 조감

### 2.1 한 줄 목표

> **원시 메뉴명 → 표준 메뉴 ID 매핑 → Mini 영양 DB 조인율 40% → 85% 달성**

### 2.2 2주차 5일 일정

| Day | 작업 테마 | 산출물 | 누적 |
|-----|---------|--------|------|
| **Day 1** | 규칙 전처리 + 동의어 사전 확장 | `rules.py`, `synonym_dict.json` v2 (150+ 엔트리) | 20% |
| **Day 2** | 편집거리 매칭기 + Levenshtein 통합 | `normalizer.py` Phase 1-2 (규칙 + 편집거리) | 40% |
| **Day 3** | 임베딩 매칭기 + 캐싱 | `embedding_matcher.py`, `.pkl` 캐시 | 60% |
| **Day 4** | 통합 `MenuNormalizer` + DB 적재 | `normalizer.py` 완성, `menu_normalization` 테이블 | 80% |
| **Day 5** | 평가 + 실패 분석 + 사전 확장 | `evaluate.py` 실행, F1 ≥ 0.85, 리포트 | 100% |

### 2.3 완료 기준 (한눈에)

| 기준 | 목표치 |
|------|-------|
| ✅ 전체 매칭 정확도 | ≥ 85% (F1) |
| ✅ 규칙 + 편집거리만으로 커버 | ≥ 60% (임베딩 전 단계) |
| ✅ 임베딩 단계 추가 후 | ≥ 85% |
| ✅ 매칭률 (매핑 성공 비율) | ≥ 90% |
| ✅ 영양 DB 조인 성공률 | 40% → **85% 이상** |
| ✅ 테스트 커버리지 | ≥ 70% |
| ✅ 동의어 사전 크기 | 150+ 엔트리 |
| ✅ 배치 처리량 | ≥ 500 메뉴/분 (CPU) |

---

## 3. 브레인스토밍 — 기술 선택 의사결정

### 3.1 매칭 전략 선택

**고려한 후보들:**

| 전략 | 장점 | 단점 | MVP 적합성 |
|------|------|------|-----------|
| **순수 규칙 기반** | 빠름, 해석 가능, 무료 | 변형·오타 약함 | ⭐⭐ |
| **편집거리 (Levenshtein)** | 오타 강함, 간단 | 의미 다른데 글자 비슷 → 오매칭 | ⭐⭐⭐ |
| **TF-IDF + 코사인** | 중간 성능, 학습 불필요 | 짧은 문자열에 약함 | ⭐⭐ |
| **Sentence-BERT 임베딩** | 의미적 유사성, 강력 | 느림, 모델 로딩 | ⭐⭐⭐⭐ |
| **LLM (Ollama) 질의** | 매우 유연 | 매우 느림 (초당 1건) | ⭐⭐ |
| **3단계 하이브리드 (규칙 → 편집거리 → 임베딩)** | 각 단계 장점 결합 | 복잡도 ↑ | ⭐⭐⭐⭐⭐ |

**의사결정:**

- **채택:** **3단계 하이브리드**
  - Stage 1 (규칙): 빠른 공통 케이스 처리 (괄호, 동의어)
  - Stage 2 (편집거리): 오타·띄어쓰기 대응 (cutoff=2)
  - Stage 3 (임베딩): 의미적 유사 (cutoff=0.85)
- **이유:** 각 단계가 이전 단계 실패를 받아내는 구조 → 처리량·정확도 모두 확보
- **미채택:** 순수 LLM (MVP 범위 초과), TF-IDF (짧은 메뉴명에 취약)

**성능 분배 가설 (Day 5 에 검증):**
```
100% 입력
├── Stage 1 (규칙)        → 50~60% 해결
├── Stage 2 (편집거리)    → +15~20% 해결  → 누적 70~80%
└── Stage 3 (임베딩)      → +10~15% 해결  → 누적 85~95%
```

### 3.2 임베딩 모델 선택

**후보 비교표:**

| 모델 | 차원 | 한국어 성능 | 크기 | MVP 적합성 |
|------|------|---------|------|-----------|
| `jhgan/ko-sroberta-multitask` | 768 | ⭐⭐⭐⭐⭐ | 450MB | ⭐⭐⭐⭐⭐ |
| `jhgan/ko-sbert-nli` | 768 | ⭐⭐⭐⭐ | 450MB | ⭐⭐⭐⭐ |
| `BM-K/KoSimCSE-roberta-multitask` | 768 | ⭐⭐⭐⭐⭐ | 450MB | ⭐⭐⭐⭐ |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | ⭐⭐⭐ | 120MB | ⭐⭐⭐ |
| `Alibaba-NLP/gte-multilingual-base` | 768 | ⭐⭐⭐⭐ | 611MB | ⭐⭐⭐ |

**의사결정:**

- **1순위:** `jhgan/ko-sroberta-multitask` — Step 1 에서 이미 언급된 모델, 재사용
- **Fallback:** `paraphrase-multilingual-MiniLM-L12-v2` — 경량 환경용

```python
# .env
EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
EMBEDDING_MODEL_FALLBACK=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

### 3.3 표준 메뉴 ID 소스

**선택지:**

| 소스 | 합법성 | 메뉴 수 | 영양 정보 | 채택 |
|------|-------|-------|---------|-----|
| 식약처 식품영양성분 DB (공공 API) | ✅ | 10,000+ | ✅ | ✅ **1순위** |
| AI-Hub 음식 데이터 | ✅ | 2,000+ | ⚠️ | 보조 |
| **합성 표준 메뉴 (본 가이드 §14.A)** | ✅ | 100 | ❌ | ✅ **스모크 테스트** |
| Wikipedia 한국 음식 카테고리 | ✅ | 500+ | ❌ | ❌ |

**의사결정 (단계적):**

1. **Day 1-3:** `§14.A` 의 **합성 표준 메뉴 100건** 으로 파이프라인 검증
2. **Day 4-5:** 식약처 DB 존재 시 → `nutrition_info.food_name` 을 표준 메뉴로 사용
3. **코드상 추상화:** `StandardMenuLoader` 인터페이스로 두 소스 모두 지원

### 3.4 편집거리 임계값 설정

**트레이드오프:**

| cutoff | 매칭률 | 오매칭 위험 |
|--------|-------|----------|
| 1 | 낮음 | 거의 없음 |
| **2** | **중간** | **낮음 (권장)** |
| 3 | 높음 | 주의 |
| 4+ | 매우 높음 | 오매칭 많음 |

**의사결정:** `cutoff=2` 기본값 + 메뉴명 길이에 따른 adaptive scaling

```python
def adaptive_cutoff(target_len: int) -> int:
    """
    짧은 메뉴는 엄격하게, 긴 메뉴는 여유롭게.
    - 3자 이하: cutoff=1
    - 4~6자: cutoff=2
    - 7자 이상: cutoff=3
    """
    if target_len <= 3:
        return 1
    elif target_len <= 6:
        return 2
    else:
        return 3
```

### 3.5 임베딩 캐싱 전략

**문제:** 표준 메뉴 10,000건 임베딩을 매번 로드하면 초기화 30초+ 소요

**해결:** **Pickle 캐시**
```python
# 최초 로드: 표준 메뉴 → 임베딩 → pickle 저장
# 재실행: pickle 로드 (1초)

cache_path = Path("nlp_mvp/menu_normalizer/.cache/standard_embeddings.pkl")
if cache_path.exists() and cache_path.stat().st_mtime > source_mtime:
    embeddings = pickle.load(open(cache_path, "rb"))
else:
    embeddings = model.encode(menus)
    pickle.dump(embeddings, open(cache_path, "wb"))
```

**무효화 트리거:**
- 표준 메뉴 DB 수정 시 (`source_mtime` 비교)
- 모델 변경 시 (파일명에 모델명 포함)
- 수동 삭제 (`rm -rf .cache/`)

### 3.6 동의어 사전 운영 방법

**사전 유형 3종:**

```json
{
  "abbreviations": {
    "김찌": "김치찌개",
    "된찌": "된장찌개"
  },
  "variants": {
    "돈가스": "돈까스",
    "오뎅": "어묵"
  },
  "compound": {
    "치즈돈까스": "돈까스",
    "왕돈까스": "돈까스"
  }
}
```

**확장 전략:**
1. **Day 1:** 스켈레톤의 60 엔트리를 150+ 로 확장 (§14.B 참고)
2. **Day 5:** 실패 케이스 로그 → 새로운 엔트리 추가
3. **지속 운영:** `evaluate.py` 실행 시 자동으로 후보 제안 (§6.6)

**형식 결정: 단일 JSON vs 분리 JSON?**
- ✅ **단일 JSON + 섹션 분리** — MVP 간편성 우선
- 미래 확장: 스프레드시트 → JSON 자동 생성 스크립트

### 3.7 DB 저장 전략

**테이블 설계: `menu_normalization`**

```sql
CREATE TABLE menu_normalization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_name TEXT NOT NULL,
    normalized_id TEXT,       -- 표준 메뉴 ID, NULL 가능
    normalized_name TEXT,     -- 표준 메뉴 이름
    confidence REAL NOT NULL,
    method TEXT NOT NULL,     -- 'rule' | 'levenshtein' | 'embedding' | 'none'
    source_table TEXT,        -- 'restaurants.menu_type' | 'meal_history.menu' 등
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_name, source_table)
);

CREATE INDEX idx_menu_norm_raw ON menu_normalization(raw_name);
CREATE INDEX idx_menu_norm_id ON menu_normalization(normalized_id);
```

**이점:**
- **캐시 역할:** 동일 raw_name 재질의 시 DB 조회로 즉시 반환
- **감사 로그:** 시간순 매핑 변화 추적 가능
- **방법별 통계:** Day 5 평가에서 `method` 분포 분석

### 3.8 에러 및 Fallback 전략

**원칙:** "매칭 실패는 정상 상태"

```python
# 매칭 실패 = matched_id=None + method="none"
# DB 에는 저장되지만, confidence=0 으로 표시
# Step 5 통합 시 matched_id IS NULL 인 레코드는 스킵

def normalize(raw: str) -> dict:
    try:
        # Stage 1 → 2 → 3
        return result
    except Exception as e:
        logger.exception(f"normalize({raw}) failed: {e}")
        return {
            "raw": raw,
            "cleaned": "",
            "matched_id": None,
            "matched_name": None,
            "confidence": 0.0,
            "method": "error",
        }
```

---

## 4. 확장 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────────┐
│                  입력: 원시 메뉴명                                 │
│  "김치찌개(大)", "김찌", "짬뽕특", "동태탕 1인분" ...               │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  STAGE 1: 규칙 기반 전처리 + 동의어                                │
│                                                                  │
│  rules.preprocess_menu_name()                                    │
│    ├── 괄호 제거: "김치찌개(大)" → "김치찌개"                      │
│    ├── 크기 표기 제거: "짬뽕특" → "짬뽕"                          │
│    ├── 수량 제거: "동태탕 1인분" → "동태탕"                        │
│    └── 공백 · 특수문자 정규화                                     │
│                                                                  │
│  rules.apply_synonyms()                                          │
│    ├── "김찌" → "김치찌개"                                        │
│    └── "오뎅" → "어묵"                                            │
│                                                                  │
│  정확 일치 검사:                                                  │
│    cleaned in standard_menus?                                    │
│    YES → method="rule", confidence=1.0                           │
│                                                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │ NO
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  STAGE 2: 편집거리 매칭 (Levenshtein)                              │
│                                                                  │
│  levenshtein.find_candidates()                                   │
│    ├── 전체 표준 메뉴와 거리 계산                                  │
│    ├── adaptive_cutoff 적용 (길이 기반)                           │
│    ├── 거리 ≤ cutoff 인 후보 Top-3                                │
│    └── 거리 기반 confidence 산출                                  │
│                                                                  │
│  후보 있음?                                                       │
│    YES (최적 후보) → method="levenshtein", confidence=1-dist/len  │
│                                                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │ NO
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  STAGE 3: Sentence-BERT 임베딩 유사도                              │
│                                                                  │
│  embedding_matcher.match()                                       │
│    ├── query → 임베딩 (Sentence-BERT)                             │
│    ├── 캐시된 표준 임베딩과 코사인 유사도                          │
│    ├── threshold ≥ 0.85 인 후보 Top-3                             │
│    └── 최고 점수 반환                                             │
│                                                                  │
│  후보 있음?                                                       │
│    YES → method="embedding", confidence=코사인 유사도              │
│    NO  → method="none", matched_id=None                           │
│                                                                  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│  출력: 정규화 결과 (dict)                                          │
│  {                                                                │
│    "raw": "김치찌개(大)",                                          │
│    "cleaned": "김치찌개",                                          │
│    "matched_id": "kimchi_jjigae",                                 │
│    "matched_name": "김치찌개",                                     │
│    "confidence": 1.0,                                             │
│    "method": "rule"                                               │
│  }                                                                │
│                                                                  │
│  → menu_normalization 테이블 UPSERT                                │
│  → Mini meal_history.normalized_menu_id 갱신                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. 파일 목록 및 의존성 그래프

```
┌─────────────────────────────────────┐
│ Step 0 (선행, 공용)                  │
├─────────────────────────────────────┤
│ shared/db.py                        │
│ shared/logger.py                    │
└────────────────┬────────────────────┘
                 │ import
                 ▼
┌─────────────────────────────────────┐
│ Step 2 — B1 메뉴 정규화              │
├─────────────────────────────────────┤
│                                     │
│  menu_normalizer/                   │
│  ├─ rules.py            ◄── Day 1  │
│  │   ├─ preprocess_menu_name()     │
│  │   ├─ apply_synonyms()           │
│  │   ├─ load_synonym_dict()        │
│  │   └─ SynonymDict 클래스         │
│  │                                  │
│  ├─ synonym_dict.json   ◄── Day 1  │
│  │   (150+ 엔트리, 섹션 분리)       │
│  │                                  │
│  ├─ levenshtein.py      ◄── Day 2  │
│  │   ├─ find_candidates()          │
│  │   ├─ adaptive_cutoff()          │
│  │   └─ distance_to_confidence()   │
│  │                                  │
│  ├─ embedding_matcher.py ◄── Day 3 │
│  │   ├─ EmbeddingMatcher           │
│  │   ├─ .match() / .batch_match()  │
│  │   └─ pickle 캐싱                │
│  │                                  │
│  ├─ loader.py           ◄── Day 3  │
│  │   ├─ StandardMenuLoader (ABC)   │
│  │   ├─ SyntheticMenuLoader        │
│  │   └─ NutritionDBLoader          │
│  │                                  │
│  ├─ normalizer.py       ◄── Day 4  │
│  │   ├─ MenuNormalizer             │
│  │   ├─ .normalize() (3단계)       │
│  │   └─ run_batch_normalization()  │
│  │                                  │
│  ├─ evaluate.py         ◄── Day 5  │
│  │   ├─ evaluate_on_test_set()     │
│  │   ├─ method_distribution()      │
│  │   └─ failure_analysis()         │
│  │                                  │
│  └─ tests/                          │
│      ├─ test_rules.py              │
│      ├─ test_levenshtein.py        │
│      ├─ test_embedding_matcher.py  │
│      ├─ test_normalizer.py         │
│      └─ test_evaluate.py           │
│                                     │
│  notebooks/02_menu_normalizer_eval.ipynb ◄── Day 5 │
└─────────────────────────────────────┘
```

**import 관계:**
- `normalizer.py` → `rules`, `levenshtein`, `embedding_matcher`, `loader`, `shared.db`, `shared.logger`
- `embedding_matcher.py` → `sentence_transformers`, `numpy`, `shared.logger`
- `levenshtein.py` → `Levenshtein` (python-Levenshtein 패키지)
- `evaluate.py` → `normalizer`, `pandas`, `sklearn.metrics`

---

## 6. 파일별 상세 명세

### 6.1 `menu_normalizer/rules.py`

**파일 상단:**
```python
"""
메뉴명 규칙 기반 전처리 모듈.

- 괄호 · 크기 · 수량 · 특수문자 제거
- 동의어 사전 기반 표준화
- 순수 함수 (side-effect 없음)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)
```

**정규식 상수:**
```python
# 괄호 (한글/영문/특수 모두)
_BRACKET_PATTERN = re.compile(r"[\(\[\{（［｛].*?[\)\]\}）］｝]")
# 크기 표기 (끝부분)
_SIZE_PATTERN = re.compile(r"[\s]?(대|중|소|특|왕|미니|라지|스몰|점보)$")
# 수량 표기
_QUANTITY_PATTERN = re.compile(r"\s?\d+\s?(인분|개|그릇|팩|세트)")
# 공백 정규화
_WHITESPACE_PATTERN = re.compile(r"\s+")
# 한글·영문·숫자·공백 외 제거
_NON_ALNUM_PATTERN = re.compile(r"[^\w가-힣\s]")
```

**함수 1 — preprocess_menu_name:**
```python
def preprocess_menu_name(raw: str) -> str:
    """
    원시 메뉴명을 정제한다.

    변환 예:
        "김치찌개(大)"           → "김치찌개"
        "짬뽕 특"                → "짬뽕"
        "동태탕 1인분"           → "동태탕"
        "제육볶음★★★"          → "제육볶음"
        "  비빔밥   "            → "비빔밥"
    """
    if not isinstance(raw, str):
        return ""
    text = raw
    text = _BRACKET_PATTERN.sub("", text)
    text = _QUANTITY_PATTERN.sub("", text)
    text = _SIZE_PATTERN.sub("", text)
    text = _NON_ALNUM_PATTERN.sub("", text)
    text = _WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()
```

**함수 2 — apply_synonyms:**
```python
def apply_synonyms(text: str, synonym_dict: dict[str, Any]) -> str:
    """
    동의어 사전 기반 치환.

    synonym_dict 구조:
        {
            "synonyms": {
                "김찌": "김치찌개",
                "된찌": "된장찌개"
            }
        }
        또는 flat dict:
        {
            "김찌": "김치찌개",
            ...
        }
    """
    if not text or not synonym_dict:
        return text

    # 섹션 분리 사전과 flat 사전 모두 지원
    mapping = synonym_dict.get("synonyms", synonym_dict)

    # 긴 key 부터 매칭 (greedy)
    for src in sorted(mapping.keys(), key=len, reverse=True):
        if src and src in text:
            text = text.replace(src, mapping[src])
            break  # 한 번만 치환
    return text
```

**함수 3 — load_synonym_dict:**
```python
def load_synonym_dict(path: str | Path | None = None) -> dict[str, Any]:
    """
    동의어 사전 JSON 로드.

    Args:
        path: None 이면 기본 경로 사용

    Returns:
        파싱된 dict. 실패 시 빈 dict.
    """
    if path is None:
        path = Path(__file__).parent / "synonym_dict.json"
    path = Path(path)

    if not path.exists():
        logger.warning(f"Synonym dict not found: {path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded synonym dict from {path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return {}
```

**class SynonymDict (선택):**
```python
class SynonymDict:
    """
    동의어 사전 래퍼. 캐싱 및 재로드 지원.
    """
    def __init__(self, path: str | Path | None = None):
        self.path = path
        self._dict: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        self._dict = load_synonym_dict(self.path)

    def apply(self, text: str) -> str:
        return apply_synonyms(text, self._dict)

    def add(self, src: str, dst: str) -> None:
        mapping = self._dict.setdefault("synonyms", {})
        mapping[src] = dst

    def save(self) -> None:
        if self.path is None:
            raise ValueError("No path to save to")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._dict, f, ensure_ascii=False, indent=2)

    def __len__(self) -> int:
        return len(self._dict.get("synonyms", {}))
```

### 6.2 `menu_normalizer/synonym_dict.json` (v2 — Day 1 확장)

**기존 (스켈레톤):** 60+ 엔트리
**목표 (Day 1 완료):** **150+ 엔트리** (§14.B 참고)

**섹션 분리 구조:**
```json
{
  "_meta": {
    "version": "0.2.0",
    "description": "Mini 메뉴명 정규화 사전",
    "last_updated": "2026-04-07"
  },
  "synonyms": {
    "...": "..."
  },
  "_stats": {
    "total_entries": 150,
    "by_category": {
      "한식": 70,
      "중식": 15,
      "일식": 25,
      "양식": 20,
      "동남아": 10,
      "기타": 10
    }
  }
}
```

### 6.3 `menu_normalizer/loader.py` — 표준 메뉴 로더 (신규)

```python
"""
표준 메뉴 로딩 추상 + 3종 구현체.

- SyntheticMenuLoader: 합성 100건 (테스트용)
- NutritionDBLoader: Mini nutrition_info 테이블 (실제)
- FileMenuLoader: CSV/JSON 파일
"""
from abc import ABC, abstractmethod
from pathlib import Path

from nlp_mvp.shared.db import get_engine
from nlp_mvp.shared.logger import get_logger
from sqlalchemy import text

logger = get_logger(__name__)


class StandardMenuLoader(ABC):
    """표준 메뉴 로딩 추상."""

    @abstractmethod
    def load(self) -> list[dict]:
        """
        Returns:
            [{"id": "kimchi_jjigae", "name": "김치찌개", "category": "한식"}, ...]
        """


class SyntheticMenuLoader(StandardMenuLoader):
    """§14.A 부록의 합성 100건."""
    def load(self) -> list[dict]:
        from nlp_mvp.menu_normalizer._synthetic_menus import SYNTHETIC_STANDARD_MENUS
        logger.info(f"Loaded {len(SYNTHETIC_STANDARD_MENUS)} synthetic menus")
        return SYNTHETIC_STANDARD_MENUS


class NutritionDBLoader(StandardMenuLoader):
    """Mini nutrition_info 테이블."""

    def __init__(self, table: str = "nutrition_info", id_col: str = "id", name_col: str = "food_name"):
        self.table = table
        self.id_col = id_col
        self.name_col = name_col

    def load(self) -> list[dict]:
        engine = get_engine()
        try:
            with engine.connect() as conn:
                rows = conn.execute(
                    text(f"SELECT {self.id_col}, {self.name_col} FROM {self.table}")
                ).fetchall()
            menus = [{"id": str(r[0]), "name": r[1]} for r in rows]
            logger.info(f"Loaded {len(menus)} menus from {self.table}")
            return menus
        except Exception as e:
            logger.warning(f"Failed to load from {self.table}: {e}")
            return []


class FileMenuLoader(StandardMenuLoader):
    """CSV/JSON 파일 로더."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self) -> list[dict]:
        if self.path.suffix == ".csv":
            import pandas as pd
            df = pd.read_csv(self.path)
            return df.to_dict(orient="records")
        elif self.path.suffix == ".json":
            import json
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported format: {self.path.suffix}")
```

### 6.4 `menu_normalizer/levenshtein.py` — 편집거리 매칭 (신규)

```python
"""
Levenshtein 기반 후보 검색.
"""
from __future__ import annotations

from typing import Any

import Levenshtein

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


def adaptive_cutoff(target_len: int) -> int:
    """
    길이에 따른 편집거리 임계값.

    - ≤ 3자: cutoff=1 (엄격)
    - 4~6자: cutoff=2 (기본)
    - ≥ 7자: cutoff=3 (여유)
    """
    if target_len <= 3:
        return 1
    elif target_len <= 6:
        return 2
    else:
        return 3


def distance_to_confidence(distance: int, target_len: int) -> float:
    """
    편집거리 → confidence 점수 (0~1).

    공식: 1 - (distance / max_len)
    """
    if target_len == 0:
        return 0.0
    return max(0.0, 1.0 - distance / target_len)


def find_candidates(
    query: str,
    standard_menus: list[dict[str, Any]],
    cutoff: int | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    편집거리 기반 후보 검색.

    Args:
        query: 전처리된 메뉴명
        standard_menus: [{"id": str, "name": str}, ...]
        cutoff: 편집거리 임계값 (None 이면 adaptive)
        top_k: 반환할 상위 후보 수

    Returns:
        [
            {"id": str, "name": str, "distance": int, "confidence": float},
            ...
        ]
        confidence 내림차순 정렬.
    """
    if not query or not standard_menus:
        return []

    if cutoff is None:
        cutoff = adaptive_cutoff(len(query))

    candidates = []
    for menu in standard_menus:
        dist = Levenshtein.distance(query, menu["name"])
        if dist <= cutoff:
            conf = distance_to_confidence(dist, max(len(query), len(menu["name"])))
            candidates.append({
                "id": menu["id"],
                "name": menu["name"],
                "distance": dist,
                "confidence": conf,
            })

    candidates.sort(key=lambda x: (-x["confidence"], x["distance"]))
    return candidates[:top_k]
```

### 6.5 `menu_normalizer/embedding_matcher.py`

```python
"""
Sentence-BERT 기반 의미 유사도 매칭기.
"""
from __future__ import annotations

import hashlib
import os
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np

from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")
CACHE_DIR = Path(__file__).parent / ".cache"


class EmbeddingMatcher:
    """
    표준 메뉴 임베딩을 사전 캐싱하고, 쿼리 임베딩과 코사인 유사도 계산.
    """

    def __init__(
        self,
        standard_menus: list[dict[str, Any]],
        model_name: str = DEFAULT_MODEL,
        cache_enabled: bool = True,
    ):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.standard_menus = standard_menus
        self.model = SentenceTransformer(model_name)
        logger.info(f"Loaded embedding model: {model_name}")

        self.embeddings: np.ndarray = self._load_or_compute(cache_enabled)

    def _cache_key(self) -> str:
        """모델명 + 메뉴 개수 해시."""
        names = "|".join(m["name"] for m in self.standard_menus)
        h = hashlib.md5(names.encode("utf-8")).hexdigest()[:8]
        safe_model = self.model_name.replace("/", "_")
        return f"{safe_model}_{len(self.standard_menus)}_{h}.pkl"

    def _load_or_compute(self, cache_enabled: bool) -> np.ndarray:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = CACHE_DIR / self._cache_key()

        if cache_enabled and cache_path.exists():
            logger.info(f"Loading cached embeddings: {cache_path}")
            with open(cache_path, "rb") as f:
                return pickle.load(f)

        logger.info(f"Computing embeddings for {len(self.standard_menus)} menus...")
        names = [m["name"] for m in self.standard_menus]
        embeddings = self.model.encode(
            names,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # 코사인 유사도 = 내적
        )

        if cache_enabled:
            with open(cache_path, "wb") as f:
                pickle.dump(embeddings, f)
            logger.info(f"Cached embeddings to {cache_path}")

        return embeddings

    def match(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.85,
    ) -> list[dict[str, Any]]:
        """
        단일 쿼리 매칭.

        Returns:
            [{"id": str, "name": str, "score": float}, ...]
            threshold 미만은 제외. 내림차순 정렬.
        """
        if not query:
            return []

        query_emb = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]

        # 정규화 벡터의 내적 = 코사인 유사도
        sims = self.embeddings @ query_emb
        top_indices = np.argsort(-sims)[:top_k]

        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score < threshold:
                continue
            results.append({
                "id": self.standard_menus[idx]["id"],
                "name": self.standard_menus[idx]["name"],
                "score": score,
            })
        return results

    def batch_match(
        self,
        queries: list[str],
        top_k: int = 3,
        threshold: float = 0.85,
        batch_size: int = 32,
    ) -> list[list[dict[str, Any]]]:
        """배치 매칭 (대량 쿼리용)."""
        if not queries:
            return []

        query_embs = self.model.encode(
            queries,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        results_all = []
        for q_emb in query_embs:
            sims = self.embeddings @ q_emb
            top_indices = np.argsort(-sims)[:top_k]
            results = []
            for idx in top_indices:
                score = float(sims[idx])
                if score < threshold:
                    continue
                results.append({
                    "id": self.standard_menus[idx]["id"],
                    "name": self.standard_menus[idx]["name"],
                    "score": score,
                })
            results_all.append(results)
        return results_all

    def invalidate_cache(self) -> None:
        cache_path = CACHE_DIR / self._cache_key()
        if cache_path.exists():
            cache_path.unlink()
            logger.info(f"Cache invalidated: {cache_path}")
```

### 6.6 `menu_normalizer/normalizer.py` — 통합 정규화기

```python
"""
3단계 하이브리드 메뉴명 정규화 엔진.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text

from nlp_mvp.menu_normalizer import levenshtein, rules
from nlp_mvp.menu_normalizer.embedding_matcher import EmbeddingMatcher
from nlp_mvp.menu_normalizer.loader import (
    StandardMenuLoader, SyntheticMenuLoader, NutritionDBLoader
)
from nlp_mvp.shared.db import get_engine, get_session
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# 결과 데이터 클래스
# =============================================================================
@dataclass
class NormalizationResult:
    raw: str
    cleaned: str
    matched_id: Optional[str]
    matched_name: Optional[str]
    confidence: float
    method: str  # "rule" | "levenshtein" | "embedding" | "none" | "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =============================================================================
# 스키마 확장
# =============================================================================
MENU_NORM_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS menu_normalization (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_name TEXT NOT NULL,
    normalized_id TEXT,
    normalized_name TEXT,
    confidence REAL NOT NULL DEFAULT 0.0,
    method TEXT NOT NULL,
    source_table TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (raw_name, source_table)
);
CREATE INDEX IF NOT EXISTS idx_menu_norm_raw ON menu_normalization(raw_name);
CREATE INDEX IF NOT EXISTS idx_menu_norm_id ON menu_normalization(normalized_id);
"""


def ensure_schema() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        for stmt in MENU_NORM_TABLE_SQL.strip().split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
    logger.info("menu_normalization schema ensured")


# =============================================================================
# 메인 클래스
# =============================================================================
class MenuNormalizer:
    """
    3단계 하이브리드 메뉴명 정규화기.

    Stage 1: 규칙 전처리 + 동의어 + 정확 일치
    Stage 2: Levenshtein 편집거리
    Stage 3: Sentence-BERT 임베딩 유사도
    """

    def __init__(
        self,
        loader: Optional[StandardMenuLoader] = None,
        synonym_dict_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        levenshtein_cutoff: Optional[int] = None,
        embedding_threshold: float = 0.85,
        enable_embedding: bool = True,
    ):
        # 1. 표준 메뉴 로드
        self.loader = loader or SyntheticMenuLoader()
        self.standard_menus = self.loader.load()
        if not self.standard_menus:
            raise ValueError("No standard menus loaded")
        self.standard_name_set = {m["name"] for m in self.standard_menus}
        self.standard_by_name = {m["name"]: m for m in self.standard_menus}

        # 2. 동의어 사전
        self.synonym_dict = rules.load_synonym_dict(synonym_dict_path)

        # 3. 편집거리 설정
        self.levenshtein_cutoff = levenshtein_cutoff  # None → adaptive

        # 4. 임베딩 매칭기 (lazy)
        self.enable_embedding = enable_embedding
        self.embedding_threshold = embedding_threshold
        self._embedding_matcher: Optional[EmbeddingMatcher] = None
        self._embedding_model_name = embedding_model

        logger.info(
            f"MenuNormalizer initialized: "
            f"{len(self.standard_menus)} menus, "
            f"embedding={'on' if enable_embedding else 'off'}"
        )

    @property
    def embedding_matcher(self) -> EmbeddingMatcher:
        """lazy 로딩."""
        if self._embedding_matcher is None:
            if not self.enable_embedding:
                raise RuntimeError("Embedding matching is disabled")
            self._embedding_matcher = EmbeddingMatcher(
                standard_menus=self.standard_menus,
                model_name=self._embedding_model_name or "jhgan/ko-sroberta-multitask",
            )
        return self._embedding_matcher

    # -------------------------------------------------------------------------
    # 메인 진입점
    # -------------------------------------------------------------------------
    def normalize(self, raw: str) -> NormalizationResult:
        try:
            # Stage 1: 규칙 + 동의어
            cleaned = rules.preprocess_menu_name(raw)
            cleaned = rules.apply_synonyms(cleaned, self.synonym_dict)

            if cleaned in self.standard_name_set:
                menu = self.standard_by_name[cleaned]
                return NormalizationResult(
                    raw=raw,
                    cleaned=cleaned,
                    matched_id=menu["id"],
                    matched_name=menu["name"],
                    confidence=1.0,
                    method="rule",
                )

            # Stage 2: 편집거리
            lev_candidates = levenshtein.find_candidates(
                cleaned, self.standard_menus, cutoff=self.levenshtein_cutoff
            )
            if lev_candidates:
                best = lev_candidates[0]
                return NormalizationResult(
                    raw=raw,
                    cleaned=cleaned,
                    matched_id=best["id"],
                    matched_name=best["name"],
                    confidence=best["confidence"],
                    method="levenshtein",
                )

            # Stage 3: 임베딩
            if self.enable_embedding:
                emb_candidates = self.embedding_matcher.match(
                    cleaned, threshold=self.embedding_threshold
                )
                if emb_candidates:
                    best = emb_candidates[0]
                    return NormalizationResult(
                        raw=raw,
                        cleaned=cleaned,
                        matched_id=best["id"],
                        matched_name=best["name"],
                        confidence=best["score"],
                        method="embedding",
                    )

            # 실패
            return NormalizationResult(
                raw=raw,
                cleaned=cleaned,
                matched_id=None,
                matched_name=None,
                confidence=0.0,
                method="none",
            )

        except Exception as e:
            logger.exception(f"normalize({raw!r}) failed: {e}")
            return NormalizationResult(
                raw=raw, cleaned="", matched_id=None, matched_name=None,
                confidence=0.0, method="error",
            )

    def normalize_batch(self, raws: list[str]) -> list[NormalizationResult]:
        return [self.normalize(r) for r in raws]

    # -------------------------------------------------------------------------
    # DB 적재
    # -------------------------------------------------------------------------
    def save_result(
        self,
        result: NormalizationResult,
        source_table: str = "restaurants.menu_type",
    ) -> None:
        with get_session() as session:
            session.execute(
                text("""
                    INSERT INTO menu_normalization
                        (raw_name, normalized_id, normalized_name,
                         confidence, method, source_table, updated_at)
                    VALUES (:raw, :nid, :nname, :conf, :method, :src, :ts)
                    ON CONFLICT (raw_name, source_table) DO UPDATE SET
                        normalized_id = excluded.normalized_id,
                        normalized_name = excluded.normalized_name,
                        confidence = excluded.confidence,
                        method = excluded.method,
                        updated_at = excluded.updated_at
                """),
                {
                    "raw": result.raw,
                    "nid": result.matched_id,
                    "nname": result.matched_name,
                    "conf": result.confidence,
                    "method": result.method,
                    "src": source_table,
                    "ts": datetime.utcnow().isoformat(),
                },
            )
            session.commit()


# =============================================================================
# 배치 파이프라인
# =============================================================================
def run_batch_normalization(
    source_query: str = "SELECT DISTINCT menu FROM meal_history WHERE menu IS NOT NULL",
    source_table: str = "meal_history.menu",
    limit: int | None = None,
    dry_run: bool = False,
    normalizer: Optional[MenuNormalizer] = None,
) -> dict[str, Any]:
    """
    DB 의 원시 메뉴명 전체를 일괄 정규화하여 menu_normalization 에 적재.
    """
    start = time.time()
    ensure_schema()
    normalizer = normalizer or MenuNormalizer()

    stats = {
        "processed": 0,
        "rule": 0,
        "levenshtein": 0,
        "embedding": 0,
        "none": 0,
        "error": 0,
    }

    with get_session() as session:
        rows = session.execute(text(source_query)).fetchall()
    raws = [r[0] for r in rows if r[0]]
    if limit:
        raws = raws[:limit]

    logger.info(f"Normalizing {len(raws)} raw menu names from {source_table}")

    for raw in raws:
        result = normalizer.normalize(raw)
        stats["processed"] += 1
        stats[result.method] = stats.get(result.method, 0) + 1
        if not dry_run:
            normalizer.save_result(result, source_table=source_table)

    stats["duration_sec"] = time.time() - start
    stats["match_rate"] = (
        (stats["processed"] - stats["none"] - stats["error"]) / max(1, stats["processed"])
    )
    logger.info(f"Batch normalization done: {stats}")
    return stats


# =============================================================================
# CLI
# =============================================================================
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Mini B1 Menu Normalizer")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--source",
        choices=["synthetic", "nutrition_db"],
        default="synthetic",
    )
    parser.add_argument("--disable-embedding", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    loader = SyntheticMenuLoader() if args.source == "synthetic" else NutritionDBLoader()
    normalizer = MenuNormalizer(
        loader=loader,
        enable_embedding=not args.disable_embedding,
    )

    stats = run_batch_normalization(
        limit=args.limit, dry_run=args.dry_run, normalizer=normalizer
    )
    print(stats)


if __name__ == "__main__":
    main()
```

**CLI 실행 예:**
```bash
cd Mini/NLP

# Dry run
python -m nlp_mvp.menu_normalizer.normalizer --limit 20 --dry-run

# 실제 실행
python -m nlp_mvp.menu_normalizer.normalizer --source synthetic

# 임베딩 없이 (빠른 테스트)
python -m nlp_mvp.menu_normalizer.normalizer --disable-embedding
```

### 6.7 `menu_normalizer/evaluate.py`

```python
"""
menu_test_set.csv 기반 정규화 성능 평가.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from nlp_mvp.menu_normalizer.normalizer import MenuNormalizer, NormalizationResult
from nlp_mvp.shared.logger import get_logger

logger = get_logger(__name__)


def evaluate_on_test_set(
    test_csv: str | Path = None,
    normalizer: MenuNormalizer | None = None,
) -> dict[str, Any]:
    """
    평가 지표 계산.

    Returns:
        {
            "total": int,
            "matched": int,
            "correct": int,
            "accuracy": float,
            "precision": float,
            "recall": float,
            "f1": float,
            "method_dist": {...},
            "failures": list[dict],
        }
    """
    if test_csv is None:
        test_csv = Path(__file__).parent.parent / "data" / "menu_test_set.csv"
    df = pd.read_csv(test_csv)

    if "raw_name" not in df.columns or "expected_id" not in df.columns:
        raise ValueError("Test CSV must have columns: raw_name, expected_id")

    normalizer = normalizer or MenuNormalizer()

    results: list[dict] = []
    correct = 0
    matched = 0
    method_counter = Counter()
    failures = []

    for _, row in df.iterrows():
        raw = row["raw_name"]
        expected = row["expected_id"]
        result = normalizer.normalize(raw)
        method_counter[result.method] += 1

        is_matched = result.matched_id is not None
        is_correct = is_matched and result.matched_id == expected

        if is_matched:
            matched += 1
        if is_correct:
            correct += 1
        else:
            failures.append({
                "raw": raw,
                "expected": expected,
                "predicted": result.matched_id,
                "method": result.method,
                "confidence": result.confidence,
            })

        results.append({**result.to_dict(), "expected": expected, "correct": is_correct})

    total = len(df)
    accuracy = correct / total if total else 0.0
    precision = correct / matched if matched else 0.0
    recall = correct / total if total else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    report = {
        "total": total,
        "matched": matched,
        "correct": correct,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "method_dist": dict(method_counter),
        "failures_top20": failures[:20],
    }

    logger.info(
        f"Evaluation: total={total}, accuracy={accuracy:.3f}, "
        f"precision={precision:.3f}, recall={recall:.3f}, f1={f1:.3f}"
    )
    return report


def print_report(report: dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print("📊 Menu Normalizer Evaluation Report")
    print("=" * 60)
    print(f"Total:      {report['total']}")
    print(f"Matched:    {report['matched']}")
    print(f"Correct:    {report['correct']}")
    print(f"Accuracy:   {report['accuracy']:.3f}")
    print(f"Precision:  {report['precision']:.3f}")
    print(f"Recall:     {report['recall']:.3f}")
    print(f"F1:         {report['f1']:.3f}")
    print("\n방법별 분포:")
    for method, count in sorted(report["method_dist"].items()):
        print(f"  {method:15s}: {count}")
    print("\n실패 케이스 상위 20:")
    for f in report["failures_top20"]:
        print(f"  {f['raw']:20s} → expected={f['expected']}, predicted={f['predicted']} ({f['method']})")
    print("=" * 60)


def main():
    import argparse, json

    parser = argparse.ArgumentParser()
    parser.add_argument("--test-csv", type=str, default=None)
    parser.add_argument("--json", action="store_true", help="JSON 으로 출력")
    args = parser.parse_args()

    report = evaluate_on_test_set(args.test_csv)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
```

### 6.8 테스트

**test_rules.py (12+ 케이스):**
```python
import pytest
from nlp_mvp.menu_normalizer.rules import (
    preprocess_menu_name, apply_synonyms, load_synonym_dict, SynonymDict
)

class TestPreprocess:
    @pytest.mark.parametrize("raw,expected", [
        ("김치찌개(大)", "김치찌개"),
        ("짬뽕 특", "짬뽕"),
        ("동태탕 1인분", "동태탕"),
        ("제육볶음★★★", "제육볶음"),
        ("  비빔밥   ", "비빔밥"),
        ("돈까스(中)", "돈까스"),
        ("순두부찌개 2개", "순두부찌개"),
    ])
    def test_cases(self, raw, expected):
        assert preprocess_menu_name(raw) == expected

    def test_none_input(self):
        assert preprocess_menu_name(None) == ""

class TestSynonyms:
    def test_abbreviation(self):
        d = {"김찌": "김치찌개"}
        assert apply_synonyms("김찌", d) == "김치찌개"

    def test_variant(self):
        d = {"synonyms": {"돈가스": "돈까스"}}
        assert apply_synonyms("돈가스", d) == "돈까스"

    def test_no_match(self):
        d = {"김찌": "김치찌개"}
        assert apply_synonyms("라면", d) == "라면"

    def test_greedy_longest_match(self):
        d = {"synonyms": {"김찌": "김치찌개", "김치찌": "김치찌개"}}
        # 더 긴 매칭이 우선
        assert apply_synonyms("김치찌", d) == "김치찌개"

class TestSynonymDict:
    def test_add_and_apply(self, tmp_path):
        path = tmp_path / "syn.json"
        path.write_text('{"synonyms": {"a": "b"}}', encoding="utf-8")
        sd = SynonymDict(path)
        assert sd.apply("a") == "b"
        sd.add("c", "d")
        assert sd.apply("c") == "d"
```

**test_levenshtein.py (6 케이스):**
```python
from nlp_mvp.menu_normalizer.levenshtein import (
    adaptive_cutoff, distance_to_confidence, find_candidates
)

class TestCutoff:
    def test_short(self):
        assert adaptive_cutoff(3) == 1
    def test_medium(self):
        assert adaptive_cutoff(5) == 2
    def test_long(self):
        assert adaptive_cutoff(10) == 3

class TestConfidence:
    def test_perfect_match(self):
        assert distance_to_confidence(0, 5) == 1.0
    def test_half(self):
        assert abs(distance_to_confidence(2, 4) - 0.5) < 0.01

class TestFindCandidates:
    def test_exact_match(self):
        menus = [{"id": "a", "name": "김치찌개"}]
        res = find_candidates("김치찌개", menus, cutoff=0)
        assert len(res) == 1
        assert res[0]["confidence"] == 1.0

    def test_one_char_diff(self):
        menus = [{"id": "a", "name": "김치찌개"}]
        res = find_candidates("김치찌게", menus)  # 1 char diff
        assert len(res) == 1

    def test_too_different(self):
        menus = [{"id": "a", "name": "김치찌개"}]
        res = find_candidates("라면", menus)
        assert len(res) == 0
```

**test_normalizer.py (8 케이스):**
```python
import pytest
from nlp_mvp.menu_normalizer.normalizer import MenuNormalizer
from nlp_mvp.menu_normalizer.loader import SyntheticMenuLoader

@pytest.fixture(scope="module")
def normalizer():
    return MenuNormalizer(
        loader=SyntheticMenuLoader(),
        enable_embedding=False,  # 빠른 테스트
    )

class TestRuleStage:
    def test_exact(self, normalizer):
        r = normalizer.normalize("김치찌개")
        assert r.method == "rule"
        assert r.confidence == 1.0

    def test_bracket(self, normalizer):
        r = normalizer.normalize("김치찌개(大)")
        assert r.method == "rule"

    def test_synonym(self, normalizer):
        r = normalizer.normalize("김찌")
        assert r.matched_name == "김치찌개"

class TestLevenshteinStage:
    def test_typo(self, normalizer):
        r = normalizer.normalize("김치찌게")  # 오타
        assert r.method == "levenshtein"

class TestNoMatch:
    def test_completely_unrelated(self, normalizer):
        r = normalizer.normalize("외계어쿠키")
        assert r.matched_id is None
        assert r.method == "none"

class TestErrorHandling:
    def test_none_input(self, normalizer):
        r = normalizer.normalize(None)
        assert r.method in ("none", "error")
```

### 6.9 검증 노트북 (`notebooks/02_menu_normalizer_eval.ipynb`)

**셀 구성 (7셀):**
1. 마크다운: 목적
2. Import + MenuNormalizer 초기화
3. `evaluate_on_test_set()` 실행
4. `print_report(report)` 출력
5. 방법별 분포 bar chart
6. 실패 케이스 상위 20 테이블 (pandas)
7. 결론 + 사전 확장 후보 목록

---

## 7. 구현 순서 (5일 체크리스트)

### Day 1 — 규칙 전처리 + 동의어 사전

- [ ] `rules.py` 의 `preprocess_menu_name()` 구현
- [ ] `apply_synonyms()` 구현
- [ ] `load_synonym_dict()` 구현
- [ ] `SynonymDict` 클래스 (선택)
- [ ] `synonym_dict.json` 을 150+ 엔트리로 확장 (§14.B 참고)
- [ ] `test_rules.py` 12+ 케이스 통과

**검증:** `pytest nlp_mvp/menu_normalizer/tests/test_rules.py -v`

### Day 2 — 편집거리 + 로더

- [ ] `loader.py` 의 `StandardMenuLoader` 추상 + 3종
- [ ] `levenshtein.py` 의 `find_candidates()`, `adaptive_cutoff()`, `distance_to_confidence()`
- [ ] `test_levenshtein.py` 6 케이스 통과
- [ ] `_synthetic_menus.py` 에 §14.A 의 100건 시드 추가

**검증:** 합성 메뉴 기준 Stage 1-2 만으로 70% 매칭 확인

### Day 3 — 임베딩 매칭기

- [ ] `embedding_matcher.py` 의 `EmbeddingMatcher` 구현
- [ ] Pickle 캐싱 로직
- [ ] `.cache/` 폴더 자동 생성
- [ ] `batch_match()` 구현
- [ ] 첫 로딩 vs 캐시 로딩 속도 비교 로그

**검증:** 캐시 로딩 시간 < 2초

### Day 4 — 통합 정규화기 + CLI

- [ ] `normalizer.py` 의 `MenuNormalizer` 클래스
- [ ] `NormalizationResult` 데이터 클래스
- [ ] 3단계 매칭 순서 구현
- [ ] `ensure_schema()` + `menu_normalization` 테이블
- [ ] `save_result()` UPSERT 로직
- [ ] `run_batch_normalization()` 파이프라인
- [ ] CLI (`argparse`)
- [ ] `test_normalizer.py` 8 케이스 통과

**검증:** `python -m nlp_mvp.menu_normalizer.normalizer --dry-run --limit 20`

### Day 5 — 평가 + 실패 분석 + 사전 확장

- [ ] `evaluate.py` 의 `evaluate_on_test_set()` 구현
- [ ] `print_report()` 및 CLI
- [ ] 전체 테스트셋(90건) 평가 실행
- [ ] F1 ≥ 0.85 달성 여부 확인
- [ ] 실패 케이스 20건 수동 검토
- [ ] 실패 원인 분석 후 `synonym_dict.json` 추가 확장
- [ ] 재평가 실행 → 최종 F1 기록
- [ ] `notebooks/02_menu_normalizer_eval.ipynb` 실행
- [ ] `nlp_mvp/README.md` 진행률 갱신

**검증:** §8 KPI 모두 달성

---

## 8. KPI 및 검증 기준

| # | 지표 | 측정 방법 | 목표 | 필수 |
|---|------|---------|-----|-----|
| 1 | 규칙 테스트 통과율 | `pytest test_rules.py` | 100% | ✅ |
| 2 | 편집거리 테스트 통과율 | `pytest test_levenshtein.py` | 100% | ✅ |
| 3 | 전체 정규화 정확도 | `evaluate.py` F1 | ≥ 0.85 | ✅ |
| 4 | 매칭률 (매핑 비율) | matched / total | ≥ 0.90 | ✅ |
| 5 | Stage 1-2 커버리지 | 임베딩 없이 F1 | ≥ 0.60 | ⭐ |
| 6 | 배치 처리량 | 1,000 메뉴 / 소요 시간 | ≥ 500/min (CPU) | ⭐ |
| 7 | 동의어 사전 크기 | `len(synonym_dict["synonyms"])` | ≥ 150 | ✅ |
| 8 | 임베딩 캐시 로딩 | 재실행 시 로드 시간 | < 2초 | ⭐ |
| 9 | 테스트 커버리지 | `pytest --cov` | ≥ 70% | ⭐ |
| 10 | `menu_normalization` 테이블 적재 | 전체 식당 메뉴 처리 | ≥ 95% 적재 | ✅ |

---

## 9. 트러블슈팅 (Step 2 한정)

### 9.1 `python-Levenshtein` 설치 실패

**증상:** `pip install python-Levenshtein` 시 C 컴파일러 에러

**해결:**
```bash
# 대안 1: rapidfuzz (C 바이너리 제공)
pip install rapidfuzz
# 그리고 Levenshtein 대신 rapidfuzz.distance.Levenshtein 사용

# 대안 2: pure python
pip install Levenshtein  # 다른 패키지명
```

### 9.2 임베딩 모델 다운로드 실패

**증상:** `OSError: Can't load tokenizer for 'jhgan/ko-sroberta-multitask'`

**해결:**
- Step 1 §9.1 과 동일 (네트워크/HF 토큰 확인)
- 폴백: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

### 9.3 Pickle 캐시 손상

**증상:** `UnpicklingError` 또는 shape mismatch

**해결:**
```bash
rm -rf nlp_mvp/menu_normalizer/.cache/
# 다음 실행 시 재생성
```

### 9.4 매칭 정확도가 낮음 (F1 < 0.75)

**원인 및 해결 순서:**
1. **동의어 사전 부족** → `evaluate.py` 의 failures 로그에서 패턴 추출하여 추가
2. **임베딩 임계값 과다** → `embedding_threshold=0.80` 으로 낮춤
3. **편집거리 cutoff 과소** → `adaptive_cutoff()` 기준 상향
4. **표준 메뉴 DB 부실** → `nutrition_info` 대신 `SyntheticMenuLoader` 시도

### 9.5 임베딩 단계가 너무 느림

**증상:** 1,000건 처리 > 5분

**해결:**
- `batch_match()` 사용 (단건이 아닌 배치)
- `batch_size=64` 이상
- GPU 사용 (`sentence-transformers` 자동 감지)

### 9.6 `menu_normalization` 테이블 UNIQUE 제약 위반

**증상:** `UNIQUE constraint failed: menu_normalization.raw_name, source_table`

**해결:** SQL 을 `ON CONFLICT DO UPDATE` (UPSERT) 로 수정 (본 가이드 §6.6 참고)

### 9.7 `meal_history.menu` 컬럼 없음

**증상:** `OperationalError: no such column: menu`

**원인:** Mini 기존 DB 스키마 다름

**해결:**
```python
# CLI 에 --source-query 옵션 추가
run_batch_normalization(
    source_query="SELECT DISTINCT menu_type FROM restaurants WHERE menu_type IS NOT NULL",
    source_table="restaurants.menu_type",
)
```

---

## 10. 재사용 가능한 기존 파일

### 10.1 본 Step 에서 채울 스켈레톤

| 파일 | 상태 |
|------|------|
| `nlp_mvp/menu_normalizer/rules.py` | 빈 파일 → §6.1 |
| `nlp_mvp/menu_normalizer/synonym_dict.json` | **60 엔트리 있음** → 150+ 로 확장 |
| `nlp_mvp/menu_normalizer/embedding_matcher.py` | 빈 파일 → §6.5 |
| `nlp_mvp/menu_normalizer/normalizer.py` | 빈 파일 → §6.6 |
| `nlp_mvp/menu_normalizer/evaluate.py` | 빈 파일 → §6.7 |
| `nlp_mvp/menu_normalizer/tests/test_rules.py` | 빈 파일 → §6.8 |
| `nlp_mvp/menu_normalizer/tests/test_normalizer.py` | 빈 파일 → §6.8 |
| `nlp_mvp/notebooks/02_menu_normalizer_eval.ipynb` | 스켈레톤 JSON → §6.9 |

### 10.2 신규 생성 필요

| 파일 | 목적 |
|------|------|
| `nlp_mvp/menu_normalizer/loader.py` | 표준 메뉴 로더 (§6.3) |
| `nlp_mvp/menu_normalizer/levenshtein.py` | 편집거리 매칭 (§6.4) |
| `nlp_mvp/menu_normalizer/_synthetic_menus.py` | §14.A 시드 100건 |
| `nlp_mvp/menu_normalizer/tests/test_levenshtein.py` | (§6.8) |
| `nlp_mvp/menu_normalizer/tests/test_embedding_matcher.py` | (§6.8) |
| `nlp_mvp/menu_normalizer/.cache/` | pickle 캐시 디렉토리 (gitignore) |

### 10.3 재사용 (shared/)

| 파일 | 용도 |
|------|------|
| `nlp_mvp/shared/db.py` | `get_session()`, `get_engine()` |
| `nlp_mvp/shared/logger.py` | 공용 로거 |

### 10.4 참조 (읽기 only)

| 파일 | 참조 목적 |
|------|---------|
| `GUIDE_NLP_MVP_SCENARIO3.md` §6 | 원본 요약 명세 |
| `GUIDE_NLP_MVP_STEP1_SENTIMENT.md` | Step 1 패턴 (플러거블 어댑터 참고) |
| `nlp_mvp/data/menu_test_set.csv` | **90건 테스트셋** (이미 존재) |
| `README.md` §6 모듈 매핑 | DB 통합 지점 |

### 10.5 테스트 데이터

| 파일 | 내용 | 이미 존재? |
|------|------|--------|
| `nlp_mvp/menu_normalizer/synonym_dict.json` | 60 엔트리 (확장 필요) | ✅ |
| `nlp_mvp/data/menu_test_set.csv` | 90 테스트 케이스 | ✅ |
| `nlp_mvp/menu_normalizer/_synthetic_menus.py` | 100 표준 메뉴 | ❌ (Day 2 생성) |

---

## 11. 외부 의존성 확인

**이미 `requirements.txt` 에 포함:**

| 패키지 | 버전 | 용도 |
|--------|-----|------|
| `sentence-transformers` | 3.0.1 | EmbeddingMatcher |
| `python-Levenshtein` | 0.25.1 | 편집거리 |
| `numpy` | (자동) | 임베딩 배열 |
| `pandas` | 2.2.2 | evaluate.py, test CSV |
| `sqlalchemy` | 2.0.32 | DB |

**추가 필요 없음.** 단, `python-Levenshtein` 설치 실패 시 `rapidfuzz` 로 교체 가능 (§9.1).

---

## 12. 표준 메뉴 ID 체계 설계

### 12.1 명명 규칙 (합성 메뉴 기준)

```
형식: <카테고리_접두사>_<한글_소문자_영어_발음>
예시:
  kimchi_jjigae   (김치찌개)
  jeyuk_bokkeum   (제육볶음)
  donkatsu        (돈까스)
  cream_pasta     (크림파스타)
```

**규칙:**
1. 영문 소문자, 밑줄(`_`) 구분
2. 한글 발음 그대로 (로마자 표기법: `Revised Romanization`)
3. 길이 최대 30자
4. 중복 방지를 위해 필요 시 카테고리 접두사 (예: `korean_bibimbap`, `jeonju_bibimbap`)

### 12.2 식약처 DB 연동 시

식약처 영양성분 DB 는 **정수 `id`** 를 사용합니다. 이 경우:

```python
# loader.py
class NutritionDBLoader(StandardMenuLoader):
    def load(self) -> list[dict]:
        # id 는 정수지만 문자열로 변환하여 일관성 유지
        return [{"id": f"nutr_{row[0]}", "name": row[1]} for row in rows]
```

### 12.3 ID 충돌 해결

- 같은 이름의 다른 메뉴 (예: "냉면" 이 물냉면·비빔냉면 둘 다) → 접미사 `_v1`, `_v2`
- 수동 매핑 우선 사전: `manual_mapping.json` (선택)

---

## 13. 다음 Step 과의 연결점

### 13.1 Step 1 (A1 감성분석) 연결

- Step 1 의 `reviews.text` 에서 메뉴명 추출 → Step 2 로 전달 가능 (선택 확장)
- 시나리오 2 Phase 6 에서 B2 Food NER 과 결합하여 재료·알레르겐 매칭

### 13.2 Step 3 (D3 RAG 챗봇) 연결

- `menu_normalization.normalized_id` 를 RAG 컨텍스트에 포함
- "비슷한 메뉴" 쿼리 시 임베딩 유사도 결과 재사용 가능

### 13.3 Step 4 (D5 NLG 리포트) 연결

- `meal_history.normalized_menu_id` 를 통해 정확한 영양 정보 조인
- 기존 40% 조인율 → 85% 로 개선된 리포트 품질

### 13.4 Step 5 (통합) 연결

- `scoring_patch.py` 가 `normalized_menu_id` 로 영양 점수 조회
- 매핑 실패(`matched_id IS NULL`) 식당은 영양 점수 0 으로 처리

### 13.5 Phase 6 (시나리오 2) 연결

- B1 의 실패 케이스가 **B2 Food NER** 학습 데이터의 우선순위 라벨링 대상
- 편집거리·임베딩 방식이 "룰 기반 베이스라인" 으로 논문 비교에 사용

---

## 14. 부록

### 14.A 합성 표준 메뉴 100건 (`_synthetic_menus.py`)

> 구현 시 Python 파일로 분리. 아래는 일부 샘플 (Day 2 에 전체 작성).

```python
# nlp_mvp/menu_normalizer/_synthetic_menus.py
"""
합성 표준 메뉴 100건.
테스트·스모크 검증 전용. Mini nutrition_info DB 미완성 시 사용.
"""

SYNTHETIC_STANDARD_MENUS = [
    # 한식 찌개/국 (15)
    {"id": "kimchi_jjigae", "name": "김치찌개", "category": "한식"},
    {"id": "doenjang_jjigae", "name": "된장찌개", "category": "한식"},
    {"id": "sundubu_jjigae", "name": "순두부찌개", "category": "한식"},
    {"id": "budae_jjigae", "name": "부대찌개", "category": "한식"},
    {"id": "cheonggukjang_jjigae", "name": "청국장찌개", "category": "한식"},
    {"id": "gukbap", "name": "국밥", "category": "한식"},
    {"id": "sundae_guk", "name": "순댓국", "category": "한식"},
    {"id": "ppyeo_haejangguk", "name": "뼈해장국", "category": "한식"},
    {"id": "kongnamul_gukbap", "name": "콩나물국밥", "category": "한식"},
    {"id": "somerihi_gukbap", "name": "소머리국밥", "category": "한식"},
    # ... (생략, 전체 100건)

    # 한식 볶음/구이 (10)
    {"id": "jeyuk_bokkeum", "name": "제육볶음", "category": "한식"},
    {"id": "bulgogi", "name": "불고기", "category": "한식"},
    # ...

    # 한식 면류 (10)
    {"id": "bibim_naengmyeon", "name": "비빔냉면", "category": "한식"},
    {"id": "mul_naengmyeon", "name": "물냉면", "category": "한식"},
    # ...

    # 한식 밥류 (15)
    {"id": "bibimbap", "name": "비빔밥", "category": "한식"},
    {"id": "dolsot_bibimbap", "name": "돌솥비빔밥", "category": "한식"},
    # ...

    # 중식 (10)
    {"id": "jjajangmyeon", "name": "짜장면", "category": "중식"},
    {"id": "jjamppong", "name": "짬뽕", "category": "중식"},
    {"id": "tangsuyuk", "name": "탕수육", "category": "중식"},
    # ...

    # 일식 (15)
    {"id": "donkatsu", "name": "돈까스", "category": "일식"},
    {"id": "udon", "name": "우동", "category": "일식"},
    {"id": "ramen", "name": "라멘", "category": "일식"},
    # ...

    # 양식 (15)
    {"id": "pasta", "name": "파스타", "category": "양식"},
    {"id": "cream_pasta", "name": "크림파스타", "category": "양식"},
    {"id": "pizza", "name": "피자", "category": "양식"},
    # ...

    # 분식·동남아·기타 (10)
    {"id": "tteokbokki", "name": "떡볶이", "category": "분식"},
    {"id": "gimbap", "name": "김밥", "category": "분식"},
    {"id": "pho", "name": "쌀국수", "category": "동남아"},
    # ...
]

assert len({m["id"] for m in SYNTHETIC_STANDARD_MENUS}) == len(SYNTHETIC_STANDARD_MENUS), "Duplicate IDs"
```

> **Day 2 작업:** 전체 100건을 `menu_test_set.csv` 의 `expected_id` 컬럼과 맞춰서 작성.

### 14.B 동의어 사전 확장 지침 (150+ 엔트리)

**확장 카테고리:**

1. **축약어** (30+): 김찌, 된찌, 부찌, 순두부, 제육, 불백, 짜장, 비빔, 물냉, 비냉, ...
2. **표기 변형** (20+): 돈가스/돈까스, 오뎅/어묵, 떡볶이/떢볶이, ...
3. **외래어** (15+): 스시→초밥, 돈부리→덮밥, 카레→카레라이스, ...
4. **복합어** (30+): 치즈돈까스→돈까스, 왕돈까스→돈까스, 마라탕→탕, ...
5. **지역명 제거** (10+): 전주비빔밥→비빔밥, 춘천닭갈비→닭갈비, ...
6. **조리법 제거** (15+): 매운김치찌개→김치찌개, 묵은지김치찌개→김치찌개, ...
7. **수식어 제거** (20+): 특제○○→○○, 신선한○○→○○, ...
8. **영문 변환** (10+): spicy chicken→매운치킨, pizza margherita→마르게리타피자

**확장 프로세스:**
1. 스켈레톤의 60 엔트리 기준선 확인
2. Day 5 `evaluate.py` failures 를 보고 카테고리별로 추가
3. `SynonymDict.add(src, dst)` → `save()` 로 자동 저장

### 14.C 편집거리 사례 스터디

| 원본 | 타겟 | 거리 | cutoff | 매칭? |
|-----|-----|-----|--------|------|
| "김치찌게" | "김치찌개" | 1 | 2 | ✅ |
| "김치째개" | "김치찌개" | 2 | 2 | ✅ |
| "짜장면" | "짬뽕" | 3 | 2 | ❌ |
| "돈까스" | "돈부리" | 3 | 2 | ❌ |
| "비빔국수" | "비빔면" | 2 | 2 | ✅ (위험!) |

**의미적 유사와 글자 유사의 괴리** → Stage 3 임베딩 필수

### 14.D 임베딩 코사인 유사도 예시

| Query | Top Match | Score |
|-------|----------|------|
| "얼큰한 김치찌개" | "김치찌개" | 0.92 |
| "매운 국밥" | "국밥" | 0.88 |
| "일본식 돈가스" | "돈까스" | 0.91 |
| "이탈리안 파스타" | "파스타" | 0.94 |
| "샌드위치 런치 세트" | "샌드위치" | 0.87 |
| "치킨 버거" | "햄버거" | 0.79 ❌ (threshold 0.85 미만) |

### 14.E 참고 자료

1. **Sentence-Transformers 공식:**
   https://www.sbert.net/
2. **python-Levenshtein 문서:**
   https://github.com/rapidfuzz/python-Levenshtein
3. **식약처 식품영양성분 DB API:**
   `Mini/api/food/` 참고
4. **한국어 발음 변환 (Revised Romanization):**
   https://en.wikipedia.org/wiki/Revised_Romanization_of_Korean
5. **메뉴 매칭 관련 논문:**
   "Entity Matching using Semi-Supervised Learning" (KDD 2019)

---

## 15. 1페이지 체크리스트 요약

### ✅ Step 2 (B1 메뉴 정규화) 2주차 체크리스트

**Day 1 — 규칙 + 사전**
- [ ] `rules.py` 3함수 구현
- [ ] `synonym_dict.json` 150+ 엔트리 확장
- [ ] `test_rules.py` 12+ 통과

**Day 2 — 편집거리 + 로더**
- [ ] `levenshtein.py` 3함수
- [ ] `loader.py` 3종 (Synthetic/NutritionDB/File)
- [ ] `_synthetic_menus.py` 100건 작성
- [ ] `test_levenshtein.py` 6 통과

**Day 3 — 임베딩**
- [ ] `EmbeddingMatcher` 구현
- [ ] Pickle 캐싱 동작
- [ ] 캐시 로딩 < 2초

**Day 4 — 통합**
- [ ] `MenuNormalizer` 3단계 매칭
- [ ] `ensure_schema()` + 테이블 생성
- [ ] `run_batch_normalization()` + CLI
- [ ] `test_normalizer.py` 8 통과

**Day 5 — 평가**
- [ ] `evaluate.py` 실행 → F1 ≥ 0.85
- [ ] 실패 20건 검토
- [ ] 사전 재확장 → 재평가
- [ ] `02_menu_normalizer_eval.ipynb` 실행

### 🎯 KPI 달성
- [ ] 테스트 통과율 100%
- [ ] 전체 정확도 F1 ≥ 0.85
- [ ] 매칭률 ≥ 90%
- [ ] 동의어 사전 ≥ 150
- [ ] 캐시 로딩 < 2초
- [ ] 영양 DB 조인율 ≥ 85%

### 📦 산출물
- [ ] `menu_normalizer/` 8개 파이썬 파일
- [ ] `tests/` 5개 테스트 파일
- [ ] `synonym_dict.json` v0.2.0 (150+)
- [ ] `_synthetic_menus.py` (100건)
- [ ] `.cache/standard_embeddings.pkl`
- [ ] `menu_normalization` 테이블 + 레코드
- [ ] `notebooks/02_menu_normalizer_eval.ipynb`

### 📎 다음 단계
- [ ] Step 3 (D3 RAG 챗봇) 로 진행
- [ ] `nlp_mvp/README.md` 진행률 갱신
- [ ] `GUIDE_NLP_MVP_SCENARIO3.md` §12.2 체크박스 동기화

---

**문서 버전:** v1.0
**작성일:** 2026-04-07
**대상:** Mini NLP MVP 2주차 구현자
**상위 문서:** [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §6
**선행 문서:** [`GUIDE_NLP_MVP_STEP1_SENTIMENT.md`](./GUIDE_NLP_MVP_STEP1_SENTIMENT.md)
**관련 문서:**
- [`README.md`](./README.md) — NLP 레이어 진입점
- [`GUIDE_NLP_RESEARCH_SCENARIO2.md`](./GUIDE_NLP_RESEARCH_SCENARIO2.md) — 연구형 심화 (B2 Food NER)

---

<div align="center">

**🔹 Step 2 — 혼돈의 메뉴명을 표준화된 지식으로.**

*Mini NLP MVP — From Chaos to Catalog.*

</div>
