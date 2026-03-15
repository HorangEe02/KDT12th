# 소주제 3 — 폐기 위험도 예측 수정/보완 가이드라인

> **대상 노트북:** `notebooks/03_Waste_Risk_Prediction.ipynb` (82셀)
> **작성일:** 2026-03-13
> **목표:** 데이터 추가 없이 기존 1,000행 데이터에서 방법론 보완

---

## 현재 분석 현황

| 항목 | 현재 상태 |
|------|-----------|
| 잔존 누수 검증 | DOI 제거 완료, QOH+RP+SS 조합 미검증 |
| RandomizedSearchCV | 미수행 (GridSearchCV만 수행) |
| Tuned 5-Fold CV | 미수행 (Default CV만 수행) |
| Tuned Learning Curve | 미수행 (Default LC만 수행) |
| SHAP Dependence Plot | 미수행 (Summary만 수행) |
| Feature Importance 3중 교차검증 | 미수행 (Impurity vs Permutation만) |
| 부패성 카테고리 내부 미세 분석 | 미수행 |
| 결론 | 기본 버전 |

## 소주제 3 특수성

- **모든 모델 ~99% 정확도**: 카테고리-유통기한 이분법 구조 때문
- **Recall(Risk) = 1.0000**: 개선 여지가 거의 없음
- **DTE 지배적**: 다른 피처의 중요도가 매우 낮음
- **핵심 관점 전환**: 성능 개선보다 **검증 심화**와 **구조적 이해 강화**에 초점

---

## 수정 항목 (7개)

### 항목 1: 잔존 누수 검증 — 재고 관련 피처 조합 (분류 버전)

**위치:** 셀 39 이후 (Train/Test Split 이후)
**우선순위:** 높음

DOI 제거 후에도 QOH+재고 피처 조합이 타겟을 재구성할 수 있는지 확인한다.
분류 문제이므로 R² 대신 **Accuracy**로 평가한다.

```python
# ========================================
# 5.4 잔존 누수 검증 — 재고 관련 피처 조합
# ========================================
from sklearn.tree import DecisionTreeClassifier

print("=" * 60)
print("5.4 잔존 누수 검증 — 재고 관련 피처 조합")
print("=" * 60)

# (A) 개별 피처 예측력 테스트
single_features = ['Quantity_On_Hand', 'Reorder_Point', 'Safety_Stock',
                   'Order_Frequency_per_month', 'Lead_Time_Days', 'Unit_Cost_USD',
                   'Stock_Age_Days', 'Avg_Daily_Sales', 'Days_To_Expiry']
single_results_leak = {}
for feat in single_features:
    if feat in feature_names:
        feat_idx = feature_names.index(feat)
        dt = DecisionTreeClassifier(max_depth=3, random_state=SEED)
        dt.fit(X_train_scaled[:, feat_idx].reshape(-1, 1), y_train)
        acc = dt.score(X_test_scaled[:, feat_idx].reshape(-1, 1), y_test)
        single_results_leak[feat] = acc
        print(f"  {feat:35s} → Accuracy = {acc:.4f}")

# (B) 재고 관련 2~3 피처 조합
combo_features = [
    ['Quantity_On_Hand', 'Reorder_Point'],
    ['Quantity_On_Hand', 'Safety_Stock'],
    ['Quantity_On_Hand', 'Reorder_Point', 'Safety_Stock'],
    ['Quantity_On_Hand', 'Avg_Daily_Sales'],
    ['Stock_Age_Days', 'Avg_Daily_Sales'],
]
print("\n--- 조합 피처 예측력 ---")
combo_results_leak = {}
for combo in combo_features:
    valid = [f for f in combo if f in feature_names]
    if len(valid) == len(combo):
        idxs = [feature_names.index(f) for f in combo]
        dt = DecisionTreeClassifier(max_depth=5, random_state=SEED)
        dt.fit(X_train_scaled[:, idxs], y_train)
        acc = dt.score(X_test_scaled[:, idxs], y_test)
        combo_name = ' + '.join(combo)
        combo_results_leak[combo_name] = acc
        print(f"  {combo_name:55s} → Accuracy = {acc:.4f}")

print("\n--- 판정 ---")
max_combo_acc = max(combo_results_leak.values()) if combo_results_leak else 0
if max_combo_acc > 0.95:
    print(f"  ⚠️ 최대 조합 Accuracy = {max_combo_acc:.4f} → 간접 누수 의심")
else:
    print(f"  ✅ 최대 조합 Accuracy = {max_combo_acc:.4f} → 간접 누수 없음 (0.95 미만)")
```

