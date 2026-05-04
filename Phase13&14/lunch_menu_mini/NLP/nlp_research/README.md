# Phase 6 — NLP Research (`nlp_research/`)

> **Status:** Phase 6 — A2 / B2 / E1 모듈 코드 스캐폴드 + 50건 시드 + 벤치마크 자동화 + Phase 5 v2 라우터 통합 완료. **모델 가중치는 미포함.** 학습은 사용자가 라벨 데이터를 마련한 뒤 직접 수행한다.

`nlp_mvp/`(Phase 5)와 분리된 독립 패키지로, 다음 3개 연구 모듈을 제공한다:

| 모듈 | ID | 역할 | 베이스 모델 |
|---|---|---|---|
| **ABSA** | A2 | 5 aspect × 3 sentiment 분리 평가 (BERT-SPC) | `beomi/KcELECTRA-base-v2022` |
| **Food NER** | B2 | DISH/INGREDIENT/FLAVOR/TEXTURE/COOKING/ALLERGEN BIO 추출 | `monologg/koelectra-base-v3-discriminator` |
| **Embedding CF** | E1 | Sentence-BERT + (FAISS / NumPy / Pure-Python) 유사 사용자 추천 | `jhgan/ko-sroberta-multitask` |

> **D1 + D2 (JointBERT) 는 본 단계에서 제외.**

---

## 디렉토리 트리

```
nlp_research/
├── configs/              YAML 학습 하이퍼파라미터 (absa / food_ner / embedding_cf)
├── data/
│   ├── seed/             50건 hand-written seed (ABSA + NER)
│   └── splits/           train.py 가 자동 생성 (gitignored)
├── models/
│   ├── absa/             BERT-SPC + 학습/평가/추론
│   ├── food_ner/         KoELECTRA + token classification (+ 옵션 CRF)
│   └── embedding_cf/     UserEmbedder + FAISS/Numpy/Py 인덱스 + Recommender
├── training/             base_trainer · data_loader · metrics · augmentation
├── evaluation/
│   ├── baselines.py      PopularRecommender · RandomRecommender
│   ├── compare_a2_vs_a1.py
│   ├── compare_b2_vs_b1.py
│   ├── compare_e1_vs_popular.py
│   └── benchmark.py      ★ 단일 진입점
├── tests/                pytest smoke tests (4 modules)
├── checkpoints/          gitignored
├── notebooks/            EDA / 실험용
└── report/benchmarks/    벤치마크 산출물 (gitignored)
```

---

## 빠른 시작

### 0) 최소 의존성으로 dry-run

```bash
# stdlib + numpy + pandas + pyyaml + python-dotenv 만 필요
pip install pyyaml python-dotenv pytest

cd Mini/NLP
PYTHONPATH=. python -m nlp_research.evaluation.benchmark --module all --smoke
# → report/benchmarks/{summary.md, summary.json, a2_vs_a1.md, b2_vs_b1.md, e1_vs_popular.md}
```

### 1) 풀 환경 (학습 가능)

```bash
pip install -r nlp_research/requirements.txt
# 옵션:
pip install pytorch-crf       # B2 + CRF 헤드
pip install faiss-cpu         # E1 FAISS 백엔드
pip install wandb             # 학습 로깅
```

### 2) 모델 학습 (실제 라벨 데이터가 있을 때)

```bash
# A2 — KcELECTRA fine-tune
PYTHONPATH=. python -m nlp_research.models.absa.train \
    --config nlp_research/configs/absa.yaml \
    --data   nlp_research/data/seed/absa_seed_50.jsonl \
    --output nlp_research/checkpoints/absa/v1

# B2 — KoELECTRA token classification
PYTHONPATH=. python -m nlp_research.models.food_ner.train \
    --config nlp_research/configs/food_ner.yaml \
    --data   nlp_research/data/seed/food_ner_seed_50.jsonl \
    --output nlp_research/checkpoints/food_ner/v1

# E1 — LOO 평가 (학습 불필요)
PYTHONPATH=. python -m nlp_research.models.embedding_cf.evaluate \
    --seed-users 8 \
    --use-sbert
```

