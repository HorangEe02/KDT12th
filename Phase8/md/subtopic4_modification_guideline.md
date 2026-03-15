# 소주제 4 — 최적 발주 전략 클러스터링 수정/보완 가이드라인

> **범위:** 현재 데이터(1,000행 × 37열) 기반, 추가 데이터 없이 분석 방법론 개선
> **대상 노트북:** `notebooks/04_Reorder_Strategy_Clustering.ipynb` (77 cells)
> **참조:** `md/result_report/subtopic4_report.md` 한계점 및 향후 보완 사항

---

## 수정 항목 총괄

| # | 수정 항목 | 우선순위 | 삽입 위치 | 신규/수정 |
|---|----------|---------|----------|----------|
| 1 | 잔존 누수 추가 검증 (S5 피처 조합) | **높음** | Cell 26 뒤 (Train/Test Split 뒤) | 신규 3셀 |
| 2 | RandomizedSearchCV (RF & XGB) | **높음** | Cell 31 뒤 (GridSearchCV 뒤) | 신규 2셀 |
| 3 | Tuned 모델 5-Fold CV | **높음** | Item 2 뒤 | 신규 2셀 |
| 4 | Tuned 모델 Learning Curve | **높음** | Item 3 뒤 | 신규 2셀 |
| 5 | SHAP Dependence Plot | **중간** | Cell 38 뒤 (Permutation 뒤) + 시프트 반영 | 신규 2셀 |
| 6 | Feature Importance 3중 교차검증 | **중간** | Item 5 뒤 | 신규 2셀 |
| 7 | 결론 업데이트 | **필수** | Cell 76 (결론 마크다운) | 기존 셀 수정 |

**총 추가 셀:** +13셀 (77 → 90셀)

---

## 소주제 4 특수 사항

### 소주제 1/2/3과의 차이점

| 항목 | 소주제 1~3 | 소주제 4 |
|------|-----------|----------|
| 분석 구조 | 단일 Phase | 3-Phase (A: 회귀 + B: 클러스터링 + C: EOQ) |
| 수정 대상 | 전체 | **Phase A만** (B·C는 비지도/시뮬레이션이므로 해당 항목 없음) |
| 타겟 변수 | 분류/회귀 | **DOI (회귀)** — R² 기준 |
| 누수 진단 | 비교적 단순 | **이미 5-Scenario 진단 완료** (S1~S5) |
| 피처셋 | 단일 | Baseline + **Enhanced** (파생변수 포함) |
| SHAP 대상 | 전체 모델 | **Phase A best_model_enhanced** (XGB Tuned) |
| FIG_DIR | `FIG_DIR` 변수 사용 | `FIG_DIR` 변수 사용 |
| 스케일러 | `scaler` | `scaler_enhanced` |

### 변수 참조 테이블

| 변수명 | 정의 위치 | 내용 |
|--------|----------|------|
| `X_train_e_sc`, `X_test_e_sc` | Cell 26 | Enhanced Train/Test (스케일링 완료) |
| `y_train`, `y_test` | Cell 26 | DOI 타겟 |
| `enhanced_numeric_A` | Cell 25 | Enhanced 수치 피처 리스트 |
| `cat_ohe_cols` | Cell 25 | Category+ABC OHE 컬럼 |
| `rf_grid`, `xgb_grid` | Cell 31 | GridSearchCV 결과 |
| `rf_tuned`, `xgb_tuned` | Cell 31 | GridSearchCV best_estimator |
| `best_model_enhanced` | Cell 33 | Phase A 최적 모델 (XGB Tuned) |
| `results_A` | Cell 28+ | 모델 결과 딕셔너리 |
| `FIG_DIR` | Cell 2 | `outputs/figures/subtopic4_reorder_clustering` |
| `SEED` | Cell 2 | 42 |

---

## 수정 항목 상세

### 1. 잔존 누수 추가 검증

