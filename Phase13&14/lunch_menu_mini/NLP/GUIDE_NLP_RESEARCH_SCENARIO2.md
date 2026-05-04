# 🔬 NLP 연구·심화 (시나리오 2) — Claude Code 구현 가이드라인

> **목표**: Mini "직장인 점심 최적화" 프로젝트 위에, **자체 학습 NLP 모델 5종**을
> 구축하여 파인튜닝 · NER · 임베딩 · 개인화 CF 까지 **NLP 풀스택 역량**을 증명합니다.
> 시나리오 3 (MVP) 을 완료한 상태에서 이어가는 것을 전제로 합니다.
>
> 본 문서는 Claude Code 에게 전달할 수 있는 **단계별 구현 프롬프트**로 작성되었으며,
> 기존 `GUIDE/` · `ChatBOT/` · `GUIDE_NLP_MVP_SCENARIO3.md` 와 동일한 포맷을 따릅니다.

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [사전 준비](#2-사전-준비)
3. [전체 아키텍처](#3-전체-아키텍처)
4. [프로젝트 초기화](#4-프로젝트-초기화)
5. [Step 1 — 모듈 A2: ABSA (속성별 감성분석)](#5-step-1--모듈-a2-absa-속성별-감성분석)
6. [Step 2 — 모듈 B2: Food NER (음식 개체 인식)](#6-step-2--모듈-b2-food-ner-음식-개체-인식)
7. [Step 3 — 모듈 D1 + D2: JointBERT (Intent + Slot)](#7-step-3--모듈-d1--d2-jointbert-intent--slot)
8. [Step 4 — 모듈 E1: 임베딩 기반 개인화 CF](#8-step-4--모듈-e1-임베딩-기반-개인화-cf)
9. [Step 5 — Before/After 벤치마크 및 통합](#9-step-5--beforeafter-벤치마크-및-통합)
10. [Step 6 — 논문/포트폴리오 산출물](#10-step-6--논문포트폴리오-산출물)
11. [트러블슈팅 가이드](#11-트러블슈팅-가이드)
12. [체크리스트](#12-체크리스트)
13. [마무리 및 발전 방향](#13-마무리-및-발전-방향)

---

## 1. 프로젝트 개요

### 1.1 목표

시나리오 3 MVP 위에 **연구 수준의 NLP 심화 모듈 5종**을 구축하여:

1. **A2 ABSA** — 리뷰를 맛/가격/서비스/청결 4축으로 분리 평가
2. **B2 Food NER** — 재료·조리법·맛·알레르겐 개체 자동 인식
3. **D1 Intent** — DistilKoBERT 로 자체 파인튜닝 (Ollama 대체)
4. **D2 Slot Filling** — JointBERT 방식으로 D1 과 통합 학습
5. **E1 개인화 CF** — Sentence-BERT + FAISS 기반 유사 사용자 추천

### 1.2 전제 조건

| 조건 | 필수 여부 | 비고 |
|------|---------|------|
| 시나리오 3 (MVP) 완료 | ✅ 필수 | `nlp_mvp/` 폴더 존재, A1/B1/D3/D5 동작 |
| Mini DB 운영 중 | ✅ 필수 | 실제 사용자 데이터 또는 시드 데이터 |
| GPU 환경 | ✅ 필수 | 로컬 RTX 3060+ 또는 Colab Pro / RunPod |
| 라벨링 도구 | ⭐ 권장 | Label Studio, Doccano, Prodigy |
| 실험 추적 | ⭐ 권장 | Weights & Biases 또는 MLflow |

### 1.3 범위 (IN / OUT)

✅ **포함 (IN)**
- 자체 모델 파인튜닝 (PyTorch + Hugging Face)
- 데이터 직접 라벨링 (~3,500건)
- 하이퍼파라미터 탐색·실험 추적
- Before/After 벤치마크 (vs MVP)
- 모델 서빙 (ONNX Runtime)
- 논문·벤치마크 문서 작성

❌ **제외 (OUT)**
- 대규모 사전학습 (from scratch) — 기존 모델 파인튜닝만
- 멀티모달 (이미지·음성) — 텍스트 전용
- 상용 API (OpenAI, Claude API) — 로컬·오픈소스만

### 1.4 성공 지표 (KPI) 및 목표 성능

| 모듈 | 지표 | 베이스라인 (MVP) | 목표 | 최소 허용 |
|------|------|--------------|------|---------|
| **A2 ABSA** | Macro F1 | KoBERT 0.72 | ≥ 0.80 | 0.75 |
| **B2 Food NER** | Entity F1 (seqeval) | Rule-based 0.55 | ≥ 0.78 | 0.70 |
| **D1 Intent** | Accuracy | Ollama zero-shot | ≥ 0.92 | 0.85 |
| **D1+D2 Joint** | Joint Accuracy | CRF 0.65 | ≥ 0.85 | 0.78 |
| **E1 CF 추천** | NDCG@10 | Popular 0.21 | ≥ 0.45 | 0.35 |
| **A2 응답속도** | Inference latency | — | ≤ 50 ms | 100 ms |
| **D1 응답속도** | vs Ollama | ~800 ms | ≤ 30 ms (**26x 빠름**) | 100 ms |

### 1.5 타임라인 (10주)

| 주차 | 작업 | 주요 산출물 |
|------|------|-----------|
| **1주** | 데이터 크롤링 · EDA · Label Studio 세팅 | 원시 corpus 20k, 라벨링 환경 |
| **2주** | A2 ABSA 500건 라벨링 | ABSA 데이터셋 v1 |
| **3주** | B2 Food NER 1,000건 라벨링 (BIO) | NER 데이터셋 v1 |
| **4주** | A2 학습 · 평가 · 에러 분석 | A2 모델 v1 + 벤치마크 |
| **5주** | B2 학습 · 평가 · 에러 분석 | B2 모델 v1 + 에러 리포트 |
| **6주** | D1+D2 발화 데이터 생성 (GPT 증강) | 발화 데이터셋 2k |
| **7주** | JointBERT 학습 · Ollama 비교 벤치마크 | D1+D2 모델 v1 |
| **8주** | E1 Sentence-BERT + FAISS CF | 추천 시스템 v1 |
| **9주** | Mini 통합 · Before/After 벤치마크 | 통합 데모 |
| **10주** | 보고서 · 논문 초안 · 포트폴리오 | 최종 산출물 |

---

## 2. 사전 준비

### 2.1 필수 환경

| 항목 | 요구사항 | 비고 |
|------|---------|------|
| Claude Code | Claude Pro($20/월) 이상 | 구현 자동화 |
| Python | 3.10 이상 | - |
| PyTorch | 2.3+ (CUDA 지원) | GPU 가속 필수 |
| GPU | RTX 3060 12GB 이상 권장 | Colab Pro T4 / RunPod 3090 대안 |
| RAM | 32GB 권장 (최소 16GB) | - |
| 디스크 | 50GB 여유 | 모델 체크포인트 · 데이터셋 |
| Hugging Face 계정 | 필수 | 모델 업로드·공유 |

### 2.2 Python 패키지

```bash
pip install \
  transformers==4.44.0 \
  torch==2.3.1 \
  datasets==2.20.0 \
  accelerate==0.33.0 \
  peft==0.12.0 \
  seqeval==1.2.2 \
  pyabsa==2.4.1 \
  sentence-transformers==3.0.1 \
  faiss-cpu==1.8.0 \
  scikit-learn==1.5.1 \
  wandb==0.17.7 \
  label-studio==1.13.0 \
  onnx==1.16.1 \
  onnxruntime==1.18.1 \
  pandas numpy matplotlib seaborn
```

### 2.3 학습 데이터 라벨링 도구

```bash
# Label Studio 설치 및 실행
pip install label-studio
label-studio start --port 8080

# 브라우저에서 http://localhost:8080 접속
# 프로젝트 생성: "Mini NLP Labeling"
# - Task 1: ABSA (속성별 감성 4축)
# - Task 2: Food NER (BIO 태깅 6클래스)
# - Task 3: Intent/Slot (5 Intent + 6 Slot)
```

### 2.4 실험 추적 (Weights & Biases)

```bash
# wandb 로그인
wandb login

# 프로젝트 생성
wandb init --project mini-nlp-research
```

### 2.5 환경 변수 (`.env` 추가)

```bash
# Mini/NLP/.env 에 추가
# === 시나리오 2 (연구) 관련 ===
WANDB_PROJECT=mini-nlp-research
HF_TOKEN=your_huggingface_token
LABEL_STUDIO_URL=http://localhost:8080
LABEL_STUDIO_TOKEN=your_label_studio_token
GPU_DEVICE=cuda:0
MODEL_CHECKPOINT_DIR=./nlp_research/checkpoints
```

---

## 3. 전체 아키텍처

```
┌──────────────────────────────────────────────────────────────────┐
│                시나리오 3 MVP (이미 구축됨)                         │
│   A1 Zero-shot │ B1 규칙 매칭 │ D3 RAG │ D5 NLG │ SQLite         │
└────────────────────────┬─────────────────────────────────────────┘
                         │ 데이터 재사용 (MVP 로그를 학습 데이터로)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                  시나리오 2 연구/심화 (본 문서)                     │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌──────────┐  │
│  │ A2 ABSA  │   │ B2 Food  │   │ D1+D2 Joint  │   │ E1 임베딩 │  │
│  │ (파인튜닝)│   │   NER    │   │    BERT      │   │   CF     │  │
│  └────┬─────┘   └────┬─────┘   └──────┬───────┘   └─────┬────┘  │
│       │              │                │                 │       │
│       ▼              ▼                ▼                 ▼       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              학습 파이프라인 (PyTorch + HF)                │  │
│  │  · Datasets 로딩 · Trainer API · W&B 추적 · 체크포인트     │  │
│  └───────────────────────┬───────────────────────────────────┘  │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 모델 서빙 (ONNX Runtime)                   │  │
│  │   · FastAPI 동일 엔드포인트 · MVP 와 A/B 비교 가능          │  │
│  └───────────────────────┬───────────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│            Before/After 벤치마크 · 논문 · 포트폴리오                │
│   · Macro F1 개선 · 응답속도 비교 · 사용자 만족도 재측정            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. 프로젝트 초기화

### 4.1 폴더 구조 생성

Claude Code 프롬프트:

```
Mini/NLP/ 아래에 `nlp_research` 폴더를 생성하고 다음 구조로 초기화해줘:

nlp_research/
├── README.md
├── requirements.txt
├── .env.example
├── configs/                    # 학습 하이퍼파라미터 (YAML)
│   ├── absa.yaml
│   ├── food_ner.yaml
│   ├── joint_bert.yaml
│   └── embedding_cf.yaml
├── data/
│   ├── raw/                    # 크롤링 원시 데이터
│   ├── labeled/                # Label Studio 내보내기
│   │   ├── absa/
│   │   ├── food_ner/
│   │   └── intent_slot/
│   ├── augmented/              # GPT/룰 기반 증강 데이터
│   └── splits/                 # train/val/test 분할
├── models/
│   ├── absa/                   # A2 모듈
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── model.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── inference.py
│   ├── food_ner/               # B2 모듈
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── model.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── inference.py
│   ├── joint_bert/             # D1 + D2 통합
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── model.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── inference.py
│   └── embedding_cf/           # E1 모듈
│       ├── __init__.py
│       ├── embedder.py
│       ├── index.py
│       ├── recommender.py
│       └── evaluate.py
├── training/
│   ├── labeling_guide.md       # 라벨링 가이드라인
│   ├── data_augmentation.py    # GPT 기반 데이터 증강
│   └── convert_labelstudio.py  # Label Studio JSON → HF Dataset
├── evaluation/
│   ├── benchmark.py            # 전체 벤치마크
│   ├── compare_with_mvp.py     # MVP vs 심화 비교
│   └── error_analysis.py
├── serving/
│   ├── export_onnx.py          # PyTorch → ONNX
│   ├── fastapi_server.py       # 서빙 서버
│   └── ab_test.py              # A/B 라우터
├── checkpoints/                # .gitignore
├── notebooks/
│   ├── 01_data_eda.ipynb
│   ├── 02_absa_experiments.ipynb
│   ├── 03_ner_experiments.ipynb
│   ├── 04_joint_bert_experiments.ipynb
│   └── 05_cf_experiments.ipynb
└── report/
    ├── paper_draft.md
    ├── benchmark_results.md
    └── figures/

각 __init__.py 는 빈 파일로, README.md 에는 모듈별 실행 명령어를 포함.
.gitignore 에 checkpoints/, data/raw/, .env 추가.
```

### 4.2 공용 학습 유틸

Claude Code 프롬프트:

```
nlp_research/training/ 아래에 공용 학습 유틸을 작성해줘:

1. base_trainer.py
   - BaseTrainer 추상 클래스
   - __init__(self, config_path: str)
     · YAML config 로드
     · device 설정
     · W&B 초기화
   - train(), evaluate(), save(), load() 추상 메서드
   - early stopping, learning rate scheduler 공용 로직
   - 체크포인트 자동 저장 (best + last)

2. data_loader.py
   - load_huggingface_dataset() 래퍼
   - stratified split (train/val/test = 8:1:1)
   - 토크나이저 캐싱
   - collate_fn 유틸

3. metrics.py
   - compute_classification_metrics() — accuracy, precision, recall, F1
   - compute_ner_metrics() — seqeval 래핑
   - compute_ranking_metrics() — Hit@K, NDCG@K
   - confusion matrix 시각화 함수

4. augmentation.py
   - synonym_replacement (KorEDA)
   - back_translation (NLLB)
   - gpt_paraphrase (OpenAI API 또는 로컬 LLM)
   - 증강 품질 필터 (Sentence-BERT 유사도 기반)

모두 타입 힌트와 docstring 포함. pytest 테스트도 함께.
```

### 4.3 데이터 증강 파이프라인

Claude Code 프롬프트:

```
nlp_research/training/data_augmentation.py 를 작성해줘.

GPT 기반 증강:
def gpt_augment(
    original: str,
    intent: str = None,
    n_variants: int = 3,
    provider: str = "ollama"
) -> list[str]:
    """
    Ollama Qwen 또는 Claude API 로 문장 변형 생성.
    시스템 프롬프트:
      "다음 한국어 문장을 의미는 동일하되 표현만 다르게 3가지로 변형해줘.
       구어체, 문어체, 짧은 버전을 각각 포함."
    """

EDA (Easy Data Augmentation):
- synonym_replacement(text, n=2)
- random_insertion(text, n=1)
- random_swap(text, n=1)
- random_deletion(text, p=0.1)

모든 증강은 KorEDA (한국어 EDA) 규칙 사용.

데이터 품질 필터:
def filter_by_similarity(
    original: str,
    augmented: list[str],
    min_sim: float = 0.75,
    max_sim: float = 0.98
) -> list[str]:
    """
    너무 다르거나(min_sim) 너무 같은(max_sim) 변형 제거.
    Sentence-BERT (ko-sroberta) 코사인 유사도 사용.
    """

CLI:
python -m nlp_research.training.data_augmentation \
    --input data/labeled/intent_slot/train.jsonl \
    --output data/augmented/intent_slot/train_aug.jsonl \
    --target-size 2000
```

---

## 5. Step 1 — 모듈 A2: ABSA (속성별 감성분석)

### 5.1 목적

시나리오 3 의 A1 감성분석은 리뷰를 단일 감성(긍/중/부) 으로만 분류합니다.
A2 는 한 리뷰 안에서 **"맛은 좋은데 서비스는 별로"** 같이 **속성별로 감성을 분리**합니다.

### 5.2 Aspect 및 라벨 정의

| Aspect | 영문 | 설명 |
|--------|------|------|
| 맛 | taste | 음식의 맛, 조리 품질 |
| 가격 | price | 가격 대비 만족도 |
| 서비스 | service | 직원 응대·속도 |
| 청결 | hygiene | 위생·청결도 |
| 분위기 | ambience | 실내 분위기·좌석 |

**감성 라벨:** `positive` / `neutral` / `negative` (각 aspect 별)

**예시:**
```json
{
  "text": "김치찌개 맛은 훌륭한데, 가격이 비싸고 직원이 불친절했어요.",
  "aspects": [
    {"aspect": "taste", "sentiment": "positive"},
    {"aspect": "price", "sentiment": "negative"},
    {"aspect": "service", "sentiment": "negative"}
  ]
}
```

### 5.3 데이터셋 구축

Claude Code 프롬프트:

```
nlp_research/data/labeled/absa/ 에 ABSA 데이터셋을 구축하는 가이드를 작성해줘.

1. nlp_research/training/labeling_guide.md 에 아래 내용 추가:
   - ABSA 라벨링 규칙 (5 aspect × 3 sentiment)
   - 애매한 경우 처리 방법
   - 예시 20건 (긍정·중립·부정·혼합)

2. nlp_research/training/convert_labelstudio.py 에 ABSA 변환 함수 추가:
   - Label Studio JSON export → Hugging Face Dataset 포맷
   - 각 리뷰를 (text, aspect, sentiment) triple 로 분해
   - train/val/test 8:1:1 분할 (stratified by aspect × sentiment)
   - 결과: data/splits/absa/{train,val,test}.jsonl

목표 데이터 규모:
- 총 500건 리뷰 × 평균 2.5 aspect = 약 1,250 triple
- 클래스별 최소 50 샘플 보장

데이터 소스:
- 시나리오 3 의 A1 으로 수집된 리뷰 재사용
- 신뢰도 낮은 리뷰(confidence < 0.6) 우선 라벨링 (Active Learning)
```

### 5.4 ABSA 모델 구현

Claude Code 프롬프트:

```
nlp_research/models/absa/model.py 를 작성해줘.

구조: BERT-SPC (Sentence Pair Classification)
- 입력: [CLS] review_text [SEP] aspect_name [SEP]
- 출력: 3-class softmax (positive/neutral/negative)

class ABSAModel(nn.Module):
    def __init__(self, model_name: str = "beomi/KcELECTRA-base-v2022"):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Linear(self.backbone.config.hidden_size, 3)

    def forward(self, input_ids, attention_mask, token_type_ids=None):
        outputs = self.backbone(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids
        )
        cls_output = outputs.last_hidden_state[:, 0, :]
        logits = self.classifier(self.dropout(cls_output))
        return logits

추가:
- Aspect-aware attention 옵션 (aspect 토큰에 가중치)
- Multi-task learning 버전 (선택) — aspect detection + sentiment 동시
```

### 5.5 ABSA 학습 스크립트

Claude Code 프롬프트:

```
nlp_research/models/absa/train.py 를 작성해줘.

요구사항:
1. Hugging Face Trainer API 사용
2. configs/absa.yaml 에서 하이퍼파라미터 로드
   · model_name: beomi/KcELECTRA-base-v2022
   · batch_size: 16
   · learning_rate: 2e-5
   · epochs: 5
   · warmup_ratio: 0.1
   · weight_decay: 0.01
   · max_length: 128
3. W&B 로깅
4. Early stopping (patience=2)
5. Best model 저장 (based on val macro F1)
6. 학습 종료 후 test set 평가 → report/absa_results.md 생성

CLI:
python -m nlp_research.models.absa.train \
    --config configs/absa.yaml \
    --data data/splits/absa \
    --output checkpoints/absa/v1

학습 리소스 예상:
- RTX 3060 기준 1 epoch ≈ 3분 (1,250 샘플)
- 전체 학습 ≈ 15분
```

### 5.6 ABSA 평가 및 에러 분석

Claude Code 프롬프트:

```
nlp_research/models/absa/evaluate.py 를 작성해줘.

def evaluate_absa(model_path: str, test_data: str) -> dict:
    """
    반환:
    {
        "overall": {
            "macro_f1": float,
            "accuracy": float,
            "precision": float,
            "recall": float
        },
        "per_aspect": {
            "taste": {...},
            "price": {...},
            ...
        },
        "per_sentiment": {
            "positive": {...},
            "neutral": {...},
            "negative": {...}
        },
        "confusion_matrix": 2d_array
    }
    """

error_analysis():
- Test set 의 오분류 샘플 Top 50 추출
- 원인 분류: 레이블 노이즈, 문맥 부족, 아이러니, 기타
- report/absa_error_analysis.md 생성

시각화:
- Aspect × Sentiment heatmap
- Confusion matrix heatmap
- Confidence histogram
```

### 5.7 MVP A1 과의 비교

Claude Code 프롬프트:

```
nlp_research/evaluation/compare_with_mvp.py 에 A2 vs A1 비교 추가.

비교 항목:
1. 동일 리뷰 200건에 대해:
   - A1 (zero-shot) 단일 감성 예측
   - A2 (파인튜닝) 속성별 감성 예측
2. A2 의 속성별 결과를 평균 내어 단일 감성과 비교 → overlap rate
3. A2 가 "혼합 감성" 을 정확히 포착하는 케이스 하이라이트
4. 응답 속도 비교 (single vs batch)
5. report/a1_vs_a2_comparison.md 생성
```

---

## 6. Step 2 — 모듈 B2: Food NER (음식 개체 인식)

### 6.1 목적

리뷰·메뉴명에서 **재료(INGREDIENT)**, **조리법(COOKING)**, **맛(FLAVOR)**,
**식감(TEXTURE)**, **요리명(DISH)**, **알레르겐(ALLERGEN)** 을 자동 추출합니다.

### 6.2 엔티티 클래스 및 BIO 태깅

| 태그 | 의미 | 예시 |
|------|------|------|
| `DISH` | 요리명 | 김치찌개, 비빔밥, 돈까스 |
| `INGREDIENT` | 재료 | 돼지고기, 양파, 마늘 |
| `FLAVOR` | 맛 표현 | 매운, 달콤한, 짠 |
| `TEXTURE` | 식감 | 바삭한, 쫄깃한, 부드러운 |
| `COOKING` | 조리법 | 볶음, 찜, 튀김 |
| `ALLERGEN` | 알레르겐 | 땅콩, 새우, 우유, 밀 |

**BIO 스킴:** `B-DISH`, `I-DISH`, `B-INGREDIENT`, `I-INGREDIENT`, ..., `O` (총 13개 태그)

**예시:**
```
매운  김치  찌개  에   들어간  돼지고기  가  부드러워요
B-FLAVOR B-DISH I-DISH O O B-INGREDIENT O B-TEXTURE
```

### 6.3 데이터셋 구축

Claude Code 프롬프트:

```
nlp_research/data/labeled/food_ner/ 에 Food NER 데이터셋 구축 프로세스를 설정해줘.

1. 라벨링 가이드 추가 (labeling_guide.md)
   - BIO 태깅 규칙
   - 13개 태그 정의 + 예시
   - 중첩 엔티티 처리 (예: "돼지고기 찜" → DISH 또는 COOKING?)
   - 1,000건 목표

2. Label Studio 프로젝트 설정
   - Labeling config: NER tagging interface
   - 태그 색상: DISH=빨강, INGREDIENT=파랑, FLAVOR=주황, ...

3. convert_labelstudio.py 에 NER 변환 함수
   - Label Studio JSON → CoNLL 형식
   - CoNLL → Hugging Face Dataset (tokens + ner_tags)
   - 분할: 8:1:1

4. 데이터 소스 우선순위:
   a) 시나리오 3 리뷰 corpus (A1 라벨된)
   b) 카카오 음식점 메뉴 description
   c) 공공 식품영양 DB 의 재료 필드
```

### 6.4 Food NER 모델 구현

Claude Code 프롬프트:

```
nlp_research/models/food_ner/model.py 를 작성해줘.

구조: KoELECTRA + Token Classification Head + CRF (선택)

class FoodNERModel(nn.Module):
    def __init__(
        self,
        model_name: str = "monologg/koelectra-base-v3-discriminator",
        num_labels: int = 13,
        use_crf: bool = True
    ):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(self.backbone.config.hidden_size, num_labels)
        if use_crf:
            from torchcrf import CRF
            self.crf = CRF(num_labels, batch_first=True)
        self.use_crf = use_crf

    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.backbone(input_ids, attention_mask=attention_mask)
        sequence_output = self.dropout(outputs.last_hidden_state)
        logits = self.classifier(sequence_output)

        if labels is not None:
            if self.use_crf:
                loss = -self.crf(logits, labels, mask=attention_mask.bool())
            else:
                loss = F.cross_entropy(
                    logits.view(-1, logits.size(-1)),
                    labels.view(-1),
                    ignore_index=-100
                )
            return loss, logits
        return logits

    def decode(self, input_ids, attention_mask):
        outputs = self.backbone(input_ids, attention_mask=attention_mask)
        logits = self.classifier(outputs.last_hidden_state)
        if self.use_crf:
            return self.crf.decode(logits, mask=attention_mask.bool())
        return logits.argmax(dim=-1).tolist()

의존성: pip install pytorch-crf
```

### 6.5 Food NER 학습·평가

Claude Code 프롬프트:

```
nlp_research/models/food_ner/train.py 및 evaluate.py 를 작성해줘.

train.py:
- configs/food_ner.yaml 로드
  · model_name: monologg/koelectra-base-v3-discriminator
  · use_crf: true
  · batch_size: 32
  · learning_rate: 5e-5
  · epochs: 10
  · max_length: 256
- W&B 로깅
- seqeval 기반 entity-level F1 으로 best 선정

evaluate.py:
- seqeval.metrics.classification_report 사용
- Entity 별 precision/recall/F1 출력
- 에러 케이스 (FP, FN) 샘플 50건 추출

벤치마크 목표:
- Entity F1 ≥ 0.78
- DISH, INGREDIENT 는 F1 ≥ 0.85
- ALLERGEN 은 재현율(recall) 우선 (≥ 0.90) — 안전이 중요
```

### 6.6 B2 활용: 알레르기 필터

Claude Code 프롬프트:

```
nlp_research/models/food_ner/inference.py 에 알레르기 필터 추가.

def extract_allergens(menu_description: str) -> list[str]:
    """
    메뉴 설명에서 알레르겐 개체 추출.
    반환: ["땅콩", "새우"] 등
    """

def filter_restaurants_by_allergies(
    restaurants: list[dict],
    user_allergies: list[str]
) -> list[dict]:
    """
    사용자 알레르기에 맞지 않는 식당 필터.
    NER 기반으로 메뉴 description 에서 알레르겐 추출 후 매칭.
    """

Mini 통합:
- restaurants 테이블에 extracted_allergens JSON 컬럼 추가
- 주기적 배치로 전체 음식점 알레르겐 추출
- 통합 스코어링 엔진에서 사용자 알레르기 기반 제외 필터 적용
```

---

## 7. Step 3 — 모듈 D1 + D2: JointBERT (Intent + Slot)

### 7.1 목적

시나리오 3 의 D3 (RAG 챗봇) 은 Ollama LLM 을 통째로 호출하여 응답 속도가
**~800 ms** 수준입니다. D1+D2 는 **Intent 분류 + Slot Filling 전용 경량 모델**을
파인튜닝하여 **~30 ms** (26배 빠름) 로 NLU 만 처리하고, 응답 생성은 별도 템플릿
또는 더 작은 LLM 에 위임하는 구조입니다.

### 7.2 Intent 및 Slot 정의

**Intent (5개):**

| Intent | 설명 | 예시 |
|--------|------|------|
| `RECOMMEND` | 메뉴·식당 추천 요청 | "오늘 뭐 먹지?", "매운 거 추천해줘" |
| `QUERY` | 정보 조회 | "어제 뭐 먹었어?", "이번 주 칼로리 어때?" |
| `ACTION` | 행동 실행 | "서브웨이에 투표할게", "점심 기록해줘" |
| `REPORT` | 리포트 요청 | "주간 리포트 보여줘" |
| `CHITCHAT` | 잡담 | "안녕", "고마워" |

**Slot (6개):**

| Slot | 설명 | 예시 |
|------|------|------|
| `LOCATION` | 장소 | 강남역, 사무실 근처 |
| `CATEGORY` | 음식 카테고리 | 한식, 일식, 샐러드 |
| `PRICE` | 가격 조건 | 만원 이하, 저렴한 |
| `FLAVOR` | 맛 | 매운, 담백한 |
| `DISTANCE` | 거리 | 가까운, 도보 5분 |
| `TIME` | 시간 | 오늘, 어제, 이번 주 |

**예시:**
```
입력: "강남역 근처에 만원 이하 매운 국밥집 추천해줘"
Intent: RECOMMEND
Slots: {
  "LOCATION": "강남역 근처",
  "PRICE": "만원 이하",
  "FLAVOR": "매운",
  "CATEGORY": "국밥"
}
```

### 7.3 데이터셋 구축 (GPT 증강 활용)

Claude Code 프롬프트:

```
nlp_research/data/labeled/intent_slot/ 에 발화 데이터셋 구축 프로세스 설정.

1. 시드 데이터 (직접 작성): 각 Intent 당 50건 × 5 = 250건
2. GPT 증강 (data_augmentation.py gpt_augment):
   - 각 시드 문장을 7~10 가지 변형 → 2,000+ 건
   - 구어체, 반말, 존댓말, 짧은 버전, 긴 버전 포함
3. Slot 자동 태깅:
   - 규칙 기반 1차: 고유명사 사전 (역 이름, 음식 카테고리 등)
   - 수동 검토 및 수정
4. 최종: 2,000건 × (Intent + BIO Slot) 라벨
5. 분할: 8:1:1

labeling_guide.md 에 Intent/Slot 태깅 규칙 추가.

예시 seed 파일 (data/seed/intent_slot_seed.jsonl):
{"text": "오늘 뭐 먹지?", "intent": "RECOMMEND", "slots": []}
{"text": "강남역 매운 국밥", "intent": "RECOMMEND",
 "slots": [
   {"start": 0, "end": 3, "type": "LOCATION", "value": "강남역"},
   {"start": 4, "end": 6, "type": "FLAVOR", "value": "매운"},
   {"start": 7, "end": 9, "type": "CATEGORY", "value": "국밥"}
 ]}
```

### 7.4 JointBERT 모델 구현

Claude Code 프롬프트:

```
nlp_research/models/joint_bert/model.py 를 작성해줘.

구조: 하나의 백본으로 Intent + Slot 동시 학습

class JointBERT(nn.Module):
    def __init__(
        self,
        model_name: str = "monologg/distilkobert",
        num_intents: int = 5,
        num_slots: int = 13,  # (6 slots × 2 BIO) + 1 O
        dropout: float = 0.1
    ):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        hidden = self.backbone.config.hidden_size
        self.intent_classifier = nn.Linear(hidden, num_intents)
        self.slot_classifier = nn.Linear(hidden, num_slots)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        input_ids,
        attention_mask,
        intent_labels=None,
        slot_labels=None
    ):
        outputs = self.backbone(input_ids, attention_mask=attention_mask)

        # Intent: [CLS] token
        pooled = outputs.last_hidden_state[:, 0, :]
        intent_logits = self.intent_classifier(self.dropout(pooled))

        # Slot: all tokens
        sequence = outputs.last_hidden_state
        slot_logits = self.slot_classifier(self.dropout(sequence))

        total_loss = None
        if intent_labels is not None and slot_labels is not None:
            intent_loss = F.cross_entropy(intent_logits, intent_labels)
            slot_loss = F.cross_entropy(
                slot_logits.view(-1, slot_logits.size(-1)),
                slot_labels.view(-1),
                ignore_index=-100
            )
            total_loss = intent_loss + slot_loss

        return {
            "loss": total_loss,
            "intent_logits": intent_logits,
            "slot_logits": slot_logits
        }

베이스 모델 선택지:
- monologg/distilkobert (경량, 추천)
- klue/bert-base (정확도 우선)
- beomi/KcELECTRA-base-v2022 (감성 도메인 유리)
```

### 7.5 학습 및 Ollama 대비 벤치마크

Claude Code 프롬프트:

```
nlp_research/models/joint_bert/train.py 작성.

하이퍼파라미터 (configs/joint_bert.yaml):
- batch_size: 32
- learning_rate: 3e-5
- epochs: 10
- intent_weight: 1.0
- slot_weight: 1.5  # slot 은 더 어려움
- warmup_ratio: 0.1

평가 지표:
- Intent accuracy
- Slot F1 (seqeval)
- Joint accuracy (둘 다 정확한 비율)

nlp_research/evaluation/ollama_vs_jointbert.py 작성.

벤치마크 항목:
1. 동일 200개 테스트 문장을 두 시스템에 입력
2. Intent 정확도 비교:
   - Ollama: 프롬프트에 "아래 Intent 중 하나로 분류하세요" 넣고 호출
   - JointBERT: 모델 추론
3. Slot 추출 F1 비교
4. 응답 속도 측정:
   - Ollama: 평균, p50, p95, p99
   - JointBERT: 동일 지표
5. 모델 크기 비교 (MB)
6. 결과 테이블을 report/benchmarks/ollama_vs_jointbert.md 로 저장

기대 결과:
- JointBERT Intent Acc ≥ Ollama + 5%
- JointBERT 속도 ≥ Ollama × 20배 빠름
- JointBERT 크기 Ollama × 1/20
```

### 7.6 JointBERT 추론 및 ChatBOT 통합

Claude Code 프롬프트:

```
nlp_research/models/joint_bert/inference.py 작성.

class JointBERTInference:
    def __init__(self, model_path: str, device: str = "auto")
    def predict(self, text: str) -> dict:
        """
        반환: {
            "intent": "RECOMMEND",
            "intent_confidence": 0.94,
            "slots": [
                {"type": "LOCATION", "value": "강남역", "start": 0, "end": 3},
                ...
            ],
            "latency_ms": 28
        }
        """

Mini ChatBOT 통합:
- 기존 D3 RAG 챗봇의 NLU 단계를 JointBERT 로 교체
- chatbot.py 에 use_joint_bert: bool 옵션 추가
  · True: JointBERT → 슬롯 기반 쿼리 → DB 조회 → 응답 템플릿
  · False: 기존 D3 RAG 방식 (Ollama 호출)
- A/B 비교를 위한 이중 모드 유지
```

---

## 8. Step 4 — 모듈 E1: 임베딩 기반 개인화 CF

### 8.1 목적

시나리오 3 의 D5 NLG 리포트는 일반적인 영양 조언에 그칩니다.
E1 은 사용자가 남긴 **만족도 텍스트 + 식사 이력**을 Sentence-BERT 로 임베딩하고,
**유사 사용자의 고평가 메뉴**를 개인화 추천합니다.

### 8.2 알고리즘 개요

```
1. 사용자별 "프로필 텍스트" 생성
   · 최근 식사 이력 + 만족도 코멘트 이어붙이기
   · 예: "김치찌개 만족 5점. 돈까스 3점 느끼해서. 샐러드 4점 가볍고 좋아요."

2. Sentence-BERT 로 임베딩
   · jhgan/ko-sroberta-multitask
   · → 768차원 벡터

3. FAISS 인덱스 구축
   · 전체 사용자 벡터 저장
   · IndexFlatIP (코사인 유사도)

4. 추천 생성 (Cold Start 도 지원)
   · 타겟 사용자 임베딩 → Top-K 유사 사용자
   · 그들의 고평가(≥4) 메뉴 중 타겟 사용자가 안 먹은 것
   · 빈도 가중 투표 → Top-N 추천

5. Cold Start:
   · 신규 사용자는 온보딩 설문으로 텍스트 프로필 생성
   · "저는 매운 거 좋아하고 국물 요리 자주 먹어요" 같은 자유 텍스트
```

### 8.3 임베딩 모듈

Claude Code 프롬프트:

```
nlp_research/models/embedding_cf/embedder.py 작성.

class UserEmbedder:
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def build_profile_text(
        self,
        meal_history: list[dict],
        max_entries: int = 30
    ) -> str:
        """
        meal_history: [
            {"menu": "김치찌개", "satisfaction": 5, "comment": "맛있어요"},
            ...
        ]
        반환: "김치찌개 만족 5점 맛있어요. 돈까스 만족 3점 느끼해요. ..."
        """

    def embed_user(self, user_id: int, db_session) -> np.ndarray:
        """사용자 프로필 텍스트 → 768차원 벡터"""

    def embed_batch(self, user_ids: list[int]) -> np.ndarray:
        """배치 임베딩 (대량 사용자)"""

class MenuEmbedder:
    """
    메뉴 + 영양정보 + 평균 감성 → 벡터
    """
    def build_menu_text(self, menu: dict) -> str:
        return f"{menu['name']} 카테고리 {menu['category']} " \
               f"칼로리 {menu['calories']} 단백질 {menu['protein']}"

    def embed_menu(self, menu: dict) -> np.ndarray
```

### 8.4 FAISS 인덱스

Claude Code 프롬프트:

```
nlp_research/models/embedding_cf/index.py 작성.

import faiss

class FAISSIndex:
    def __init__(self, dim: int = 768, metric: str = "cosine")
    def build(self, vectors: np.ndarray, ids: list[int])
        """IndexFlatIP 사용, 코사인 유사도를 위해 L2 정규화"""
    def save(self, path: str)
    def load(self, path: str)
    def search(self, query_vec: np.ndarray, top_k: int = 10) -> tuple:
        """반환: (ids, scores)"""
    def add(self, new_vec: np.ndarray, new_id: int)
        """증분 업데이트"""

CLI:
python -m nlp_research.models.embedding_cf.index build \
    --output checkpoints/embedding_cf/user_index.faiss
```

### 8.5 추천 엔진

Claude Code 프롬프트:

```
nlp_research/models/embedding_cf/recommender.py 작성.

class EmbeddingCFRecommender:
    def __init__(
        self,
        user_embedder: UserEmbedder,
        user_index: FAISSIndex,
        db_session
    )

    def recommend(
        self,
        user_id: int,
        top_k_users: int = 20,
        top_n_menus: int = 5,
        exclude_visited: bool = True,
        min_satisfaction: float = 4.0
    ) -> list[dict]:
        """
        1. 타겟 사용자 임베딩 조회
        2. FAISS 로 top-k 유사 사용자 검색
        3. 유사 사용자들의 high-rating (≥ min_satisfaction) 메뉴 수집
        4. 타겟이 이미 먹은 메뉴 제외 (exclude_visited)
        5. 빈도 × 유사도 가중 점수
        6. Top-N 반환

        반환: [
            {
                "menu": "닭가슴살 샐러드",
                "restaurant": "○○샐러드",
                "score": 0.87,
                "similar_user_count": 8,
                "reason": "비슷한 취향 사용자 8명이 고평가"
            },
            ...
        ]
        """

    def cold_start_recommend(
        self,
        onboarding_text: str,
        top_n: int = 5
    ) -> list[dict]:
        """신규 사용자: 온보딩 텍스트 → 임시 임베딩 → 추천"""
```

### 8.6 평가 및 베이스라인 비교

Claude Code 프롬프트:

```
nlp_research/models/embedding_cf/evaluate.py 작성.

평가 방식: Leave-One-Out
1. 각 사용자의 가장 최근 식사를 test 로 제외
2. 나머지로 추천 생성
3. 실제 다음 식사가 Top-K 추천에 포함되는지 확인

지표:
- Hit@5, Hit@10
- NDCG@10
- Coverage (추천된 전체 메뉴 수 / 전체 메뉴 수)
- Diversity (추천 내 카테고리 다양성)

베이스라인 비교:
- Random
- Popular (전체 평균 평점)
- User-User CF (전통 방식)
- Content-Based (메뉴 영양 유사도)
- Embedding CF (ours)

report/embedding_cf_eval.md 에 결과 테이블 저장.

목표:
- NDCG@10 ≥ 0.45 (Popular 베이스라인 0.21 대비 2배+)
- Coverage ≥ 0.60 (롱테일 메뉴도 추천)
```

---

## 9. Step 5 — Before/After 벤치마크 및 통합

### 9.1 통합 벤치마크 스크립트

Claude Code 프롬프트:

```
nlp_research/evaluation/benchmark.py 작성.

전체 파이프라인 벤치마크:

1. A1 vs A2 (감성분석)
   - 동일 리뷰셋
   - A1: zero-shot 단일 감성
   - A2: 속성별 감성
   - 정확도, 속성 분리 능력, 속도

2. B1 vs B2 (메뉴 이해)
   - B1: 규칙 + 임베딩 매칭
   - B2: Food NER 기반 속성 추출
   - 매칭률, 알레르겐 추출 성능

3. D3 vs D1+D2 (NLU)
   - D3: Ollama RAG
   - D1+D2: JointBERT + 템플릿
   - Intent 정확도, Slot F1, 응답속도

4. D5 vs E1 (추천)
   - D5: NLG 일반 리포트
   - E1: 임베딩 CF 개인화
   - NDCG, 만족도

5. 사용자 만족도 설문 (MVP vs 심화)
   - 동일 유저풀에 10개 점심 추천
   - Likert 5점 척도
   - t-test 유의성 검증

출력: report/final_benchmark.md
  - 모듈별 표
  - 모든 p-value
  - 결론 및 한계점
```

### 9.2 MVP 통합 및 A/B 라우팅

Claude Code 프롬프트:

```
nlp_research/serving/ab_test.py 작성.

FastAPI 라우터 확장:
- 동일 엔드포인트 (/nlp/sentiment, /nlp/chatbot/chat 등)
- 쿼리 파라미터 ?version=mvp|research
- 로그 기록: 어느 버전이 호출되었는지
- 응답 시간 측정

middleware/ab_logger.py:
- 모든 요청을 ab_test_logs 테이블에 기록
- 컬럼: request_id, endpoint, version, latency_ms, timestamp, user_id

대시보드 통합:
- React 설정 패널에 "NLP 버전" 토글 추가
- 기본: MVP, 고급 사용자: Research
- 내부 A/B 테스트 모드: 50/50 랜덤 분기
```

### 9.3 ONNX 변환 및 서빙 최적화

Claude Code 프롬프트:

```
nlp_research/serving/export_onnx.py 작성.

모델별 ONNX 변환:
- A2 ABSA
- B2 Food NER
- D1+D2 JointBERT
- E1 Sentence-BERT

def export_model_to_onnx(
    model: nn.Module,
    dummy_input: torch.Tensor,
    output_path: str,
    opset_version: int = 14
)

검증:
- ONNX 출력과 PyTorch 출력 수치 차이 < 1e-4
- ONNX Runtime 추론 속도 비교

기대 효과:
- 추론 속도 1.5~3배 향상
- 메모리 사용량 30% 감소
- CPU 전용 배포 가능
```

---

## 10. Step 6 — 논문/포트폴리오 산출물

### 10.1 논문 초안

Claude Code 프롬프트:

```
nlp_research/report/paper_draft.md 에 논문 초안 작성.

구성 (IEEE 스타일):
1. Title:
   "Multi-Task NLP Pipeline for Data-Driven Lunch Recommendation:
    A Korean-Language Case Study"

2. Abstract (250 words)
   - 문제: 직장인 점심 의사결정 피로
   - 방법: Mini + NLP 5모듈
   - 결과: MVP 대비 F1 +X%, 속도 +Y배
   - 의의: 한국어 도메인 특화 NLP 스택

3. Introduction
   - 배경: 의사결정 피로 연구 (0README 인용)
   - 관련 연구: ABSA, Food NER, Intent/Slot, CF
   - 기여점 4가지

4. Method
   - 4.1 시스템 아키텍처
   - 4.2 ABSA (BERT-SPC)
   - 4.3 Food NER (KoELECTRA + CRF)
   - 4.4 JointBERT (Intent + Slot)
   - 4.5 Embedding-based CF

5. Experiments
   - 5.1 Dataset
   - 5.2 Baselines
   - 5.3 Metrics
   - 5.4 Hyperparameters

6. Results
   - Table 1: 모듈별 성능
   - Table 2: 속도 비교
   - Figure: Confusion matrix, Ablation study

7. Discussion
   - 한계점
   - Future work

8. Conclusion
9. References

report/figures/ 에 필요한 그림 생성 요청.
```

### 10.2 포트폴리오 리포지토리

Claude Code 프롬프트:

```
Mini 루트에 포트폴리오용 README 섹션 추가.

nlp_research/README.md 작성:
- 프로젝트 스크린샷 (대시보드, 챗봇 데모)
- 벤치마크 결과 요약 (차트 포함)
- 모델 카드 (Hugging Face 스타일)
  · 각 모델의 input/output spec
  · 학습 데이터 설명
  · 성능 지표
  · 사용 예시 코드
- Reproducibility 가이드
  · 환경 세팅
  · 데이터 다운로드
  · 학습 스크립트 실행
  · 평가 재현

Hugging Face Hub 업로드 (선택):
- nlp_research/scripts/push_to_hub.py 작성
- A2, B2, D1+D2 모델을 각각 업로드
- 모델 카드 자동 생성
```

### 10.3 블로그 포스트 (선택)

Claude Code 프롬프트:

```
nlp_research/report/blog_post.md 작성.

"4주 MVP 에서 10주 연구로: Mini NLP 레이어 구축기"

섹션:
1. 프로젝트 배경
2. 왜 MVP 후 연구형으로 확장했나
3. 5개 모듈 심화 과정
4. 가장 어려웠던 부분 (에러 분석 솔직하게)
5. 결과 및 배운 점
6. 다음 도전 과제

미디엄·벨로그·개인 블로그에 그대로 게시 가능한 형식.
마크다운 + 이미지 + 코드블록.
```

---

## 11. 트러블슈팅 가이드

### 11.1 GPU / 학습 이슈

| 증상 | 원인 | 해결 |
|------|------|------|
| `CUDA out of memory` | 배치 크기 과다 | `batch_size=8` 축소, gradient accumulation 사용 |
| 학습 loss 발산 | learning rate 과다 | `lr=1e-5` 로 낮춤, warmup 비율 0.2로 증가 |
| 학습 loss 수렴 안함 | 데이터 라벨 노이즈 | 수동 재검토, 신뢰도 낮은 샘플 제거 |
| val F1 정체 | 모델 용량 부족 | 더 큰 백본(KoELECTRA-base → large) |

### 11.2 ABSA (A2) 이슈

| 증상 | 원인 | 해결 |
|------|------|------|
| 특정 aspect 만 저조 | 클래스 불균형 | class_weight 또는 focal loss |
| "중립" 과다 예측 | 라벨 애매 | 라벨링 가이드 재검토, 중립 케이스 명확화 |
| 혼합 감성 포착 실패 | 모델 구조 한계 | Aspect-aware attention 추가 |

### 11.3 Food NER (B2) 이슈

| 증상 | 원인 | 해결 |
|------|------|------|
| 긴 엔티티 경계 오류 | 토크나이저 분리 | Subword 처리 강화 (B-/I- 규칙 엄격화) |
| 복합 엔티티 ("돼지고기 찜") | 중첩 모호성 | 라벨링 가이드에 우선순위 명시 |
| ALLERGEN recall 낮음 | 희소 클래스 | oversampling, 알레르겐 사전 증강 |

### 11.4 JointBERT (D1+D2) 이슈

| 증상 | 원인 | 해결 |
|------|------|------|
| Intent 는 높은데 Slot F1 낮음 | loss weight 균형 | `slot_weight: 2.0` 로 증가 |
| 짧은 발화 오분류 | 데이터 편향 | 짧은 발화 oversampling |
| Ollama 보다 정확도 낮음 | 데이터 양 부족 | GPT 증강 추가 2,000건 |

### 11.5 임베딩 CF (E1) 이슈

| 증상 | 원인 | 해결 |
|------|------|------|
| Cold Start 추천 부정확 | 온보딩 텍스트 짧음 | 필수 질문 5개 이상 유도 |
| 추천 다양성 부족 | 인기 메뉴 편중 | Diversity 패널티 추가 (MMR) |
| 동일 사용자군 반복 | FAISS top-k 낮음 | top-k 를 20→50 증가 |

### 11.6 Before/After 통계 검정

| 증상 | 원인 | 해결 |
|------|------|------|
| p-value > 0.05 | 샘플 수 부족 | 사용자 100명+ 확보 |
| 효과 크기 작음 | 모듈 개별 평가 | 통합 end-to-end 지표 측정 |

---

## 12. 체크리스트

### 12.1 Step 1 — A2 ABSA

- [ ] 라벨링 가이드 작성 + 예시 20건
- [ ] Label Studio ABSA 프로젝트 세팅
- [ ] 500건 수동 라벨링
- [ ] Label Studio → HF Dataset 변환
- [ ] 8:1:1 stratified 분할
- [ ] BERT-SPC 모델 구현
- [ ] W&B 연동 학습 완료
- [ ] Macro F1 ≥ 0.80 달성
- [ ] 에러 분석 리포트 작성
- [ ] A1 vs A2 비교 리포트

### 12.2 Step 2 — B2 Food NER

- [ ] 13개 태그 정의 · 라벨링 가이드
- [ ] Label Studio NER 프로젝트 세팅
- [ ] 1,000건 BIO 라벨링
- [ ] KoELECTRA + CRF 모델 구현
- [ ] 학습 및 seqeval 평가
- [ ] Entity F1 ≥ 0.78 달성
- [ ] ALLERGEN recall ≥ 0.90
- [ ] 알레르기 필터 Mini 통합

### 12.3 Step 3 — D1 + D2 JointBERT

- [ ] 5 Intent × 50 seed 발화 작성
- [ ] GPT 증강으로 2,000건 확장
- [ ] Slot BIO 자동 태깅 + 수동 검토
- [ ] JointBERT 모델 구현
- [ ] 학습 · Joint Accuracy ≥ 0.85
- [ ] Ollama 대비 벤치마크 (속도 + 정확도)
- [ ] ChatBOT 통합 (A/B 모드)

### 12.4 Step 4 — E1 Embedding CF

- [ ] UserEmbedder 구현
- [ ] MenuEmbedder 구현
- [ ] FAISS 인덱스 빌드
- [ ] Recommender 클래스
- [ ] Cold Start 지원
- [ ] Leave-One-Out 평가
- [ ] NDCG@10 ≥ 0.45 달성
- [ ] Popular·User-CF·Content-CF 베이스라인 비교

### 12.5 Step 5 — 통합·벤치마크

- [ ] 전체 벤치마크 스크립트 작성
- [ ] A/B 라우팅 FastAPI 구현
- [ ] ONNX 변환 완료 (4개 모델)
- [ ] 사용자 만족도 설문 (100명+)
- [ ] t-test 유의성 검증

### 12.6 Step 6 — 산출물

- [ ] 논문 초안 (IEEE 스타일)
- [ ] nlp_research/README.md (포트폴리오)
- [ ] Hugging Face Hub 모델 업로드
- [ ] 블로그 포스트 초안
- [ ] 최종 리포지토리 정리 · 태그

---

## 13. 마무리 및 발전 방향

### 13.1 달성한 역량 증명

본 시나리오 완료 시 다음을 포트폴리오로 제시할 수 있습니다:

| 역량 | 증거 |
|------|------|
| **데이터 수집·라벨링** | 3,500건 직접 라벨링 + Label Studio 운용 |
| **모델 파인튜닝** | BERT-SPC / KoELECTRA+CRF / JointBERT 3종 |
| **NLP 전반** | 분류·NER·NLU·임베딩·추천 |
| **실험 설계** | W&B 추적, 베이스라인 비교, A/B 테스트 |
| **논문 작성** | IEEE 스타일 초안, 정량·정성 분석 |
| **배포** | ONNX 변환, FastAPI 서빙, Hugging Face Hub |
| **한국어 특화** | KcELECTRA, KoELECTRA, ko-sroberta 활용 |

### 13.2 추가 발전 가능성

시나리오 2 완료 후 더 확장할 수 있는 방향:

1. **Phase 7 — 멀티모달 확장**
   - 음식 사진 → 메뉴 인식 (CLIP, BLIP-2)
   - 영수증 OCR → 자동 meal_history 입력

2. **Phase 8 — 강화학습**
   - 사용자 피드백 기반 RLHF
   - Multi-armed bandit 추천

3. **Phase 9 — 한국어 특화 대규모 학습**
   - 도메인 적응 (Domain Adaptation)
   - 자체 BERT 계열 사전학습 (food-domain corpus)

4. **Phase 10 — 실서비스 배포**
   - Kubernetes 오케스트레이션
   - Redis 캐싱
   - Prometheus 모니터링

### 13.3 한계점 명시 (논문용)

솔직한 한계 기술도 포트폴리오의 일부입니다:

- **데이터 규모:** 3,500건은 일반 연구 대비 적음 (크라우드소싱 미활용)
- **사용자 평가:** 100명 규모는 통계적으로 작음
- **도메인 제약:** 한식 중심, 타 문화권 미포함
- **실시간성:** 배치 기반이라 즉시 반영 한계
- **Cold Start:** 온보딩 설문 의존

---

## 📎 부록

### A. 참고 문헌 (논문용)

| 주제 | 논문 / 자료 |
|------|------------|
| ABSA | Sun et al. (2019) "Utilizing BERT for Aspect-Based Sentiment Analysis" |
| KoELECTRA | Park (2020) "KoELECTRA: Pretrained ELECTRA Model for Korean" |
| KcELECTRA | Lee (2021) "KcELECTRA: Korean Comments ELECTRA" |
| JointBERT | Chen et al. (2019) "BERT for Joint Intent Classification and Slot Filling" |
| Sentence-BERT | Reimers & Gurevych (2019) "Sentence-BERT" |
| FAISS | Johnson et al. (2019) "Billion-scale similarity search with GPUs" |
| Food NER | 안 외 (2020) "한국어 음식 리뷰 개체명 인식" |
| Decision Fatigue | Pignatiello et al. (2020) — (이미 0README 에 인용) |

### B. 데이터셋 출처

| 데이터셋 | 용도 | 링크 |
|---------|------|------|
| KLUE | Intent/Slot 사전학습 참고 | https://klue-benchmark.com/ |
| AI-Hub 한국어 음식 리뷰 | ABSA/NER 보조 | https://aihub.or.kr/ |
| NSMC | 감성분석 사전 평가 | https://github.com/e9t/nsmc |
| KorEDA | 데이터 증강 | https://github.com/catSirup/KorEDA |

### C. 폴더 구조 최종본

```
Mini/
├── 0README.md
├── README.md
├── lunch-optimizer-dashboard.jsx
├── api/
├── GUIDE/                              # 기존 4 서브토픽
├── ChatBOT/                            # 기존 챗봇 5 단계
└── NLP/
    ├── README.md                       # NLP 진입점
    ├── GUIDE_NLP_MVP_SCENARIO3.md      # 시나리오 3 (MVP, 4주)
    ├── GUIDE_NLP_RESEARCH_SCENARIO2.md # 시나리오 2 (연구, 10주) ← 본 문서
    ├── nlp_mvp/                        # 시나리오 3 구현물 (완료)
    └── nlp_research/                   # 시나리오 2 구현물 (본 문서의 산출물)
        ├── data/
        ├── models/
        │   ├── absa/
        │   ├── food_ner/
        │   ├── joint_bert/
        │   └── embedding_cf/
        ├── training/
        ├── evaluation/
        ├── serving/
        ├── checkpoints/                # .gitignore
        ├── notebooks/
        └── report/
            ├── paper_draft.md
            ├── benchmark_results.md
            └── figures/
```

### D. 실험 재현 명령어 요약

```bash
# 데이터 준비
python -m nlp_research.training.convert_labelstudio \
    --task absa --input data/labeled/absa

# A2 학습
python -m nlp_research.models.absa.train \
    --config configs/absa.yaml

# B2 학습
python -m nlp_research.models.food_ner.train \
    --config configs/food_ner.yaml

# D1+D2 학습
python -m nlp_research.models.joint_bert.train \
    --config configs/joint_bert.yaml

# E1 인덱스 빌드
python -m nlp_research.models.embedding_cf.index build

# 전체 벤치마크
python -m nlp_research.evaluation.benchmark

# ONNX 변환
python -m nlp_research.serving.export_onnx --all

# A/B 서빙 시작
uvicorn nlp_research.serving.fastapi_server:app --port 8002
```

---

**문서 버전:** v1.0
**작성일:** 2026-04-07
**대상:** Claude Code 기반 구현 (시나리오 3 완료자 전용)
**예상 소요 기간:** 10주 (1인 + GPU 기준)
**선행 문서:** [`GUIDE_NLP_MVP_SCENARIO3.md`](./GUIDE_NLP_MVP_SCENARIO3.md)
**관련 문서:** [`README.md`](./README.md) (NLP 레이어 진입점)

---

<div align="center">

**🔬 MVP 를 넘어, 연구와 학습으로.**

*Mini × NLP Research — From Production to Publication.*

</div>