> **시드 50건은 데모용**이다. 실제 학습은 1,000+ 라벨이 있어야 의미 있는 정확도가 나온다. Label Studio 등으로 추가 라벨링한 뒤 같은 JSONL 포맷으로 합쳐 사용.

---

## 벤치마크 자동화

`evaluation/benchmark.py` 가 단일 진입점이다.

```bash
# 모든 모듈 (smoke = 더미 가중치, 5초 안에 끝남)
PYTHONPATH=. python -m nlp_research.evaluation.benchmark --module all --smoke

# 특정 모듈만
PYTHONPATH=. python -m nlp_research.evaluation.benchmark --module a2 --smoke
PYTHONPATH=. python -m nlp_research.evaluation.benchmark --module b2 --smoke
PYTHONPATH=. python -m nlp_research.evaluation.benchmark --module e1 --smoke

# 실 학습 후 본격 평가
PYTHONPATH=. python -m nlp_research.evaluation.benchmark \
    --module all --sample-size 200 --use-sbert --from-db
```

산출물 (`report/benchmarks/`):
- `summary.md` + `summary.json` — 표 형식 비교 (baseline vs challenger vs Δ)
- `a2_vs_a1.md` — 단일감성 vs 속성별 감성
- `b2_vs_b1.md` — MenuNormalizer vs Food NER (DISH F1 + allergen recall)
- `e1_vs_popular.md` — Random / Popular / E1 LOO Hit@K, NDCG@10, Coverage, Diversity

---

## 테스트

```bash
cd Mini/NLP
PYTHONPATH=. pytest nlp_research/tests/ -v
```

테스트는 두 그룹으로 분류된다:
- **smoke (기본):** numpy/torch/transformers 없이도 동작 — 37개 통과
- **`@pytest.mark.requires_torch / requires_transformers / requires_sbert`:** 해당 패키지 미설치 시 자동 skip

---

## Phase 5 통합 — `/nlp/v2/*` 라우터

`nlp_mvp/api/routers/v2.py` 가 추가되어 다음 엔드포인트가 8001 포트에 노출된다:

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/nlp/v2/sentiment/{restaurant_id}` | A2 ABSA — aspect별 감성 |
| `POST` | `/nlp/v2/menu/extract` | B2 NER — 음식 엔티티 추출 |
| `GET` | `/nlp/v2/recommend?user_id=X&top_n=5` | E1 CF — 개인화 추천 |

가중치가 없을 때는 `backend: "dummy"` / `backend: "rule_based"` 로 동작하여 React 통합 테스트를 막지 않는다. 학습 완료 후 `nlp_research/checkpoints/{absa,food_ner}/best/` 에 가중치를 두면 자동으로 `backend: "trained"` 로 승격된다.

비활성화: `NLP_V2_DISABLE=1` 환경변수 → 모든 v2 엔드포인트 503.

---

## KPI 목표 (가이드 §1.4)

| 모듈 | 지표 | MVP 베이스라인 | 목표 | 최소 합격 |
|---|---|---|---|---|
| A2 ABSA | Macro F1 | 0.72 (KoBERT) | ≥ 0.80 | 0.75 |
| B2 Food NER | Entity F1 | 0.55 (rule-based) | ≥ 0.78 | 0.70 |
| B2 Allergen | Recall | — | ≥ 0.90 | — |
| E1 CF | NDCG@10 | 0.21 (Popular) | ≥ 0.45 | 0.35 |

---

## 한계

1. **모델 가중치 미포함** — 본 저장소는 학습 코드만 제공. fine-tuning 후 사용해야 의미 있는 정확도.
2. **시드 50건 → 충분한 학습 데이터 아님** — Label Studio 등으로 1,000+ 건 추가 필요.
3. **B2 CRF 헤드는 옵션** — `use_crf: true` 설정 시 `pytorch-crf` 추가 설치 필요.
4. **E1 학습 데이터 부족 시** — `MealHistorySource.synthetic(n_users=N)` 으로 mock 사용자 자동 생성.
5. **D1 + D2 (JointBERT) 미구현** — Phase 6 후속 작업.
