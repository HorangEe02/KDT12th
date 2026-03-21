# 시나리오 D: Severstal 메인 + NEU-DET 교차 검증 — 상세 구현 계획

## 1. 프로젝트 재구성 개요

### 기존 구조 (Before)
```
NEU-DET 1,800장 (결함만 6종)
  ├── Phase 1: OpenCV 전처리 → 특징 추출 → ML 6종 분류
  ├── Phase 2: DL 6종 분류 (CNN, ResNet-18)
  └── Phase 3: 이상탐지 (정상 데이터 별도 구축 → AE/IF/OCSVM)
```

### 새로운 구조 (After — 시나리오 D)
```
Severstal 12,568장 (정상 5,902 + 비정상 6,666)
  ├── Stage 1: 정상 vs 비정상 이진 분류
  │     ├── ML (SVM, RF, XGB, LGBM, Ensemble, MLP, KNN)
  │     ├── DL (Custom CNN, ResNet-18)
  │     └── 이상탐지 (AE, IF, OCSVM)
  │
  └── Stage 2: 비정상 → 4종 결함 세부 분류
        ├── ML (동일 7종 모델)
        └── DL (Custom CNN, ResNet-18)

NEU-DET 1,800장 (결함만 6종) → 교차 검증
  ├── 검증①: NEU 전체 → Stage 1 투입 → Recall 측정
  └── 검증②: NEU 6종 독립 분류 → 동일 모델 아키텍처 성능 비교
```

---

## 2. 데이터 현황 및 전처리 전략

### 2.1 Severstal Steel Defect Detection

| 항목 | 값 |
|------|-----|
| 위치 | `data/Severstal_Steel Defect Detection/` |
| 전체 이미지 | 12,568장 |
| 정상 (Normal) | 5,902장 (47.0%) — CSV에 미등록 |
| 비정상 (Abnormal) | 6,666장 (53.0%) — CSV에 등록 |
| 이미지 크기 | 256 × 1,600 × 3 (BGR, 와이드 스트립) |
| 라벨 형식 | train.csv — ImageId, ClassId(1~4), EncodedPixels(RLE) |

### ClassId별 분포 및 직관적 명칭 (방안 C: 하이브리드)

| ClassId | 영문명 | 한글명 | 약어 | 이미지 수 | 결함 면적 비율 | 형태 특징 |
|---------|--------|--------|------|----------|--------------|----------|
| 1 | Pitting Spot | 점상 결함 | PS | 897장 | 0.92% (소형) | 균일 덩어리, 밝기 +18 |
| 2 | Linear Scratch | 선형 긁힘 | LS | 247장 | 0.79% (소형) | 세로 선형(W/H=0.14), 밝기 +64 |
| 3 | Surface Stain | 표면 변색 | SS | 5,150장 | 9.06% (대형) | 가로 넓은 영역, 밝기 +17 |
| 4 | Rolling Dent | 압연 압흔 | RD | 801장 | 9.71% (대형) | 가로 넓은 영역, 밝기 -8 |

> ⚠️ Severstal은 ClassId 1~4의 공식 명칭을 공개하지 않았으며, 위 명칭은 결함 영역의
> 형태적 특징(면적, 가로세로비, 밝기 차이)을 통계적으로 분석하여 부여한 것임.

### 결함 조합 분포

| 조합 | 이미지 수 | 비율 |
|------|----------|------|
| 단일 결함 | 6,239장 | 93.6% |
| 다중 결함 | 427장 | 6.4% |

→ **다중 결함 이미지(427장) 처리 전략**: 가장 큰 면적의 결함 ClassId를 대표 라벨로 사용

### 2.2 이미지 전처리 전략

Severstal 이미지는 256×1600 와이드 스트립 → 모델 입력 형식으로 변환 필요

#### 방법: 슬라이딩 윈도우 크롭 + 리사이즈

```
원본: 256 × 1600
  ↓ 256×256 윈도우로 크롭 (stride=128, 50% 오버랩, 12패치/이미지)
  ↓ 결함 마스크와 교차 확인 → 결함 포함 패치 = 해당 ClassId, 결함 미포함 = normal
  ↓ 224×224 리사이즈 (ResNet-18 입력) 또는 200×200 (ML 파이프라인)
```

