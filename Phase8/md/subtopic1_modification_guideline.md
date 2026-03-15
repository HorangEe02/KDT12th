# 소주제 1 — 재고 상태 분류 수정/보완 가이드라인

> **범위:** 현재 데이터(1,000행 × 37열) 기반, 추가 데이터 없이 분석 방법론 개선
> **대상 노트북:** `notebooks/01_Inventory_Status_Classification.ipynb`
> **참조:** `md/result_report/subtopic1_report.md` 한계점 및 향후 보완 사항

---

## 수정 항목 총괄

| # | 수정 항목 | 우선순위 | 삽입 위치 (셀 기준) | 신규/수정 |
|---|----------|---------|-------------------|----------|
| 1 | 잔존 누수 추가 검증 (RP + QOH 조합) | **높음** | Cell 27~28 사이 (누수 진단 섹션 내) | 신규 셀 추가 |
| 2 | SHAP 분석 도입 | **높음** | Cell 60 뒤 (Feature Importance 섹션 내) | 신규 셀 추가 |
| 3 | Tuned 모델 Learning Curve | **높음** | Cell 50 뒤 (Default vs Tuned 비교 섹션 뒤) | 신규 셀 추가 |
| 4 | 자동 하이퍼파라미터 탐색 (GridSearchCV) | **중간** | Cell 43~44 사이 (튜닝 섹션 대체/보완) | 기존 셀 수정 |
| 5 | Tuned 모델 5-Fold CV | **중간** | Cell 40 뒤 (CV 섹션 확장) | 신규 셀 추가 |
| 6 | ROC-AUC 곡선 (One-vs-Rest) | **중간** | Cell 54 뒤 (Classification Report 뒤) | 신규 셀 추가 |
| 7 | 비용 민감 학습 실험 | **낮음** | Cell 62 뒤 (심층 분석 마지막) | 신규 셀 추가 |
| 8 | 결론 섹션 업데이트 | **필수** | Cell 65~66 (결론 마크다운 + 코드) | 기존 셀 수정 |

---

## 1. 잔존 누수 추가 검증 (RP + QOH 조합)

### 배경
- 현재 98~99% 정확도가 잔존 누수 때문인지 확인 필요
- `Reorder_Point - Quantity_On_Hand` 조합이 Low Stock 정의와 직접 대응할 가능성
- result_report에서 명시적으로 "미검증" 한계로 기술됨

### 구현 내용

#### 1-1. RP - QOH 조합의 Low Stock 대응률 검증

```python
# 잔존 누수 추가 검증: Reorder_Point - Quantity_On_Hand 조합
print('=' * 60)
print('4-6) 잔존 누수 검증: Reorder_Point + Quantity_On_Hand 조합')
print('=' * 60)

# RP > QOH 인 경우와 Low Stock 대응 확인
rp_gt_qoh = df['Reorder_Point'] > df['Quantity_On_Hand']
low_stock_mask = df['Status_3cls'] == 'Low Stock'

# 대응 테이블
print('\n📊 Reorder_Point > Quantity_On_Hand vs Low Stock:')
ct = pd.crosstab(rp_gt_qoh, low_stock_mask, margins=True)
ct.index = ['RP <= QOH', 'RP > QOH', 'Total']
ct.columns = ['Not Low Stock', 'Low Stock', 'Total']
print(ct)

# 대응률 계산
if rp_gt_qoh.sum() > 0:
    match_rate = (rp_gt_qoh & low_stock_mask).sum() / low_stock_mask.sum()
    print(f'\n   Low Stock 중 RP > QOH 비율: {match_rate:.4f} ({(rp_gt_qoh & low_stock_mask).sum()}/{low_stock_mask.sum()})')

# RP - QOH 차이값 분포
print('\n📊 (Reorder_Point - Quantity_On_Hand) 클래스별 분포:')
df['RP_minus_QOH'] = df['Reorder_Point'] - df['Quantity_On_Hand']
for cls in ['In Stock', 'Expiring Soon', 'Low Stock']:
    subset = df[df['Status_3cls'] == cls]['RP_minus_QOH']
    print(f'   {cls:15s}: mean={subset.mean():8.2f}, median={subset.median():8.2f}, '
          f'min={subset.min():8.2f}, max={subset.max():8.2f}')
```

#### 1-2. 2-피처 조합 누수 진단 (DecisionTree)