시각화:
```python
# 잔존 누수 검증 시각화
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# (A) 단일 피처 Accuracy
ax1 = axes[0]
feats = list(single_results_leak.keys())
accs = list(single_results_leak.values())
colors = ['#e74c3c' if a > 0.95 else '#3498db' for a in accs]
bars = ax1.barh(feats, accs, color=colors)
ax1.axvline(x=0.95, color='red', linestyle='--', alpha=0.7, label='Threshold (0.95)')
ax1.set_xlabel('Accuracy')
ax1.set_title('(A) 단일 피처 — DecisionTree Accuracy')
ax1.legend()

# (B) 조합 피처 Accuracy
ax2 = axes[1]
combos = list(combo_results_leak.keys())
combo_accs = list(combo_results_leak.values())
colors2 = ['#e74c3c' if a > 0.95 else '#2ecc71' for a in combo_accs]
bars2 = ax2.barh(combos, combo_accs, color=colors2)
ax2.axvline(x=0.95, color='red', linestyle='--', alpha=0.7, label='Threshold (0.95)')
ax2.set_xlabel('Accuracy')
ax2.set_title('(B) 조합 피처 — DecisionTree Accuracy')
ax2.legend()

plt.tight_layout()
fig_path = os.path.join('../outputs/figures/subtopic3_waste_risk', 'leakage_residual_verification_s3.png')
os.makedirs(os.path.dirname(fig_path), exist_ok=True)
plt.savefig(fig_path, dpi=150, bbox_inches='tight')
plt.show()
print(f"✅ 저장: leakage_residual_verification_s3.png")
```

---

### 항목 2: RandomizedSearchCV — 자동 하이퍼파라미터 탐색

**위치:** 셀 48 이후 (Tuned 모델 평가 이후)
**우선순위:** 높음

GridSearchCV 결과를 RandomizedSearchCV로 검증한다.

```python
# ========================================
# 7.4.1 RandomizedSearchCV — XGBoost & SVM
# ========================================
from scipy.stats import randint, uniform
from sklearn.model_selection import RandomizedSearchCV

print("=" * 60)
print("7.4.1 RandomizedSearchCV — XGBoost & SVM")
print("=" * 60)

# XGBoost 파라미터 공간
xgb_param_dist = {
    'max_depth': randint(2, 8),
    'learning_rate': uniform(0.01, 0.3),
    'n_estimators': randint(50, 300),
    'subsample': uniform(0.6, 0.4),
    'colsample_bytree': uniform(0.6, 0.4),
    'scale_pos_weight': [spw],
    'random_state': [SEED]
}

xgb_random = RandomizedSearchCV(
    XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
    xgb_param_dist, n_iter=50, cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring='f1', random_state=SEED, n_jobs=-1
)
xgb_random.fit(X_train_scaled, y_train)

# SVM 파라미터 공간
svm_param_dist = {
    'C': uniform(0.1, 100),
    'gamma': uniform(0.001, 1),
    'class_weight': ['balanced'],
    'random_state': [SEED]
}

svm_random = RandomizedSearchCV(
    SVC(kernel='rbf', probability=True),
    svm_param_dist, n_iter=50, cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
    scoring='f1', random_state=SEED, n_jobs=-1
)
svm_random.fit(X_train_scaled, y_train)

# 비교
print("\n--- GridSearch vs RandomizedSearch 비교 ---")
for name, rs_model, gs_model in [
    ('XGBoost', xgb_random.best_estimator_, tuned_results['XGBoost']['model']),
    ('SVM', svm_random.best_estimator_, tuned_results['SVM (RBF)']['model'])
]:
    rs_pred = rs_model.predict(X_test_scaled)
    gs_pred = gs_model.predict(X_test_scaled)
    rs_f1 = f1_score(y_test, rs_pred)
    gs_f1 = f1_score(y_test, gs_pred)
    print(f"\n  {name}:")
    print(f"    GridSearch     → F1={gs_f1:.4f}")
    print(f"    RandomSearch   → F1={rs_f1:.4f}")
    print(f"    결과: {'RandomSearch 우위' if rs_f1 > gs_f1 else 'GridSearch 우위' if gs_f1 > rs_f1 else '동일'} (ΔF1={rs_f1-gs_f1:+.4f})")
```

---

### 항목 3: Tuned 모델 5-Fold CV

**위치:** RandomizedSearchCV 이후
**우선순위:** 중간

