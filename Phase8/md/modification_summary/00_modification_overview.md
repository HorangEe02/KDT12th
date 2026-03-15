# Phase8_mini 수정/보완 총괄 보고서

> **작업일:** 2026-03-13
> **범위:** 소주제 1~4 전체 (추가 데이터 없이 분석 방법론 개선)
> **원본 데이터:** Kaggle E-Grocery (1,000행 × 37열, 인도네시아 로케일)

---

## 1. 수정/보완 배경

Phase8_mini 프로젝트의 4개 소주제에 대해 초판(V5) 분석 완료 후, 결과 보고서에서 도출된 한계점 및 향후 보완 사항을 기반으로 **추가 데이터 없이 방법론만 개선**하는 수정/보완 작업을 수행하였다.

### 공통 수정 항목 (7개)

| # | 항목 | 목적 | 적용 범위 |
|---|------|------|-----------|
| 1 | 잔존 누수 추가 검증 | 채택 피처셋의 간접 누수 여부 재확인 | 전 소주제 |
| 2 | RandomizedSearchCV | GridSearchCV 결과 신뢰성 교차 검증 | 전 소주제 |
| 3 | Tuned 5-Fold CV | 튜닝 모델 일반화 성능 정량 검증 | 전 소주제 |
| 4 | Tuned Learning Curve | 과적합 경향 시각적 확인 | 전 소주제 |
| 5 | SHAP Dependence Plot | 핵심 피처 상호작용 시각화 | 전 소주제 |
| 6 | Feature Importance 3중 교차검증 | Impurity/Permutation/SHAP 일관성 | 전 소주제 |
| 7 | 결론 업데이트 | 새 분석 결과를 결론에 반영 | 전 소주제 |

### 소주제별 도메인 특화 항목

| 소주제 | 추가 항목 |
|--------|-----------|
| 1 (재고 상태 분류) | ROC-AUC 분석, 비용 민감 학습 |
| 2 (판매량 예측) | 고판매량 구간 분석, 예측 오차 비대칭 분석 |
| 3 (폐기 위험도) | 부패성 카테고리 내부 분석 |
| 4 (발주 전략) | Phase A만 대상 (Phase B·C는 비지도/시뮬레이션) |

---

## 2. 정량 변화 요약

### 노트북 셀 수 변화

| 소주제 | 변경 전 | 변경 후 | 증감 |
|--------|:-------:|:-------:|:----:|
| 1. 재고 상태 분류 | 67 | 86 | +19 |
| 2. 일일 판매량 예측 | 67 | 84 | +17 |
| 3. 폐기 위험도 예측 | 82 | 97 | +15 |
| 4. 재주문 전략 군집화 | 77 | 90 | +13 |
| **합계** | **293** | **357** | **+64** |

### 시각화 산출물 변화

| 소주제 | 신규 시각화 | 주요 추가 항목 |
|--------|:----------:|---------------|
| 1 | +5종 | Tuned LC, SHAP Dependence, Triple Comparison 등 |
| 2 | +5종 | Tuned LC, SHAP Dependence, Triple Comparison, 고판매량 분석 등 |
| 3 | +5종 | Tuned LC, SHAP Dependence, Triple Comparison, 부패성 분석 등 |
| 4 | +4종 | Tuned LC, SHAP Dependence, Triple Comparison, 잔존 누수 검증 |
| **합계** | **+19종** | |

### 인사이트 변화

| 소주제 | 변경 전 | 변경 후 | 증감 |
|--------|:-------:|:-------:|:----:|
| 1. 재고 상태 분류 | 8 | 13 | +5 |
| 2. 일일 판매량 예측 | 6 | 13 | +7 |
| 3. 폐기 위험도 예측 | 8 | 13 | +5 |
| 4. 재주문 전략 군집화 | 8 | 13 | +5 |
| **합계** | **30** | **52** | **+22** |

---

## 3. 산출물 목록

### 가이드라인 (4개)