```python
# 2-피처 조합 누수 테스트
print('\n📊 2-피처 조합 분류력 진단 (DecisionTree, max_depth=3):')
combo_pairs = [
    ('Reorder_Point', 'Quantity_On_Hand'),
    ('Days_of_Inventory', 'Avg_Daily_Sales'),
    ('Lead_Time_Days', 'Days_of_Inventory'),
    ('Safety_Stock', 'Quantity_On_Hand'),
]

for feat1, feat2 in combo_pairs:
    dt = DecisionTreeClassifier(max_depth=3, random_state=SEED)
    dt.fit(df[[feat1, feat2]], y_temp)
    acc = dt.score(df[[feat1, feat2]], y_temp)
    flag = '🔴 누수 의심' if acc >= 0.95 else ('🟡 높음' if acc >= 0.85 else '')
    print(f'   ({feat1}, {feat2}): Acc = {acc:.4f}  {flag}')
```

#### 1-3. 판정 기준
- **대응률 95% 이상**: 해당 조합도 누수 → Scenario C 생성 고려
- **대응률 80~95%**: 강한 예측력이지만 비즈니스 논리로 설명 가능한 수준
- **대응률 80% 미만**: 잔존 누수 아님 확인 → 높은 성능의 정당성 확보

#### 1-4. 시각화

```python
# RP vs QOH 산점도 (Status별 색상)
fig, ax = plt.subplots(figsize=(10, 8))
for cls, color, marker in zip(['In Stock', 'Expiring Soon', 'Low Stock'],
                               ['#2ecc71', '#f39c12', '#e74c3c'],
                               ['o', 's', '^']):
    mask = df['Status_3cls'] == cls
    ax.scatter(df.loc[mask, 'Quantity_On_Hand'], df.loc[mask, 'Reorder_Point'],
              c=color, marker=marker, label=cls, alpha=0.6, s=40, edgecolors='white')

# y=x 대각선 (RP = QOH 경계)
lims = [0, max(df['Quantity_On_Hand'].max(), df['Reorder_Point'].max()) + 10]
ax.plot(lims, lims, 'k--', alpha=0.5, label='RP = QOH (경계)')
ax.set_xlabel('Quantity_On_Hand')
ax.set_ylabel('Reorder_Point')
ax.set_title('Reorder_Point vs Quantity_On_Hand (재고 상태별)', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'leakage_rp_vs_qoh.png'), dpi=150, bbox_inches='tight')
plt.show()
```

---

## 2. SHAP 분석 도입

### 배경
- Feature Importance만으로는 "왜 이 제품이 Low Stock인가"를 개별 설명 불가
- Permutation vs Impurity 교차검증은 전역적(global) 설명만 제공
- SHAP은 개별 예측(local) + 전역(global) 모두 가능

### 라이브러리 추가 (Cell 1 수정)

```python
# Cell 1에 추가
import shap
```

> **설치 필요 시:** `pip install shap`

### 구현 내용

#### 2-1. SHAP Summary Plot (Global)

```python
# ========================================
# 9.5 SHAP 분석 (최적 모델)
# ========================================
print('📊 SHAP 분석 시작...')

# TreeExplainer (LightGBM/XGBoost/RF에 최적화)
explainer = shap.TreeExplainer(best_model_tuned)
shap_values = explainer.shap_values(X_test_scaled)

# Summary Plot — 전체 클래스
fig, ax = plt.subplots(figsize=(12, 8))
shap.summary_plot(shap_values, X_test_scaled,
                  class_names=list(class_names),
                  show=False, max_display=15)
plt.title(f'SHAP Summary Plot — {best_name_tuned}', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'shap_summary_all_classes.png'),
            dpi=150, bbox_inches='tight')
plt.show()
print('✅ 저장: shap_summary_all_classes.png')
```

#### 2-2. SHAP Summary Plot (클래스별)

```python
# 클래스별 SHAP Summary Plot
fig, axes = plt.subplots(1, 3, figsize=(24, 8))
for i, cls_name in enumerate(class_names):
    plt.sca(axes[i])
    shap.summary_plot(shap_values[i], X_test_scaled,
                      show=False, max_display=10)
    axes[i].set_title(f'SHAP — {cls_name}', fontsize=12, fontweight='bold')

plt.suptitle(f'클래스별 SHAP Summary — {best_name_tuned}',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'shap_summary_per_class.png'),
            dpi=150, bbox_inches='tight')
plt.show()
print('✅ 저장: shap_summary_per_class.png')
```

