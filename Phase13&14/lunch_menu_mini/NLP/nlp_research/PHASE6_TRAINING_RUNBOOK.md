# Phase 6 Training Runbook — A2 ABSA · B2 Food NER

End-to-end operational guide for turning raw reviews into `/nlp/v2/*` served checkpoints.
This doc is the single source of truth for the "label → train → deploy" loop.

---

## 0. Prerequisites

```bash
# Python 3.9+ with the research requirements
cd Mini/NLP
pip install -r nlp_research/requirements.txt

# Optional heavy deps (only needed for real training):
pip install torch transformers datasets seqeval accelerate wandb

# Label Studio (labeling UI)
pip install label-studio
label-studio start        # http://localhost:8080
```

Dataset targets (from `labeling/labeling_guide.md`):

| Task | Target rows | Min for viable model |
|---|---|---|
| A2 ABSA | 1,000 reviews (≥ 20 % mixed-sentiment) | 500 |
| B2 Food NER | 1,000 sentences | 500 |

---

## 1. Label Studio Setup

1. Create project **"Mini ABSA"**, paste `labeling/absa_label_config.xml` into the Labeling Interface tab.
2. Create project **"Mini Food NER"**, paste `labeling/food_ner_label_config.xml`.
3. Import raw texts (JSON/CSV with `text` column). Reviews can be exported from Phase 5 DB:
   ```bash
   sqlite3 Mini/lunch-optimizer/mini.db \
     "SELECT json_object('text', text) FROM reviews LIMIT 2000;" > reviews.jsonl
   ```
