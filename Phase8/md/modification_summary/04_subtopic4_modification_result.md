# 소주제 4 — 최적 발주 전략 군집화 수정/보완 결과

> **분석 유형:** Regression (Phase A) + K-Means (Phase B) + EOQ Simulation (Phase C)
> **노트북:** `04_Reorder_Strategy_Clustering.ipynb` (77 → 90 cells, +13)
> **수정 대상:** Phase A만 (Phase B·C는 비지도/시뮬레이션이므로 해당 항목 없음)
> **수정일:** 2026-03-13

---

## 수정/보완 완료 항목

| # | 항목 | 상태 | 결과 요약 |
|---|------|:----:|-----------|
| 1 | 잔존 누수 추가 검증 (S5 피처 조합) | ✅ | max combo R²=0.0615 < 0.85 → 간접 누수 없음 |
| 2 | RandomizedSearchCV (RF & XGB) | ✅ | RF Δ=+0.0014, XGB Δ=-0.0058 → Grid 결과 신뢰 |
| 3 | Tuned 모델 5-Fold CV | ✅ | XGB Val R²=0.4176±0.0407, LR Gap=0.0332 안정 |
| 4 | Tuned 모델 Learning Curve | ✅ | Default LC와 패턴 일치 |
| 5 | SHAP Dependence Plot | ✅ | 상위 4개 피처 상호작용 시각화 |
| 6 | Feature Importance 3중 교차검증 | ✅ | 공통 Top3 = {ABC_Class_C, Reorder_Urgency} |
| 7 | 결론 업데이트 | ✅ | 인사이트 8→13개, 산출물 21→25종 |

---

## 소주제 4 특수 사항

| 항목 | 소주제 1~3 | 소주제 4 |
|------|-----------|----------|
| 분석 구조 | 단일 Phase | 3-Phase (A: 회귀 + B: 클러스터링 + C: EOQ) |
| 수정 대상 | 전체 | **Phase A만** |
| 타겟 변수 | 분류/회귀 | **DOI (회귀)** — R² 기준 |
| 누수 진단 | 비교적 단순 | **5-Scenario 진단 완료** (S1~S5) |
| 누수 검증 기준 | Acc > 0.95 | **R² > 0.85** |

---

## 핵심 결과

### 1. 잔존 누수 검증

**단일 피처 검증:**

| 피처 | R² | 판정 |
|------|:--:|:----:|
| Reorder_Urgency | 0.0896 | ✅ |
| Safety_Stock | 0.0202 | ✅ |
| 나머지 9개 | < 0 (음수) | ✅ |

**조합 피처 검증:**

| 조합 | R² | 판정 |
|------|:--:|:----:|
| Reorder_Urgency + Supply_Risk | 0.0615 | ✅ |
| Reorder_Point + Safety_Stock | -0.0470 | ✅ |
| Unit_Cost_USD + Lead_Time_Days | -0.1403 | ✅ |

**판정:** 최대 조합 R² = 0.0615 ≪ 0.85 → **S5 피처셋에 간접 누수 없음.** 단일 피처 최대도 0.0896으로 DOI 재구성 불가.

### 2. RandomizedSearchCV

| 모델 | Grid R² | Random R² | Δ | 판정 |
|------|:-------:|:---------:|:--:|:----:|
| RF | 0.3710 | 0.3725 | +0.0014 | ✅ 유사 |
| XGB | 0.4218 | 0.4161 | -0.0058 | ✅ 유사 |

> Grid vs Random 차이 미미 → GridSearchCV 결과 신뢰. XGB Grid(0.4218) > Random(0.4161)이므로 기존 결과 유지.

### 3. Tuned 5-Fold CV

| 모델 | Train R² | Val R² (±std) | Gap | 판정 |
|------|:--------:|:-------------:|:---:|:----:|
| LR | 0.3709 | 0.3377 ± 0.0428 | 0.0332 | ✅ 안정 |
| RF Tuned | 0.8732 | 0.4011 ± 0.0523 | 0.4721 | ⚠️ 과적합 |
| XGB Tuned | 0.7437 | 0.4176 ± 0.0407 | 0.3261 | ⚠️ 과적합 |

> RF·XGB 과적합 경향은 트리 기반 특성상 불가피하나, Val R² 기준 XGB Tuned(0.4176)가 최우수.

### 4. Tuned Learning Curve

| 모델 | Train R² | Val R² | Gap |
|------|:--------:|:------:|:---:|
| LR | 0.3709 | 0.3377 | 0.0332 |
| RF Tuned | 0.8732 | 0.4011 | 0.4721 |
| XGB Tuned | 0.7437 | 0.4176 | 0.3261 |

> Default LC와 Tuned LC 패턴 일치 — 정규화 적용 후에도 트리 과적합 경향 유지.

### 5. SHAP Dependence Plot

| Rank | 피처 | SHAP 특성 |
|:----:|------|-----------|
| 1 | ABC_Class_C | C등급 여부에 따라 SHAP 값 이분화 |
| 2 | Unit_Cost_USD | 단가 증가 시 SHAP 값 양(+) 방향 |
| 3 | Reorder_Urgency | 긴급도 높을수록 SHAP 값 증가 |
| 4 | Lead_Time_Days | 리드타임 증가 시 약한 양(+) |

### 6. Feature Importance 3중 교차검증

| 순위 | Impurity | Permutation | SHAP |
|:----:|----------|-------------|------|
| 1 | Reorder_Urgency | ABC_Class_C | ABC_Class_C |
| 2 | ABC_Class_C | Unit_Cost_USD | Unit_Cost_USD |
| 3 | Lead_Time_Days | Reorder_Urgency | Reorder_Urgency |

> **공통 Top3 = {ABC_Class_C, Reorder_Urgency}** → 일관성 ✅ 높음. Impurity는 Reorder_Urgency를 1위로 과대평가 (편향 확인).

---

## 추가된 인사이트 (+5개)

| # | 인사이트 | 출처 |
|---|---------|------|
| 1 | S5 피처셋 간접 누수 없음 (max R²=0.0615) | 잔존 누수 검증 |
| 2 | Grid vs Random Δ ≤ 0.006 → Grid 신뢰 | RandomizedSearchCV |
| 3 | XGB Tuned Val R²=0.4176, LR 안정 (Gap=0.0332) | Tuned CV |
| 4 | ABC_Class_C 이분화, 비선형 상호작용 확인 | SHAP Dependence |
| 5 | 공통 Top3 = {ABC_Class_C, Reorder_Urgency} | 3중 교차검증 |

---

## 추가된 시각화 (+4종)

| # | 시각화 | 파일명 |
|---|--------|--------|
| 1 | 잔존 누수 검증 | `leakage_residual_verification_s4.png` |
| 2 | Tuned Learning Curve | `learning_curve_tuned_s4.png` |
| 3 | SHAP Dependence Plot | `shap_dependence_s4.png` |
| 4 | Feature Importance 3중 교차검증 | `feature_importance_triple_comparison_s4.png` |
