# 소주제 2 수정/보완 가이드라인

> **대상 노트북:** `notebooks/02_Avg_Daily_Sales_Prediction.ipynb` (67셀)
> **현재 최적 모델:** XGBoost Tuned (R²=0.9477, RMSE=4.79, Gap=0.0436)
> **핵심 원칙:** 데이터 추가 없이, 기존 1,000행 데이터에서 방법론적 개선만 수행

---

## 현재 노트북 보유 항목 vs 보완 필요 항목

### 이미 구현된 항목 (수정 불필요)
| 항목 | 셀 위치 | 비고 |
| --- | --- | --- |
| 데이터 누수 진단 (DOI=QOH/ADS) | 셀 26~28 | 97.2% 일치, 제거 완료 |
| Order_Frequency 준누수 검증 | 셀 29~30 | RF ΔR²=-0.005, 누수 아님 |
| Default 5-Fold CV | 셀 37 | 5개 모델 CV R² |
| Default Learning Curve | 셀 44 | 5개 모델 수렴 확인 |
| Shapiro-Wilk 잔차 검정 | 셀 52 | W=0.9240, p<0.05 |
| Permutation Importance | 셀 56~57 | Reorder_Point 7위→2위 |
| SHAP Bar + Summary | 셀 59~60 | 기본 SHAP 분석 |

### 보완 필요 항목 (8개)

| # | 항목 | 우선순위 | 근거 |
| --- | --- | --- | --- |
| 1 | 잔존 누수 검증 (QOH, RP, Safety_Stock 조합) | 높음 | R²=0.9477이 여전히 높아 간접 누수 가능성 |
| 2 | RandomizedSearchCV (자동 튜닝 검증) | 높음 | 수동 튜닝이 최적인지 확인 필요 |
| 3 | Tuned 모델 5-Fold CV | 중간 | Default CV만 있고 Tuned CV 미수행 |
| 4 | Tuned 모델 Learning Curve | 중간 | Default LC만 있고 Tuned LC 미수행 |
| 5 | 고판매량 구간 심층 분석 | 중간 | 70+ 과소예측 원인 규명 |
| 6 | SHAP Dependence Plot (상호작용) | 중간 | 핵심 피처 간 비선형 상호작용 시각화 |
| 7 | 예측 오차 비대칭 분석 | 낮음 | 과대/과소 예측의 비즈니스 영향 비교 |
| 8 | 결론 업데이트 | 낮음 | 보완 결과 반영 |

---

## 구현 상세

### 항목 1: 잔존 누수 검증 (QOH + RP + Safety_Stock 조합)

**삽입 위치:** 셀 30 이후 (준누수 검증 다음)

**배경:** DOI를 제거했지만, ADS = QOH / DOI 수식에서 QOH가 피처로 남아있고, RP와 Safety_Stock이 QOH와 높은 상관(0.65)을 가지므로, 이 조합이 간접적으로 타겟을 역산할 수 있는지 확인 필요.

```python
# ========================================
# 4.5 잔존 누수 검증 — QOH, RP, Safety_Stock 조합
# ========================================
from sklearn.tree import DecisionTreeRegressor

print("=" * 60)
print("4.5 잔존 누수 검증 — 재고 관련 피처 조합")
print("=" * 60)

# (A) 개별 피처 예측력 테스트
single_features = ['Quantity_On_Hand', 'Reorder_Point', 'Safety_Stock',
                   'Order_Frequency_per_month', 'Lead_Time_Days', 'Unit_Cost_USD']
single_results = {}
for feat in single_features:
    dt = DecisionTreeRegressor(max_depth=3, random_state=42)
    dt.fit(X_train_scaled[:, [list(X.columns).index(feat)]],
           y_train)
    r2 = dt.score(X_test_scaled[:, [list(X.columns).index(feat)]],
                  y_test)
    single_results[feat] = r2
    print(f"  {feat:35s} → R² = {r2:.4f}")

# (B) 2~3-피처 조합 테스트
combo_features = [
    ['Quantity_On_Hand', 'Reorder_Point'],
    ['Quantity_On_Hand', 'Safety_Stock'],
    ['Quantity_On_Hand', 'Reorder_Point', 'Safety_Stock'],
    ['Order_Frequency_per_month', 'Quantity_On_Hand'],
]
print("\n--- 조합 피처 예측력 ---")
combo_results = {}
for combo in combo_features:
    idxs = [list(X.columns).index(f) for f in combo]
    dt = DecisionTreeRegressor(max_depth=5, random_state=42)
    dt.fit(X_train_scaled[:, idxs], y_train)
    r2 = dt.score(X_test_scaled[:, idxs], y_test)
    combo_name = ' + '.join(combo)
    combo_results[combo_name] = r2
    print(f"  {combo_name:55s} → R² = {r2:.4f}")
```

