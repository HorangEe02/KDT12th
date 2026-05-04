# Phase 6 — Labeling Guide

> **목적:** Mini A2/B2 모델 학습에 필요한 **1,000+ 건 라벨링 데이터** 를 일관성 있게 수집하기 위한 실무 가이드.

---

## 0. 준비

```bash
pip install label-studio
label-studio start --port 8080
# → http://localhost:8080
```

프로젝트 생성:
- **ABSA 프로젝트**: Import `labeling/absa_label_config.xml` → 리뷰 텍스트 업로드
- **Food NER 프로젝트**: Import `labeling/food_ner_label_config.xml`

데이터 소스 (우선순위):
1. Phase 5 `reviews` 테이블의 `confidence < 0.6` 리뷰 (Active Learning)
2. 카카오맵 크롤링 신규 리뷰
3. AIHub 한국어 리뷰 코퍼스
4. 합성 시드 (이미 `data/seed/` 에 50건씩)

---

## 1. ABSA (A2) — 속성별 감성

### 태깅 규칙

| aspect | 영문 | 포함 내용 | 예시 키워드 |
|---|---|---|---|
| **taste** | 맛 | 음식의 맛, 조리 상태, 신선도 | 맛있다/조미료/신선/질김 |
| **price** | 가격 | 가성비, 가격 인상/할인 | 싸다/비싸다/가성비/합리적 |
| **service** | 서비스 | 직원 응대, 속도, 정확성 | 친절/불친절/빠르다/기다림 |
| **hygiene** | 청결 | 위생, 화장실, 식기 | 깨끗/더럽/청결/위생 |
| **ambience** | 분위기 | 인테리어, 소음, 좌석 | 아늑/시끄럽/인테리어 |

### 감성 결정 기준

| sentiment | 기준 |
|---|---|
| **positive** | 명시적 긍정("맛있어요", "친절") 또는 강한 암시("다시 가고 싶다") |
| **neutral** | 사실 진술, 판단 유보, 양가 감정 내 중립 언급 |
| **negative** | 명시적 불만, 실망, 재방문 거부 |

### 애매한 케이스 처리

1. **미언급 속성은 비워두기** — "김치찌개 맛있어요" → taste만 positive, 나머지 공란
2. **양가 감정 혼재** — "맛은 좋은데 비싸요" → taste=positive, price=negative (두 개 동시)
3. **아이러니/반어** — 명시적 부정어("전혀", "정말로" + 반어) 판단 시 negative
4. **가격 대비 만족** — "가격 대비 맛있다" → taste=positive + price=positive (가성비)
5. **양 적음 ≠ 맛** — "양이 적다"는 **price**(가성비) 로 분류, **taste** 아님

### 목표 분포

| aspect | 최소 샘플 | positive : neutral : negative |
|---|---|---|
| taste | 300 | 4 : 2 : 4 |
| price | 200 | 4 : 2 : 4 |
| service | 200 | 4 : 2 : 4 |
| hygiene | 150 | 5 : 3 : 2 (청결 리뷰가 적음) |
| ambience | 150 | 4 : 3 : 3 |

**Mixed-sentiment 리뷰** (2+ aspect가 다른 감성) 를 의도적으로 20% 이상 포함하세요. A2의 핵심 가치가 거기서 나옵니다.

### 품질 체크

라벨링 완료 후:
```bash
python -m nlp_research.labeling.check_absa data/labeled/absa/v1.jsonl
# → aspect별 분포, mixed ratio, 중복 리뷰 경고
```

---

## 2. Food NER (B2) — BIO 태깅

### 태그 정의

| Tag | 의미 | 예시 | 주의 |
|---|---|---|---|
| **DISH** | 요리명 완성본 | 김치찌개, 돈까스, 비빔밥 | 재료 단독 제외 |
| **INGREDIENT** | 재료 단일 | 돼지고기, 양파, 마늘 | 요리명 일부면 DISH 우선 |
| **FLAVOR** | 맛 표현 | 매운, 달콤한, 짠 | 형용사 어간 포함 |
| **TEXTURE** | 식감 | 바삭한, 쫄깃한, 부드러운 | |
| **COOKING** | 조리법 | 구운, 튀긴, 찐, 삶은 | |
| **ALLERGEN** | **알레르겐** | 땅콩, 새우, 우유, 계란, 밀, 메밀, 콩, 복숭아, 고등어, 조개 | **재료이기도 하면 ALLERGEN 우선** |