#### 2-3. SHAP Bar Plot (Mean |SHAP|)

```python
# Mean |SHAP| Bar Plot
fig, ax = plt.subplots(figsize=(10, 8))
shap.summary_plot(shap_values, X_test_scaled,
                  plot_type='bar',
                  class_names=list(class_names),
                  show=False, max_display=15)
plt.title(f'Mean |SHAP| — {best_name_tuned}', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'shap_bar_mean.png'),
            dpi=150, bbox_inches='tight')
plt.show()
print('✅ 저장: shap_bar_mean.png')
```

#### 2-4. SHAP Force Plot (개별 예측 설명 — 오분류 케이스)

```python
# 오분류 케이스 SHAP 분석
misclassified = np.where(best_pred_tuned != y_test)[0]
print(f'\n📊 오분류 케이스 수: {len(misclassified)}건')

if len(misclassified) > 0:
    for idx in misclassified[:3]:  # 최대 3건 표시
        true_cls = class_names[y_test[idx]]
        pred_cls = class_names[best_pred_tuned[idx]]
        print(f'\n   Test[{idx}]: 실제={true_cls}, 예측={pred_cls}')

        # Waterfall Plot
        shap_explanation = shap.Explanation(
            values=shap_values[best_pred_tuned[idx]][idx],
            base_values=explainer.expected_value[best_pred_tuned[idx]],
            data=X_test_scaled.iloc[idx],
            feature_names=list(X.columns)
        )
        fig, ax = plt.subplots(figsize=(12, 6))
        shap.waterfall_plot(shap_explanation, max_display=10, show=False)
        plt.title(f'오분류 분석 — 실제: {true_cls}, 예측: {pred_cls}', fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(FIG_DIR, f'shap_waterfall_misclassified_{idx}.png'),
                    dpi=150, bbox_inches='tight')
        plt.show()
else:
    print('   오분류 없음 — 정분류 샘플에 대해 SHAP 분석 수행')
    # 각 클래스별 대표 샘플 1건씩 설명
    for cls_idx, cls_name in enumerate(class_names):
        sample_indices = np.where(y_test == cls_idx)[0]
        if len(sample_indices) > 0:
            idx = sample_indices[0]
            shap_explanation = shap.Explanation(
                values=shap_values[cls_idx][idx],
                base_values=explainer.expected_value[cls_idx],
                data=X_test_scaled.iloc[idx],
                feature_names=list(X.columns)
            )
            fig, ax = plt.subplots(figsize=(12, 6))
            shap.waterfall_plot(shap_explanation, max_display=10, show=False)
            plt.title(f'SHAP Waterfall — {cls_name} 샘플', fontweight='bold')
            plt.tight_layout()
            plt.savefig(os.path.join(FIG_DIR, f'shap_waterfall_{cls_name.replace(" ","_")}.png'),
                        dpi=150, bbox_inches='tight')
            plt.show()
```

#### 2-5. SHAP vs Permutation vs Impurity 3중 비교

```python
# 3중 Feature Importance 비교
if hasattr(best_model_tuned, 'feature_importances_'):
    # Mean |SHAP| 계산
    shap_mean = np.abs(np.array(shap_values)).mean(axis=(0, 1))
    shap_imp = pd.Series(shap_mean, index=X.columns).sort_values(ascending=False)

    # 비교 테이블
    comparison_df = pd.DataFrame({
        'Impurity_Rank': feat_imp_impurity_sorted.rank(ascending=False).astype(int),
        'Permutation_Rank': perm_imp_sorted.rank(ascending=False).astype(int),
        'SHAP_Rank': shap_imp.rank(ascending=False).astype(int),
    })
    comparison_df['Avg_Rank'] = comparison_df.mean(axis=1)
    comparison_df = comparison_df.sort_values('Avg_Rank')

    print(f'\n📊 3중 Feature Importance 순위 비교 (Top 10):')
    print(comparison_df.head(10).to_string())
```

### 기대 효과
- 개별 예측에 대한 설명 가능성 확보 → 실무 담당자 설득 근거
- Impurity/Permutation과의 교차검증으로 Feature Importance 신뢰도 최종 확인
- 오분류 케이스의 원인 분석 가능