| 파일 | 설명 |
|------|------|
| `md/subtopic1_modification_guideline.md` | 소주제 1 수정 가이드라인 |
| `md/subtopic2_modification_guideline.md` | 소주제 2 수정 가이드라인 |
| `md/subtopic3_modification_guideline.md` | 소주제 3 수정 가이드라인 |
| `md/subtopic4_modification_guideline.md` | 소주제 4 수정 가이드라인 |

### 수정된 노트북 (4개)

| 파일 | 셀 수 | 백업 |
|------|:-----:|------|
| `notebooks/01_Inventory_Status_Classification.ipynb` | 86 | `*_backup.ipynb` |
| `notebooks/02_Avg_Daily_Sales_Prediction.ipynb` | 84 | `*_backup.ipynb` |
| `notebooks/03_Waste_Risk_Prediction.ipynb` | 97 | `*_backup.ipynb` |
| `notebooks/04_Reorder_Strategy_Clustering.ipynb` | 90 | `*_backup.ipynb` |

### 업데이트된 보고서 (4개)

| 파일 | 주요 변경 |
|------|-----------|
| `md/result_report/subtopic1_report.md` | 인사이트 +5, 수정/보완 완료 항목 추가 |
| `md/result_report/subtopic2_report.md` | 인사이트 +7, 수정/보완 완료 항목 추가 |
| `md/result_report/subtopic3_report.md` | 인사이트 +5, 수정/보완 완료 항목 추가 |
| `md/result_report/subtopic4_report.md` | 인사이트 +5, 수정/보완 완료 항목 추가 |

### 수정/보완 총괄 문서 (본 폴더)

| 파일 | 설명 |
|------|------|
| `00_modification_overview.md` | 전체 총괄 보고서 (본 문서) |
| `01_subtopic1_modification_result.md` | 소주제 1 수정 결과 상세 |
| `02_subtopic2_modification_result.md` | 소주제 2 수정 결과 상세 |
| `03_subtopic3_modification_result.md` | 소주제 3 수정 결과 상세 |
| `04_subtopic4_modification_result.md` | 소주제 4 수정 결과 상세 |

---

## 4. 폴더 구조

```
Phase8_mini/
├── notebooks/
│   ├── 01_Inventory_Status_Classification.ipynb        (86 cells, 수정 완료)
│   ├── 01_Inventory_Status_Classification_backup.ipynb  (67 cells, 원본)
│   ├── 02_Avg_Daily_Sales_Prediction.ipynb             (84 cells, 수정 완료)
│   ├── 02_Avg_Daily_Sales_Prediction_backup.ipynb      (67 cells, 원본)
│   ├── 03_Waste_Risk_Prediction.ipynb                  (97 cells, 수정 완료)
│   ├── 03_Waste_Risk_Prediction_backup.ipynb           (82 cells, 원본)
│   ├── 04_Reorder_Strategy_Clustering.ipynb            (90 cells, 수정 완료)
│   └── 04_Reorder_Strategy_Clustering_backup.ipynb     (77 cells, 원본)
├── md/
│   ├── subtopic1_modification_guideline.md
│   ├── subtopic2_modification_guideline.md
│   ├── subtopic3_modification_guideline.md
│   ├── subtopic4_modification_guideline.md
│   ├── result_report/
│   │   ├── subtopic1_report.md  (업데이트 완료)
│   │   ├── subtopic2_report.md  (업데이트 완료)
│   │   ├── subtopic3_report.md  (업데이트 완료)
│   │   └── subtopic4_report.md  (업데이트 완료)
│   └── modification_summary/   ← 본 폴더
│       ├── 00_modification_overview.md
│       ├── 01_subtopic1_modification_result.md
│       ├── 02_subtopic2_modification_result.md
│       ├── 03_subtopic3_modification_result.md
│       └── 04_subtopic4_modification_result.md
└── outputs/figures/
    ├── subtopic1_inventory_status/  (16종)
    ├── subtopic2_daily_sales/       (기존)
    ├── subtopic3_waste_risk/        (21종, +5 신규)
    ├── subtopic4_reorder_clustering/(17종)
    ├── *_s1.png, *_s2.png, *_s3.png, *_s4.png (parent dir)
    └── 신규 시각화 총 +19종
```