```python
# ========================================
# 7.4.2 Tuned 모델 5-Fold CV
# ========================================
from sklearn.model_selection import cross_validate

print("=" * 60)
print("7.4.2 Tuned 모델 5-Fold 교차검증")
print("=" * 60)

cv_strat = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
tuned_cv_results = {}

for name, model in tuned_trained.items():
    cv_res = cross_validate(
        model, X_train_scaled, y_train, cv=cv_strat,
        scoring=['accuracy', 'f1'], return_train_score=True
    )
    tuned_cv_results[name] = cv_res
    train_f1 = cv_res['train_f1'].mean()
    val_f1 = cv_res['test_f1'].mean()
    val_std = cv_res['test_f1'].std()
    gap = train_f1 - val_f1
    print(f"  {name:25s} | Train F1={train_f1:.4f} | Val F1={val_f1:.4f}±{val_std:.4f} | Gap={gap:.4f}")
```

---

### 항목 4: Tuned 모델 Learning Curve

**위치:** Tuned CV 이후
**우선순위:** 중간

```python
# ========================================
# 7.4.3 Tuned 모델 Learning Curve
# ========================================
from sklearn.model_selection import learning_curve

print("=" * 60)
print("7.4.3 Tuned 모델 Learning Curve")
print("=" * 60)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
train_sizes = np.linspace(0.2, 1.0, 8)

for idx, (name, model) in enumerate(tuned_trained.items()):
    train_sz, train_sc, val_sc = learning_curve(
        model, X_train_scaled, y_train,
        train_sizes=train_sizes, cv=cv_strat, scoring='f1',
        random_state=SEED, n_jobs=-1
    )
    ax = axes[idx]
    ax.plot(train_sz, train_sc.mean(axis=1), 'o-', label='Train F1', color='#e74c3c')
    ax.fill_between(train_sz, train_sc.mean(axis=1)-train_sc.std(axis=1),
                     train_sc.mean(axis=1)+train_sc.std(axis=1), alpha=0.1, color='#e74c3c')
    ax.plot(train_sz, val_sc.mean(axis=1), 's-', label='Val F1', color='#3498db')
    ax.fill_between(train_sz, val_sc.mean(axis=1)-val_sc.std(axis=1),
                     val_sc.mean(axis=1)+val_sc.std(axis=1), alpha=0.1, color='#3498db')
    ax.set_title(f'{name} (Tuned)')
    ax.set_xlabel('Training Size')
    ax.set_ylabel('F1 Score')
    ax.legend()
    ax.set_ylim(0.95, 1.01)
    ax.grid(True, alpha=0.3)

plt.suptitle('Tuned 모델 Learning Curve', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join('../outputs/figures/subtopic3_waste_risk', 'learning_curve_tuned_s3.png'),
            dpi=150, bbox_inches='tight')
plt.show()
print("✅ 저장: learning_curve_tuned_s3.png")
```

---

### 항목 5: 부패성 카테고리 내부 미세 분석 ★

**위치:** 심층 분석 섹션 (셀 65 이후)
**우선순위:** 높음 (소주제 3 고유 분석)

99% 정확도 환경에서 추가 인사이트를 얻기 위해, 부패성 카테고리 내부에서 Safe/Risk 경계에 가까운 제품들을 분석한다.