---

## 3. Tuned 모델 Learning Curve

### 배경
- 현재 Learning Curve는 Default 모델에 대해서만 생성 (Cell 42)
- 튜닝 후 과적합 방지 효과가 학습 곡선에서 어떻게 나타나는지 확인 필요
- result_report 한계점에서 명시적으로 "Tuned 모델의 수렴 패턴 미확인" 기술

### 구현 내용

```python
# ========================================
# 8-6. Tuned 모델 Learning Curve
# ========================================
lc_models_tuned = {
    'LR (Tuned)': lr_tuned,
    'RF (Tuned)': rf_tuned,
    'XGB (Tuned)': xgb_tuned,
    'LGBM (Tuned)': lgbm_tuned,
}

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.flatten()

for ax, (name, model) in zip(axes, lc_models_tuned.items()):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_train_scaled, y_train,
        train_sizes=np.linspace(0.1, 1.0, 10),
        cv=5, scoring='f1_macro', n_jobs=-1, random_state=SEED
    )

    train_mean = train_scores.mean(axis=1)
    train_std = train_scores.std(axis=1)
    val_mean = val_scores.mean(axis=1)
    val_std = val_scores.std(axis=1)

    ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std,
                    alpha=0.15, color='#e74c3c')
    ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std,
                    alpha=0.15, color='#3498db')
    ax.plot(train_sizes, train_mean, 'o-', color='#e74c3c', label='Train F1', linewidth=2)
    ax.plot(train_sizes, val_mean, 'o-', color='#3498db', label='Validation F1', linewidth=2)

    final_gap = train_mean[-1] - val_mean[-1]
    overfit_label = '⚠️ 과적합' if final_gap > 0.05 else ('🟡 주의' if final_gap > 0.02 else '✅ 양호')
    ax.set_title(f'{name}\nFinal Gap = {final_gap:.4f} {overfit_label}',
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('훈련 데이터 크기')
    ax.set_ylabel('F1 Macro')
    ax.legend(loc='lower right')
    ax.set_ylim([0.8, 1.02])
    ax.grid(True, alpha=0.3)

plt.suptitle('Learning Curve — Tuned 모델 (Scenario B)', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'learning_curve_tuned.png'),
            dpi=150, bbox_inches='tight')
plt.show()
print('✅ 저장: learning_curve_tuned.png')
```

#### Default vs Tuned Gap 비교 요약

```python
# Default vs Tuned Learning Curve Gap 비교
print('\n📊 Default vs Tuned Learning Curve 최종 Gap 비교:')
print(f'   {"모델":20s}  {"Default Gap":>12s}  {"Tuned Gap":>12s}  {"개선":>8s}')
print(f'   {"-"*20}  {"-"*12}  {"-"*12}  {"-"*8}')
# (실제 값은 실행 시 채워짐 — 위 코드에서 gap 값을 저장하여 비교)
```

---

## 4. 자동 하이퍼파라미터 탐색 (GridSearchCV)

### 배경
- 현재 수동 설정 (경험 기반) → 최적 파라미터가 아닐 가능성
- GridSearchCV로 체계적 탐색 후, 기존 수동 결과와 비교

### 구현 내용

> **기존 수동 튜닝 셀(44~47)은 유지하고**, 그 아래에 GridSearchCV 결과를 추가하여 비교

