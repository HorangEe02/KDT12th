# Phase 16 (Research 모델) + Phase 17 (Embedding CF) — 사전 상세 계획

> **작성일**: 2026-05-02
> **컨텍스트**: Phase 15 (감성 분석 + Insights UI) 완료 후 차기 단계.
> nlp_research 모듈은 골격(코드 4,281 LOC)은 존재하지만 학습 가중치 부재 → dummy fallback 동작 중.

---

## 1. 현재 상태

### 1-1. 모듈 골격 보유 현황
| 위치 | LOC | 상태 |
|---|---:|---|
| `NLP/nlp_research/models/absa/` | ~628 | 학습/추론 코드 ✅, 가중치 ❌ |
| `NLP/nlp_research/models/food_ner/` | ? | 학습 코드 ✅, rule fallback ✅ |
| `NLP/nlp_research/models/embedding_cf/` | ~549 | 추천 코드 ✅, 학습 데이터 ❌ |
| `NLP/nlp_research/checkpoints/` | — | 비어 있음 |
| `NLP/nlp_research/data/` | — | 라벨링 데이터 부재 |

### 1-2. v2 라우터 엔드포인트 동작
| 엔드포인트 | 라이브 응답 | 상태 |
|---|:-:|---|
| `GET /nlp/v2/sentiment/{rid}` (ABSA) | 200 | dummy ABSA |
| `POST /nlp/v2/menu/extract` (Food NER) | 200 | rule fallback |
| `GET /nlp/v2/recommend` (CF) | 422 | 파라미터 검증 실패 |

---

## 2. 두 가지 진행 옵션

### 옵션 A — **시연용 활성화** (권장, 2–3시간)
실 학습 데이터/가중치 없이도 시연 가능 상태로:
- **ABSA**: 측면별(맛·서비스·가격·위생) 합성 점수 시드 (sentiment_score 기반 분해)
- **Food NER**: rule-based fallback의 음식 사전 확장 + 인식률 향상
- **Embedding CF**: 사용자 meal_history 기반 cosine similarity 추천 (이미 코드 보유)
- **/v2/recommend 422 fix**: 파라미터 문제 진단 + 수정

→ 시연 가능 + 학습 가치(아키텍처 학습)는 보존 + 시간 합리적

### 옵션 B — **본격 모델 학습** (8–20시간)
- KorASBA, NSMC, KLUE-NER 등 공개 데이터셋 수집
- KoELECTRA fine-tune (Mac M-series GPU mps 또는 CPU 24h+)
- 가중치를 ckpt로 저장 + 컨테이너 배포
- 평가 지표 추적

→ 학습 가치 최대, 그러나 시간/하드웨어 큼. Mac 호스트에서 KoELECTRA 파인튜닝 가능하지만 MPS backend 신중 (transformers 호환성).

---

## 3. ⭐ 권장 진행안: 옵션 A 세부 단계

### Phase 16-A: ABSA 활성화 (1h)

#### 16-A1. 측면별 시드 데이터 생성
`scripts/seed_absa.py`:
- 100개 식당의 4개 측면(맛/서비스/가격/위생) 합성 점수
- 기준: `sentiment_score` ± Gaussian (각 측면 sigma 0.15)
- 새 테이블 `restaurant_absa` (또는 restaurants 컬럼 추가)

```sql
CREATE TABLE restaurant_absa (
  id INTEGER PRIMARY KEY,
  restaurant_id TEXT NOT NULL,
  aspect VARCHAR(20),   -- taste/service/price/hygiene
  score FLOAT,
  pos_ratio FLOAT,
  sample_size INTEGER,
  updated_at DATETIME
);
```

#### 16-A2. v2 라우터 갱신
`NLP/nlp_mvp/api/routers/v2.py` 의 `/v2/sentiment/{rid}` 가 dummy 대신 `restaurant_absa` 테이블 SELECT.

#### 16-A3. 프런트 ABSA 패널 (옵션, 추가 30m)
`/insights` 페이지에 ABSA radar chart 컴포넌트.

### Phase 16-B: Food NER 강화 (45m)

#### 16-B1. Food 사전 확장
- `NLP/nlp_research/models/food_ner/` 의 rule-based dictionary 확장
- 표준 메뉴 104종 + 식재료 50종 + 조리법 30종

#### 16-B2. /v2/menu/extract 응답 풍부화
- 음식명만이 아닌 (음식, 식재료, 조리법, 향미) 4-class 분류
- entity_type 필드 추가

### Phase 17: Embedding CF (1h)

#### 17-1. /v2/recommend 422 fix
파라미터 문제 진단 (잘못된 user_id 형식 또는 필수 누락).

#### 17-2. 합성 사용자 임베딩 시드
- 13명 사용자 × 8759 식당 → numpy 임베딩 매트릭스 (cosine sim)
- meal_history 기반 일부 + 합성 데이터로 보완
- 사용자별 top-N 추천 응답

#### 17-3. 프런트 추천 위젯 (옵션, 30m)
- /insights 또는 / 페이지 하단에 "당신을 위한 추천" 카드

---

## 4. 시간 계획 (옵션 A)

| Phase | 시간 | 산출물 |
|---|:-:|---|
| 16-A ABSA | 1h | seed_absa.py + restaurant_absa 테이블 + v2 라우터 |
| 16-B NER | 45m | food_dictionary.json + 4-class 응답 |
| 17 CF | 1h | recommend 422 fix + 합성 임베딩 시드 |
| 검증 + 배포 | 30m | E2E + Firebase 재배포 |
| **총** | **3h** | |

---

## 5. 옵션 B (본격 학습) 시 필요사항

| 항목 | 내용 |
|---|---|
| 데이터셋 | NSMC (네이버 영화), KorASBA (식당 측면 라벨) |
| 모델 베이스 | monologg/koelectra-base-v3-discriminator |
| 학습 환경 | Mac M-series GPU (MPS) 또는 CPU + transformers |
| 학습 시간 | ABSA 4–8h, NER 6–12h |
| 평가 지표 | accuracy/F1 per aspect, NER F1 per entity |
| 가중치 배포 | Hugging Face Hub or local ckpt 폴더 |

---

## 6. 사용자 결정 필요

- **A안 (시연 즉시 활성)**: 3시간 — 시연 + 학습 가치 보존
- **B안 (실 학습)**: 8–20시간 — 학습 가치 최대
- **A→B 단계적**: A 먼저 + B는 별도 트랙

---

## 7. 즉시 시작 가능

옵션 A 결정 시 이 순서로 진행:
1. seed_absa.py + 테이블 생성
2. v2 sentiment/{rid} 갱신
3. food_ner 사전 확장
4. /v2/recommend 422 fix
5. 프런트 ABSA 패널 (옵션)
6. 빌드 + 재배포 + E2E