### BIO 표기

- `B-DISH`: 엔티티 시작 토큰
- `I-DISH`: 엔티티 연속 토큰
- `O`: 엔티티 아님

**예시:**
```
매운  김치  찌개  에  들어간  돼지고기  가  부드러워요
B-FLAVOR B-DISH I-DISH O O B-INGREDIENT O B-TEXTURE
```

### 중첩/경계 규칙

1. **중첩 금지** — "돼지갈비찜"은 통째로 DISH (INGREDIENT+COOKING으로 쪼개지 않음)
2. **알레르겐 우선** — "계란말이"의 계란 → ALLERGEN(B-ALLERGEN), "말이" → I-DISH? → "**계란말이**" 전체를 DISH로 하되 "계란" 부분은 별도 태깅 X. 예외: "계란을 넣은" → 계란 단독 → ALLERGEN
3. **형용사 어간** — "매콤한" → B-FLAVOR (어미 포함)
4. **복합 조리법** — "볶음밥"은 DISH, "볶은 양파"는 B-COOKING + B-INGREDIENT
5. **브랜드명/상호는 태깅 X** — "스시로"는 O

### 목표 규모 & 분포

- 총 1,000 문장 목표
- DISH, INGREDIENT 각 ≥ 800개 발생
- FLAVOR, TEXTURE, COOKING 각 ≥ 300개
- ALLERGEN ≥ 200개 (안전 critical — recall 우선)

### ALLERGEN 특별 주의

**"ALLERGEN recall ≥ 0.90"** 이 목표입니다. 의심스러우면 태깅하세요. False positive는 허용, false negative는 불가.

알레르기 기본 리스트 (식약처 기준):
> 알류(계란), 우유, 메밀, 땅콩, 대두, 밀, 고등어, 게, 새우, 돼지고기, 복숭아, 토마토, 아황산, 호두, 닭고기, 쇠고기, 오징어, 조개류(굴/전복/홍합 등), 잣

---

## 3. 작업 흐름

```
Day 1-2: 셋업
  ├─ Label Studio 설치
  ├─ 두 프로젝트 생성 + XML import
  └─ 초기 50건으로 가이드 숙지 (seed 재라벨링)

Day 3-7: 본 라벨링 (하루 150건 목표)
  ├─ ABSA 먼저 (간단함)
  └─ NER 병행 (숙련 후)

Day 8: 품질 검증
  ├─ 2명 라벨러 중복 검수 (kappa ≥ 0.70)
  └─ 갈등 케이스 미팅

Day 9: Export + 변환
  ├─ Label Studio → JSON export
  └─ python -m nlp_research.labeling.convert_labelstudio ...

Day 10: 학습
  └─ PHASE6_TRAINING_RUNBOOK.md 참고
```

---

## 4. 카파 계수 (inter-annotator agreement)

2명 라벨러가 동일 100건을 병렬 라벨링한 후:

```bash
python -m nlp_research.labeling.kappa \
    --rater1 labeler_a.jsonl \
    --rater2 labeler_b.jsonl \
    --task absa
```

Cohen's κ 기준:
- `κ ≥ 0.80` — 우수
- `0.60 ≤ κ < 0.80` — 양호 (학습 가능)
- `κ < 0.60` — 가이드 재검토 필요

---

## 5. Active Learning 루프

첫 학습 후, confidence < 0.6 인 예측을 다음 라벨링 배치 우선순위로:

```bash
# 1. 학습
python -m nlp_research.models.absa.train --config configs/absa.yaml \
       --data data/labeled/absa/v1.jsonl --output checkpoints/absa/v1

# 2. 미라벨 리뷰에 대해 예측 + confidence 낮은 것 추출
python -m nlp_research.labeling.active_select \
       --model checkpoints/absa/v1/best \
       --pool NLP/nlp_mvp/data/reviews_pool.jsonl \
       --out data/to_label/absa_round2.jsonl \
       --top-k 200

# 3. Label Studio에 업로드 → 라벨링 → 머지 후 v2 학습
```

이 루프를 2-3 라운드 돌리면 **500건이 1500건과 비슷한 정확도**를 낼 수 있습니다.