```python
# ========================================
# 8-7. GridSearchCV 자동 하이퍼파라미터 탐색
# ========================================
from sklearn.model_selection import GridSearchCV

print('📊 GridSearchCV 하이퍼파라미터 탐색 시작...')
print('   (소요 시간: 약 1~3분)')

# LightGBM GridSearchCV
lgbm_param_grid = {
    'num_leaves': [15, 20, 31],
    'max_depth': [4, 6, 8],
    'learning_rate': [0.01, 0.05, 0.1],
    'reg_alpha': [0.0, 0.1, 0.5],
    'reg_lambda': [0.5, 1.0, 2.0],
    'min_child_samples': [5, 10, 20],
}

lgbm_base = LGBMClassifier(
    objective='multiclass', num_class=3,
    is_unbalance=True, n_estimators=200,
    subsample=0.8, colsample_bytree=0.8,
    random_state=SEED, verbosity=-1
)

cv_inner = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

# 탐색 공간이 크므로 RandomizedSearchCV 권장
from sklearn.model_selection import RandomizedSearchCV

lgbm_search = RandomizedSearchCV(
    lgbm_base, lgbm_param_grid,
    n_iter=50,  # 50개 조합 샘플링
    cv=cv_inner, scoring='f1_macro',
    n_jobs=-1, random_state=SEED, verbose=0
)
lgbm_search.fit(X_train_scaled, y_train)

print(f'\n🏆 최적 파라미터: {lgbm_search.best_params_}')
print(f'   CV Macro F1: {lgbm_search.best_score_:.4f}')

# 최적 모델로 Test 평가
y_pred_search = lgbm_search.predict(X_test_scaled)
search_acc = accuracy_score(y_test, y_pred_search)
search_f1 = f1_score(y_test, y_pred_search, average='macro')
y_pred_search_train = lgbm_search.predict(X_train_scaled)
search_train_acc = accuracy_score(y_train, y_pred_search_train)

print(f'\n📊 GridSearchCV 최적 모델 vs 수동 튜닝 비교:')
print(f'   {"":20s}  {"Train Acc":>10s}  {"Test Acc":>10s}  {"Macro F1":>10s}  {"Gap":>8s}')
print(f'   {"수동 튜닝":20s}  {results_tuned["LightGBM"]["Train Acc"]:10.4f}  '
      f'{results_tuned["LightGBM"]["Accuracy"]:10.4f}  '
      f'{results_tuned["LightGBM"]["Macro F1"]:10.4f}  '
      f'{results_tuned["LightGBM"]["Train Acc"]-results_tuned["LightGBM"]["Accuracy"]:8.4f}')
print(f'   {"GridSearchCV":20s}  {search_train_acc:10.4f}  '
      f'{search_acc:10.4f}  {search_f1:10.4f}  {search_train_acc-search_acc:8.4f}')
```

### XGBoost GridSearchCV (선택적)

```python
# XGBoost GridSearchCV (선택적)
xgb_param_grid = {
    'max_depth': [3, 4, 6],
    'learning_rate': [0.01, 0.05, 0.1],
    'reg_alpha': [0.0, 0.1, 0.5],
    'reg_lambda': [0.5, 1.0, 2.0],
    'subsample': [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 0.9],
}

xgb_base = XGBClassifier(
    objective='multi:softmax', num_class=3,
    n_estimators=200, use_label_encoder=False,
    eval_metric='mlogloss', random_state=SEED, verbosity=0
)

xgb_search = RandomizedSearchCV(
    xgb_base, xgb_param_grid,
    n_iter=50, cv=cv_inner, scoring='f1_macro',
    n_jobs=-1, random_state=SEED, verbose=0
)
xgb_search.fit(X_train_scaled, y_train)

print(f'\n🏆 XGBoost 최적 파라미터: {xgb_search.best_params_}')
print(f'   CV Macro F1: {xgb_search.best_score_:.4f}')
```

---

## 5. Tuned 모델 5-Fold CV

### 배경
- 현재 5-Fold CV는 Default 모델에 대해서만 수행 (Cell 40)
- 튜닝 후 CV Gap이 어떻게 변하는지 비교 필요

### 구현 내용

```python
# ========================================
# 8-8. Tuned 모델 5-Fold 교차검증
# ========================================
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

tuned_models_cv = {
    'LR (Tuned)': lr_tuned,
    'RF (Tuned)': rf_tuned,
    'XGB (Tuned)': xgb_tuned,
    'LGBM (Tuned)': lgbm_tuned,
}

print('📊 Tuned 모델 5-Fold 교차검증:')
print(f'   {"모델":20s}  {"Train F1":>10s}  {"Val F1":>10s}  {"Gap":>8s}  {"판정":>8s}')
print(f'   {"-"*20}  {"-"*10}  {"-"*10}  {"-"*8}  {"-"*8}')

cv_results_tuned = {}
for name, model in tuned_models_cv.items():
    scores = cross_validate(model, X_train_scaled, y_train,
                           cv=cv, scoring='f1_macro',
                           return_train_score=True, n_jobs=-1)
    train_f1 = scores['train_score'].mean()
    val_f1 = scores['test_score'].mean()
    gap = train_f1 - val_f1
    judge = '⚠️ 과적합' if gap > 0.05 else ('🟡 주의' if gap > 0.02 else '✅ 양호')

    cv_results_tuned[name] = {'train_f1': train_f1, 'val_f1': val_f1, 'gap': gap}
    print(f'   {name:20s}  {train_f1:10.4f}  {val_f1:10.4f}  {gap:8.4f}  {judge}')
```