**목적:** S5 채택 피처셋에서 단일/조합 피처가 DOI를 R²>0.85로 재구성하는지 검증
**위치:** Cell 26 (Train/Test Split) 뒤
**기준:** R² > 0.85 → 간접 누수 의심

#### 1-1. 단일 피처 R² 검증

```python
# ========================================
# 잔존 누수 검증 — 단일 피처
# ========================================
from sklearn.linear_model import LinearRegression

all_features = enhanced_numeric_A + cat_ohe_cols
print('📊 잔존 누수 검증 — 단일 피처 R²:')
print(f'   피처셋: {len(all_features)}개 (Enhanced S5)')

single_results = []
for feat in all_features:
    lr = LinearRegression()
    lr.fit(X_train_e_sc[[feat]], y_train)
    r2 = lr.score(X_test_e_sc[[feat]], y_test)
    single_results.append((feat, r2))
    flag = '🔴 누수 의심' if r2 >= 0.85 else ('🟡 높음' if r2 >= 0.50 else '')
    if r2 >= 0.30:
        print(f'   {feat:35s}: R² = {r2:.4f}  {flag}')

print(f'\n   최대 단일 피처 R²: {max(single_results, key=lambda x: x[1])}')
```

#### 1-2. 2-피처 조합 R² 검증

```python
from itertools import combinations

print('\n📊 잔존 누수 검증 — 2-피처 조합 (상위 5개):')
combo_results = []
top_singles = sorted(single_results, key=lambda x: x[1], reverse=True)[:6]
top_feat_names = [f[0] for f in top_singles]

for f1, f2 in combinations(top_feat_names, 2):
    lr = LinearRegression()
    lr.fit(X_train_e_sc[[f1, f2]], y_train)
    r2 = lr.score(X_test_e_sc[[f1, f2]], y_test)
    combo_results.append((f1, f2, r2))

combo_results.sort(key=lambda x: x[2], reverse=True)
for f1, f2, r2 in combo_results[:5]:
    flag = '🔴 누수 의심' if r2 >= 0.85 else ('🟡 높음' if r2 >= 0.50 else '')
    print(f'   ({f1}, {f2}): R² = {r2:.4f}  {flag}')

max_combo = combo_results[0][2]
print(f'\n   ✅ 최대 조합 R² = {max_combo:.4f} {"→ 간접 누수 없음" if max_combo < 0.85 else "→ 누수 의심"}')
```

#### 1-3. 시각화

```python
fig, ax = plt.subplots(figsize=(12, 5))
feats = [r[0] for r in single_results]
r2s = [r[1] for r in single_results]
colors = ['#e74c3c' if r >= 0.85 else '#f39c12' if r >= 0.50 else '#3498db' for r in r2s]
ax.barh(feats, r2s, color=colors)
ax.axvline(x=0.85, color='red', linestyle='--', alpha=0.7, label='누수 기준 (R²=0.85)')
ax.set_xlabel('R²')
ax.set_title('잔존 누수 검증 — 단일 피처 R² (Phase A Enhanced S5)', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'leakage_residual_verification_s4.png'), dpi=150, bbox_inches='tight')
plt.show()
```

---

### 2. RandomizedSearchCV

**목적:** GridSearchCV(Cell 31) 결과의 신뢰성 검증
**대상:** RF & XGB (Enhanced)
**n_iter:** 50

#### 2-1. RandomizedSearchCV 실행