**크롭 후 예상 데이터량:**
- 정상 이미지 5,902 × ~12패치 = ~70,000+ 정상 패치
- 비정상 이미지 → 결함 포함 패치만 추출 = ~30,233 결함 패치 (PS 2,638 + LS 457 + SS 23,408 + RD 3,730)

→ **데이터 불균형 해결**: 정상 패치를 서브샘플링하여 비정상과 균형 맞춤

#### 대안: 전체 이미지 리사이즈 (단순 방식)

```
원본: 256 × 1600 → 리사이즈: 256 × 256 (가로 압축)
  또는
원본: 256 × 1600 → 중앙 크롭: 256 × 256
```

→ **추천: 슬라이딩 윈도우 크롭** (결함 위치 정보 보존, 데이터 증강 효과)

### 2.3 NEU-DET (교차 검증용)

| 항목 | 값 |
|------|-----|
| 위치 | `data/NEU-DET/` |
| 전체 이미지 | 1,800장 |
| 클래스 | 6종 (Cr, In, Pa, PS, RS, Sc) × 300장 |
| 이미지 크기 | 200 × 200, 그레이스케일 |
| 역할 | Stage 1 교차 검증 + 독립 6종 분류 실험 |

---

## 3. 구현 단계 (30단계)

### Stage 0: 데이터 파이프라인 구축 — 3개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 0-1 | `utils/severstal_loader.py` | SeverstalDataLoader 클래스 (CSV 파싱, RLE 디코딩, 크롭, 정상/비정상 분리) | **신규** |
| 0-2 | `utils/severstal_preprocessor.py` | 256×1600 → 256×256 슬라이딩 크롭, 결함 매핑, 패치 저장 | **신규** |
| 0-3 | `utils/data_loader.py` | NEUDataLoader 유지 (교차 검증용) | 유지 |

### Stage 1A: 정상 vs 비정상 ML 분류 — 4개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 1A-1 | `models/train_binary.py` | 이진 분류(정상/비정상) ML 학습 (7종 모델) | **신규** |
| 1A-2 | `models/evaluate.py` | 이진 분류용 평가 함수 추가 (ROC, PR Curve) | 수정 |
| 1A-3 | `features/feature_pipeline.py` | Severstal 패치 크기 대응 (256×256) | 수정 |
| 1A-4 | `notebooks/07_severstal_binary_ml.ipynb` | Stage 1 ML 실험 노트북 | **신규** |

### Stage 1B: 정상 vs 비정상 DL 분류 — 3개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 1B-1 | `deep_learning/datasets_severstal.py` | Severstal PyTorch Dataset (이진 분류) | **신규** |
| 1B-2 | `deep_learning/train_dl.py` | num_classes=2 실험 추가 | 수정 |
| 1B-3 | `notebooks/08_severstal_binary_dl.ipynb` | Stage 1 DL 실험 노트북 | **신규** |

### Stage 1C: 정상 vs 비정상 이상탐지 — 3개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 1C-1 | `anomaly_detection/datasets_severstal_ad.py` | Severstal 정상 데이터 로더 (이상탐지용) | **신규** |
| 1C-2 | `anomaly_detection/train_ad.py` | Severstal 이상탐지 학습 함수 추가 | 수정 |
| 1C-3 | `notebooks/09_severstal_anomaly.ipynb` | Stage 1 이상탐지 실험 노트북 | **신규** |

### Stage 2: 비정상 → 4종 결함 분류 — 4개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 2-1 | `models/train_defect4.py` | 4종 결함 ML 분류 학습 | **신규** |
| 2-2 | `deep_learning/train_dl_defect4.py` | 4종 결함 DL 분류 학습 | **신규** |
| 2-3 | `anomaly_detection/two_stage_pipeline.py` | Severstal 기반 2단계 파이프라인 재구성 | 수정 |
| 2-4 | `notebooks/10_severstal_defect_classification.ipynb` | Stage 2 실험 노트북 | **신규** |

### Stage 3: NEU-DET 교차 검증 — 3개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 3-1 | `validation/cross_domain_validation.py` | NEU→Stage 1 교차 검증 (Recall 측정) | **신규** |
| 3-2 | `validation/neu_independent_classification.py` | NEU 6종 독립 분류 (동일 모델 아키텍처) | **신규** |
| 3-3 | `notebooks/11_cross_domain_validation.ipynb` | 교차 검증 실험 노트북 | **신규** |