---

## 6. ROC-AUC 곡선 (One-vs-Rest)

### 배경
- 현재 평가지표: Accuracy, Macro F1, Confusion Matrix만 사용
- ROC-AUC로 클래스별 분류 경계의 품질 확인 가능
- 다중 클래스에서는 One-vs-Rest 방식 사용

### 구현 내용

```python
# ========================================
# 9.6 ROC-AUC 곡선 (One-vs-Rest)
# ========================================
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize

# 타겟 이진화
y_test_bin = label_binarize(y_test, classes=[0, 1, 2])
n_classes = y_test_bin.shape[1]

# 최적 모델의 확률 예측
if hasattr(best_model_tuned, 'predict_proba'):
    y_score = best_model_tuned.predict_proba(X_test_scaled)

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ['#2ecc71', '#f39c12', '#e74c3c']

    roc_auc_dict = {}
    for i, (cls_name, color) in enumerate(zip(class_names, colors)):
        fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
        roc_auc_val = auc(fpr, tpr)
        roc_auc_dict[cls_name] = roc_auc_val
        ax.plot(fpr, tpr, color=color, linewidth=2,
                label=f'{cls_name} (AUC = {roc_auc_val:.4f})')

    ax.plot([0, 1], [0, 1], 'k--', alpha=0.5)
    ax.set_xlabel('False Positive Rate')
    ax.set_ylabel('True Positive Rate')
    ax.set_title(f'ROC Curve (One-vs-Rest) — {best_name_tuned}', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'roc_auc_ovr.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print('✅ 저장: roc_auc_ovr.png')

    # Macro 평균 AUC
    macro_auc = np.mean(list(roc_auc_dict.values()))
    print(f'\n📊 ROC-AUC (One-vs-Rest):')
    for cls_name, auc_val in roc_auc_dict.items():
        print(f'   {cls_name:15s}: AUC = {auc_val:.4f}')
    print(f'   {"Macro Average":15s}: AUC = {macro_auc:.4f}')
```

---

## 7. 비용 민감 학습 실험

### 배경
- Macro F1은 모든 오분류를 동등하게 취급
- 실무에서는 Low Stock 미탐지가 In Stock 오분류보다 비용이 큼
- `sample_weight` 또는 `class_weight`를 활용한 비용 비대칭 반영

### 구현 내용

```python
# ========================================
# 9.7 비용 민감 학습 실험 (Cost-Sensitive)
# ========================================
print('📊 비용 민감 학습 실험:')
print('   Low Stock 미탐지 비용 > In Stock 오분류 비용')
print('   → class_weight 조정으로 Low Stock recall 향상 시도')

# 비용 가중치: Low Stock에 더 높은 가중치
# class_names: ['Expiring Soon', 'In Stock', 'Low Stock']
cost_weight = {0: 1.5, 1: 1.0, 2: 2.0}  # Low Stock(2)에 2배 가중

lgbm_cost = LGBMClassifier(
    objective='multiclass', num_class=3,
    n_estimators=200, learning_rate=0.05,
    num_leaves=20, min_child_samples=10, max_depth=6,
    reg_alpha=0.1, reg_lambda=1.0,
    subsample=0.8, colsample_bytree=0.8,
    class_weight=cost_weight,
    random_state=SEED, verbosity=-1
)
lgbm_cost.fit(X_train_scaled, y_train)

y_pred_cost = lgbm_cost.predict(X_test_scaled)
cost_acc = accuracy_score(y_test, y_pred_cost)
cost_f1 = f1_score(y_test, y_pred_cost, average='macro')

print(f'\n📊 비용 민감 모델 vs 기본 Tuned 비교:')
print(f'   {"":15s}  {"Accuracy":>10s}  {"Macro F1":>10s}')
print(f'   {"Tuned":15s}  {results_tuned["LightGBM"]["Accuracy"]:10.4f}  '
      f'{results_tuned["LightGBM"]["Macro F1"]:10.4f}')
print(f'   {"Cost-Sensitive":15s}  {cost_acc:10.4f}  {cost_f1:10.4f}')

# 클래스별 Recall 비교
print(f'\n📊 클래스별 Recall 비교:')
cm_tuned = confusion_matrix(y_test, results_tuned['LightGBM']['y_pred'])
cm_cost = confusion_matrix(y_test, y_pred_cost)
for i, cls in enumerate(class_names):
    recall_tuned = cm_tuned[i][i] / cm_tuned[i].sum() if cm_tuned[i].sum() > 0 else 0
    recall_cost = cm_cost[i][i] / cm_cost[i].sum() if cm_cost[i].sum() > 0 else 0
    diff = recall_cost - recall_tuned
    arrow = '↑' if diff > 0 else ('↓' if diff < 0 else '=')
    print(f'   {cls:15s}: Tuned={recall_tuned:.4f} → Cost={recall_cost:.4f} ({arrow}{abs(diff):.4f})')
```