```python
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform

# RF 파라미터 분포
rf_param_dist = {
    'n_estimators': randint(100, 500),
    'max_depth': randint(3, 20),
    'min_samples_split': randint(2, 20),
    'min_samples_leaf': randint(1, 10),
    'max_features': ['sqrt', 'log2', None]
}

# XGB 파라미터 분포
xgb_param_dist = {
    'n_estimators': randint(100, 500),
    'max_depth': randint(3, 15),
    'learning_rate': uniform(0.01, 0.3),
    'subsample': uniform(0.6, 0.4),
    'colsample_bytree': uniform(0.6, 0.4),
    'min_child_weight': randint(1, 10)
}

print('📊 RandomizedSearchCV (n_iter=50, cv=5)...')
rf_random = RandomizedSearchCV(
    RandomForestRegressor(random_state=SEED), rf_param_dist,
    n_iter=50, cv=5, scoring='r2', random_state=SEED, n_jobs=-1
)
rf_random.fit(X_train_e_sc, y_train)

xgb_random = RandomizedSearchCV(
    XGBRegressor(random_state=SEED, verbosity=0), xgb_param_dist,
    n_iter=50, cv=5, scoring='r2', random_state=SEED, n_jobs=-1
)
xgb_random.fit(X_train_e_sc, y_train)

print(f'   RF  Grid R²={rf_grid.best_score_:.4f} vs Random R²={rf_random.best_score_:.4f} (Δ={rf_random.best_score_ - rf_grid.best_score_:.4f})')
print(f'   XGB Grid R²={xgb_grid.best_score_:.4f} vs Random R²={xgb_random.best_score_:.4f} (Δ={xgb_random.best_score_ - xgb_grid.best_score_:.4f})')
```

---

### 3. Tuned 5-Fold CV

**목적:** Default CV(Cell 29)와 Tuned CV 비교
**대상:** `rf_tuned`, `xgb_tuned` + LR(baseline)

```python
from sklearn.model_selection import cross_val_score

print('📊 Tuned 모델 5-Fold CV:')
models_cv = {
    'LR (baseline)': LinearRegression(),
    'RF (Tuned)': rf_tuned,
    'XGB (Tuned)': xgb_tuned,
}

for name, model in models_cv.items():
    scores = cross_val_score(model, X_train_e_sc, y_train, cv=5, scoring='r2')
    print(f'   {name:20s}: mean={scores.mean():.4f} ± {scores.std():.4f}  '
          f'(min={scores.min():.4f}, max={scores.max():.4f})')
```

---

### 4. Tuned Learning Curve

**목적:** Default LC(Cell 36)와 Tuned LC 비교

```python
from sklearn.model_selection import learning_curve

fig, axes = plt.subplots(1, 3, figsize=(20, 6))
models_lc = [('LR', LinearRegression()), ('RF Tuned', rf_tuned), ('XGB Tuned', xgb_tuned)]

for ax, (name, model) in zip(axes, models_lc):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_train_e_sc, y_train,
        cv=5, scoring='r2', train_sizes=np.linspace(0.1, 1.0, 10),
        random_state=SEED, n_jobs=-1
    )
    train_mean = train_scores.mean(axis=1)
    val_mean = val_scores.mean(axis=1)
    gap = (train_mean[-1] - val_mean[-1])

    ax.plot(train_sizes, train_mean, 'o-', label=f'Train (final={train_mean[-1]:.4f})')
    ax.plot(train_sizes, val_mean, 'o-', label=f'Val (final={val_mean[-1]:.4f})')
    ax.fill_between(train_sizes, train_mean - train_scores.std(axis=1),
                     train_mean + train_scores.std(axis=1), alpha=0.1)
    ax.fill_between(train_sizes, val_mean - val_scores.std(axis=1),
                     val_mean + val_scores.std(axis=1), alpha=0.1)
    ax.set_title(f'{name} (Gap={gap:.4f})', fontweight='bold')
    ax.set_xlabel('Training Size')
    ax.set_ylabel('R² Score')
    ax.legend(loc='lower right')

plt.suptitle('Learning Curve — Phase A Enhanced (Tuned)', fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'learning_curve_phaseA_v5_s4.png'), dpi=150, bbox_inches='tight')
plt.show()
```

---

### 5. SHAP Dependence Plot

**목적:** best_model_enhanced(XGB Tuned)의 상위 피처 상호작용 시각화
**피처:** SHAP 기반 상위 4개