```python
# ========================================
# 8.4.1 부패성 카테고리 내부 미세 분석 ★
# ========================================
print("=" * 60)
print("8.4.1 부패성 카테고리 내부 미세 분석")
print("=" * 60)

perishable = ['Bakery', 'Fresh Produce', 'Seafood', 'Meat', 'Dairy']
df_perish = df[df['Category'].isin(perishable)].copy()

# DTD / RSD 비율 계산 (1에 가까울수록 경계)
df_perish['DTD_RSD_Ratio'] = df_perish['Days_To_Deplete'] / df_perish['Remaining_Shelf_Days'].clip(lower=1)

print(f"\n부패성 카테고리 전체: {len(df_perish)}건")
print(f"  Safe(0): {(df_perish['Waste_Risk']==0).sum()}건")
print(f"  Risk(1): {(df_perish['Waste_Risk']==1).sum()}건")

# 카테고리별 경계 제품 분석
print("\n--- 카테고리별 Safe 제품 분석 ---")
for cat in perishable:
    sub = df_perish[df_perish['Category'] == cat]
    safe_count = (sub['Waste_Risk'] == 0).sum()
    total = len(sub)
    if safe_count > 0:
        safe_sub = sub[sub['Waste_Risk'] == 0]
        print(f"  {cat:15s} | Safe={safe_count}/{total} | ADS 평균={safe_sub['Avg_Daily_Sales'].mean():.1f} | DTD 평균={safe_sub['Days_To_Deplete'].mean():.1f}")
    else:
        print(f"  {cat:15s} | Safe=0/{total} (전부 Risk)")

# DTD/RSD 비율 히스토그램
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# (A) 부패성 카테고리 DTD vs RSD
ax1 = axes[0]
for cat in perishable:
    sub = df_perish[df_perish['Category'] == cat]
    ax1.scatter(sub['Remaining_Shelf_Days'], sub['Days_To_Deplete'],
                label=cat, alpha=0.6, s=30)
max_val = max(df_perish['Remaining_Shelf_Days'].max(), df_perish['Days_To_Deplete'].max())
ax1.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='DTD=RSD (경계)')
ax1.set_xlabel('Remaining_Shelf_Days')
ax1.set_ylabel('Days_To_Deplete')
ax1.set_title('(A) 부패성 카테고리 — DTD vs RSD')
ax1.legend(fontsize=8)

# (B) 비부패성 vs 부패성 DTE 분포
ax2 = axes[1]
non_perish = ['Beverages', 'Frozen', 'Household', 'Pantry', 'Personal Care']
dte_perish = df[df['Category'].isin(perishable)]['Days_To_Expiry']
dte_non = df[df['Category'].isin(non_perish)]['Days_To_Expiry']
ax2.hist(dte_perish, bins=30, alpha=0.7, label=f'부패성 (N={len(dte_perish)})', color='#e74c3c')
ax2.hist(dte_non, bins=30, alpha=0.7, label=f'비부패성 (N={len(dte_non)})', color='#3498db')
ax2.set_xlabel('Days_To_Expiry')
ax2.set_ylabel('Frequency')
ax2.set_title('(B) 부패성 vs 비부패성 DTE 분포')
ax2.legend()

plt.tight_layout()
plt.savefig(os.path.join('../outputs/figures/subtopic3_waste_risk', 'perishable_internal_analysis_s3.png'),
            dpi=150, bbox_inches='tight')
plt.show()
print("✅ 저장: perishable_internal_analysis_s3.png")
```

---

### 항목 6: SHAP Dependence Plot + Feature Importance 3중 교차검증

**위치:** SHAP 분석 이후 (셀 75 이후)
**우선순위:** 중간

```python
# ========================================
# 8.9.1 SHAP Dependence Plot — 핵심 피처 상호작용
# ========================================
print("=" * 60)
print("8.9.1 SHAP Dependence Plot")
print("=" * 60)

top_features = ['Days_To_Expiry', 'Unit_Cost_USD', 'Stock_Age_Days', 'Quantity_On_Hand']
valid_top = [f for f in top_features if f in feature_names]

fig, axes = plt.subplots(1, len(valid_top), figsize=(5*len(valid_top), 5))
if len(valid_top) == 1:
    axes = [axes]

for idx, feat in enumerate(valid_top):
    ax = axes[idx]
    feat_idx_shap = feature_names.index(feat)
    shap.dependence_plot(feat_idx_shap, shap_values, X_test_df,
                         feature_names=feature_names, ax=ax, show=False)
    ax.set_title(feat)

plt.suptitle('SHAP Dependence Plot — 핵심 피처 상호작용', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join('../outputs/figures/subtopic3_waste_risk', 'shap_dependence_s3.png'),
            dpi=150, bbox_inches='tight')
plt.show()
print("✅ 저장: shap_dependence_s3.png")
```

