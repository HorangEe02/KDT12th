# 소주제 2 — 일일 판매량 예측 수정/보완 결과

> **분석 유형:** Regression
> **노트북:** `02_Avg_Daily_Sales_Prediction.ipynb` (67 → 84 cells, +17)
> **수정일:** 2026-03-13
> **담당:** 이현아

---

## 수정/보완 완료 항목

| # | 항목 | 상태 | 결과 요약 |
|---|------|:----:|-----------|
| 1 | 잔존 누수 검증 (QOH+RP+SS 조합) | ✅ | R²=0.7830 < 0.85 → 간접 누수 없음 |
| 2 | RandomizedSearchCV (자동 탐색 50회) | ✅ | XGB R²=0.9659, RF R²=0.9290 → 수동 튜닝 검증 |
| 3 | Tuned 모델 5-Fold CV | ✅ | XGB Tuned CV R²=0.9458±0.0110 |
| 4 | Tuned 모델 Learning Curve | ✅ | 모든 Tuned 모델 수렴 확인 |
| 5 | 고판매량 구간 분석 | ✅ | 4구간 RMSE/MAE/Bias 정량 분석 |
| 6 | SHAP Dependence Plot + 3중 교차검증 | ✅ | 상호작용 패턴 + 3방법 1위 일치 |
| 7 | 예측 오차 비대칭 분석 | ✅ | 과대 60.5% vs 과소 39.5% |
| 8 | 결론 업데이트 | ✅ | 수정/보완 버전으로 갱신 |

---

## 핵심 결과

### 1. 잔존 누수 검증

**개별 피처 예측력:**

| 피처 | 단독 R² | 해석 |
|------|:-------:|------|
| Order_Frequency_per_month | **0.8205** | 가장 높은 단독 예측력 |
| Quantity_On_Hand | 0.6771 | 중간 수준 |
| Reorder_Point | 0.4968 | 중간 이하 |

**조합 피처 예측력:**

| 조합 | R² | 판정 |
|------|:--:|:----:|
| QOH + RP + Safety_Stock | 0.7830 | ✅ 정상 (< 0.85) |
| Order_Frequency + QOH | 0.8737 | ⚠️ 주의 (단독 예측력 합산) |

**판정:** QOH+RP+SS 조합 R²=0.7830 < 0.85 → **간접 누수 없음.** Order_Frequency+QOH 조합(0.8737)은 Order_Frequency 단독(0.8205)의 강한 예측력이 주 원인.

### 2. RandomizedSearchCV

| 모델 | 수동 튜닝 R² | RandomSearch R² | ΔR² |
|------|:------------:|:---------------:|:---:|
| XGBoost | 0.9477 | **0.9659** | +0.0183 |
| Random Forest | 0.9045 | **0.9290** | +0.0245 |

> RandomizedSearchCV가 소폭 향상. 수동 튜닝의 방향성 올바름을 확인. 최종 모델은 해석 가능성을 위해 수동 튜닝 기반 유지.

### 3. Tuned 5-Fold CV

| 모델 | Train R² | Val R² (±SD) | Gap |
|------|:--------:|:------------:|:---:|
| Linear Regression | 0.9083 | 0.8995 ± 0.0123 | 0.0087 |
| RF (Tuned) | 0.9570 | 0.9059 ± 0.0200 | 0.0512 |
| **XGB (Tuned)** | 0.9923 | **0.9458 ± 0.0110** | 0.0465 |

### 4. 고판매량 구간 분석

| 구간 | N | RMSE | MAE | Bias | 해석 |
|------|:-:|:----:|:---:|:----:|------|
| 저판매 (0~20) | 109 | 2.78 | 2.08 | -0.82 | 정확 |
| 중판매 (20~40) | 53 | 3.81 | 3.08 | -0.33 | 양호 |
| 고판매 (40~70) | 28 | 8.74 | 7.15 | -2.03 | 과소예측 |
| 초고판매 (70+) | 10 | 9.13 | 7.39 | +6.94 | 과대예측 전환 |

### 5. 예측 오차 비대칭

| 유형 | 건수 | 평균 오차 | 비즈니스 영향 |
|------|:----:|:---------:|--------------|
| 과대 예측 (실제 < 예측) | 121건 (60.5%) | -3.13 | 재고 과다/폐기 위험 |
| 과소 예측 (실제 > 예측) | 79건 (39.5%) | +3.61 | 판매 기회 손실 |
| 정확 예측 (\|오차\| < 2) | 86건 (43.0%) | — | 안정 구간 |

### 6. Feature Importance 3중 교차검증

| 순위 | Impurity | Permutation | SHAP |
|:----:|----------|-------------|------|
| 1 | **Order_Frequency** | **Order_Frequency** | **Order_Frequency** |
| 2 | Quantity_On_Hand | Reorder_Point | Reorder_Point |
| 3 | Category_Beverages | Lead_Time_Days | Quantity_On_Hand |

> **3개 방법 모두 Order_Frequency 1위** → 방법론에 무관한 일관성. Permutation과 SHAP 유사, Impurity 편향(Category_Beverages 과대평가) 확인.

---

## 추가된 인사이트 (+7개)

| # | 인사이트 | 출처 |
|---|---------|------|
| 1 | 잔존 누수 없음 (QOH+RP+SS R²=0.7830) | 잔존 누수 검증 |
| 2 | RandomizedSearchCV XGB R²=0.9659 | RandomizedSearchCV |
| 3 | XGB Tuned CV R²=0.9458±0.0110 | Tuned CV |
| 4 | 고판매 구간 과소예측 (Bias=-2.03) | 구간 분석 |
| 5 | 초고판매 구간 과대예측 전환 (Bias=+6.94) | 구간 분석 |
| 6 | 예측 오차 비대칭 (과대 60.5% vs 과소 39.5%) | 오차 비대칭 |
| 7 | 3중 교차검증 1위 일치 (Order_Frequency) | 3중 교차검증 |

---

## 추가된 시각화 (+5종)

| # | 시각화 | 파일명 |
|---|--------|--------|
| 1 | 잔존 누수 검증 | `leakage_residual_verification_s2.png` |
| 2 | Tuned Learning Curve | `learning_curve_tuned_s2.png` |
| 3 | SHAP Dependence Plot | `shap_dependence_s2.png` |
| 4 | Feature Importance 3중 교차검증 | `feature_importance_triple_comparison_s2.png` |
| 5 | 고판매량 구간 분석 | `high_sales_segment_analysis_s2.png` |