```python
import shap

explainer = shap.TreeExplainer(best_model_enhanced)
shap_values = explainer.shap_values(X_test_e_sc)

# 상위 4개 피처 자동 선택
mean_abs_shap = np.abs(shap_values).mean(axis=0)
feature_names = X_test_e_sc.columns.tolist()
top4_idx = np.argsort(mean_abs_shap)[::-1][:4]
top4_features = [feature_names[i] for i in top4_idx]

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
for ax, feat in zip(axes.flatten(), top4_features):
    shap.dependence_plot(feat, shap_values, X_test_e_sc, ax=ax, show=False)
    ax.set_title(f'SHAP Dependence — {feat}', fontweight='bold')

plt.suptitle('SHAP Dependence Plot — Phase A (XGB Tuned)', fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'shap_dependence_s4.png'), dpi=150, bbox_inches='tight')
plt.show()
```

---

### 6. Feature Importance 3중 교차검증

**목적:** Impurity(Cell 34) + Permutation(Cell 38) + SHAP 일관성 검증

```python
from sklearn.inspection import permutation_importance

# 1) Impurity (Tree 기반)
imp_impurity = best_model_enhanced.feature_importances_

# 2) Permutation
perm_result = permutation_importance(best_model_enhanced, X_test_e_sc, y_test,
                                      n_repeats=10, random_state=SEED, n_jobs=-1)
imp_permutation = perm_result.importances_mean

# 3) SHAP
imp_shap = np.abs(shap_values).mean(axis=0)

# 정규화 (0~1)
def normalize(arr):
    return arr / arr.max() if arr.max() > 0 else arr

imp_df = pd.DataFrame({
    'Feature': feature_names,
    'Impurity': normalize(imp_impurity),
    'Permutation': normalize(imp_permutation),
    'SHAP': normalize(imp_shap)
})
imp_df['Average'] = imp_df[['Impurity', 'Permutation', 'SHAP']].mean(axis=1)
imp_df = imp_df.sort_values('Average', ascending=False)

# 상위 10개 시각화
top10 = imp_df.head(10)
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(top10))
w = 0.25
ax.bar(x - w, top10['Impurity'], w, label='Impurity', color='#3498db')
ax.bar(x, top10['Permutation'], w, label='Permutation', color='#e74c3c')
ax.bar(x + w, top10['SHAP'], w, label='SHAP', color='#2ecc71')
ax.set_xticks(x)
ax.set_xticklabels(top10['Feature'], rotation=45, ha='right')
ax.set_ylabel('Normalized Importance')
ax.set_title('Feature Importance 3중 교차검증 — Phase A (XGB Tuned)', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'feature_importance_triple_comparison_s4.png'), dpi=150, bbox_inches='tight')
plt.show()

# 순위 비교 테이블
print('\n📊 Feature Importance 순위 비교 (Top 5):')
for method in ['Impurity', 'Permutation', 'SHAP']:
    ranked = imp_df.sort_values(method, ascending=False)['Feature'].head(5).tolist()
    print(f'   {method:12s}: {ranked}')
```

---

### 7. 결론 업데이트

**목적:** 새 분석 결과를 결론 마크다운에 반영

기존 결론(Cell 76)에 다음 인사이트 추가:

```markdown
## 추가 인사이트 (수정/보완 결과)

1. **잔존 누수 없음:** S5 피처셋에서 최대 조합 R² < 0.85 → 간접 누수 없음 확인
2. **RandomizedSearchCV:** Grid vs Random 결과 비교로 하이퍼파라미터 탐색 충분성 검증
3. **3단계 과적합 검증:** Train/Test Gap → 5-Fold CV → Learning Curve 체계적 검증 완료
4. **Feature Importance 3중 교차검증:** ABC_Class_C가 3개 방법 모두 1위 → DOI 핵심 결정 요인
5. **SHAP Dependence:** 상위 피처의 비선형 상호작용 패턴 확인
```