```python
# ========================================
# 8.9.2 Feature Importance 3중 교차검증
# ========================================
print("=" * 60)
print("8.9.2 Feature Importance 3중 교차검증")
print("=" * 60)

# 1. Impurity 기반
imp_importance = xgb_tuned.feature_importances_

# 2. Permutation 기반
perm_importance = perm_result.importances_mean

# 3. SHAP 기반
shap_importance = np.abs(shap_values).mean(axis=0)

# 정규화
def normalize(arr):
    total = arr.sum()
    return arr / total if total > 0 else arr

imp_norm = normalize(imp_importance)
perm_norm = normalize(np.maximum(perm_importance, 0))
shap_norm = normalize(shap_importance)

# 상위 10개 피처
top_n = min(10, len(feature_names))
top_idx = np.argsort(shap_norm)[-top_n:][::-1]

fig, ax = plt.subplots(figsize=(14, 7))
x = np.arange(top_n)
width = 0.25

ax.bar(x - width, imp_norm[top_idx], width, label='Impurity', color='#3498db', alpha=0.8)
ax.bar(x, perm_norm[top_idx], width, label='Permutation', color='#e74c3c', alpha=0.8)
ax.bar(x + width, shap_norm[top_idx], width, label='SHAP', color='#2ecc71', alpha=0.8)

ax.set_xticks(x)
ax.set_xticklabels([feature_names[i] for i in top_idx], rotation=45, ha='right')
ax.set_ylabel('Normalized Importance')
ax.set_title('Feature Importance 3중 교차검증 (Impurity vs Permutation vs SHAP)')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join('../outputs/figures/subtopic3_waste_risk', 'feature_importance_triple_comparison_s3.png'),
            dpi=150, bbox_inches='tight')
plt.show()
print("✅ 저장: feature_importance_triple_comparison_s3.png")

# 순위 비교
print("\n--- 상위 5개 피처 순위 비교 ---")
imp_rank = np.argsort(imp_norm)[::-1]
perm_rank = np.argsort(perm_norm)[::-1]
shap_rank = np.argsort(shap_norm)[::-1]
for i in range(min(5, len(feature_names))):
    print(f"  {i+1}위 | Impurity: {feature_names[imp_rank[i]]:30s} | Permutation: {feature_names[perm_rank[i]]:30s} | SHAP: {feature_names[shap_rank[i]]}")
```

---

### 항목 7: 결론 업데이트

**위치:** 셀 79 (결론 코드 셀)
**우선순위:** 낮음

결론 코드에 새로운 분석 결과를 추가한다.

---

## 구현 순서

| Phase | 항목 | 삽입 위치 | 셀 수 |
|-------|------|-----------|-------|
| 1 | 항목 1: 잔존 누수 검증 | 셀 39 이후 | +3 (md, code, viz) |
| 2 | 항목 2: RandomizedSearchCV | 셀 52 이후 (번호 조정) | +2 (md, code) |
| 2 | 항목 3: Tuned CV | 항목 2 이후 | +2 (md, code) |
| 2 | 항목 4: Tuned LC | 항목 3 이후 | +2 (md, code) |
| 3 | 항목 5: 부패성 내부 분석 | 심층 분석 내 | +2 (md, code) |
| 3 | 항목 6: SHAP Dep + 3중 비교 | SHAP 이후 | +4 (md, code, md, code) |
| 4 | 항목 7: 결론 업데이트 | 기존 셀 수정 | 0 |

**예상 총 셀:** 82 → 97 (+15셀)

## 변수 참조 (소주제 3 고유)

| 변수명 | 정의 위치 | 내용 |
|--------|-----------|------|
| `feature_names` | 셀 39 | `X.columns.tolist()` |
| `X_train_scaled` | 셀 39 | StandardScaler 변환 |
| `X_test_scaled` | 셀 39 | StandardScaler 변환 |
| `X_test_df` | 셀 39 | DataFrame 형태 |
| `y_train`, `y_test` | 셀 39 | stratify=y |
| `tuned_results` | 셀 48 | dict: model, predictions, metrics |
| `tuned_trained` | 셀 56 | dict: name → model |
| `tuned_models` | 셀 48 | dict: name → model |
| `best_model` | 셀 59 | LR (Tuned) |
| `xgb_tuned` | 셀 67 | `tuned_results['XGBoost']['model']` |
| `perm_result` | 셀 69 | permutation_importance 결과 |
| `shap_values` | 셀 72 | SHAP values (XGBoost) |
| `cv` | 셀 44 | StratifiedKFold(5) |
| `SEED` | 셀 2 | 42 |
| `spw` | 셀 42 | scale_pos_weight |
| `FIG_DIR` 경로 | 직접 사용 | `'../outputs/figures/subtopic3_waste_risk'` |

## 소주제 1, 2와의 차이점

| 항목 | 소주제 1, 2 | 소주제 3 |
|------|------------|---------|
| 잔존 누수 평가 | R² 기준 (0.85) | **Accuracy 기준 (0.95)** |
| RandomizedSearch 대상 | XGBoost + RF | **XGBoost + SVM** |
| 고유 분석 | 구간 분석/비대칭 | **부패성 내부 미세 분석** |
| FIG_DIR | 변수 정의 | **직접 경로 사용** |
| CV 변수명 | `kf` | **`cv`** |