**시각화:**

```python
# 잔존 누수 검증 시각화
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# (A) 단일 피처 R²
ax = axes[0]
names = list(single_results.keys())
vals = list(single_results.values())
colors = ['red' if v > 0.7 else 'orange' if v > 0.5 else 'steelblue' for v in vals]
ax.barh(names, vals, color=colors)
ax.set_xlabel('R² Score')
ax.set_title('단일 피처 예측력 (DecisionTree, max_depth=3)')
ax.axvline(x=0.7, color='red', linestyle='--', alpha=0.5, label='누수 의심 (0.7)')
ax.legend()

# (B) 조합 피처 R²
ax = axes[1]
combo_names = [n.replace('_per_month', '').replace('Quantity_On_Hand', 'QOH')
               .replace('Reorder_Point', 'RP').replace('Safety_Stock', 'SS')
               .replace('Order_Frequency', 'OF') for n in combo_results.keys()]
combo_vals = list(combo_results.values())
colors2 = ['red' if v > 0.7 else 'orange' if v > 0.5 else 'steelblue' for v in combo_vals]
ax.barh(combo_names, combo_vals, color=colors2)
ax.set_xlabel('R² Score')
ax.set_title('조합 피처 예측력 (DecisionTree, max_depth=5)')
ax.axvline(x=0.7, color='red', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig(f'{FIG_DIR}leakage_residual_verification_s2.png', dpi=150, bbox_inches='tight')
plt.show()
```

**판정 기준:**
- 2~3-피처 조합 R² > 0.85 → 간접 누수 의심, 해당 피처 제거 고려
- R² < 0.7 → 간접 누수 아님 (소주제 1과 동일 기준)

---

### 항목 2: RandomizedSearchCV (자동 튜닝 검증)

**삽입 위치:** 셀 39 이후 (수동 튜닝 다음)

```python
# ========================================
# 6.3.1 RandomizedSearchCV — 자동 하이퍼파라미터 탐색
# ========================================
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint, uniform

print("=" * 60)
print("6.3.1 RandomizedSearchCV — XGBoost & Random Forest")
print("=" * 60)

# XGBoost 탐색 공간
xgb_param_dist = {
    'max_depth': randint(3, 8),
    'learning_rate': uniform(0.01, 0.2),
    'n_estimators': randint(100, 500),
    'subsample': uniform(0.6, 0.4),
    'colsample_bytree': uniform(0.6, 0.4),
    'reg_alpha': uniform(0, 1),
    'reg_lambda': uniform(0.5, 2),
    'min_child_weight': randint(1, 10)
}

xgb_random = RandomizedSearchCV(
    XGBRegressor(random_state=42, verbosity=0),
    param_distributions=xgb_param_dist,
    n_iter=50, cv=5, scoring='r2',
    random_state=42, n_jobs=-1
)
xgb_random.fit(X_train_scaled, y_train)

# RF 탐색 공간
rf_param_dist = {
    'n_estimators': randint(100, 500),
    'max_depth': randint(5, 20),
    'min_samples_split': randint(2, 20),
    'min_samples_leaf': randint(1, 10),
    'max_features': ['sqrt', 'log2', None]
}

rf_random = RandomizedSearchCV(
    RandomForestRegressor(random_state=42),
    param_distributions=rf_param_dist,
    n_iter=50, cv=5, scoring='r2',
    random_state=42, n_jobs=-1
)
rf_random.fit(X_train_scaled, y_train)

# 결과 비교
from sklearn.metrics import mean_squared_error, mean_absolute_error
import numpy as np

for name, model_rs, model_manual in [
    ('XGBoost', xgb_random, xgb_tuned),
    ('Random Forest', rf_random, rf_tuned)
]:
    y_pred_rs = model_rs.predict(X_test_scaled)
    y_pred_mn = model_manual.predict(X_test_scaled)
    r2_rs = model_rs.score(X_test_scaled, y_test)
    r2_mn = model_manual.score(X_test_scaled, y_test)
    print(f"\n{name}:")
    print(f"  수동 튜닝  → R²={r2_mn:.4f}, RMSE={np.sqrt(mean_squared_error(y_test, y_pred_mn)):.2f}")
    print(f"  RandomSearch → R²={r2_rs:.4f}, RMSE={np.sqrt(mean_squared_error(y_test, y_pred_rs)):.2f}")
    print(f"  Best params: {model_rs.best_params_}")
```

