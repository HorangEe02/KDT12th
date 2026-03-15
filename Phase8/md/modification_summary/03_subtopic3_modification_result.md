# 소주제 3 — 폐기 위험도 예측 수정/보완 결과

> **분석 유형:** Binary Classification (Waste_Risk)
> **노트북:** `03_Waste_Risk_Prediction.ipynb` (82 → 97 cells, +15)
> **수정일:** 2026-03-13
> **담당:** 박준영

---

## 수정/보완 완료 항목

| # | 항목 | 상태 | 결과 요약 |
|---|------|:----:|-----------|
| 1 | 잔존 누수 검증 | ✅ | max combo Acc=0.7150 < 0.95 → 간접 누수 없음 |
| 2 | RandomizedSearchCV (XGB & SVM) | ✅ | Grid vs Random Δ=0.0000 → 완전 일치 |
| 3 | Tuned 5-Fold CV | ✅ | 전 모델 Gap ≤ 0.0007 → 매우 안정 |
| 4 | Tuned Learning Curve | ✅ | LR/SVM Gap≈0, XGB Gap=0.0007 |
| 5 | 부패성 카테고리 내부 분석 | ✅ | 428행, Safe=3 (0.7%), Bakery/Fresh/Seafood 100% Risk |
| 6 | SHAP Dependence Plot | ✅ | 상위 4개 피처 상호작용 시각화 |
| 7 | Feature Importance 3중 교차검증 | ✅ | 공통 Top3 = {Days_To_Expiry, FIFO_FEFO_encoded} |

---

## 핵심 결과

### 1. 잔존 누수 검증

**단일 피처 검증:**

| 피처 | Accuracy | 판정 |
|------|:--------:|:----:|
| DTE (Days_To_Expiry) | 0.9900 | ⚠️ 구조적 (누수 아닌 도메인 특성) |
| FIFO_FEFO_encoded | 0.5250 | ✅ |
| 나머지 | < 0.55 | ✅ |

**조합 피처 검증:**

| 조합 | Accuracy | 판정 |
|------|:--------:|:----:|
| 최대 조합 | 0.7150 | ✅ (< 0.95) |

**판정:** DTE 단독 Acc=0.99는 도메인 특성(유통기한이 폐기와 직결). 다피처 조합 max=0.7150 < 0.95 → **간접 누수 없음.**

### 2. RandomizedSearchCV

| 모델 | Grid F1 | Random F1 | Δ |
|------|:-------:|:---------:|:-:|
| XGBoost | 0.9884 | 0.9884 | 0.0000 |
| SVM (RBF) | 0.9884 | 0.9884 | 0.0000 |

> Grid와 Random 결과가 **완전 일치** → GridSearchCV가 최적점을 정확히 찾음.

### 3. Tuned 5-Fold CV

| 모델 | Train Score | Val Score | Gap | 판정 |
|------|:-----------:|:---------:|:---:|:----:|
| LR | ~1.0 | ~1.0 | ≤ 0.0007 | ✅ 매우 안정 |
| SVM (RBF) | ~1.0 | ~1.0 | ≤ 0.0007 | ✅ 매우 안정 |
| XGBoost | ~1.0 | ~1.0 | ≤ 0.0007 | ✅ 매우 안정 |

> 전 모델 Gap ≤ 0.0007 → 99%+ 정확도에서 과적합 징후 없음.

### 4. Tuned Learning Curve

| 모델 | Train Score | Val Score | Gap |
|------|:-----------:|:---------:|:---:|
| LR | ~1.0 | ~1.0 | -0.0000 |
| SVM | ~1.0 | ~1.0 | -0.0000 |
| XGB | ~1.0 | ~1.0 | 0.0007 |

### 5. 부패성 카테고리 내부 분석

| 카테고리 | 총 수 | Risk | Safe | Risk 비율 |
|----------|:-----:|:----:|:----:|:---------:|
| Bakery | 87 | 87 | 0 | 100.0% |
| Fresh Produce | 94 | 94 | 0 | 100.0% |
| Seafood | 60 | 60 | 0 | 100.0% |
| Meat | 93 | 92 | 1 | 98.9% |
| Dairy | 94 | 92 | 2 | 97.9% |
| **합계** | **428** | **425** | **3** | **99.3%** |

> Safe 3건(0.7%)은 Meat 1건 + Dairy 2건. 부패성 카테고리 내부 미세 차이 분석 완료.

### 6. Feature Importance 3중 교차검증

| 순위 | Impurity | Permutation | SHAP |
|:----:|----------|-------------|------|
| 1 | Days_To_Expiry | Days_To_Expiry | Days_To_Expiry |
| 2 | FIFO_FEFO_encoded | FIFO_FEFO_encoded | FIFO_FEFO_encoded |
| 3 | Unit_Cost_USD | Stock_Age_Days | Unit_Cost_USD |

> **공통 Top3 = {Days_To_Expiry, FIFO_FEFO_encoded}** → 3개 방법론 모두 일치. 일관성 ✅ 높음.

---

## 추가된 인사이트 (+5개)

| # | 인사이트 | 출처 |
|---|---------|------|
| 1 | 잔존 누수 없음 (max combo Acc=0.7150) | 잔존 누수 검증 |
| 2 | Grid vs Random 완전 일치 (Δ=0.0000) | RandomizedSearchCV |
| 3 | 전 모델 Gap ≤ 0.0007 (매우 안정) | Tuned CV |
| 4 | 부패성 내부 Safe 3/428=0.7% | 부패성 분석 |
| 5 | 공통 Top3 = {DTE, FIFO_FEFO} | 3중 교차검증 |

---

## 추가된 시각화 (+5종)

| # | 시각화 | 파일명 |
|---|--------|--------|
| 1 | 잔존 누수 검증 | `leakage_residual_verification_s3.png` |
| 2 | Tuned Learning Curve | `learning_curve_tuned_s3.png` |
| 3 | 부패성 카테고리 내부 분석 | `perishable_internal_analysis_s3.png` |
| 4 | SHAP Dependence Plot | `shap_dependence_s3.png` |
| 5 | Feature Importance 3중 교차검증 | `feature_importance_triple_comparison_s3.png` |