### Stage 4: 통합 비교 분석 — 2개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 4-1 | `validation/comparison_analysis.py` | Phase별 성능 통합 비교표 생성 | **신규** |
| 4-2 | `notebooks/12_final_comparison.ipynb` | 최종 비교 분석 노트북 | **신규** |

### Stage 5: Streamlit 대시보드 재구성 — 5개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 5-1 | `streamlit/app.py` | 8탭 체제로 리팩토링 | **대폭 수정** |
| 5-2 | `streamlit/tabs/tab_severstal_binary.py` | Stage 1 정상/비정상 분류 탭 | **신규** |
| 5-3 | `streamlit/tabs/tab_severstal_defect.py` | Stage 2 결함 4종 분류 탭 | **신규** |
| 5-4 | `streamlit/tabs/tab_cross_validation.py` | NEU 교차 검증 결과 탭 | **신규** |
| 5-5 | `streamlit/tabs/tab_comparison.py` | 통합 비교 탭 업데이트 | 수정 |

### Stage 6: 보고서 및 문서 업데이트 — 4개 파일

| # | 파일 | 작업 | 신규/수정 |
|---|------|------|----------|
| 6-1 | `md/final_report.md` | 최종 보고서 v5.0 (시나리오 D 반영) | 수정 |
| 6-2 | `md/subtopic_05_report.md` | 소주제 5 보고서 업데이트 | 수정 |
| 6-3 | `README.md` | 프로젝트 README 업데이트 | 수정 |
| 6-4 | `md/brainstorming_scenario_d.md` | 본 문서 (계획서) | **신규** (현재 파일) |

---

## 4. 핵심 데이터 흐름도

```
[Severstal 12,568장]
     │
     ├── 정상 5,902장 ──────────────────────────────────────────┐
     │                                                          │
     ├── 비정상 6,666장 ───┐                                     │
     │    ├── ClassId 1 (PS: 점상 결함) 897장                    │
     │    ├── ClassId 2 (LS: 선형 긁힘) 247장                    │
     │    ├── ClassId 3 (SS: 표면 변색) 5,150장                  │
     │    └── ClassId 4 (RD: 압연 압흔) 801장                    │
     │                     │                                     │
     ▼                     ▼                                     ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │  256×1600 → 슬라이딩 윈도우 크롭 (256×256) → 패치 생성         │
 │  결함 마스크 교차 → 정상 패치 / 결함 패치 분리                   │
 └─────────────────────────────────────────────────────────────────┘
     │                     │
     ▼                     ▼
 ┌──────────┐      ┌──────────────┐
 │ 정상 패치  │      │ 결함 패치     │
 │ ~70,000+  │      │ ~15,000~20,000│
 └────┬─────┘      └──────┬───────┘
      │                    │
      ▼                    ▼
 ═══════════════════════════════════════
 ║  Stage 1: 정상 vs 비정상 이진 분류     ║
 ║  ├── ML: SVM, RF, XGB, LGBM, ...    ║
 ║  ├── DL: CNN, ResNet-18              ║
 ║  └── AD: AE, IF, OCSVM              ║
 ═══════════════════════════════════════
                   │
                   │ "비정상" 판정된 이미지
                   ▼
 ═══════════════════════════════════════
 ║  Stage 2: 4종 결함 세부 분류           ║
 ║  ├── ML: 특징 추출 + 7종 분류기       ║
 ║  └── DL: ResNet-18 Fine-tune         ║
 ║                                       ║
 ║  PS(점상) / LS(선형) / SS(변색) / RD(압흔) ║
 ═══════════════════════════════════════
                   │
                   ▼
 ┌─────────────────────────────────────┐
 │  교차 검증: NEU-DET 1,800장 투입      │
 │                                     │
 │  검증①: NEU → Stage 1               │
 │    → 1,800장 모두 "비정상" 탐지?     │
 │    → Recall 측정                     │
 │                                     │
 │  검증②: NEU 6종 독립 분류             │
 │    → 동일 모델 아키텍처 적용           │
 │    → Severstal vs NEU 성능 비교       │
 └─────────────────────────────────────┘
                   │
                   ▼
 ┌─────────────────────────────────────┐
 │  최종 통합 비교 분석                   │
 │  + Streamlit 8탭 대시보드             │
 │  + 보고서 업데이트                     │
 └─────────────────────────────────────┘
```

---

