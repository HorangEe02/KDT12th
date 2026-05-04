# 🔹 Step 1 — A1 리뷰 감성분석 파이프라인 상세 구현 가이드

> **Mini NLP MVP 의 1주차 전용 심화 가이드**
>
> 본 문서는 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §5 의
> Step 1 섹션을 **1주차 단일 독립 체크리스트** 로 확장한 문서입니다.
> 브레인스토밍 결과 · 대안 비교 · 파일별 상세 명세 · 테스트 전략 · 트러블슈팅을
> 한 문서에 집약하여, **이 문서만으로 Step 1 을 완수할 수 있도록** 설계되었습니다.

---

## 📋 목차

1. [문서 목적 및 위치](#1-문서-목적-및-위치)
2. [Step 1 전체 조감](#2-step-1-전체-조감)
3. [브레인스토밍 — 기술 선택 의사결정](#3-브레인스토밍--기술-선택-의사결정)
4. [확장 아키텍처 다이어그램](#4-확장-아키텍처-다이어그램)
5. [파일 목록 및 의존성 그래프](#5-파일-목록-및-의존성-그래프)
6. [파일별 상세 명세](#6-파일별-상세-명세)
7. [구현 순서 (5일 체크리스트)](#7-구현-순서-5일-체크리스트)
8. [KPI 및 검증 기준](#8-kpi-및-검증-기준)
9. [트러블슈팅 (Step 1 한정)](#9-트러블슈팅-step-1-한정)
10. [재사용 가능한 기존 파일](#10-재사용-가능한-기존-파일)
11. [외부 의존성 확인](#11-외부-의존성-확인)
12. [보안 및 법적 주의사항](#12-보안-및-법적-주의사항)
13. [다음 Step 과의 연결점](#13-다음-step-과의-연결점)
14. [부록](#14-부록)
15. [1페이지 체크리스트 요약](#15-1페이지-체크리스트-요약)

---

## 1. 문서 목적 및 위치

### 1.1 왜 별도 가이드인가

상위 가이드 [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) 는 4주 전체
로드맵을 개괄하는 **요약형 Claude Code 프롬프트 묶음**입니다. 1주차 A1 감성분석을
실제로 구현하기 위해서는 다음이 추가로 필요합니다:

- **기술 선택의 근거** — KcELECTRA 를 왜 골랐는지, 데이터 소스 전략은 어떻게 세웠는지
- **함수 시그니처 이상의 세부 명세** — 입력·출력·예외·엣지케이스
- **5일 단위 체크리스트** — 하루 단위로 무엇을 완료해야 하는지
- **트러블슈팅 지식** — 실제 구현 중 마주칠 이슈들의 대응법

본 문서는 이 모든 것을 한 파일에 집약합니다.

### 1.2 상위 문서와의 관계

```
Mini/NLP/
├── README.md                        # NLP 레이어 진입점
├── GUIDE_NLP_MVP_SCENARIO3.md       # 4주 전체 요약 가이드 (상위)
│   └── §5 Step 1                    #   → 본 문서가 확장
├── GUIDE_NLP_MVP_STEP1_SENTIMENT.md # 🆕 본 문서 (Step 1 전용 상세)
└── GUIDE_NLP_RESEARCH_SCENARIO2.md  # 10주 연구 가이드
```

**독자 권장 순서:**
1. `README.md` 로 NLP 레이어 전체 이해
2. `GUIDE_NLP_MVP_SCENARIO3.md` 로 4주 로드맵 파악
3. **본 문서** 로 1주차 착수
4. (2주차부터는 상위 가이드의 §6~§8 참조)

### 1.3 선행 조건

본 문서를 시작하기 전 다음이 완료되어 있어야 합니다:

- [x] `Mini/NLP/nlp_mvp/` 스켈레톤 생성 완료 (폴더·빈 파일)
- [x] `Mini/NLP/.env` 파일 작성 (`.env.example` 복사 후 편집)
- [x] Python 3.10+ 가상환경 + `requirements.txt` 설치
- [x] Mini 기존 SQLite DB 존재 (시드 데이터라도 OK)
- [x] (선택) Ollama 설치 — Step 3 (D3 챗봇) 부터 필요, Step 1 에서는 불필요
- [ ] `shared/db.py`, `shared/logger.py` 구현 완료 (**Step 0 선행 작업**)

> 💡 **Step 0 공용 유틸이 아직 비어있다면**, 본 가이드의 §6.1 을 먼저 확인하세요.

---

## 2. Step 1 전체 조감

### 2.1 한 줄 목표

> **리뷰 텍스트 → 음식점별 감성 점수 (-1 ~ +1) → Mini 스코어링 엔진 보정**

### 2.2 1주차 5일 일정

| Day | 작업 테마 | 산출물 | 누적 진행도 |
|-----|---------|--------|-----------|
| **Day 1** | DB 스키마 + 전처리 + 단위 테스트 | `update_db.ensure_schema()`, `preprocess.py`, 5+ 테스트 | 20% |
| **Day 2** | 데이터 소스 어댑터 3종 | `ReviewSource` 추상, `SyntheticSource`, `AIHubSource`, `ReviewCrawler` | 40% |
| **Day 3** | 감성분석 모델 통합 | `SentimentAnalyzer` 클래스, `aggregate()`, 6개 테스트 | 60% |
| **Day 4** | 통합 파이프라인 + CLI | `run_sentiment_update()`, dry-run 모드, 10 식당 end-to-end | 80% |
| **Day 5** | 배치 실행 + 검증 노트북 | 100 식당 처리, `01_sentiment_eda.ipynb`, KPI 측정 | 100% |

### 2.3 완료 기준 (한눈에)

| 기준 | 목표치 |
|------|-------|
| ✅ 처리량 (CPU) | ≥ 1,000 리뷰/시간 |
| ✅ 스모크 정확도 | 긍/부 12건 중 ≥ 11건 정답 |
| ✅ 100 식당 배치 실행 | 에러 0건, 95% 이상 업데이트 |
| ✅ 테스트 커버리지 | ≥ 70% (pytest --cov) |
| ✅ DB 멱등성 | `ensure_schema()` 2회 호출 성공 |

---

## 3. 브레인스토밍 — 기술 선택 의사결정

### 3.1 감성분석 모델 선택

**고려한 후보들:**

| 모델 | 장점 | 단점 | MVP 적합성 |
|------|------|------|-----------|
| `nlp04/korean_sentiment_analysis_kcelectra` | ⭐ 3-class (pos/neu/neg) 즉시 사용<br>⭐ 한국어 리뷰 도메인 근접<br>⭐ Hugging Face pipeline 호환 | 유지보수 활발성 미지수 | ⭐⭐⭐⭐⭐ |
| `beomi/KcELECTRA-base-v2022` + 커스텀 헤드 | 최신 사전학습, 코멘트 특화 | 파인튜닝 필요 → MVP 범위 초과 | ⭐⭐⭐ |
| `snunlp/KR-FinBert-SC` | 한국어 특화, SNU 품질 | 금융 도메인 편향 | ⭐⭐ |
| `cardiffnlp/twitter-xlm-roberta-base-sentiment` | 다국어 지원 | 한국어 리뷰 성능 미검증 | ⭐⭐ |
| OpenAI `gpt-4o-mini` API | 최고 정확도, zero-shot | 유료·네트워크 의존 | ⭐⭐ (MVP 원칙 위배) |

**의사결정:**

- **1순위 (주 모델):** `nlp04/korean_sentiment_analysis_kcelectra`
  - 이유: 별도 파인튜닝 없이 3-class 분류 즉시 가능, MVP "Zero-shot" 원칙에 부합
- **2순위 (fallback):** `beomi/KcELECTRA-base-v2022` + `pipeline("text-classification")`
  - 1순위 모델 다운로드 실패·환경 이슈 시 대체
- **미채택:** OpenAI API (로컬·무료 원칙 위배), KR-FinBert (도메인 불일치)

**코드상 반영 방식:**
```python
# .env
SENTIMENT_MODEL=nlp04/korean_sentiment_analysis_kcelectra

# sentiment_pipeline.py
DEFAULT_MODEL = os.getenv("SENTIMENT_MODEL", "nlp04/korean_sentiment_analysis_kcelectra")
FALLBACK_MODEL = "beomi/KcELECTRA-base-v2022"
```

### 3.2 리뷰 데이터 소스 선택

**고려한 후보들:**

| 소스 | 합법성 | 리뷰 풍부도 | 구현 난이도 | MVP 채택 |
|------|-------|----------|----------|---------|
| 카카오 REST Local API (공식) | ✅ ToS 준수 | ⚠️ 리뷰 필드 미제공 (메타만) | ⭐ | ❌ |
| 카카오맵 공개 Place 페이지 (HTML) | 🟡 연구 한정 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 🟡 선택적 |
| 네이버 지도 공개 페이지 (HTML) | 🟡 연구 한정 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 🟡 선택적 |
| **AI-Hub "한국어 음식 리뷰 데이터셋"** | ✅ 완전 합법 | ⭐⭐⭐ | ⭐⭐ | ✅ **1순위** |
| NSMC (네이버 영화 리뷰) | ✅ 학습 목적 | ❌ 도메인 불일치 | ⭐ | ❌ |
| **합성/시드 리뷰 (직접 작성)** | ✅ | ⭐⭐ | ⭐ | ✅ **스모크 테스트** |

**의사결정 (단계적 접근):**

1. **Day 1-2 (파이프라인 검증):**
   - **`SyntheticSource`** — 100건 하드코딩된 리뷰 (§14.A 부록 참고)
   - 목적: 네트워크·외부 데이터 의존 없이 파이프라인 end-to-end 검증

2. **Day 3-4 (실데이터 도입):**
   - **`AIHubSource`** — AI-Hub 공개 음식 리뷰 데이터셋 CSV 로더
   - 합법성 ✅, 라이선스 명확, 재현 가능

3. **Day 5+ (선택적 확장):**
   - **`KakaoPublicSource`** — 공개 페이지 HTML 파싱
   - 상단 ToS 경고문 필수, 연구 목적 한정, rate limit 준수

**설계 원칙: 플러거블 어댑터 패턴**

```python
# sentiment/crawler.py
from abc import ABC, abstractmethod

class ReviewSource(ABC):
    """리뷰 데이터 소스 추상 인터페이스"""
    @abstractmethod
    def fetch(self, restaurant_id: int, max_count: int) -> list[dict]:
        ...

class SyntheticSource(ReviewSource): ...    # Day 1-2
class AIHubSource(ReviewSource): ...        # Day 3-4
class KakaoPublicSource(ReviewSource): ...  # Day 5+ (선택)
```

**이점:**
- 크롤링 이슈로 전체 파이프라인이 블로킹되지 않음
- 단위 테스트 시 `SyntheticSource` 만으로 완결 가능
- 법적 리스크 회피 (기본 경로가 합성 + 공개 데이터)
- 장기적으로 새로운 소스 추가 용이

### 3.3 배치 처리 및 디바이스 전략

**MVP 타겟 환경:** 일반 개발자 노트북 (CPU 전용 가능)

**고려 사항:**
- ✅ GPU 없어도 동작해야 함
- ✅ 모델 로딩은 1회만 (재사용)
- ✅ 배치 추론으로 처리량 극대화

**해결 방식:**

```python
import torch
from functools import lru_cache

class SentimentAnalyzer:
    def __init__(self, model_name: str | None = None, device: str = "auto"):
        self.device = self._resolve_device(device)
        self.batch_size = 32 if self.device == "cuda" else 8  # 자동 조정
        self._load_model(model_name or DEFAULT_MODEL)

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def analyze_batch(self, texts, batch_size=None):
        batch_size = batch_size or self.batch_size
        with torch.no_grad():  # 메모리 절약
            # ... 배치 추론
```

**모델 싱글톤 (선택):**
```python
@lru_cache(maxsize=1)
def get_analyzer() -> SentimentAnalyzer:
    return SentimentAnalyzer()
```

### 3.4 데이터베이스 연결 관리

**선택지 비교:**

| 방식 | 장점 | 단점 | 선택 |
|------|------|------|------|
| (A) 매 호출마다 연결 생성·해제 | 단순 | 오버헤드 큼 | ❌ |
| (B) SQLAlchemy `sessionmaker` + 컨텍스트 매니저 | 풀링, 트랜잭션 | 초기 설정 필요 | ✅ |
| (C) 글로벌 session 싱글톤 | 빠름 | 테스트 격리 어려움 | ❌ |

**결정:** (B) — `shared/db.py` 의 `get_session()` 컨텍스트 매니저 재사용

**트랜잭션 전략:** 식당 단위 커밋 (중간 실패 시 부분 진행 보장)

```python
with get_session() as session:
    for rest_id in restaurant_ids:
        try:
            # 1개 식당 처리
            session.commit()  # 식당 단위 커밋
        except Exception as e:
            session.rollback()
            errors += 1
            logger.error(f"restaurant {rest_id} failed: {e}")
```

### 3.5 집계 공식 — 점수 정규화

**후보 공식:**

| 공식 | 수식 | 범위 | 특징 |
|------|------|------|------|
| (A) **대칭 비율** | `(pos - neg) / total` | [-1, +1] | ✅ 직관적, 중립 포함 |
| (B) 긍정 비율 | `pos / (pos + neg)` | [0, 1] | 중립 무시 |
| (C) 가중 평균 | `sum(conf × label)` | [-1, +1] | 신뢰도 반영 |
| (D) Wilson score | 보수적 CI | [0, 1] | 샘플 수 적을 때 유리 |

**결정:** (A) `(pos - neg) / total` + `min_reviews=5` 가드

**근거:**
- 해석 용이: "+1 = 전부 긍정, -1 = 전부 부정, 0 = 균형"
- Mini 스코어링 엔진의 곱 보정 (`× (1 + 0.15 × score)`) 에 자연스럽게 연결
- 샘플 5건 미만은 `sentiment_score=NULL` 유지하여 편향 방지

```python
def aggregate(results: list[dict], min_sample: int = 5) -> dict:
    total = len(results)
    if total < min_sample:
        return {"score": None, "sample_size": total, "reason": "insufficient_samples"}

    pos = sum(1 for r in results if r["label"] == "positive")
    neg = sum(1 for r in results if r["label"] == "negative")
    return {
        "score": (pos - neg) / total,
        "pos_ratio": pos / total,
        "neg_ratio": neg / total,
        "sample_size": total,
    }
```

### 3.6 크롤링 ToS 및 보안 원칙

**모든 `KakaoPublicSource` · `NaverPublicSource` 어댑터 파일 상단에 필수:**

```python
"""
⚠️ 법적 고지 (Legal Notice)
================================
1. 본 크롤러는 연구·학습 목적의 공개 데이터 수집용입니다.
2. 상업적 재배포 및 대량 크롤링은 카카오·네이버 ToS 위반입니다.
3. 로그인 필요 영역·개인정보 필드에 접근하지 않습니다.
4. 운영 배포 시 공식 파트너 API 교체가 필수입니다.
5. 저작권은 원 작성자·플랫폼에 귀속됩니다.
"""
```

**기술적 준수 사항:**
- `User-Agent` 명시 (`"Mini-NLP-MVP/1.0 (research)"`)
- 요청 간 `time.sleep(1.5)` 이상
- HTTP 429 응답 시 `Retry-After` 헤더 존중
- 타임아웃: `requests.get(..., timeout=10)` 필수
- 원문 저장 시 `source`, `fetched_at`, `external_id` 메타 필수

### 3.7 에러 격리 및 복구 전략

**원칙:** "식당 1곳의 실패가 전체 배치를 막지 않는다"

| 에러 계층 | 대응 |
|---------|------|
| 네트워크 (크롤러) | 빈 리스트 반환, 로그, 다음 식당 계속 |
| 전처리 (preprocess) | 해당 리뷰 스킵, 카운터 증가 |
| 모델 추론 (transformers) | try/except 로 배치 단위 재시도, 실패 시 리뷰 단위 fallback |
| DB 쓰기 (SQLAlchemy) | `session.rollback()` + 에러 로그, 다음 식당 계속 |
| 전역 | KeyboardInterrupt / 치명적 에러만 전파 |

**구조:**
```python
def run_sentiment_update(...):
    stats = {"processed": 0, "updated": 0, "skipped": 0, "errors": 0}
    for rest_id in restaurant_ids:
        try:
            process_one(rest_id)
            stats["updated"] += 1
        except InsufficientSamplesError:
            stats["skipped"] += 1
        except Exception as e:
            stats["errors"] += 1
            logger.exception(f"restaurant {rest_id}: {e}")
        finally:
            stats["processed"] += 1
    return stats
```

---

## 4. 확장 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────────┐
│                    MINI 기존 DB (SQLite)                       │
│   restaurants (id, name, ...) ← Step 1 컬럼 추가 대상             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ ① restaurant_ids 조회
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                   run_sentiment_update()                         │
│                                                                  │
│   식당 루프 (트랜잭션 경계)                                       │
│   ┌───────────────────────────────────────────────────────────┐ │
│   │ for rest_id in restaurant_ids:                             │ │
│   │   try:                                                      │ │
│   │     ┌──────────────┐                                       │ │
│   │     │ ② Crawler    │ ◄── SyntheticSource                  │ │
│   │     │ .fetch_      │      AIHubSource                     │ │
│   │     │   reviews()  │      KakaoPublicSource (선택)         │ │
│   │     └──────┬───────┘                                       │ │
│   │            │ list[dict]                                    │ │
│   │     ┌──────▼────────┐                                      │ │
│   │     │ ③ Preprocess  │                                      │ │
│   │     │  clean_text   │                                      │ │
│   │     │  is_valid     │                                      │ │
│   │     │  deduplicate  │                                      │ │
│   │     └──────┬────────┘                                      │ │
│   │            │                                                │ │
│   │     ┌──────▼─────────────┐                                 │ │
│   │     │ ④ SentimentAnalyzer│                                 │ │
│   │     │   .analyze_batch() │  ◄── KcELECTRA 모델              │ │
│   │     │    (torch.no_grad) │                                 │ │
│   │     └──────┬─────────────┘                                 │ │
│   │            │ list of {label, confidence}                   │ │
│   │     ┌──────▼──────┐                                        │ │
│   │     │ ⑤ aggregate │                                        │ │
│   │     │   → score   │                                        │ │
│   │     └──────┬──────┘                                        │ │
│   │            │                                                │ │
│   │     ┌──────▼──────────────┐                                │ │
│   │     │ ⑥ DB UPSERT         │                                │ │
│   │     │  INSERT reviews ... │                                │ │
│   │     │  UPDATE restaurants │                                │ │
│   │     └──────┬──────────────┘                                │ │
│   │            │                                                │ │
│   │     session.commit()  ◄── 식당 단위 트랜잭션                │ │
│   │                                                             │ │
│   │   except InsufficientSamplesError: skipped++                │ │
│   │   except Exception:                 errors++, rollback      │ │
│   │   finally:                          processed++             │ │
│   └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│   return {processed, updated, skipped, errors, duration_sec}    │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    CLI 또는 노트북에서 호출
                    (--dry-run · --limit · --source)
```

**에러 경로 요약:**
- ②③ 실패 → 빈 리스트 전파 → ⑤ `insufficient_samples` → 스킵
- ④ 실패 → 예외 → errors++, rollback
- ⑥ 실패 → rollback, 다음 식당 계속

---

## 5. 파일 목록 및 의존성 그래프

```
┌─────────────────────────────────────┐
│ Step 0 (선행, 공용)                  │
├─────────────────────────────────────┤
│ shared/db.py          (SQLAlchemy)  │
│ shared/logger.py      (logging)     │
└────────────────┬────────────────────┘
                 │ import
                 ▼
┌─────────────────────────────────────┐
│ Step 1 — A1 감성분석                 │
├─────────────────────────────────────┤
│                                     │
│  sentiment/                         │
│  ├─ update_db.py                    │
│  │   ├─ ensure_schema()  ◄── Day 1 │
│  │   └─ run_sentiment_update()     │
│  │                                  │
│  │   imports ▼                     │
│  │                                  │
│  ├─ crawler.py           ◄── Day 2 │
│  │   ├─ ReviewSource (ABC)         │
│  │   ├─ SyntheticSource            │
│  │   ├─ AIHubSource                │
│  │   ├─ KakaoPublicSource (선택)    │
│  │   └─ ReviewCrawler              │
│  │                                  │
│  ├─ preprocess.py        ◄── Day 1 │
│  │   ├─ clean_text()               │
│  │   ├─ is_valid_review()          │
│  │   └─ deduplicate()              │
│  │                                  │
│  ├─ sentiment_pipeline.py ◄── Day 3│
│  │   ├─ SentimentAnalyzer          │
│  │   ├─ analyze() / analyze_batch()│
│  │   └─ aggregate()                │
│  │                                  │
│  └─ tests/                          │
│      ├─ test_preprocess.py         │
│      ├─ test_crawler.py            │
│      ├─ test_sentiment_pipeline.py │
│      └─ test_update_db.py          │
│                                     │
│  notebooks/01_sentiment_eda.ipynb   │
│  ◄── Day 5 검증                     │
└─────────────────────────────────────┘
```

**import 방향성:**
- `update_db.py` → `crawler`, `preprocess`, `sentiment_pipeline`, `shared.db`, `shared.logger`
- `crawler.py` → `shared.logger`, `preprocess` 는 안 씀 (관심사 분리)
- `preprocess.py` → 표준 라이브러리만 + `emoji`
- `sentiment_pipeline.py` → `transformers`, `torch`, `shared.logger`

**순환 의존 없음.**

---

## 6. 파일별 상세 명세

### 6.1 `shared/db.py` (Step 0 선행)

본 Step 에서 `get_session()` 컨텍스트 매니저만 재사용합니다. 아직 미구현이라면
다음 최소 구현을 먼저 작성하세요.

**최소 인터페이스:**
```python
# nlp_mvp/shared/db.py
import os
from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()  # Mini/NLP/.env

DB_PATH = os.getenv("MINI_DB_PATH", "../data/mini.db")
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        db_url = f"sqlite:///{Path(DB_PATH).resolve()}"
        _engine = create_engine(db_url, future=True)
    return _engine

def get_sessionmaker():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal

@contextmanager
def get_session() -> Session:
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def get_metadata() -> MetaData:
    """기존 Mini 테이블 reflect 용"""
    metadata = MetaData()
    metadata.reflect(bind=get_engine())
    return metadata
```

### 6.2 `sentiment/update_db.py` — `ensure_schema()`

**시그니처:**
```python
from sqlalchemy import text
from sqlalchemy.engine import Engine

def ensure_schema(engine: Engine) -> None:
    """
    restaurants 테이블에 감성 관련 컬럼을 추가하고,
    reviews 테이블을 생성한다. 멱등 실행 가능.

    Raises:
        sqlalchemy.exc.OperationalError: restaurants 테이블 자체가 없을 때
    """
```

**동작 세부:**

1. **컬럼 추가 (restaurants):**
   ```python
   REQUIRED_COLUMNS = {
       "sentiment_score": "REAL DEFAULT NULL",
       "sentiment_pos_ratio": "REAL DEFAULT NULL",
       "sentiment_neg_ratio": "REAL DEFAULT NULL",
       "sentiment_sample_size": "INTEGER DEFAULT 0",
       "sentiment_updated_at": "DATETIME DEFAULT NULL",
   }
   ```
   - `PRAGMA table_info(restaurants)` 로 기존 컬럼 조회
   - 없는 컬럼만 `ALTER TABLE restaurants ADD COLUMN ...` 실행

2. **reviews 테이블 생성:**
   ```sql
   CREATE TABLE IF NOT EXISTS reviews (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       restaurant_id INTEGER NOT NULL,
       source TEXT NOT NULL,
       text TEXT NOT NULL,
       sentiment_label TEXT,
       sentiment_confidence REAL,
       external_id TEXT,
       fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
       UNIQUE (restaurant_id, source, text)
   );
   ```

3. **인덱스 (선택):**
   ```sql
   CREATE INDEX IF NOT EXISTS idx_reviews_restaurant ON reviews(restaurant_id);
   CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews(source);
   ```

**엣지 케이스:**
- `restaurants` 테이블이 없는 경우 → `OperationalError` 전파 (상위에서 catch)
- 컬럼이 이미 있음 → 스킵
- 동시 호출 → SQLite 는 단일 파일 락 사용, 문제 없음

### 6.3 `sentiment/crawler.py` — 플러거블 어댑터

**파일 상단 필수 주석:**
```python
"""
⚠️ 법적 고지 (Legal Notice)
================================
1. 본 크롤러는 연구·학습 목적의 공개 데이터 수집용입니다.
2. 상업적 재배포 및 대량 크롤링은 카카오·네이버 ToS 위반입니다.
3. 로그인 필요 영역·개인정보 필드에 접근하지 않습니다.
4. 운영 배포 시 공식 파트너 API 교체가 필수입니다.
5. 저작권은 원 작성자·플랫폼에 귀속됩니다.
"""
```

**추상 인터페이스:**
```python
from abc import ABC, abstractmethod
from typing import Iterable

class ReviewSource(ABC):
    name: str  # "synthetic" | "aihub" | "kakao_public"

    @abstractmethod
    def fetch(self, restaurant_id: int, max_count: int = 100) -> list[dict]:
        """
        Returns:
            [
                {
                    "source": str,        # self.name
                    "text": str,          # 원문
                    "external_id": str | None,
                    "fetched_at": str,    # ISO datetime
                },
                ...
            ]
        """
```

**구현 1 — SyntheticSource:**
```python
from datetime import datetime

class SyntheticSource(ReviewSource):
    """
    테스트·파이프라인 검증용 합성 리뷰.
    100건 내외의 하드코딩된 리뷰를 rotate 하여 반환.
    restaurant_id 해시로 deterministic 하게 선택.
    """
    name = "synthetic"

    # §14.A 부록의 50건 시드를 모듈 레벨 상수로
    SEED_REVIEWS = [
        "음식이 정말 맛있고 사장님도 친절해요. 다음에도 올게요!",
        "가격 대비 양도 많고 만족스럽네요.",
        "재료가 신선해서 좋았습니다.",
        # ... (§14.A 전체 50건)
    ]

    def fetch(self, restaurant_id: int, max_count: int = 100) -> list[dict]:
        import random
        rng = random.Random(restaurant_id)  # deterministic
        count = min(max_count, len(self.SEED_REVIEWS))
        sampled = rng.sample(self.SEED_REVIEWS, count)
        now = datetime.utcnow().isoformat()
        return [
            {
                "source": self.name,
                "text": text,
                "external_id": f"synthetic-{restaurant_id}-{i}",
                "fetched_at": now,
            }
            for i, text in enumerate(sampled)
        ]
```

**구현 2 — AIHubSource (스켈레톤):**
```python
import pandas as pd
from pathlib import Path

class AIHubSource(ReviewSource):
    """
    AI-Hub "한국어 음식 리뷰 데이터셋" 로더.

    사전 준비:
    1. https://aihub.or.kr 에서 회원가입 · 데이터셋 다운로드
    2. CSV 를 nlp_mvp/data/raw/aihub_food_reviews.csv 경로에 저장
    3. CSV 컬럼: restaurant_name, review_text, rating, date
    """
    name = "aihub"

    def __init__(self, csv_path: Path | None = None):
        self.csv_path = csv_path or Path("nlp_mvp/data/raw/aihub_food_reviews.csv")
        self._df = None

    def _load(self):
        if self._df is None:
            if not self.csv_path.exists():
                raise FileNotFoundError(
                    f"AI-Hub CSV not found: {self.csv_path}\n"
                    "다운로드 가이드: §14.B 참고"
                )
            self._df = pd.read_csv(self.csv_path)
        return self._df

    def fetch(self, restaurant_id: int, max_count: int = 100) -> list[dict]:
        df = self._load()
        # restaurant_id → 랜덤 샘플 (실제 매핑 없을 때)
        sample = df.sample(n=min(max_count, len(df)), random_state=restaurant_id)
        now = datetime.utcnow().isoformat()
        return [
            {
                "source": self.name,
                "text": row["review_text"],
                "external_id": f"aihub-{idx}",
                "fetched_at": now,
            }
            for idx, row in sample.iterrows()
        ]
```

**구현 3 — KakaoPublicSource (선택, 스켈레톤만):**
```python
import time, requests
from bs4 import BeautifulSoup

class KakaoPublicSource(ReviewSource):
    """⚠️ 공개 Place 페이지 크롤러. 연구 한정, ToS 경고 필수."""
    name = "kakao_public"
    USER_AGENT = "Mini-NLP-MVP/1.0 (research)"
    SLEEP = 1.5

    def __init__(self, rate_limit_sec: float = SLEEP):
        self.rate_limit_sec = rate_limit_sec

    def fetch(self, restaurant_id: int, max_count: int = 100) -> list[dict]:
        # TODO: 실제 페이지 URL 스키마는 공식 문서 참조
        time.sleep(self.rate_limit_sec)
        try:
            # ... 파싱 ...
            return []
        except Exception as e:
            import logging
            logging.getLogger("nlp_mvp.crawler").error(f"kakao fetch failed: {e}")
            return []
```

**ReviewCrawler (통합):**
```python
class ReviewCrawler:
    """
    여러 ReviewSource 를 순차 시도하여 최초로 결과가 나오는 소스를 사용.
    Day 1-2 에서는 SyntheticSource 만 주입하여 시작.
    """
    def __init__(self, sources: list[ReviewSource]):
        if not sources:
            raise ValueError("At least one ReviewSource required")
        self.sources = sources
        self.logger = logging.getLogger("nlp_mvp.crawler")

    def fetch_reviews(self, restaurant_id: int, max_count: int = 100) -> list[dict]:
        for src in self.sources:
            try:
                results = src.fetch(restaurant_id, max_count)
                if results:
                    self.logger.info(
                        f"[{src.name}] restaurant {restaurant_id}: "
                        f"{len(results)} reviews fetched"
                    )
                    return results
            except Exception as e:
                self.logger.warning(f"[{src.name}] failed: {e}, trying next source")
        return []
```

### 6.4 `sentiment/preprocess.py` — 순수 함수 3종

```python
import re
import hashlib
import emoji

# 모듈 레벨에서 정규식 컴파일 (성능)
_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_NON_MEANINGFUL_PATTERN = re.compile(r"^[\d\s\W]+$")  # 숫자·특수문자·공백만

def clean_text(text: str) -> str:
    """
    리뷰 텍스트 정제.

    단계:
    1. URL 제거
    2. 이모지 제거
    3. 연속 공백 정규화
    4. 양쪽 공백 트림
    """
    if not isinstance(text, str):
        return ""
    text = _URL_PATTERN.sub("", text)
    text = emoji.replace_emoji(text, replace="")
    text = _WHITESPACE_PATTERN.sub(" ", text)
    return text.strip()

def is_valid_review(text: str, min_len: int = 5) -> bool:
    """
    리뷰 유효성 검사.

    Returns:
        True if:
            - 길이 ≥ min_len
            - 숫자·특수문자·공백 외에 실제 문자가 있음
    """
    if not text or len(text) < min_len:
        return False
    if _NON_MEANINGFUL_PATTERN.match(text):
        return False
    return True

def deduplicate(reviews: list[dict], text_key: str = "text") -> list[dict]:
    """
    동일 텍스트 리뷰 제거. 순서 보존.
    clean_text() 결과의 MD5 해시로 비교.
    """
    seen: set[str] = set()
    result: list[dict] = []
    for r in reviews:
        cleaned = clean_text(r.get(text_key, ""))
        digest = hashlib.md5(cleaned.encode("utf-8")).hexdigest()
        if digest not in seen:
            seen.add(digest)
            result.append(r)
    return result
```

**순수 함수 원칙:** 모든 함수는 side-effect 없음 (DB·파일·네트워크 접근 없음).

### 6.5 `sentiment/sentiment_pipeline.py` — `SentimentAnalyzer`

```python
import os
import time
import logging
from functools import lru_cache
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

DEFAULT_MODEL = os.getenv(
    "SENTIMENT_MODEL",
    "nlp04/korean_sentiment_analysis_kcelectra"
)
FALLBACK_MODEL = "beomi/KcELECTRA-base-v2022"

# 모델별 id2label 편차를 흡수하는 표준 매핑
CANONICAL_LABELS = {"positive", "neutral", "negative"}
LABEL_ALIASES = {
    "긍정": "positive", "pos": "positive", "LABEL_2": "positive",
    "중립": "neutral",  "neu": "neutral",  "LABEL_1": "neutral",
    "부정": "negative", "neg": "negative", "LABEL_0": "negative",
}

logger = logging.getLogger("nlp_mvp.sentiment_pipeline")

class SentimentAnalyzer:
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: str = "auto",
    ):
        self.model_name = model_name or DEFAULT_MODEL
        self.device = self._resolve_device(device)
        self.default_batch_size = 32 if self.device == "cuda" else 8
        self._load_model()

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def _load_model(self):
        logger.info(f"Loading model: {self.model_name} on {self.device}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            ).to(self.device)
        except Exception as e:
            logger.warning(f"Primary model failed: {e}, falling back to {FALLBACK_MODEL}")
            self.model_name = FALLBACK_MODEL
            self.tokenizer = AutoTokenizer.from_pretrained(FALLBACK_MODEL)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                FALLBACK_MODEL
            ).to(self.device)
        self.model.eval()
        # id2label 정규화
        self.id2label = {
            idx: LABEL_ALIASES.get(lbl, lbl.lower())
            for idx, lbl in self.model.config.id2label.items()
        }
        logger.info(f"id2label: {self.id2label}")

    def analyze(self, text: str) -> dict:
        """단건 추론."""
        return self.analyze_batch([text], batch_size=1)[0]

    def analyze_batch(
        self,
        texts: list[str],
        batch_size: Optional[int] = None,
    ) -> list[dict]:
        """
        배치 추론.

        Returns:
            [{"label": "positive|neutral|negative", "confidence": float}, ...]
        """
        if not texts:
            return []
        batch_size = batch_size or self.default_batch_size
        results: list[dict] = []
        start = time.time()

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                logits = self.model(**enc).logits
            probs = torch.softmax(logits, dim=-1)
            confidences, indices = probs.max(dim=-1)
            for conf, idx in zip(confidences.tolist(), indices.tolist()):
                label = self.id2label.get(idx, "neutral")
                # 표준 라벨이 아니면 neutral 로 강제
                if label not in CANONICAL_LABELS:
                    label = "neutral"
                results.append({"label": label, "confidence": conf})

        elapsed = time.time() - start
        logger.info(
            f"Analyzed {len(texts)} samples in {elapsed:.2f}s "
            f"({len(texts)/elapsed:.1f} samples/s)"
        )
        return results


def aggregate(results: list[dict], min_sample: int = 5) -> dict:
    """
    음식점별 리뷰 분석 결과 집계.

    Returns:
        {
            "score": float | None,     # (pos - neg) / total ∈ [-1, +1]
            "pos_ratio": float,
            "neg_ratio": float,
            "sample_size": int,
            "reason": str | None,      # "insufficient_samples" 등
        }
    """
    total = len(results)
    if total < min_sample:
        return {
            "score": None,
            "pos_ratio": 0.0,
            "neg_ratio": 0.0,
            "sample_size": total,
            "reason": "insufficient_samples",
        }

    pos = sum(1 for r in results if r["label"] == "positive")
    neg = sum(1 for r in results if r["label"] == "negative")
    return {
        "score": (pos - neg) / total,
        "pos_ratio": pos / total,
        "neg_ratio": neg / total,
        "sample_size": total,
        "reason": None,
    }


@lru_cache(maxsize=1)
def get_default_analyzer() -> SentimentAnalyzer:
    """프로세스당 1회 초기화되는 싱글톤 analyzer."""
    return SentimentAnalyzer()
```

### 6.6 `sentiment/update_db.py` — `run_sentiment_update()`

```python
import argparse
import logging
import time
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import text
from sqlalchemy.engine import Engine

from nlp_mvp.shared.db import get_engine, get_session
from nlp_mvp.sentiment.crawler import (
    ReviewCrawler, SyntheticSource, AIHubSource, KakaoPublicSource
)
from nlp_mvp.sentiment import preprocess
from nlp_mvp.sentiment.sentiment_pipeline import (
    get_default_analyzer, aggregate
)

logger = logging.getLogger("nlp_mvp.sentiment.update_db")

# =========================================
# 스키마 마이그레이션 (§6.2 참고)
# =========================================
REQUIRED_COLUMNS = {
    "sentiment_score": "REAL DEFAULT NULL",
    "sentiment_pos_ratio": "REAL DEFAULT NULL",
    "sentiment_neg_ratio": "REAL DEFAULT NULL",
    "sentiment_sample_size": "INTEGER DEFAULT 0",
    "sentiment_updated_at": "DATETIME DEFAULT NULL",
}

REVIEWS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    text TEXT NOT NULL,
    sentiment_label TEXT,
    sentiment_confidence REAL,
    external_id TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
    UNIQUE (restaurant_id, source, text)
);
"""

def ensure_schema(engine: Engine) -> None:
    """멱등 스키마 마이그레이션."""
    with engine.begin() as conn:
        # 기존 컬럼 조회
        existing = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(restaurants)"))
        }
        # 누락된 컬럼 추가
        for col, col_def in REQUIRED_COLUMNS.items():
            if col not in existing:
                logger.info(f"Adding column: restaurants.{col}")
                conn.execute(text(f"ALTER TABLE restaurants ADD COLUMN {col} {col_def}"))
        # reviews 테이블
        conn.execute(text(REVIEWS_TABLE_SQL))
        # 인덱스
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reviews_restaurant ON reviews(restaurant_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews(source)"))


# =========================================
# 메인 파이프라인
# =========================================
SourceName = Literal["synthetic", "aihub", "kakao_public"]

def _build_crawler(source: SourceName) -> ReviewCrawler:
    mapping = {
        "synthetic": [SyntheticSource()],
        "aihub": [AIHubSource(), SyntheticSource()],  # fallback
        "kakao_public": [KakaoPublicSource(), SyntheticSource()],
    }
    return ReviewCrawler(mapping[source])


def run_sentiment_update(
    limit: int | None = None,
    min_reviews: int = 5,
    dry_run: bool = False,
    source: SourceName = "synthetic",
    refresh_after_days: int = 7,
) -> dict:
    """
    감성분석 전체 파이프라인 실행.

    Returns:
        {
            "processed": int,
            "updated": int,
            "skipped": int,
            "errors": int,
            "duration_sec": float,
        }
    """
    start = time.time()
    stats = {"processed": 0, "updated": 0, "skipped": 0, "errors": 0}

    engine = get_engine()
    ensure_schema(engine)

    crawler = _build_crawler(source)
    analyzer = get_default_analyzer()

    # 대상 식당 조회
    cutoff = (datetime.utcnow() - timedelta(days=refresh_after_days)).isoformat()
    query = text("""
        SELECT id FROM restaurants
        WHERE sentiment_updated_at IS NULL
           OR sentiment_updated_at < :cutoff
        ORDER BY id
        LIMIT :limit
    """)
    with get_session() as session:
        rows = session.execute(
            query, {"cutoff": cutoff, "limit": limit or 10**9}
        ).fetchall()
        restaurant_ids = [row[0] for row in rows]

    logger.info(f"Target restaurants: {len(restaurant_ids)}")

    for rest_id in restaurant_ids:
        stats["processed"] += 1
        try:
            # ① 수집
            raw_reviews = crawler.fetch_reviews(rest_id, max_count=100)

            # ② 전처리
            cleaned = [
                {**r, "text": preprocess.clean_text(r["text"])}
                for r in raw_reviews
            ]
            valid = [r for r in cleaned if preprocess.is_valid_review(r["text"])]
            unique = preprocess.deduplicate(valid)

            if len(unique) < min_reviews:
                stats["skipped"] += 1
                logger.info(f"restaurant {rest_id}: skipped ({len(unique)} < {min_reviews})")
                continue

            # ③ 감성분석
            analyses = analyzer.analyze_batch([r["text"] for r in unique])

            # ④ 집계
            agg = aggregate(analyses, min_sample=min_reviews)
            if agg["score"] is None:
                stats["skipped"] += 1
                continue

            # ⑤ DB 쓰기
            if not dry_run:
                with get_session() as session:
                    # reviews INSERT
                    for review, result in zip(unique, analyses):
                        session.execute(
                            text("""
                                INSERT OR IGNORE INTO reviews
                                    (restaurant_id, source, text,
                                     sentiment_label, sentiment_confidence,
                                     external_id, fetched_at)
                                VALUES
                                    (:rid, :src, :txt, :lbl, :conf, :eid, :ft)
                            """),
                            {
                                "rid": rest_id,
                                "src": review["source"],
                                "txt": review["text"],
                                "lbl": result["label"],
                                "conf": result["confidence"],
                                "eid": review.get("external_id"),
                                "ft": review.get("fetched_at"),
                            },
                        )
                    # restaurants UPDATE
                    session.execute(
                        text("""
                            UPDATE restaurants
                            SET sentiment_score = :score,
                                sentiment_pos_ratio = :pos,
                                sentiment_neg_ratio = :neg,
                                sentiment_sample_size = :size,
                                sentiment_updated_at = :ts
                            WHERE id = :rid
                        """),
                        {
                            "score": agg["score"],
                            "pos": agg["pos_ratio"],
                            "neg": agg["neg_ratio"],
                            "size": agg["sample_size"],
                            "ts": datetime.utcnow().isoformat(),
                            "rid": rest_id,
                        },
                    )
                    session.commit()

            stats["updated"] += 1
            logger.info(
                f"restaurant {rest_id}: score={agg['score']:.3f} "
                f"(pos={agg['pos_ratio']:.2f}, neg={agg['neg_ratio']:.2f}, n={agg['sample_size']})"
            )

        except Exception as e:
            stats["errors"] += 1
            logger.exception(f"restaurant {rest_id} failed: {e}")

    stats["duration_sec"] = time.time() - start
    logger.info(f"Done: {stats}")
    return stats


# =========================================
# CLI 진입점
# =========================================
def main():
    parser = argparse.ArgumentParser(description="Mini A1 Sentiment Update")
    parser.add_argument("--limit", type=int, default=None, help="처리할 식당 최대 수")
    parser.add_argument("--min-reviews", type=int, default=5, help="최소 리뷰 수")
    parser.add_argument("--dry-run", action="store_true", help="DB 쓰기 없이 시뮬레이션")
    parser.add_argument(
        "--source",
        choices=["synthetic", "aihub", "kakao_public"],
        default="synthetic",
        help="리뷰 데이터 소스",
    )
    parser.add_argument("--refresh-after-days", type=int, default=7)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    stats = run_sentiment_update(
        limit=args.limit,
        min_reviews=args.min_reviews,
        dry_run=args.dry_run,
        source=args.source,
        refresh_after_days=args.refresh_after_days,
    )
    print(stats)


if __name__ == "__main__":
    main()
```

**CLI 실행 예:**
```bash
cd Mini/NLP

# Dry run (DB 변경 없이 10 식당)
python -m nlp_mvp.sentiment.update_db --limit 10 --dry-run

# 실제 실행 (합성 데이터)
python -m nlp_mvp.sentiment.update_db --limit 100 --source synthetic

# AI-Hub 데이터셋 사용
python -m nlp_mvp.sentiment.update_db --source aihub
```

### 6.7 테스트 (`sentiment/tests/`)

**test_preprocess.py (5+ 케이스):**
```python
import pytest
from nlp_mvp.sentiment.preprocess import (
    clean_text, is_valid_review, deduplicate
)

class TestCleanText:
    def test_url_removal(self):
        assert clean_text("맛있어요 https://example.com 최고") == "맛있어요 최고"

    def test_emoji_removal(self):
        assert clean_text("정말 맛있어요 😍👍") == "정말 맛있어요"

    def test_whitespace_normalization(self):
        assert clean_text("  좋아요    정말   ") == "좋아요 정말"

    def test_empty_input(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""

class TestIsValidReview:
    def test_too_short(self):
        assert not is_valid_review("굿")
        assert not is_valid_review("1234")

    def test_only_symbols(self):
        assert not is_valid_review("!!!!!!")
        assert not is_valid_review("12345")

    def test_valid(self):
        assert is_valid_review("음식 맛있어요")

class TestDeduplicate:
    def test_removes_exact_duplicates(self):
        reviews = [
            {"text": "맛있어요"},
            {"text": "맛있어요"},
            {"text": "좋아요"},
        ]
        result = deduplicate(reviews)
        assert len(result) == 2

    def test_preserves_order(self):
        reviews = [{"text": "A"}, {"text": "B"}, {"text": "A"}]
        result = deduplicate(reviews)
        assert [r["text"] for r in result] == ["A", "B"]
```

**test_sentiment_pipeline.py (6 케이스):**
```python
import pytest
from nlp_mvp.sentiment.sentiment_pipeline import (
    SentimentAnalyzer, aggregate
)

@pytest.fixture(scope="module")
def analyzer():
    return SentimentAnalyzer()

class TestAnalyzer:
    @pytest.mark.parametrize("text", [
        "정말 맛있고 친절해요. 최고의 식당이에요!",
        "분위기도 좋고 음식도 훌륭합니다.",
        "가격 대비 만족도가 정말 높아요.",
    ])
    def test_clearly_positive(self, analyzer, text):
        result = analyzer.analyze(text)
        assert result["label"] == "positive"
        assert result["confidence"] > 0.5

    @pytest.mark.parametrize("text", [
        "음식이 너무 짜고 서비스도 최악이었어요.",
        "다시는 안 갈 거예요. 정말 실망.",
        "가격만 비싸고 맛은 형편없어요.",
    ])
    def test_clearly_negative(self, analyzer, text):
        result = analyzer.analyze(text)
        assert result["label"] == "negative"
        assert result["confidence"] > 0.5

class TestAggregate:
    def test_all_positive(self):
        results = [{"label": "positive", "confidence": 0.9}] * 10
        agg = aggregate(results)
        assert agg["score"] == 1.0

    def test_all_negative(self):
        results = [{"label": "negative", "confidence": 0.9}] * 10
        agg = aggregate(results)
        assert agg["score"] == -1.0

    def test_insufficient_samples(self):
        results = [{"label": "positive", "confidence": 0.9}] * 3
        agg = aggregate(results, min_sample=5)
        assert agg["score"] is None
        assert agg["reason"] == "insufficient_samples"

    def test_mixed(self):
        results = (
            [{"label": "positive", "confidence": 0.9}] * 6
            + [{"label": "negative", "confidence": 0.9}] * 4
        )
        agg = aggregate(results)
        assert agg["score"] == pytest.approx(0.2)  # (6-4)/10
```

**test_crawler.py (2 케이스):**
```python
from nlp_mvp.sentiment.crawler import (
    SyntheticSource, ReviewCrawler
)

def test_synthetic_source_returns_reviews():
    src = SyntheticSource()
    reviews = src.fetch(restaurant_id=1, max_count=50)
    assert len(reviews) >= 10  # 최소 10건은 나와야
    for r in reviews:
        assert r["source"] == "synthetic"
        assert isinstance(r["text"], str)
        assert len(r["text"]) > 0

def test_crawler_fallback():
    class FailingSource:
        name = "failing"
        def fetch(self, *a, **kw):
            raise RuntimeError("simulated failure")

    crawler = ReviewCrawler([FailingSource(), SyntheticSource()])
    reviews = crawler.fetch_reviews(restaurant_id=1)
    assert len(reviews) > 0
    assert reviews[0]["source"] == "synthetic"
```

**test_update_db.py (2 케이스):**
```python
import pytest
from sqlalchemy import create_engine, text
from nlp_mvp.sentiment.update_db import ensure_schema, run_sentiment_update

@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE restaurants (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """))
        conn.execute(text("INSERT INTO restaurants (id, name) VALUES (1, 'Test')"))
    return engine

def test_ensure_schema_idempotent(test_engine):
    ensure_schema(test_engine)
    ensure_schema(test_engine)  # 두 번 호출해도 에러 없어야
    with test_engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(restaurants)"))}
        assert "sentiment_score" in cols
        assert "sentiment_updated_at" in cols

def test_dry_run_no_writes(monkeypatch, test_engine):
    # 실제 DB 경로 대신 in-memory engine 사용하도록 monkeypatch
    import nlp_mvp.shared.db as db_module
    monkeypatch.setattr(db_module, "_engine", test_engine)
    stats = run_sentiment_update(limit=1, dry_run=True)
    assert stats["processed"] >= 0  # 에러 없이 완료
```

**실행:**
```bash
cd Mini/NLP
pytest nlp_mvp/sentiment/tests/ -v --tb=short
```

### 6.8 검증 노트북 (`notebooks/01_sentiment_eda.ipynb`)

**셀 구성 (7개):**

**셀 1 — 마크다운:**
```markdown
# A1 감성분석 결과 EDA

## 목적
1. 감성분석 파이프라인이 실제 DB 에 정상 반영되었는지 확인
2. 레이블 분포 및 confidence 분포 시각화
3. 저신뢰도 리뷰 수동 검토를 통한 모델 품질 추정
```

**셀 2 — 임포트 및 DB 연결:**
```python
import pandas as pd
import matplotlib.pyplot as plt
from nlp_mvp.shared.db import get_engine

engine = get_engine()
```

**셀 3 — 식당 샘플:**
```python
df_r = pd.read_sql(
    "SELECT id, name, sentiment_score, sentiment_sample_size "
    "FROM restaurants WHERE sentiment_score IS NOT NULL LIMIT 100",
    engine,
)
df_r.head()
df_r["sentiment_score"].describe()
```

**셀 4 — 레이블 분포 pie:**
```python
df_rev = pd.read_sql(
    "SELECT sentiment_label, COUNT(*) as cnt FROM reviews GROUP BY sentiment_label",
    engine,
)
plt.pie(df_rev["cnt"], labels=df_rev["sentiment_label"], autopct="%1.1f%%")
plt.title("리뷰 감성 분포")
plt.show()
```

**셀 5 — confidence 히스토그램:**
```python
df_conf = pd.read_sql("SELECT sentiment_confidence FROM reviews", engine)
plt.hist(df_conf["sentiment_confidence"], bins=20)
plt.xlabel("Confidence")
plt.ylabel("Count")
plt.title("감성분석 신뢰도 분포")
plt.show()
```

**셀 6 — 저신뢰도 수동 검토:**
```python
low_conf = pd.read_sql(
    "SELECT text, sentiment_label, sentiment_confidence "
    "FROM reviews WHERE sentiment_confidence < 0.6 LIMIT 20",
    engine,
)
low_conf
```

**셀 7 — 결론 마크다운:**
```markdown
## 결론
- 전체 N 건 리뷰 중 긍정 X%, 중립 Y%, 부정 Z%
- 평균 confidence: W
- 저신뢰도 20건 수동 검토 결과: 정답률 V/20
- **다음 단계:** Step 2 (B1 메뉴 정규화) 로 진행
```

---

## 7. 구현 순서 (5일 체크리스트)

### Day 1 — 스키마 + 전처리 + 테스트

- [ ] `shared/db.py` 구현 (Step 0 미완료 시)
- [ ] `shared/logger.py` 구현 (Step 0 미완료 시)
- [ ] `sentiment/update_db.py` 에 `ensure_schema()` 작성
- [ ] `sentiment/preprocess.py` 3함수 작성
- [ ] `test_preprocess.py` 5+ 케이스 작성 및 통과
- [ ] `test_update_db.py` 의 `ensure_schema` 테스트 통과

**검증:** `pytest nlp_mvp/sentiment/tests/test_preprocess.py -v` 통과

### Day 2 — 데이터 소스

- [ ] `crawler.py` 상단에 법적 고지 주석 추가
- [ ] `ReviewSource` 추상 클래스 정의
- [ ] `SyntheticSource` 구현 (§14.A 의 50건 시드 포함)
- [ ] `AIHubSource` 스켈레톤 구현 (CSV 로딩)
- [ ] `KakaoPublicSource` 스켈레톤 (Day 5+ 에 필요 시 채움)
- [ ] `ReviewCrawler` 통합 (fallback 로직)
- [ ] `test_crawler.py` 2 케이스 통과

**검증:** `python -c "from nlp_mvp.sentiment.crawler import SyntheticSource; print(SyntheticSource().fetch(1, 10))"`

### Day 3 — 감성분석 모델

- [ ] `sentiment_pipeline.py` 의 `SentimentAnalyzer.__init__` 구현
- [ ] 모델 로딩 + fallback 로직
- [ ] `id2label` 정규화 (LABEL_ALIASES)
- [ ] `analyze()` 단건 추론
- [ ] `analyze_batch()` 배치 추론 (`torch.no_grad`, 디바이스 자동)
- [ ] `aggregate()` 집계 함수
- [ ] `get_default_analyzer()` 싱글톤
- [ ] `test_sentiment_pipeline.py` 6 케이스 통과

**검증:** 스모크 테스트 정확도 ≥ 11/12 (긍·부정 각 3건 + 집계 3건)

### Day 4 — 통합 파이프라인 + CLI

- [ ] `update_db.py` 의 `_build_crawler()` 헬퍼
- [ ] `run_sentiment_update()` 메인 로직 (수집 → 전처리 → 분석 → 집계 → DB)
- [ ] 식당 단위 트랜잭션 커밋
- [ ] 에러 격리 (`try/except` 식당 단위)
- [ ] CLI 진입점 (`argparse`)
- [ ] `--dry-run` 모드 검증
- [ ] 10 식당 end-to-end 실행 (synthetic)

**검증:**
```bash
python -m nlp_mvp.sentiment.update_db --limit 10 --dry-run
# stats = {"processed": 10, "updated": 10, "skipped": 0, "errors": 0}
```

### Day 5 — 검증 및 평가

- [ ] 100 식당 배치 실행 (실제 DB 쓰기)
- [ ] 처리량 측정 (`duration_sec` 로그 확인)
- [ ] `notebooks/01_sentiment_eda.ipynb` 작성 및 실행
- [ ] 저신뢰도 20건 수동 검토
- [ ] KPI 달성 여부 체크 (§8 표)
- [ ] `nlp_mvp/README.md` 의 진행 체크박스 갱신

**검증:** §8 의 모든 KPI 충족 확인

---

## 8. KPI 및 검증 기준

| # | 지표 | 측정 방법 | 목표 | 필수 여부 |
|---|------|---------|-----|---------|
| 1 | 전처리 테스트 통과율 | `pytest test_preprocess.py` | 100% | ✅ 필수 |
| 2 | 감성분류 스모크 정확도 | 긍·부 12건 정답 수 | ≥ 11/12 | ✅ 필수 |
| 3 | 배치 처리량 (CPU) | 100 리뷰 / 소요 시간 | ≥ 1,000건/hr | ✅ 필수 |
| 4 | 배치 처리량 (GPU) | 동일 | ≥ 10,000건/hr | ⚪ 선택 |
| 5 | DB 멱등성 | `ensure_schema()` 2회 실행 | 에러 0 | ✅ 필수 |
| 6 | 100 식당 end-to-end | `run_sentiment_update(limit=100)` | errors=0, updated ≥ 95 | ✅ 필수 |
| 7 | 테스트 커버리지 | `pytest --cov=nlp_mvp/sentiment` | ≥ 70% | ⭐ 권장 |
| 8 | 검증 노트북 실행 | 7개 셀 모두 에러 없음 | 100% | ✅ 필수 |

**KPI 자동 측정 스크립트 (선택):**
```bash
# Day 5 에 실행
pytest nlp_mvp/sentiment/ --cov=nlp_mvp/sentiment --cov-report=term
python -m nlp_mvp.sentiment.update_db --limit 100 | tee day5_benchmark.log
```

---

## 9. 트러블슈팅 (Step 1 한정)

### 9.1 모델 다운로드 실패

**증상:** `OSError: Can't load tokenizer for 'nlp04/...'`

**원인 및 해결:**
- ❓ 네트워크 / 방화벽 → 프록시 환경변수 설정 (`HTTPS_PROXY`)
- ❓ Hugging Face 접근 제한 → `HF_TOKEN` 환경변수 추가
- ❓ 모델 삭제됨 → `FALLBACK_MODEL` (KcELECTRA-base-v2022) 로 자동 전환 확인

### 9.2 OOM (Out of Memory) on CPU

**증상:** `RuntimeError: [enforce fail] ... memory allocation failed`

**해결:**
- `SentimentAnalyzer` 생성 시 `device="cpu"` 명시
- `analyze_batch(batch_size=4)` 로 축소
- `max_length=128` 로 감소 (토크나이저)

### 9.3 이모지 제거 미동작

**증상:** `AttributeError: module 'emoji' has no attribute 'replace_emoji'`

**원인:** `emoji` 1.x 버전 사용 중

**해결:**
```bash
pip install "emoji>=2.0.0"
```

### 9.4 SQLite ALTER 에러

**증상:** `sqlite3.OperationalError: duplicate column name`

**원인:** `ensure_schema()` 가 PRAGMA 체크 전에 ALTER 실행

**해결:** §6.2 의 `existing` set 로 컬럼 존재 여부 확인 로직 확인

### 9.5 zero-shot 라벨 편향 (전부 positive)

**증상:** 모든 리뷰가 `positive` 로 분류됨

**원인:** 모델의 `id2label` 이 표준과 다름 (예: `{0: "LABEL_0", 1: "LABEL_1"}`)

**해결:**
1. `SentimentAnalyzer._load_model()` 의 `logger.info(f"id2label: {self.id2label}")` 출력 확인
2. `LABEL_ALIASES` 딕셔너리에 필요한 매핑 추가
3. 가능하다면 `transformers pipeline` 대신 `AutoModelForSequenceClassification` 직접 사용하여
   `config.id2label` 을 명시적으로 재매핑

### 9.6 AI-Hub 데이터셋 다운로드

**증상:** `FileNotFoundError: nlp_mvp/data/raw/aihub_food_reviews.csv`

**해결 절차:**
1. [AI-Hub](https://aihub.or.kr) 회원가입 및 로그인
2. "한국어 음식 리뷰" 또는 유사 데이터셋 검색
3. 다운로드 → 압축 해제
4. CSV 파일을 `nlp_mvp/data/raw/aihub_food_reviews.csv` 로 복사
5. 컬럼명 확인 (`restaurant_name`, `review_text`, ...) 후 필요 시 리네이밍

### 9.7 실행 디렉토리 혼동

**증상:** `ModuleNotFoundError: No module named 'nlp_mvp'`

**원인:** `Mini/` 에서 실행 (상위 가이드 §2.5 참고)

**해결:** 반드시 `Mini/NLP/` 에서 실행
```bash
cd Mini/NLP
python -m nlp_mvp.sentiment.update_db --dry-run
```

---

## 10. 재사용 가능한 기존 파일

### 10.1 본 Step 에서 채울 스켈레톤 (이미 존재)

| 파일 | 용도 | 상태 |
|------|------|------|
| `nlp_mvp/shared/db.py` | DB 세션 (Step 0) | 빈 파일 → §6.1 참고 |
| `nlp_mvp/shared/logger.py` | 공용 로거 (Step 0) | 빈 파일 |
| `nlp_mvp/sentiment/crawler.py` | 데이터 소스 어댑터 | 빈 파일 → §6.3 |
| `nlp_mvp/sentiment/preprocess.py` | 전처리 순수 함수 | 빈 파일 → §6.4 |
| `nlp_mvp/sentiment/sentiment_pipeline.py` | 모델 추론 | 빈 파일 → §6.5 |
| `nlp_mvp/sentiment/update_db.py` | 스키마 + 파이프라인 + CLI | 빈 파일 → §6.2, §6.6 |
| `nlp_mvp/sentiment/tests/test_preprocess.py` | 단위 테스트 | 빈 파일 → §6.7 |
| `nlp_mvp/sentiment/tests/test_crawler.py` | 단위 테스트 | 빈 파일 → §6.7 |
| `nlp_mvp/sentiment/tests/test_sentiment_pipeline.py` | 단위 테스트 | 빈 파일 → §6.7 |
| `nlp_mvp/notebooks/01_sentiment_eda.ipynb` | 검증 노트북 | 스켈레톤 JSON → §6.8 |

### 10.2 참조 전용 (읽기 only)

| 파일 | 참조 목적 |
|------|---------|
| `Mini/NLP/GUIDE_NLP_MVP_SCENARIO3.md` §5 | 원본 요약 명세 (본 문서의 상위 가이드) |
| `Mini/NLP/README.md` §7 | DB 스키마 통합 지점 표 |
| `Mini/api/maps/api.pdf` | 카카오 API 키 (`KakaoPublicSource` 사용 시) |
| `Mini/0README.md` §핵심 알고리즘 | 스코어링 공식 (감성 보정 연결점) |
| `Mini/GUIDE/GUIDE_SUBTOPIC_1_RESTAURANT_COLLECTOR.md` | `restaurants` 테이블 기존 스키마 |

### 10.3 테스트 데이터 (이미 존재)

| 파일 | 용도 |
|------|------|
| `nlp_mvp/menu_normalizer/synonym_dict.json` | (Step 2 전용, Step 1 에서는 미사용) |
| `nlp_mvp/data/menu_test_set.csv` | (Step 2 전용) |

---

## 11. 외부 의존성 확인

**`nlp_mvp/requirements.txt` 에 이미 포함된 패키지 (재확인):**

| 패키지 | 버전 | 본 Step 사용처 |
|--------|-----|-------------|
| `transformers` | 4.44.0 | 모델 로딩 (`AutoTokenizer`, `AutoModelForSequenceClassification`) |
| `torch` | — | 추론 (`torch.no_grad`, 디바이스 관리) |
| `sqlalchemy` | 2.0.32 | DB 세션·쿼리 |
| `requests` | 2.32.3 | 크롤러 HTTP (선택) |
| `beautifulsoup4` | 4.12.3 | HTML 파싱 (선택) |
| `pandas` | 2.2.2 | AI-Hub CSV 로딩, EDA 노트북 |
| `python-dotenv` | 1.0.1 | `.env` 로드 |
| `pytest` | ≥ 7.4 | 단위 테스트 |

**추가 필요 (requirements.txt 에 이미 있음, 재확인):**
- `emoji>=2.0.0` — 본 문서에서는 명시되지 않았지만 §6.4 에서 사용
- 없다면 추가:
  ```bash
  pip install "emoji>=2.0.0"
  ```
  그리고 `requirements.txt` 에 `emoji>=2.0.0` 추가

**Ollama 는 Step 1 에서 불필요** (Step 3 D3 챗봇부터 사용)

---

## 12. 보안 및 법적 주의사항

### 12.1 API 키 보호

- `.env` 파일의 `KAKAO_REST_API_KEY` 는 **절대 로그에 출력 금지**
  ```python
  # ❌ BAD
  logger.info(f"Using key: {api_key}")

  # ✅ GOOD
  logger.info(f"Using key: {api_key[:4]}****{api_key[-2:]}")
  ```
- `.env` 는 `.gitignore` 에 포함되어 있음 (NLP/.gitignore 확인)

### 12.2 저작권 및 ToS

- **수집한 리뷰 원문은 상용 재배포 금지**
- `reviews` 테이블 백업 파일은 `.gitignore` 로 제외
- 본 크롤러는 "연구·학습 목적의 공개 데이터 수집" 으로만 사용
- 운영 배포 시 **반드시 공식 파트너 API 로 교체**

### 12.3 AI-Hub 데이터 사용

- 다운로드 시 라이선스 동의서 확인
- 사용 목적 명시: "학술 연구 · 교육 목적의 NLP 모델 평가"
- 원본 데이터 재배포 금지

### 12.4 개인정보 보호

- 리뷰 작성자 ID / 닉네임 / 프로필 사진 수집 금지
- `reviews.text` 에 개인 식별 정보 포함 시 마스킹 고려 (MVP 범위 외)

---

## 13. 다음 Step 과의 연결점

### 13.1 Step 2 (B1 메뉴 정규화) 와의 연결

본 Step 에서 생성된 `reviews.text` 는 Step 2 의 **메뉴명 추출 후보** 로 활용됩니다.

```
Step 1: reviews 테이블 (원문 + 감성)
            │
            ▼ (Step 2 에서 읽어감)
Step 2: 메뉴명 추출 → 정규화 → normalized_menu_id
```

### 13.2 Step 5 (통합) 와의 연결

`sentiment_score` 는 `nlp_mvp/integration/scoring_patch.py` 가 읽어서 Mini 의
통합 스코어링 엔진에 보정값으로 반영합니다.

```python
# integration/scoring_patch.py (Step 5 에서 구현 예정)
def compute_composite_score_v2(restaurant, ...):
    base = compute_composite_score_v1(restaurant, ...)
    sentiment = restaurant.get("sentiment_score")
    if sentiment is not None:
        return base * (1 + 0.15 * sentiment)  # ±15% 보정
    return base
```

### 13.3 Phase 6 (시나리오 2) 와의 연결

시나리오 2 의 **A2 ABSA 파인튜닝 데이터셋** 시드로 본 Step 의 `reviews` 테이블이 사용됩니다.

- `A1 confidence < 0.6` 인 애매한 리뷰 → Active Learning 우선 라벨링 대상
- `A2` 학습 후 `A1` 의 점수를 교체하여 MVP 대비 성능 향상 측정

---

## 14. 부록

### 14.A 합성 리뷰 50건 샘플 (`SyntheticSource.SEED_REVIEWS`)

**긍정 20건:**
```python
POSITIVE_REVIEWS = [
    "음식이 정말 맛있고 사장님도 친절해요. 다음에도 올게요!",
    "가격 대비 양도 많고 정말 만족스럽네요.",
    "재료가 신선해서 좋았습니다. 분위기도 좋아요.",
    "분위기가 좋고 음식도 훌륭해요. 데이트 장소로 추천!",
    "최고의 맛집! 주변 사람들에게 추천하고 싶어요.",
    "서비스가 빠르고 친절해요. 음식 맛도 일품입니다.",
    "가성비 최고네요. 재방문 의사 100%.",
    "청결하고 맛있어요. 가족들과 함께 가기 좋아요.",
    "사장님이 정말 친절하시고 음식도 맛있어요.",
    "정성이 느껴지는 한 끼였습니다. 감동!",
    "매운맛이 일품이에요. 속이 뻥 뚫립니다.",
    "국물이 깊고 진해서 정말 좋아요.",
    "반찬까지 하나하나 맛있어요. 대단합니다.",
    "밥이 찰지고 반찬도 깔끔해요.",
    "고기 질이 정말 좋네요. 부드럽고 맛있어요.",
    "디저트까지 완벽한 식사였어요.",
    "매장이 깨끗하고 직원분들이 친절해요.",
    "회식 장소로 딱 좋아요. 다들 만족했어요.",
    "혼밥하기 편한 분위기에요. 음식도 맛있고.",
    "정말 오랜만에 맛있는 한 끼를 먹었네요. 감사합니다.",
]
```

**중립 10건:**
```python
NEUTRAL_REVIEWS = [
    "평범한 맛이에요. 특별하진 않지만 무난합니다.",
    "가격은 적당하고 맛도 그럭저럭이네요.",
    "위치는 좋은데 음식은 보통이에요.",
    "대기 시간이 조금 있었지만 그런대로 먹을 만했어요.",
    "혼자 먹기엔 괜찮은 정도의 맛이에요.",
    "평균적인 한식당입니다.",
    "점심 메뉴로 먹기에 무난해요.",
    "크게 맛있지도 나쁘지도 않아요.",
    "한 번 가볼 만한 곳이에요.",
    "기본은 하는 집이네요.",
]
```

**부정 20건:**
```python
NEGATIVE_REVIEWS = [
    "음식이 너무 짜고 서비스도 최악이었어요.",
    "다시는 안 갈 거예요. 정말 실망.",
    "가격만 비싸고 맛은 형편없어요.",
    "위생 상태가 의심스러워요. 비추천.",
    "주문한지 40분 지나도 음식이 안 나와요.",
    "재료가 신선하지 않아요. 비린 맛이 나요.",
    "사장님이 불친절해서 기분 상했어요.",
    "양이 너무 적어서 배고파서 나왔어요.",
    "음식이 식어서 나왔어요. 맛도 별로.",
    "화장실이 너무 더러웠어요. 기본이 안 됐네요.",
    "소음이 너무 심해서 대화가 안 돼요.",
    "가격 대비 품질이 떨어져요.",
    "매장이 좁고 답답해요. 재방문 안 할래요.",
    "직원들이 바빠서 부를 수가 없었어요.",
    "맛이 너무 자극적이에요. 조미료 맛만 나요.",
    "예약을 했는데도 한참 기다렸어요.",
    "사진과 실제가 너무 달라요. 실망.",
    "반찬이 모자라서 추가 요청했는데 안 줘요.",
    "음식이 덜 익어서 나왔어요. 위험해요.",
    "주차가 너무 어려워요. 편의성이 떨어집니다.",
]
```

**통합:**
```python
SEED_REVIEWS = POSITIVE_REVIEWS + NEUTRAL_REVIEWS + NEGATIVE_REVIEWS  # 50건
```

### 14.B AI-Hub 데이터셋 다운로드 가이드

1. **URL:** https://aihub.or.kr
2. 회원가입 (한국인 SSO 또는 이메일)
3. 로그인 후 "데이터" → 검색창에 "음식 리뷰" 또는 "식당 리뷰"
4. 관련 데이터셋 선택 (예: "한국어 속성별 감성 리뷰 데이터셋")
5. "다운로드 신청" → 사용 목적 작성 (학술 연구)
6. 승인 후 다운로드 (수 시간~1일 소요)
7. 압축 해제 → CSV 파일 확인
8. 경로 지정:
   ```bash
   mkdir -p Mini/NLP/nlp_mvp/data/raw
   cp ~/Downloads/aihub_food_reviews.csv Mini/NLP/nlp_mvp/data/raw/
   ```
9. `AIHubSource` 의 컬럼명이 CSV 와 다르면 `_load()` 메서드에서 리네이밍

### 14.C 감성분석 모델별 라이선스

| 모델 | 라이선스 | 상업 사용 |
|------|---------|---------|
| `nlp04/korean_sentiment_analysis_kcelectra` | Apache 2.0 (확인 필요) | ⚠️ 확인 권장 |
| `beomi/KcELECTRA-base-v2022` | Apache 2.0 | ✅ |
| `snunlp/KR-FinBert-SC` | MIT | ✅ |
| `cardiffnlp/twitter-xlm-roberta-base-sentiment` | MIT | ✅ |

⚠️ 배포 전 반드시 각 모델의 Hugging Face 카드에서 라이선스 확인

### 14.D SQLite PRAGMA 치트시트

```sql
-- 테이블 컬럼 조회
PRAGMA table_info(restaurants);

-- 인덱스 조회
PRAGMA index_list(reviews);

-- 외래키 제약 활성화
PRAGMA foreign_keys = ON;

-- WAL 모드 (동시성 향상)
PRAGMA journal_mode = WAL;

-- DB 무결성 체크
PRAGMA integrity_check;
```

### 14.E 참고 자료

1. **Hugging Face Transformers 튜토리얼:**
   https://huggingface.co/docs/transformers/tasks/sequence_classification
2. **KcELECTRA 원 논문:**
   Lee (2021) "KcELECTRA: Korean Comments ELECTRA"
3. **의사결정 피로 연구:**
   Pignatiello et al. (2020) — (Mini 0README 인용)
4. **한국어 감성분석 벤치마크 (NSMC):**
   https://github.com/e9t/nsmc
5. **SQLAlchemy 2.0 마이그레이션 가이드:**
   https://docs.sqlalchemy.org/en/20/changelog/migration_20.html

---

## 15. 1페이지 체크리스트 요약

> **이 섹션은 복사해서 종이에 출력하거나 Notion 에 붙여넣어 사용할 수 있습니다.**

### ✅ Step 1 (A1 감성분석) 1주차 체크리스트

**Day 1 — 스키마 + 전처리**
- [ ] `shared/db.py` · `shared/logger.py` 구현 (Step 0)
- [ ] `ensure_schema()` 작성 + 멱등 테스트
- [ ] `preprocess.py` 3함수 작성
- [ ] `test_preprocess.py` 5+ 케이스 통과

**Day 2 — 데이터 소스**
- [ ] `crawler.py` 법적 고지 주석
- [ ] `SyntheticSource` (50건 시드)
- [ ] `AIHubSource` (스켈레톤)
- [ ] `KakaoPublicSource` (스켈레톤만)
- [ ] `ReviewCrawler` 통합
- [ ] `test_crawler.py` 통과

**Day 3 — 감성분석 모델**
- [ ] `SentimentAnalyzer` 구현 (device auto)
- [ ] `id2label` 정규화
- [ ] `analyze_batch()` + `torch.no_grad`
- [ ] `aggregate()` 함수
- [ ] `test_sentiment_pipeline.py` 6 케이스 통과

**Day 4 — 통합 파이프라인**
- [ ] `run_sentiment_update()` 메인 로직
- [ ] 에러 격리 (식당 단위)
- [ ] CLI + argparse
- [ ] `--dry-run` 10 식당 검증

**Day 5 — 배치 + 노트북**
- [ ] 100 식당 실제 실행
- [ ] `01_sentiment_eda.ipynb` 작성
- [ ] KPI 8개 달성 여부 확인
- [ ] 저신뢰도 20건 수동 검토

### 🎯 KPI 달성 기준
- [ ] 전처리 테스트 100%
- [ ] 스모크 정확도 ≥ 11/12
- [ ] CPU 처리량 ≥ 1,000건/hr
- [ ] DB 멱등성 ✓
- [ ] 100 식당 end-to-end (errors=0)
- [ ] 테스트 커버리지 ≥ 70%
- [ ] 검증 노트북 7셀 실행 성공

### 📦 산출물
- [ ] `sentiment/` 5개 파이썬 파일
- [ ] `tests/` 4개 테스트 파일
- [ ] `notebooks/01_sentiment_eda.ipynb`
- [ ] `reviews` 테이블 + 감성 컬럼 DB 반영
- [ ] 배치 실행 로그 (`day5_benchmark.log`)

### 📎 다음 단계
- [ ] Step 2 (B1 메뉴 정규화) 로 진행
- [ ] `nlp_mvp/README.md` 진행률 업데이트
- [ ] `GUIDE_NLP_MVP_SCENARIO3.md` §12.1 체크박스 동기화

---

**문서 버전:** v1.0
**작성일:** 2026-04-07
**대상:** Mini NLP MVP 1주차 구현자
**상위 문서:** [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md) §5
**관련 문서:**
- [`README.md`](./README.md) — NLP 레이어 진입점
- [`GUIDE_NLP_RESEARCH_SCENARIO2.md`](./GUIDE_NLP_RESEARCH_SCENARIO2.md) — 연구형 심화 (A2 ABSA)

---

<div align="center">

**🔹 Step 1 — 리뷰 텍스트를 데이터로 변환하는 첫 걸음.**

*Mini NLP MVP — One Week, One Module.*

</div>