---

### 항목 3: Tuned 모델 5-Fold CV

**삽입 위치:** 셀 42 이후 (Default vs Tuned 비교 다음)

```python
# ========================================
# 6.4.1 Tuned 모델 교차검증 (5-Fold CV)
# ========================================
from sklearn.model_selection import cross_validate

print("=" * 60)
print("6.4.1 Tuned 모델 5-Fold 교차검증")
print("=" * 60)

tuned_models_cv = {
    'Linear Regression': lr_model,  # LR은 Default = Tuned
    'Ridge (Tuned)': ridge_tuned,
    'Lasso (Tuned)': lasso_tuned,
    'RF (Tuned)': rf_tuned,
    'XGB (Tuned)': xgb_tuned
}

cv_tuned_list = []
for name, model in tuned_models_cv.items():
    cv_res = cross_validate(model, X_train_scaled, y_train,
                            cv=5, scoring='r2',
                            return_train_score=True)
    train_mean = cv_res['train_score'].mean()
    val_mean = cv_res['test_score'].mean()
    val_std = cv_res['test_score'].std()
    gap = train_mean - val_mean
    cv_tuned_list.append({
        '모델': name, 'Train R² (CV)': train_mean,
        'Val R² (CV)': val_mean, 'Val Std': val_std, 'Gap': gap
    })
    print(f"  {name:25s} | Train={train_mean:.4f} | Val={val_mean:.4f}±{val_std:.4f} | Gap={gap:.4f}")

df_cv_tuned = pd.DataFrame(cv_tuned_list)

# Default vs Tuned CV 비교 (df_cv는 Default CV 결과)
print("\n--- Default vs Tuned CV Gap 비교 ---")
for _, row_t in df_cv_tuned.iterrows():
    name_t = row_t['모델']
    # Default CV에서 매칭
    d_name = name_t.replace(' (Tuned)', '')
    match = df_cv[df_cv['모델'] == d_name]
    if len(match) > 0:
        gap_d = match.iloc[0]['Gap']
        gap_t = row_t['Gap']
        change = '↓ 개선' if gap_t < gap_d else '↑ 악화' if gap_t > gap_d else '= 동일'
        print(f"  {name_t:25s} | Default Gap={gap_d:.4f} → Tuned Gap={gap_t:.4f} | {change}")
```

---

### 항목 4: Tuned 모델 Learning Curve

**삽입 위치:** 항목 3 다음

```python
# ========================================
# 6.4.2 Tuned 모델 Learning Curve
# ========================================
from sklearn.model_selection import learning_curve

print("=" * 60)
print("6.4.2 Tuned 모델 Learning Curve")
print("=" * 60)

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
axes = axes.flatten()

for idx, (name, model) in enumerate(tuned_models_cv.items()):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_train_scaled, y_train,
        cv=5, scoring='r2',
        train_sizes=np.linspace(0.1, 1.0, 10),
        n_jobs=-1, random_state=42
    )
    ax = axes[idx]
    ax.plot(train_sizes, train_scores.mean(axis=1), 'o-', color='red', label='Train')
    ax.plot(train_sizes, val_scores.mean(axis=1), 'o-', color='blue', label='Validation')
    ax.fill_between(train_sizes,
                    train_scores.mean(axis=1) - train_scores.std(axis=1),
                    train_scores.mean(axis=1) + train_scores.std(axis=1),
                    alpha=0.1, color='red')
    ax.fill_between(train_sizes,
                    val_scores.mean(axis=1) - val_scores.std(axis=1),
                    val_scores.mean(axis=1) + val_scores.std(axis=1),
                    alpha=0.1, color='blue')
    ax.set_title(name, fontsize=11)
    ax.set_xlabel('Training Size')
    ax.set_ylabel('R² Score')
    ax.legend(loc='lower right', fontsize=9)
    ax.set_ylim(0.7, 1.05)
    ax.grid(True, alpha=0.3)

# 마지막 빈 subplot 숨기기
if len(tuned_models_cv) < len(axes):
    for j in range(len(tuned_models_cv), len(axes)):
        axes[j].set_visible(False)

plt.suptitle('Learning Curve — Tuned 모델', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{FIG_DIR}learning_curve_tuned_s2.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

### 항목 5: 고판매량 구간 심층 분석

**삽입 위치:** 셀 50 이후 (잔차 분석 다음)

```python
# ========================================
# 7.2.2 고판매량 구간 과소예측 분석
# ========================================
print("=" * 60)
print("7.2.2 고판매량 구간 과소예측 분석")
print("=" * 60)

