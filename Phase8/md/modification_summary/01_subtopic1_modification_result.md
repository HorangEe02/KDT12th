# 소주제 1 — 재고 상태 분류 수정/보완 결과

> **분석 유형:** Multi-class Classification
> **노트북:** `01_Inventory_Status_Classification.ipynb` (67 → 86 cells, +19)
> **수정일:** 2026-03-13
> **담당:** 정이랑

---

## 수정/보완 완료 항목

| # | 항목 | 상태 | 결과 요약 |
|---|------|:----:|-----------|
| 1 | 잔존 누수 추가 검증 | ✅ | RP+QOH 조합 → 2-피처 Acc=0.606 → 잔존 누수 없음 |
| 2 | SHAP 분석 도입 | ✅ | Global/Per-class/Waterfall 분석, 3중 교차검증 |
| 3 | Tuned 모델 Learning Curve | ✅ | 4개 Tuned 모델 학습 곡선 생성 |
| 4 | RandomizedSearchCV (자동 탐색 50회) | ✅ | 수동 튜닝과 동일 결과 (LightGBM F1=0.9879) |
| 5 | Tuned 5-Fold 교차검증 | ✅ | Default vs Tuned CV Gap 비교 완료 |
| 6 | ROC-AUC 분석 | ✅ | One-vs-Rest Macro AUC = 0.9997 |
| 7 | 비용 민감 학습 | ✅ | class_weight 적용 → 성능 변화 없음 (이미 최적) |

---

## 핵심 결과

### 1. 잔존 누수 검증

| 검증 항목 | 결과 | 해석 |
|-----------|------|------|
| RP > QOH ↔ Low Stock 대응률 | 97.94% | 규칙적 대응 존재 |
| RP+QOH 2-피처 DecisionTree Acc | 0.606 | 분류력 부족 |
| RP 단독 DecisionTree Acc | 0.535 | 약한 분류력 |
| QOH 단독 DecisionTree Acc | 0.465 | 분류력 없음 |

**판정:** Stock_Gap = RP - QOH의 "차이값" 계산이 핵심 누수 메커니즘이었으며, RP와 QOH가 개별적으로는 이를 재현 불가. **잔존 누수 없음.**

### 2. RandomizedSearchCV

- LightGBM: RandomizedSearchCV F1 = 0.9879 → 수동 튜닝과 동일
- XGBoost: RandomizedSearchCV F1 = 0.9820 → 수동 튜닝과 동일
- **수동 튜닝이 최적점에 도달해 있음을 검증**

### 3. Tuned 5-Fold CV

| 모델 | Default CV Gap | Tuned CV Gap | 판정 |
|------|:--------------:|:------------:|:----:|
| Logistic Regression | 0.0197 | — | 안정 |
| Random Forest | 0.0537 | 개선 (Gap 감소) | 개선 |
| XGBoost | 0.0350 | 개선 (Gap 감소) | 개선 |
| LightGBM | 0.0262 | 소폭 증가 | 미세 |

### 4. ROC-AUC

- One-vs-Rest Macro AUC = **0.9997** → 거의 완벽한 분류 경계

### 5. 비용 민감 학습

- class_weight 적용 후 성능 변화 없음 → 이미 98~99% 수준에서 추가 개선 여지 없음

### 6. Feature Importance 3중 교차검증

- **Lead_Time_Days가 3개 방법 모두에서 진정한 핵심 피처**로 확인
- SHAP Waterfall Plot으로 2건의 오분류 원인 분석 완료

---

## 추가된 인사이트 (+5개)

| # | 인사이트 | 출처 |
|---|---------|------|
| 1 | 잔존 누수 없음 확인 (RP+QOH Acc=0.606) | 잔존 누수 검증 |
| 2 | RandomizedSearchCV 결과 수동 튜닝과 동일 | RandomizedSearchCV |
| 3 | 3단계 과적합 검증 체계 확립 (Tuned 포함) | Tuned CV + LC |
| 4 | ROC-AUC = 0.9997 | ROC-AUC 분석 |
| 5 | 비용 민감 학습 한계 확인 | 비용 민감 학습 |

---

## 추가된 시각화 (+5종)

| # | 시각화 | 파일명 |
|---|--------|--------|
| 1 | 잔존 누수 검증 | `leakage_residual_verification_s1.png` |
| 2 | Tuned Learning Curve | `learning_curve_tuned_s1.png` |
| 3 | SHAP Dependence Plot | `shap_dependence_s1.png` |
| 4 | Feature Importance 3중 교차검증 | `feature_importance_triple_comparison_s1.png` |
| 5 | ROC-AUC Curve | `roc_auc_s1.png` |