4. Label following `labeling/labeling_guide.md` (BIO scheme, 3-annotator overlap for Cohen's κ ≥ 0.7).
5. Export as **JSON-MIN** → `absa_export.json` / `food_ner_export.json`.

---

## 2. Convert Export → Training JSONL

```bash
cd Mini/NLP
PYTHONPATH=nlp_research python -m nlp_research.labeling.convert_labelstudio absa \
  --input  /path/to/absa_export.json \
  --output nlp_research/data/labeled/absa/v1.jsonl

PYTHONPATH=nlp_research python -m nlp_research.labeling.convert_labelstudio food_ner \
  --input  /path/to/food_ner_export.json \
  --output nlp_research/data/labeled/food_ner/v1.jsonl
```

The converter prints per-class distribution stats. Flag any aspect/entity with < 50 samples before training.

### Low-data escape hatch: rule-based augmentation

```bash
PYTHONPATH=nlp_research python -m nlp_research.labeling.augment_seed all --n 100
# → data/seed/{absa,food_ner}_seed_aug.jsonl (+100 rows each)
```

Concatenate with the real labels:
```bash
cat nlp_research/data/seed/absa_seed_50.jsonl \
    nlp_research/data/seed/absa_seed_aug.jsonl \
    nlp_research/data/labeled/absa/v1.jsonl \
    > nlp_research/data/labeled/absa/v1_full.jsonl
```

---

## 3. Smoke Test (no GPU)

Before spinning up GPU training, confirm the pipeline end-to-end:

```bash
PYTHONPATH=nlp_research python -m nlp_research.models.absa.train \
  --config nlp_research/configs/absa.yaml \
  --data   nlp_research/data/seed/absa_seed_50.jsonl \
  --output /tmp/absa_dryrun --dry-run

PYTHONPATH=nlp_research python -m nlp_research.models.food_ner.train \
  --config nlp_research/configs/food_ner.yaml \
  --data   nlp_research/data/seed/food_ner_seed_50.jsonl \
  --output /tmp/ner_dryrun --dry-run
```

Expect exit code 0 plus a `dry_run.json` summary in each output dir.

Run the unit-test suite:

```bash
PYTHONPATH=nlp_research python -m pytest nlp_research/tests -v
```

---

## 4. Real Training

Tweak the configs (`configs/absa.yaml`, `configs/food_ner.yaml`) for your GPU
(`batch_size`, `epochs`, `learning_rate`), then:

```bash
# A2 ABSA  — ~15 min on a single T4 with 1,000 rows
PYTHONPATH=nlp_research python -m nlp_research.models.absa.train \
  --config nlp_research/configs/absa.yaml \
  --data   nlp_research/data/labeled/absa/v1_full.jsonl \
  --output nlp_research/checkpoints/absa

# B2 Food NER — ~25 min on a single T4 with 1,000 rows
PYTHONPATH=nlp_research python -m nlp_research.models.food_ner.train \
  --config nlp_research/configs/food_ner.yaml \
  --data   nlp_research/data/labeled/food_ner/v1_full.jsonl \
  --output nlp_research/checkpoints/food_ner
```

Artifacts land in:
```
nlp_research/checkpoints/absa/best/pytorch_model.bin
nlp_research/checkpoints/food_ner/best/pytorch_model.bin
```

Pass/fail gates:

| Task | Metric | Target |
|---|---|---|
| A2 | macro F1 (sentiment) | ≥ 0.75 |
| A2 | per-aspect F1 (lowest) | ≥ 0.60 |
| B2 | entity-level F1 (seqeval) | ≥ 0.70 |
| B2 | ALLERGEN recall | ≥ 0.90 (safety critical) |

---

## 5. Evaluate + Benchmark

```bash
# Per-model detailed report
PYTHONPATH=nlp_research python -m nlp_research.models.absa.evaluate \
  --model nlp_research/checkpoints/absa/best \
  --data  nlp_research/data/labeled/absa/v1_full.jsonl

# Before/after benchmark (A1 vs A2, B1 vs B2, Popular vs E1)
PYTHONPATH=nlp_research python -m nlp_research.evaluation.benchmark \
  --module all --output-dir nlp_research/report/benchmarks
```

Reports appear in `nlp_research/report/benchmarks/{summary.md, summary.json, *.md}`.

---

## 6. Activate `/nlp/v2/*`

Checkpoint auto-discovery is already wired. The v2 router looks for a checkpoint at:

1. `$NLP_V2_ABSA_CKPT` / `$NLP_V2_NER_CKPT` (env override)
2. `nlp_research/checkpoints/absa/best/` or `…/v1/`
3. `nlp_research/checkpoints/food_ner/best/` or `…/v1/`

If `pytorch_model.bin` is present at any of those paths, the router will instantiate
the real inferencer; otherwise it falls back to the dummy/rule-based path (`backend: dummy`).

Verify:
```bash
cd Mini && uvicorn nlp_mvp.api.main:app --port 8001 &
curl 'http://localhost:8001/nlp/v2/sentiment/1' | jq .backend
# "trained"  (or "dummy" if no checkpoint)

curl -X POST http://localhost:8001/nlp/v2/menu/extract \
  -H 'Content-Type: application/json' \
  -d '{"text":"매운 김치찌개에 땅콩이 들어있어요"}' | jq .backend
# "trained" or "rule_based"
```

Force-disable v2 without removing checkpoints:
```bash
NLP_V2_DISABLE=1 uvicorn nlp_mvp.api.main:app --port 8001
# → /nlp/v2/* returns 503
```

---

## 7. Active Learning Loop

Once v1 is deployed:

1. Collect production inputs via `/nlp/v2/*` logs.
2. Rank by model uncertainty (ABSA: low max-softmax; NER: high per-token entropy).
3. Export top-500 to Label Studio → label → convert → retrain as v2.
4. Bump the checkpoint dir: `checkpoints/absa/v2/`, update `$NLP_V2_ABSA_CKPT`, restart.

Target cadence: v1 → v2 within 2 weeks, then monthly.

---

## 8. Rollback

```bash
# Revert to a previous checkpoint without code changes
# (호스트 절대경로. 2026-05-04 부로 운영 경로는 ~/Downloads/lunch_menu_mini.
#  외장 SSD 시기에는 /Volumes/Corsair EX300U Media/.../checkpoints/... 였음.
#  Docker 컨테이너 내부에서는 /app/nlp_research/checkpoints/... 가 bind mount됨.)
export NLP_V2_ABSA_CKPT=$HOME/Downloads/lunch_menu_mini/NLP/nlp_research/checkpoints/absa/v1/best
export NLP_V2_NER_CKPT=$HOME/Downloads/lunch_menu_mini/NLP/nlp_research/checkpoints/food_ner/v1/best
systemctl restart mini-nlp-api   # or uvicorn reload

# Or disable v2 entirely (UI degrades gracefully)
export NLP_V2_DISABLE=1
```

---

## Files Touched by This Runbook

| Path | Role |
|---|---|
| `labeling/{absa,food_ner}_label_config.xml` | Label Studio UI configs |
| `labeling/labeling_guide.md` | Annotator instructions |
| `labeling/convert_labelstudio.py` | Export → JSONL converter |
| `labeling/augment_seed.py` | Rule-based data expansion |
| `data/seed/*.jsonl` | Hand-written + augmented seed |
| `data/labeled/*/v*.jsonl` | Real labeled data (gitignored) |
| `configs/*.yaml` | Training hyperparameters |
| `models/{absa,food_ner}/train.py` | Training entry points |
| `models/{absa,food_ner}/evaluate.py` | Detailed evaluation |
| `models/{absa,food_ner}/inference.py` | Auto-discovery loader |
| `evaluation/benchmark.py` | A/B benchmark harness |
| `checkpoints/` | Trained artifacts (gitignored) |
| `nlp_mvp/api/routers/v2.py` | FastAPI serving layer |