## 5. 새 디렉토리 구조

```
Phase9/
├── utils/                       # MODIFIED
│   ├── data_loader.py           # 유지 (NEU 교차 검증용)
│   ├── severstal_loader.py      # NEW — SeverstalDataLoader
│   ├── severstal_preprocessor.py # NEW — 크롭/전처리
│   └── filter_utils.py          # 유지
├── preprocessing/               # 유지 (OpenCV 전처리 파이프라인)
├── features/                    # MODIFIED
│   └── feature_pipeline.py      # 256×256 대응 추가
├── models/                      # MODIFIED
│   ├── train.py                 # 유지 (기존 NEU 실험 보존)
│   ├── train_binary.py          # NEW — Stage 1 ML 이진 분류
│   ├── train_defect4.py         # NEW — Stage 2 ML 4종 분류
│   ├── evaluate.py              # 수정 (이진 분류 평가 추가)
│   └── inference.py             # 수정
├── deep_learning/               # MODIFIED
│   ├── datasets.py              # 유지 (NEU용)
│   ├── datasets_severstal.py    # NEW — Severstal PyTorch Dataset
│   ├── train_dl.py              # 수정 (Severstal 실험 추가)
│   ├── train_dl_defect4.py      # NEW — Stage 2 DL 4종 분류
│   └── models/                  # 유지 (num_classes 파라미터화)
├── anomaly_detection/           # MODIFIED
│   ├── datasets_severstal_ad.py # NEW — Severstal 이상탐지 데이터
│   ├── train_ad.py              # 수정 (Severstal 학습 추가)
│   ├── two_stage_pipeline.py    # 수정 (Severstal 2단계 파이프라인)
│   └── models/                  # 유지
├── validation/                  # NEW — 교차 검증 모듈
│   ├── __init__.py
│   ├── cross_domain_validation.py    # NEU → Stage 1 교차 검증
│   ├── neu_independent_classification.py  # NEU 6종 독립 분류
│   └── comparison_analysis.py        # 통합 비교 분석
├── notebooks/                   # MODIFIED (+6 NEW)
│   ├── 01~06 기존 유지
│   ├── 07_severstal_binary_ml.ipynb          # NEW
│   ├── 08_severstal_binary_dl.ipynb          # NEW
│   ├── 09_severstal_anomaly.ipynb            # NEW
│   ├── 10_severstal_defect_classification.ipynb  # NEW
│   ├── 11_cross_domain_validation.ipynb      # NEW
│   └── 12_final_comparison.ipynb             # NEW
├── streamlit/                   # MODIFIED
│   ├── app.py                   # 8탭 체제
│   └── tabs/
│       ├── tab_deep_learning.py         # 유지
│       ├── tab_anomaly_detection.py     # 유지
│       ├── tab_severstal_binary.py      # NEW
│       ├── tab_severstal_defect.py      # NEW
│       ├── tab_cross_validation.py      # NEW
│       └── tab_comparison.py            # 수정
├── outputs/
│   ├── models_severstal/        # NEW — Severstal 학습 모델
│   │   ├── binary_ml/           # Stage 1 ML 모델
│   │   ├── binary_dl/           # Stage 1 DL 모델
│   │   ├── defect4_ml/          # Stage 2 ML 모델
│   │   ├── defect4_dl/          # Stage 2 DL 모델
│   │   └── anomaly/             # 이상탐지 모델
│   ├── models_dl/               # 유지 (기존 NEU 모델)
│   ├── models_ad/               # 유지 (기존 NEU 모델)
│   └── figures/
│       └── severstal/           # NEW — Severstal 시각화
├── data/
│   ├── NEU-DET/                 # 유지
│   ├── Severstal_Steel Defect Detection/  # 유지
│   └── severstal_patches/       # NEW — 크롭된 패치
│       ├── normal/
│       └── defect/
│           ├── class_1_PS/
│           ├── class_2_LS/
│           ├── class_3_SS/
│           └── class_4_RD/
└── md/
    └── brainstorming_scenario_d.md  # NEW (본 문서)
```

---

## 6. 기존 코드 재사용 매핑