---

## 8. 결론 섹션 업데이트

### Cell 65 (마크다운) 수정사항

기존 파이프라인 요약에 추가:
```
> 6. SHAP 분석 → 개별 예측 설명 가능성 확보 ★ (신규)
> 7. 잔존 누수 추가 검증 → RP + QOH 조합 확인 ★ (신규)
> 8. ROC-AUC → 클래스별 분류 경계 품질 검증 ★ (신규)
```

### Cell 66 (코드) 수정사항

결론 인사이트에 추가할 항목:
- SHAP 분석 결과 요약 (전역 + 개별)
- 잔존 누수 검증 결과 (RP + QOH 대응률)
- GridSearchCV 결과 vs 수동 튜닝 비교
- Tuned Learning Curve 결과 요약
- ROC-AUC 결과
- 비용 민감 학습 결과 (Low Stock Recall 변화)

---

## 구현 순서 권장

### Phase 1: 핵심 검증 (먼저 수행)
1. **잔존 누수 추가 검증** — 98~99% 성능의 정당성 확보가 최우선
2. **Tuned 모델 Learning Curve** — 기존 한계점 해소

### Phase 2: 설명 가능성 강화
3. **SHAP 분석 도입** — 모델 해석력 대폭 향상
4. **ROC-AUC 곡선** — 평가지표 다양화

### Phase 3: 방법론 고도화
5. **Tuned 모델 5-Fold CV** — 교차검증 완성
6. **GridSearchCV 자동 탐색** — 수동 튜닝 검증
7. **비용 민감 학습** — 비즈니스 관점 반영

### Phase 4: 문서 정리
8. **결론 섹션 업데이트** — 모든 수정 사항 반영

---

## 예상 산출물

### 신규 시각화 파일
| 파일명 | 설명 |
|--------|------|
| `leakage_rp_vs_qoh.png` | RP vs QOH 산점도 (잔존 누수 검증) |
| `shap_summary_all_classes.png` | SHAP Summary Plot (전체) |
| `shap_summary_per_class.png` | SHAP Summary Plot (클래스별) |
| `shap_bar_mean.png` | Mean \|SHAP\| Bar Plot |
| `shap_waterfall_*.png` | SHAP Waterfall (오분류/대표 샘플) |
| `learning_curve_tuned.png` | Tuned 모델 Learning Curve |
| `roc_auc_ovr.png` | ROC-AUC 곡선 (One-vs-Rest) |

### 수정되는 기존 파일
| 파일 | 수정 내용 |
|------|----------|
| `01_Inventory_Status_Classification.ipynb` | 신규 셀 추가 + 결론 업데이트 |
| `md/result_report/subtopic1_report.md` | 한계점 해소 내용 반영, 향후 보완 사항 업데이트 |

---

## 주의사항

1. **shap 라이브러리 설치 확인**: `pip install shap` (버전 >= 0.42 권장)
2. **TreeExplainer 호환성**: LightGBM/XGBoost에 대해 TreeExplainer 사용, LR에는 KernelExplainer 필요
3. **실행 순서**: 잔존 누수 검증 결과에 따라 Scenario C 생성 여부 결정 후 후속 분석 진행
4. **파일 저장 경로**: 기존 `outputs/figures/subtopic1_classification/` 폴더에 저장
5. **GridSearchCV 소요 시간**: RandomizedSearchCV(n_iter=50) 기준 약 1~3분
6. **결론 업데이트 시**: 실행 결과 수치를 반영하여 구체적으로 작성