y_pred_best = best_model.predict(X_test_scaled)
residuals = y_test.values - y_pred_best

# 구간별 성능 분석
bins = [(0, 20, '저판매 (0~20)'),
        (20, 40, '중판매 (20~40)'),
        (40, 70, '고판매 (40~70)'),
        (70, 100, '초고판매 (70+)')]

segment_stats = []
for low, high, label in bins:
    mask = (y_test.values >= low) & (y_test.values < high)
    if mask.sum() > 0:
        seg_rmse = np.sqrt(np.mean(residuals[mask]**2))
        seg_mae = np.mean(np.abs(residuals[mask]))
        seg_bias = np.mean(residuals[mask])
        segment_stats.append({
            '구간': label, '건수': mask.sum(),
            'RMSE': seg_rmse, 'MAE': seg_mae,
            '평균 편향': seg_bias
        })
        print(f"  {label:20s} | N={mask.sum():3d} | RMSE={seg_rmse:.2f} | MAE={seg_mae:.2f} | Bias={seg_bias:+.2f}")

# 시각화
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# (A) 구간별 RMSE
df_seg = pd.DataFrame(segment_stats)
ax = axes[0]
colors = ['green', 'steelblue', 'orange', 'red'][:len(df_seg)]
ax.bar(df_seg['구간'], df_seg['RMSE'], color=colors)
ax.set_ylabel('RMSE')
ax.set_title('판매량 구간별 RMSE')
for i, row in df_seg.iterrows():
    ax.text(i, row['RMSE'] + 0.1, f"N={row['건수']}", ha='center', fontsize=9)

# (B) 구간별 편향
ax = axes[1]
bar_colors = ['green' if b < 0 else 'red' for b in df_seg['평균 편향']]
ax.bar(df_seg['구간'], df_seg['평균 편향'], color=bar_colors)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax.set_ylabel('평균 편향 (양수=과소예측)')
ax.set_title('판매량 구간별 예측 편향')