| 새 모듈 | 재사용할 기존 코드 | 재사용율 |
|---------|-------------------|---------|
| `utils/severstal_loader.py` | `utils/data_loader.py` → 클래스 구조 패턴 | 30% |
| `models/train_binary.py` | `models/train.py` → get_models(), train_single_model() | 80% |
| `models/train_defect4.py` | `models/train.py` → 동일 구조, 클래스 수만 변경 | 80% |
| `deep_learning/datasets_severstal.py` | `deep_learning/datasets.py` → Dataset 패턴 | 50% |
| `deep_learning/train_dl_defect4.py` | `deep_learning/train_dl.py` → 학습 루프 | 70% |
| `anomaly_detection/datasets_severstal_ad.py` | `anomaly_detection/datasets_normal_patches.py` | 40% |
| `validation/cross_domain_validation.py` | `models/evaluate.py` → 평가 함수 | 60% |

---

## 7. 기대 성과 및 보고서 스토리라인

### 기승전결 구조

| 단계 | 내용 |
|------|------|
| **기 (도입)** | Severstal 철강 결함 데이터에서 ClassId 1~4는 공식 명칭이 없다. 형태적 특징(면적, 가로세로비, 밝기)을 통계 분석하여 점상 결함(PS), 선형 긁힘(LS), 표면 변색(SS), 압연 압흔(RD)으로 명명하였다. |
| **승 (전개)** | 2단계 파이프라인을 구축했다. Stage 1에서 정상/비정상을 ML·DL·이상탐지 3가지 접근법으로 분류하고, Stage 2에서 비정상 이미지의 결함 유형을 4종으로 세분류했다. |
| **전 (절정)** | 모델의 범용성을 검증하기 위해 NEU-DET(결함만 1,800장)를 Stage 1에 투입했다. X%가 비정상으로 정확히 탐지되어 교차 도메인 일반화 능력을 입증했다. 동시에 NEU 6종 독립 분류 실험에서 동일 모델 아키텍처가 Y% 정확도를 달성했다. |
| **결 (결론)** | 단일 모델이 서로 다른 출처의 철강 결함을 탐지할 수 있음을 확인했다. 다만 Z%의 성능 차이는 도메인 적응(Domain Adaptation)의 필요성을 시사하며, 실무 배포 시 파인튜닝 전략이 필요하다. |

### 기대 성능 범위

| 실험 | 모델 | 기대 성능 |
|------|------|----------|
| Stage 1 ML (이진) | VotingEnsemble | Accuracy 73.00% (AUC 0.7916) |
| Stage 1 DL (이진) | ResNet-18 FT | Accuracy 90.87~92.19% |
| Stage 1 AD | Autoencoder | AUROC 0.7023, Recall 96.0%, F1 0.7442 |
| Stage 2 ML (4종) | LightGBM | Accuracy 77.72% |
| Stage 2 DL (4종) | ResNet-18 FT | Accuracy 86.01% |
| NEU 교차 검증 | Stage 1 모델 | ML Recall 51.6%, DL Recall 14.4% |
| 도메인 갭 | ResNet-18 | -76.47%p (90.87% → 14.4%) |

---

## 8. 구현 순서 및 우선순위

### Phase 1: 데이터 준비 (Stage 0)
1. `severstal_loader.py` — CSV 파싱, RLE 디코딩
2. `severstal_preprocessor.py` — 패치 크롭 및 저장
3. 데이터 EDA 노트북

### Phase 2: Stage 1 구현 (ML → DL → AD 순)
4. 이진 ML 분류
5. 이진 DL 분류
6. 이상탐지

### Phase 3: Stage 2 구현
7. 4종 ML 분류
8. 4종 DL 분류
9. 2단계 파이프라인 통합

### Phase 4: 교차 검증
10. NEU → Stage 1 Recall 측정
11. NEU 6종 독립 분류
12. 통합 비교 분석

### Phase 5: 대시보드 및 보고서
13. Streamlit 8탭 재구성
14. 보고서 업데이트

---

## 9. 검증 방법

1. **Stage 0**: `python -m utils.severstal_preprocessor` → 패치 생성 확인
2. **Stage 1**: 노트북 07~09 실행 → 이진 분류 결과표 출력
3. **Stage 2**: 노트북 10 실행 → 4종 분류 결과표 출력
4. **교차 검증**: 노트북 11 실행 → NEU Recall + 독립 분류 결과
5. **통합 비교**: 노트북 12 실행 → 최종 비교 차트 출력
6. **Streamlit**: `streamlit run streamlit/app.py` → 8탭 정상 렌더링