plt.tight_layout()
plt.savefig(f'{FIG_DIR}segment_analysis_s2.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

### 항목 6: SHAP Dependence Plot (핵심 피처 상호작용)

**삽입 위치:** 셀 60 이후 (SHAP Summary 다음)

```python
# ========================================
# 7.5.2 SHAP Dependence Plot — 핵심 피처 상호작용
# ========================================
import shap

print("=" * 60)
print("7.5.2 SHAP Dependence Plot — 피처 상호작용 분석")
print("=" * 60)

# TreeExplainer (회귀 모델은 2D array 반환)
explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_test_scaled)

# 상위 4개 피처에 대한 Dependence Plot
top_features = ['Order_Frequency_per_month', 'Reorder_Point',
                'Lead_Time_Days', 'Quantity_On_Hand']

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
for idx, feat in enumerate(top_features):
    ax = axes[idx // 2][idx % 2]
    feat_idx = list(X.columns).index(feat)
    shap.dependence_plot(
        feat_idx, shap_values,
        X_test_scaled if isinstance(X_test_scaled, np.ndarray) else X_test_scaled,
        feature_names=list(X.columns),
        ax=ax, show=False
    )
    ax.set_title(f'SHAP Dependence: {feat}', fontsize=11)

plt.suptitle('SHAP Dependence Plot — 핵심 피처 상호작용', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{FIG_DIR}shap_dependence_s2.png', dpi=150, bbox_inches='tight')
plt.show()
```

**기대 인사이트:**
- Order_Frequency의 비선형 기여 패턴
- Lead_Time_Days의 상호작용 대상 피처 식별
- Reorder_Point와 QOH의 관계 시각화

---

### 항목 7: 예측 오차 비대칭 분석

**삽입 위치:** 항목 5 다음

```python
# ========================================
# 7.2.3 예측 오차 비대칭 분석
# ========================================
print("=" * 60)
print("7.2.3 과대 vs 과소 예측 비대칭 분석")
print("=" * 60)

over_pred = residuals[residuals < 0]   # 과대 예측 (실제 < 예측)
under_pred = residuals[residuals > 0]  # 과소 예측 (실제 > 예측)

print(f"  과대 예측: {len(over_pred)}건, 평균 오차={over_pred.mean():.2f}")
print(f"  과소 예측: {len(under_pred)}건, 평균 오차={under_pred.mean():.2f}")
print(f"  정확 예측 (오차 < 2): {(np.abs(residuals) < 2).sum()}건")

# 비즈니스 관점: 과소예측(재고 부족) vs 과대예측(재고 과다)
print("\n--- 비즈니스 영향 분석 ---")
print(f"  과소 예측 → 판매 기회 손실 위험: {len(under_pred)}건 ({len(under_pred)/len(residuals)*100:.1f}%)")
print(f"  과대 예측 → 재고 과다/폐기 위험: {len(over_pred)}건 ({len(over_pred)/len(residuals)*100:.1f}%)")

# 시각화
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(over_pred, bins=20, alpha=0.7, color='blue', label=f'과대 예측 ({len(over_pred)}건)')
ax.hist(under_pred, bins=20, alpha=0.7, color='red', label=f'과소 예측 ({len(under_pred)}건)')
ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
ax.set_xlabel('잔차 (실제 - 예측)')
ax.set_ylabel('빈도')
ax.set_title('예측 오차 비대칭 분석 — 비즈니스 영향 관점')
ax.legend()
plt.tight_layout()
plt.savefig(f'{FIG_DIR}prediction_asymmetry_s2.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

### 항목 8: 결론 업데이트

**수정 위치:** 셀 66 (기존 결론 셀)

기존 결론에 다음 내용 추가:
- 잔존 누수 검증 결과
- RandomizedSearchCV 검증 결과
- Tuned CV/LC 결과
- 고판매량 구간 분석 결과
- SHAP Dependence 핵심 인사이트
- 예측 오차 비대칭 분석 결과

---

## 구현 순서 (권장)

### Phase 1: 신뢰성 검증 (우선)
1. **항목 1** — 잔존 누수 검증 (셀 30 이후)
2. **항목 2** — RandomizedSearchCV (셀 39 이후)

### Phase 2: 과적합 심층 검증
3. **항목 3** — Tuned 5-Fold CV (셀 42 이후)
4. **항목 4** — Tuned Learning Curve (항목 3 다음)

### Phase 3: 성능 심층 분석
5. **항목 5** — 고판매량 구간 분석 (셀 50 이후)
6. **항목 6** — SHAP Dependence Plot (셀 60 이후)
7. **항목 7** — 예측 오차 비대칭 분석 (항목 5 다음)

### Phase 4: 문서화
8. **항목 8** — 결론 업데이트 (셀 66)

---

## 주의사항

### 변수명 참조
- `best_model` — 최적 모델 (XGBoost Tuned)
- `X_train_scaled`, `X_test_scaled` — 스케일된 학습/테스트 데이터
- `y_train`, `y_test` — 타겟 변수
- `xgb_tuned`, `rf_tuned` — Tuned 모델 객체
- `lr_model`, `ridge_tuned`, `lasso_tuned` — 선형 모델 객체
- `df_cv` — Default CV 결과 DataFrame
- `X` — 인코딩 후 전체 피처 DataFrame (column names 보유)
- `FIG_DIR` — 그래프 저장 경로 (`outputs/figures/subtopic2_sales_prediction/`)

### SHAP 버전 호환성
- 회귀 모델에서는 `shap_values`가 2D ndarray (samples × features)로 반환 — 분류와 다름
- `shap.dependence_plot`은 2D 입력 기대 → 별도 변환 불필요

### 소주제 1과의 차이점
- 회귀 문제이므로 ROC-AUC, Confusion Matrix 해당 없음
- 대신 잔차 분석, 구간별 성능, 예측 편향 분석이 핵심
- 비용 민감 학습 대신 예측 오차 비대칭 분석으로 대체

---

## 예상 결과물

### 신규 생성 파일
| 파일 | 내용 |
| --- | --- |
| `leakage_residual_verification_s2.png` | 잔존 누수 검증 시각화 |
| `learning_curve_tuned_s2.png` | Tuned 모델 학습 곡선 |
| `segment_analysis_s2.png` | 고판매량 구간별 성능 분석 |
| `shap_dependence_s2.png` | SHAP Dependence Plot |
| `prediction_asymmetry_s2.png` | 예측 오차 비대칭 분석 |

### 예상 셀 수 변화
- 현재: 67셀
- 추가: ~14셀 (Markdown 6 + Code 8)
- 예상 최종: ~81셀
