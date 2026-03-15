#!/usr/bin/env python3
"""소주제 4 Enhanced 노트북 생성 스크립트"""
import json
import os

cells = []

def md(text):
    lines = text.strip().split("\n")
    formatted = [line + "\n" for line in lines[:-1]] + [lines[-1]]
    cells.append({"cell_type": "markdown", "metadata": {}, "source": formatted})

def code(text):
    lines = text.strip().split("\n")
    formatted = [line + "\n" for line in lines[:-1]] + [lines[-1]]
    cells.append({
        "cell_type": "code", "execution_count": None,
        "metadata": {}, "outputs": [], "source": formatted
    })

# ============================================================
# 0. Title + Import
# ============================================================
md("""# 소주제 4: 최적 발주 전략 클러스터링 — Enhanced (보강 데이터 통합)

> Phase A: 재고 회전율 예측 (회귀) + Phase B: 발주 패턴 클러스터링 (K-Means)
> Baseline vs Enhanced 비교 — EOQ·안전재고·수요변동성 파생변수 보강""")

code("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, mean_squared_error, r2_score
from sklearn.decomposition import PCA
import xgboost as xgb
import warnings
import os
import joblib
import glob

warnings.filterwarnings('ignore')
SEED = 42
np.random.seed(SEED)

sns.set_style('whitegrid')
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

FIGURE_DIR = '../outputs/figures/subtopic4_cluster'
MODEL_DIR = '../outputs/models'
os.makedirs(FIGURE_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
print("라이브러리 로드 완료")""")

# ============================================================
# 1. Data Load
# ============================================================
md("""## 1. 데이터 로드 및 기본 확인""")

code("""df = pd.read_csv('../data/Grocery_Inventory_and_Sales_Dataset.csv')
print(f"원본 데이터: {df.shape}")
print(f"\\n컬럼: {list(df.columns)}")
print(f"\\n타겟 — Inventory_Turnover_Rate 기초 통계:")
print(df['Inventory_Turnover_Rate'].describe())
print(f"\\n카테고리 분포:")
print(df['Catagory'].value_counts())""")

# ============================================================
# 2. Supplementary Data Exploration
# ============================================================
md("""## 2. 보강 데이터 탐색

| # | 데이터 | 활용 방식 |
|---|--------|-----------|
| ① | Inventory Optimization for Retail | EOQ·안전재고·비용 구조 참고 → 파생변수 설계 |
| ② | FMCG Supply Chain | FMCG 업종 벤치마크 비교 |
| ③ | Retail Inventory & Demand Forecasting | 수요 예측 기반 동적 ROP 개념 도입 |""")

md("""### 2.1 ① Inventory Optimization for Retail — EOQ·안전재고 개념 참고""")

code("""inv_opt_dir = glob.glob('../data/etc_subtopic4/Inventory Optimization for Retail*')[0]

df_inv_monitor = pd.read_csv(os.path.join(inv_opt_dir, 'inventory_monitoring.csv'))
df_inv_pricing = pd.read_csv(os.path.join(inv_opt_dir, 'pricing_optimization.csv'))
df_inv_demand = pd.read_csv(os.path.join(inv_opt_dir, 'demand_forecasting.csv'))

print("=== Inventory Monitoring ===")
print(f"크기: {df_inv_monitor.shape}")
print(f"컬럼: {list(df_inv_monitor.columns)}")
print(df_inv_monitor.describe().round(2))

print("\\n=== Pricing Optimization (Storage Cost 포함) ===")
print(f"크기: {df_inv_pricing.shape}")
print(f"Storage Cost 통계:")
print(df_inv_pricing['Storage Cost'].describe().round(2))

print("\\n=== 핵심 통계 요약 (파생변수 설계 근거) ===")
print(f"  중위 리드타임: {df_inv_monitor['Supplier Lead Time (days)'].median():.0f}일")
print(f"  중위 재주문점: {df_inv_monitor['Reorder Point'].median():.0f}")
print(f"  평균 품절빈도: {df_inv_monitor['Stockout Frequency'].mean():.1f}회")
print(f"  중위 보관비용: {df_inv_pricing['Storage Cost'].median():.2f}")
holding_ratio = (df_inv_pricing['Storage Cost'] / df_inv_pricing['Price'].replace(0, np.nan)).median()
print(f"  보유비용 비율(보관비/가격): {holding_ratio:.2%}")
print(f"\\n→ 보유비용 비율 ≈ 20% 가정의 타당성: 실제 중위 비율 {holding_ratio:.1%} 기반 확인")""")

md("""### 2.2 ② FMCG Supply Chain — 업종 벤치마크""")

code("""df_fmcg = pd.read_csv('../data/etc_subtopic4/Supply Chain Optimization for a FMCG Company/FMCG_data.csv')
print(f"FMCG 데이터 크기: {df_fmcg.shape}")
print(f"컬럼: {list(df_fmcg.columns)}")

print("\\n=== FMCG 공급망 운영 패턴 ===")
print(f"  평균 보충 요청 (최근 3개월): {df_fmcg['num_refill_req_l3m'].mean():.1f}회")
print(f"  평균 운송 이슈 (최근 1년): {df_fmcg['transport_issue_l1y'].mean():.1f}건")
print(f"  평균 보관 이슈 (최근 3개월): {df_fmcg['storage_issue_reported_l3m'].mean():.1f}건")
print(f"  평균 고장/중단 (최근 3개월): {df_fmcg['wh_breakdown_l3m'].mean():.1f}건")
print(f"  평균 제품 중량 (톤): {df_fmcg['product_wg_ton'].mean():.0f}")

print("\\n=== 창고 소유 유형별 비교 ===")
fmcg_by_owner = df_fmcg.groupby('wh_owner_type').agg({
    'num_refill_req_l3m': 'mean',
    'storage_issue_reported_l3m': 'mean',
    'product_wg_ton': 'mean'
}).round(2)
print(fmcg_by_owner)

print("\\n=== 지역별 FMCG 패턴 ===")
fmcg_by_zone = df_fmcg.groupby('zone').agg({
    'num_refill_req_l3m': 'mean',
    'product_wg_ton': 'mean',
    'wh_breakdown_l3m': 'mean'
}).round(2)
print(fmcg_by_zone)""")

md("""### 2.3 ③ Retail Inventory & Demand Forecasting — 동적 ROP 개념""")

code("""df_sc = pd.read_csv('../data/etc_subtopic4/supply_chain_dataset1.csv')
print(f"Supply Chain 데이터 크기: {df_sc.shape}")
print(f"컬럼: {list(df_sc.columns)}")
print(df_sc.describe().round(2))

print("\\n=== 동적 ROP 관련 핵심 통계 ===")
print(f"  중위 수요예측량: {df_sc['Demand_Forecast'].median():.1f}")
print(f"  중위 재고수준: {df_sc['Inventory_Level'].median():.0f}")
print(f"  중위 리드타임: {df_sc['Supplier_Lead_Time_Days'].median():.0f}일")
print(f"  중위 재주문점: {df_sc['Reorder_Point'].median():.0f}")
print(f"  품절률: {df_sc['Stockout_Flag'].mean():.1%}")

print("\\n=== 리드타임별 품절률 (ROP 설계 참고) ===")
lt_bins = pd.cut(df_sc['Supplier_Lead_Time_Days'], bins=[0, 5, 10, 15, 20, 30])
stockout_by_lt = df_sc.groupby(lt_bins, observed=True)['Stockout_Flag'].mean()
for lt_range, rate in stockout_by_lt.items():
    print(f"  리드타임 {lt_range}: 품절률 {rate:.1%}")
print("\\n→ 리드타임이 길수록 품절 위험 ↑ → Safety Stock + Dynamic ROP 필요")""")

# ============================================================
# 3. Preprocessing + Derived Features
# ============================================================
md("""## 3. 전처리 + 보강 파생변수 생성

| 파생변수 | 수식 | 출처 |
|----------|------|------|
| Supply_Lead_Gap | (Date_Received - Last_Order_Date).days | 원본 |
| Demand_Variability | 카테고리 내 Sales_Volume CV (std/mean) | ① 참고 |
| Safety_Stock_Proxy | Z × CV × √(lead_time) × daily_sales | ① 참고 |
| EOQ_Proxy | √(2 × D × S / H) | ① 참고 |
| Reorder_Efficiency | Reorder_Quantity / EOQ_Proxy | ① 참고 |
| Stock_Safety_Gap | Stock_Quantity - Safety_Stock_Proxy | ① 참고 |
| Dynamic_ROP | (daily_sales × lead_time) + Safety_Stock | ③ 참고 |
| ROP_Coverage_Ratio | Stock_Quantity / Dynamic_ROP | ③ 참고 |

> EOQ 가정: 발주비용(S) = Unit_Price, 보유비용(H) = Unit_Price × 20% (시뮬레이션)""")

code("""# 날짜 변환 + Supply_Lead_Gap
df['Date_Received'] = pd.to_datetime(df['Date_Received'])
df['Last_Order_Date'] = pd.to_datetime(df['Last_Order_Date'])
df['Supply_Lead_Gap'] = (df['Date_Received'] - df['Last_Order_Date']).dt.days

# ── 방식 A: EOQ·안전재고 파생변수 ──
cat_cv = df.groupby('Catagory')['Sales_Volume'].agg(['mean', 'std'])
cat_cv['CV'] = cat_cv['std'] / cat_cv['mean']
df['Demand_Variability'] = df['Catagory'].map(cat_cv['CV'])

df['Safety_Stock_Proxy'] = 1.65 * df['Demand_Variability'] * np.sqrt(
    df['Supply_Lead_Gap'].clip(lower=1).abs()
) * df['Sales_Volume'] / 30

df['Annual_Demand_Est'] = df['Sales_Volume'] * 12
df['EOQ_Proxy'] = np.sqrt(
    2 * df['Annual_Demand_Est'] * df['Unit_Price'] /
    (df['Unit_Price'] * 0.2).replace(0, 1)
)

df['Reorder_Efficiency'] = (
    df['Reorder_Quantity'] / df['EOQ_Proxy'].replace(0, np.nan)
).fillna(1).clip(upper=5)

df['Stock_Safety_Gap'] = df['Stock_Quantity'] - df['Safety_Stock_Proxy']

# ── 방식 C: 동적 ROP ──
df['Dynamic_ROP'] = (
    (df['Sales_Volume'] / 30) * df['Supply_Lead_Gap'].clip(lower=1).abs()
    + df['Safety_Stock_Proxy']
)
df['ROP_Coverage_Ratio'] = (
    df['Stock_Quantity'] / df['Dynamic_ROP'].replace(0, np.nan)
).fillna(1).clip(upper=10)

# 카테고리 One-Hot
df_encoded = pd.get_dummies(df, columns=['Catagory'], prefix='Catagory', drop_first=False)
cat_cols = [c for c in df_encoded.columns if c.startswith('Catagory_')]

print("보강 파생변수 생성 완료")
derived_cols = ['Supply_Lead_Gap', 'Demand_Variability', 'Safety_Stock_Proxy',
                'EOQ_Proxy', 'Reorder_Efficiency', 'Stock_Safety_Gap',
                'Dynamic_ROP', 'ROP_Coverage_Ratio']
print(f"\\n파생변수 통계:")
print(df[derived_cols].describe().round(2))""")

# ============================================================
# 4. EDA
# ============================================================
md("""## 4. EDA — 주요 변수 탐색""")

code("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(df['Inventory_Turnover_Rate'], bins=30, color='#3498db',
             edgecolor='white', alpha=0.8)
axes[0].set_title('재고 회전율 분포', fontsize=14)
axes[0].set_xlabel('Inventory_Turnover_Rate')
axes[0].set_ylabel('빈도')

sns.boxplot(data=df, x='Catagory', y='Inventory_Turnover_Rate',
            ax=axes[1], palette='Set2')
axes[1].set_title('카테고리별 재고 회전율', fontsize=14)
axes[1].tick_params(axis='x', rotation=30)

plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'turnover_rate_distribution.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

code("""scatter_features = ['Sales_Volume', 'Stock_Quantity', 'Unit_Price',
                    'Reorder_Level', 'EOQ_Proxy', 'Safety_Stock_Proxy']
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
for idx, feat in enumerate(scatter_features):
    ax = axes[idx // 3][idx % 3]
    ax.scatter(df[feat], df['Inventory_Turnover_Rate'],
               alpha=0.4, s=20, color='#2ecc71')
    ax.set_xlabel(feat)
    ax.set_ylabel('Turnover Rate')
    ax.set_title(f'{feat} vs 회전율')
plt.suptitle('주요 피처 vs 재고 회전율', fontsize=16, y=1.02)
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'feature_vs_turnover.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

# ============================================================
# 5. Phase A — Regression
# ============================================================
md("""## 5. Phase A — 재고 회전율 예측 (Baseline vs Enhanced)

| 구분 | 피처 | 모델 |
|------|------|------|
| Baseline | 원본 수치 5개 + 카테고리 더미 | RandomForest, XGBoost |
| Enhanced | + EOQ·안전재고·수요변동성·동적ROP 7개 | RandomForest, XGBoost |""")

code("""baseline_num = ['Unit_Price', 'Sales_Volume', 'Stock_Quantity',
                'Reorder_Level', 'Reorder_Quantity']
baseline_features_A = baseline_num + cat_cols

enhanced_extra_A = ['Supply_Lead_Gap', 'Demand_Variability', 'Safety_Stock_Proxy',
                    'EOQ_Proxy', 'Reorder_Efficiency', 'Stock_Safety_Gap', 'Dynamic_ROP']
enhanced_features_A = baseline_features_A + enhanced_extra_A

target_A = 'Inventory_Turnover_Rate'
y = df_encoded[target_A]

print(f"Baseline 피처 ({len(baseline_features_A)}개)")
print(f"Enhanced 피처 ({len(enhanced_features_A)}개)")
print(f"  보강 피처: {enhanced_extra_A}")

X_train_b, X_test_b, y_train, y_test = train_test_split(
    df_encoded[baseline_features_A], y, test_size=0.2, random_state=SEED)
X_train_e, X_test_e, _, _ = train_test_split(
    df_encoded[enhanced_features_A], y, test_size=0.2, random_state=SEED)

scaler_Ab = StandardScaler()
X_train_b_sc = scaler_Ab.fit_transform(X_train_b)
X_test_b_sc = scaler_Ab.transform(X_test_b)

scaler_Ae = StandardScaler()
X_train_e_sc = scaler_Ae.fit_transform(X_train_e)
X_test_e_sc = scaler_Ae.transform(X_test_e)
print(f"\\nTrain: {X_train_b_sc.shape[0]}건 / Test: {X_test_b_sc.shape[0]}건")""")

code("""def run_regression(X_train, X_test, y_train, y_test, label):
    results = {}
    # Random Forest
    rf = RandomForestRegressor(n_estimators=100, random_state=SEED)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    results['RandomForest'] = {
        'model': rf,
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
        'r2': r2_score(y_test, y_pred),
        'y_pred': y_pred
    }
    # XGBoost
    xgb_model = xgb.XGBRegressor(
        n_estimators=100, max_depth=6, learning_rate=0.1,
        objective='reg:squarederror', random_state=SEED, verbosity=0)
    xgb_model.fit(X_train, y_train)
    y_pred = xgb_model.predict(X_test)
    results['XGBoost'] = {
        'model': xgb_model,
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
        'r2': r2_score(y_test, y_pred),
        'y_pred': y_pred
    }
    print(f"\\n=== {label} ===")
    for name, res in results.items():
        print(f"  {name:15s} | RMSE: {res['rmse']:.4f} | R²: {res['r2']:.4f}")
    return results

results_baseline = run_regression(
    X_train_b_sc, X_test_b_sc, y_train, y_test, "Baseline (원본 피처)")
results_enhanced = run_regression(
    X_train_e_sc, X_test_e_sc, y_train, y_test, "Enhanced (보강 피처)")""")

# ============================================================
# 6. Phase A Comparison
# ============================================================
md("""### 5.2 Phase A 성능 비교""")

code("""print("=" * 70)
print("Phase A: Baseline vs Enhanced 성능 비교")
print("=" * 70)

comp_data = []
for mn in ['RandomForest', 'XGBoost']:
    bl = results_baseline[mn]
    en = results_enhanced[mn]
    imp = (en['r2'] - bl['r2']) / max(abs(bl['r2']), 0.0001) * 100
    comp_data.append({'모델': mn, 'BL_RMSE': bl['rmse'], 'EN_RMSE': en['rmse'],
                      'BL_R²': bl['r2'], 'EN_R²': en['r2'], 'R²_향상률': imp})
    print(f"  {mn:15s} | BL R²: {bl['r2']:.4f} → EN R²: {en['r2']:.4f} | 향상: {imp:+.1f}%")

df_comp = pd.DataFrame(comp_data)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
x = np.arange(len(df_comp))
w = 0.35

axes[0].bar(x - w/2, df_comp['BL_RMSE'], w, label='Baseline', color='#95a5a6')
axes[0].bar(x + w/2, df_comp['EN_RMSE'], w, label='Enhanced', color='#e74c3c')
axes[0].set_xticks(x)
axes[0].set_xticklabels(df_comp['모델'])
axes[0].set_ylabel('RMSE (↓)')
axes[0].set_title('RMSE 비교', fontsize=14)
axes[0].legend()

axes[1].bar(x - w/2, df_comp['BL_R²'], w, label='Baseline', color='#95a5a6')
axes[1].bar(x + w/2, df_comp['EN_R²'], w, label='Enhanced', color='#2ecc71')
axes[1].set_xticks(x)
axes[1].set_xticklabels(df_comp['모델'])
axes[1].set_ylabel('R² (↑)')
axes[1].set_title('R² Score 비교', fontsize=14)
axes[1].legend()

plt.suptitle('Phase A: Baseline vs Enhanced 성능 비교', fontsize=16, y=1.02)
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'phaseA_comparison.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

code("""best_model_name = max(results_enhanced, key=lambda k: results_enhanced[k]['r2'])
best_result = results_enhanced[best_model_name]

fig, ax = plt.subplots(figsize=(8, 8))
ax.scatter(y_test, best_result['y_pred'], alpha=0.5, s=30, color='#3498db')
lims = [min(y_test.min(), best_result['y_pred'].min()),
        max(y_test.max(), best_result['y_pred'].max())]
ax.plot(lims, lims, 'r--', linewidth=2, label='y=x (이상적)')
ax.set_xlabel('실제 회전율', fontsize=12)
ax.set_ylabel('예측 회전율', fontsize=12)
ax.set_title(f'실제 vs 예측 — {best_model_name} Enhanced (R²={best_result["r2"]:.4f})', fontsize=14)
ax.legend()
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'actual_vs_predicted_turnover.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

code("""best_model = best_result['model']
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    feat_imp = pd.Series(importances, index=enhanced_features_A).sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ['#e74c3c' if f in enhanced_extra_A else '#3498db' for f in feat_imp.index]
    feat_imp.plot(kind='barh', ax=ax, color=colors)
    ax.set_xlabel('Feature Importance')
    ax.set_title(f'피처 중요도 — {best_model_name} Enhanced', fontsize=14)

    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='#e74c3c', label='보강 파생변수 ★'),
                       Patch(facecolor='#3498db', label='원본 피처')]
    ax.legend(handles=legend_elements, loc='lower right')

    plt.tight_layout()
    fname = os.path.join(FIGURE_DIR, 'feature_importance_turnover.png')
    plt.savefig(fname, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"저장 완료: {os.path.basename(fname)}")

    print("\\n=== 피처 중요도 (내림차순) ===")
    for feat, imp in feat_imp.sort_values(ascending=False).items():
        marker = "★" if feat in enhanced_extra_A else " "
        print(f"  {marker} {feat:30s}: {imp:.4f}")""")

# ============================================================
# 7-8. Phase B — Clustering
# ============================================================
md("""## 6. Phase B — 발주 패턴 클러스터링

| 구분 | 피처 수 | 피처 |
|------|---------|------|
| Baseline | 4 | Stock_Quantity, Reorder_Level, Reorder_Quantity, Inventory_Turnover_Rate |
| Enhanced | 7 | + EOQ_Proxy, Safety_Stock_Proxy, Demand_Variability |""")

code("""baseline_cluster_features = ['Stock_Quantity', 'Reorder_Level',
                             'Reorder_Quantity', 'Inventory_Turnover_Rate']
enhanced_cluster_features = baseline_cluster_features + [
    'EOQ_Proxy', 'Safety_Stock_Proxy', 'Demand_Variability']

X_clust_b = df_encoded[baseline_cluster_features].values
X_clust_e = df_encoded[enhanced_cluster_features].values

scaler_cb = StandardScaler()
X_clust_b_sc = scaler_cb.fit_transform(X_clust_b)
scaler_ce = StandardScaler()
X_clust_e_sc = scaler_ce.fit_transform(X_clust_e)

print(f"Baseline 클러스터링 피처 ({len(baseline_cluster_features)}개): {baseline_cluster_features}")
print(f"Enhanced 클러스터링 피처 ({len(enhanced_cluster_features)}개): {enhanced_cluster_features}")""")

code("""K_range = range(2, 8)
results_clustering = {}

for name, X_sc in [('Baseline', X_clust_b_sc), ('Enhanced', X_clust_e_sc)]:
    inertias = []
    silhouettes = []
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=SEED, n_init=10)
        labels = km.fit_predict(X_sc)
        inertias.append(km.inertia_)
        sil = silhouette_score(X_sc, labels)
        silhouettes.append(sil)
    results_clustering[name] = {'inertias': inertias, 'silhouettes': silhouettes}

    print(f"\\n=== {name} 클러스터링 ===")
    for k, sil in zip(K_range, silhouettes):
        print(f"  K={k}: Silhouette = {sil:.4f}")""")

code("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for name, color in [('Baseline', '#95a5a6'), ('Enhanced', '#e74c3c')]:
    axes[0].plot(list(K_range), results_clustering[name]['inertias'],
                 'o-', label=name, color=color, linewidth=2)
axes[0].set_xlabel('K (클러스터 수)')
axes[0].set_ylabel('Inertia')
axes[0].set_title('Elbow Method 비교', fontsize=14)
axes[0].legend()

for name, color in [('Baseline', '#95a5a6'), ('Enhanced', '#2ecc71')]:
    axes[1].plot(list(K_range), results_clustering[name]['silhouettes'],
                 'o-', label=name, color=color, linewidth=2)
axes[1].set_xlabel('K (클러스터 수)')
axes[1].set_ylabel('Silhouette Score')
axes[1].set_title('Silhouette Score 비교', fontsize=14)
axes[1].legend()

plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'elbow_comparison.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")

# Silhouette 막대 비교
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(K_range))
w = 0.35
ax.bar(x - w/2, results_clustering['Baseline']['silhouettes'], w,
       label='Baseline (4피처)', color='#95a5a6')
ax.bar(x + w/2, results_clustering['Enhanced']['silhouettes'], w,
       label='Enhanced (7피처)', color='#2ecc71')
ax.set_xticks(x)
ax.set_xticklabels([f'K={k}' for k in K_range])
ax.set_ylabel('Silhouette Score')
ax.set_title('Baseline vs Enhanced Silhouette Score 비교', fontsize=14)
ax.legend()
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'silhouette_comparison.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

code("""best_k_b = list(K_range)[np.argmax(results_clustering['Baseline']['silhouettes'])]
best_k_e = list(K_range)[np.argmax(results_clustering['Enhanced']['silhouettes'])]
best_sil_b = max(results_clustering['Baseline']['silhouettes'])
best_sil_e = max(results_clustering['Enhanced']['silhouettes'])

print(f"Baseline 최적 K={best_k_b} (Silhouette: {best_sil_b:.4f})")
print(f"Enhanced 최적 K={best_k_e} (Silhouette: {best_sil_e:.4f})")

optimal_k = best_k_e
print(f"\\n→ Enhanced 기준 최적 K={optimal_k}로 클러스터링 수행")""")

code("""# Baseline 클러스터링 + PCA
km_baseline = KMeans(n_clusters=optimal_k, random_state=SEED, n_init=10)
df_encoded['Cluster_Baseline'] = km_baseline.fit_predict(X_clust_b_sc)

pca_b = PCA(n_components=2, random_state=SEED)
X_pca_b = pca_b.fit_transform(X_clust_b_sc)
var_b = pca_b.explained_variance_ratio_.sum()

fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(X_pca_b[:, 0], X_pca_b[:, 1],
                     c=df_encoded['Cluster_Baseline'], cmap='Set2',
                     alpha=0.6, s=30, edgecolors='white', linewidth=0.5)
ax.set_xlabel(f'PC1 ({pca_b.explained_variance_ratio_[0]:.1%})')
ax.set_ylabel(f'PC2 ({pca_b.explained_variance_ratio_[1]:.1%})')
ax.set_title(f'Baseline 클러스터링 — PCA 2D (K={optimal_k}, 설명분산: {var_b:.1%})', fontsize=14)
plt.colorbar(scatter, label='Cluster')
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'pca_clusters_baseline.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

code("""# Enhanced 클러스터링 + PCA
km_enhanced_model = KMeans(n_clusters=optimal_k, random_state=SEED, n_init=10)
df_encoded['Cluster_Enhanced'] = km_enhanced_model.fit_predict(X_clust_e_sc)

pca_e = PCA(n_components=2, random_state=SEED)
X_pca_e = pca_e.fit_transform(X_clust_e_sc)
var_e = pca_e.explained_variance_ratio_.sum()

fig, ax = plt.subplots(figsize=(10, 8))
scatter = ax.scatter(X_pca_e[:, 0], X_pca_e[:, 1],
                     c=df_encoded['Cluster_Enhanced'], cmap='Set2',
                     alpha=0.6, s=30, edgecolors='white', linewidth=0.5)
ax.set_xlabel(f'PC1 ({pca_e.explained_variance_ratio_[0]:.1%})')
ax.set_ylabel(f'PC2 ({pca_e.explained_variance_ratio_[1]:.1%})')
ax.set_title(f'Enhanced 클러스터링 — PCA 2D (K={optimal_k}, 설명분산: {var_e:.1%})', fontsize=14)
plt.colorbar(scatter, label='Cluster')
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'pca_clusters_enhanced.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")

sil_b = silhouette_score(X_clust_b_sc, df_encoded['Cluster_Baseline'])
sil_e = silhouette_score(X_clust_e_sc, df_encoded['Cluster_Enhanced'])
print(f"\\nSilhouette 비교 (K={optimal_k}):")
print(f"  Baseline: {sil_b:.4f}")
print(f"  Enhanced: {sil_e:.4f}")
print(f"  변화: {sil_e - sil_b:+.4f}")""")

# ============================================================
# 10. Cluster Interpretation
# ============================================================
md("""## 7. 군집 해석 + EOQ 기반 발주 전략 제안""")

code("""df['Cluster_Enhanced'] = df_encoded['Cluster_Enhanced'].values

summary_cols = list(dict.fromkeys(
    enhanced_cluster_features + ['Unit_Price', 'Sales_Volume',
    'Reorder_Efficiency', 'Dynamic_ROP', 'Stock_Safety_Gap', 'ROP_Coverage_Ratio']
))
cluster_summary = df.groupby('Cluster_Enhanced')[summary_cols].mean().round(2)
cluster_summary['제품 수'] = df.groupby('Cluster_Enhanced').size().values
cluster_summary['주요 카테고리'] = df.groupby('Cluster_Enhanced')['Catagory'].agg(
    lambda x: x.mode()[0]).values

print("=== Enhanced 군집별 요약 ===")
print(cluster_summary.T.to_string())""")

code("""# 레이더 차트 (Enhanced 7피처)
radar_features = enhanced_cluster_features
n_features = len(radar_features)
angles = np.linspace(0, 2 * np.pi, n_features, endpoint=False).tolist()
angles += angles[:1]

cluster_means = df.groupby('Cluster_Enhanced')[radar_features].mean()
cluster_normalized = (cluster_means - cluster_means.min()) / (cluster_means.max() - cluster_means.min() + 1e-10)

colors_radar = plt.cm.Set2(np.linspace(0, 1, optimal_k))
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
for cid in range(optimal_k):
    values = cluster_normalized.loc[cid].tolist()
    values += values[:1]
    ax.plot(angles, values, 'o-', linewidth=2, label=f'Cluster {cid}',
            color=colors_radar[cid])
    ax.fill(angles, values, alpha=0.15, color=colors_radar[cid])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(radar_features, fontsize=9)
ax.set_title(f'Enhanced 군집별 레이더 차트 (K={optimal_k})', fontsize=14, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'radar_chart_enhanced.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

code("""# 카테고리별 군집 분포
ct = pd.crosstab(df['Catagory'], df['Cluster_Enhanced'], normalize='index')
fig, ax = plt.subplots(figsize=(12, 6))
ct.plot(kind='bar', stacked=True, ax=ax, colormap='Set2', edgecolor='white')
ax.set_title(f'카테고리별 군집 분포 (K={optimal_k})', fontsize=14)
ax.set_xlabel('카테고리')
ax.set_ylabel('비율')
ax.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.tick_params(axis='x', rotation=30)
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'category_cluster_distribution.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

code("""# 군집별 EOQ·안전재고·ROP 비교
eoq_cols = ['EOQ_Proxy', 'Safety_Stock_Proxy', 'Dynamic_ROP']
eoq_summary = df.groupby('Cluster_Enhanced')[eoq_cols].mean()

fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(optimal_k)
w = 0.25
label_map = {'EOQ_Proxy': 'EOQ (경제적 발주량)',
             'Safety_Stock_Proxy': '안전재고',
             'Dynamic_ROP': '동적 재주문점'}
for i, col in enumerate(eoq_cols):
    ax.bar(x + i * w, eoq_summary[col], w, label=label_map[col])
ax.set_xticks(x + w)
ax.set_xticklabels([f'Cluster {i}' for i in range(optimal_k)])
ax.set_ylabel('수량')
ax.set_title('군집별 EOQ·안전재고·ROP 비교', fontsize=14)
ax.legend()
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'cluster_eoq_comparison.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

code("""print("=" * 70)
print("군집별 EOQ 기반 최적 발주 전략 제안")
print("=" * 70)

for cid in range(optimal_k):
    mask = df['Cluster_Enhanced'] == cid
    subset = df[mask]
    avg_eoq = subset['EOQ_Proxy'].mean()
    avg_safety = subset['Safety_Stock_Proxy'].mean()
    avg_rop = subset['Dynamic_ROP'].mean()
    avg_eff = subset['Reorder_Efficiency'].mean()
    avg_turn = subset['Inventory_Turnover_Rate'].mean()
    avg_stock = subset['Stock_Quantity'].mean()
    main_cat = subset['Catagory'].mode()[0]
    n = len(subset)

    print(f"\\n{'━' * 50}")
    print(f"Cluster {cid} ({n}개 제품, 주요: {main_cat})")
    print(f"{'━' * 50}")
    print(f"  평균 EOQ (경제적 발주량): {avg_eoq:.1f}")
    print(f"  평균 안전재고 수준:       {avg_safety:.1f}")
    print(f"  평균 재주문점 (ROP):      {avg_rop:.1f}")
    print(f"  발주 효율 (실제/EOQ):     {avg_eff:.2f}")
    print(f"  평균 회전율:              {avg_turn:.1f}")
    print(f"  평균 현재 재고:           {avg_stock:.1f}")

    if avg_turn > 60:
        strategy = "Fast Mover — 소량 빈번 발주 (JIT), 안전재고 최소화"
    elif avg_turn < 30:
        strategy = "Slow Mover — 재주문점 하향, 프로모션 소진, 발주량 축소"
    else:
        strategy = "Balanced — 현행 유지, EOQ 기반 미세 조정"
    print(f"  → 전략: {strategy}")

    if avg_eff > 1.5:
        print(f"  ⚠️ 현재 발주량이 EOQ 대비 {avg_eff:.1f}배 → 과잉 발주 주의")
    elif avg_eff < 0.5:
        print(f"  ⚠️ 현재 발주량이 EOQ 대비 {avg_eff:.1f}배 → 과소 발주, 품절 리스크")""")

# ============================================================
# 11. FMCG Benchmark
# ============================================================
md("""## 8. FMCG 벤치마크 비교""")

code("""original_stats = df.groupby('Catagory').agg({
    'Reorder_Level': 'mean',
    'Reorder_Quantity': 'mean',
    'Inventory_Turnover_Rate': 'mean',
    'EOQ_Proxy': 'mean',
    'Safety_Stock_Proxy': 'mean'
}).round(2)

print("=== 원본 데이터 카테고리별 발주 패턴 ===")
print(original_stats)

print(f"\\n=== Supply Chain 벤치마크 요약 ===")
print(f"  벤치마크 평균 재주문점: {df_sc['Reorder_Point'].mean():.0f}")
print(f"  벤치마크 평균 발주수량: {df_sc['Order_Quantity'].mean():.0f}")
print(f"  벤치마크 평균 리드타임: {df_sc['Supplier_Lead_Time_Days'].mean():.0f}일")
print(f"  벤치마크 품절률:       {df_sc['Stockout_Flag'].mean():.1%}")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

axes[0].bar(range(len(original_stats)), original_stats['Reorder_Level'],
            color='#3498db', alpha=0.8)
axes[0].axhline(y=df_sc['Reorder_Point'].mean(), color='#e74c3c', linestyle='--',
                linewidth=2, label=f'벤치마크 평균: {df_sc["Reorder_Point"].mean():.0f}')
axes[0].set_xticks(range(len(original_stats)))
axes[0].set_xticklabels(original_stats.index, rotation=30, fontsize=8)
axes[0].set_title('재주문점 비교', fontsize=13)
axes[0].legend()

axes[1].bar(range(len(original_stats)), original_stats['Reorder_Quantity'],
            color='#2ecc71', alpha=0.8)
axes[1].axhline(y=df_sc['Order_Quantity'].mean(), color='#e74c3c', linestyle='--',
                linewidth=2, label=f'벤치마크 평균: {df_sc["Order_Quantity"].mean():.0f}')
axes[1].set_xticks(range(len(original_stats)))
axes[1].set_xticklabels(original_stats.index, rotation=30, fontsize=8)
axes[1].set_title('발주 수량 비교', fontsize=13)
axes[1].legend()

axes[2].bar(['벤치마크'], [df_sc['Stockout_Flag'].mean()], color='#e74c3c', alpha=0.8)
axes[2].set_ylabel('품절률')
axes[2].set_title(f'벤치마크 품절률: {df_sc["Stockout_Flag"].mean():.1%}', fontsize=13)

plt.suptitle('원본 데이터 vs Supply Chain 벤치마크', fontsize=16, y=1.02)
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'fmcg_benchmark.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

# ============================================================
# 12. Cross-subtopic Synthesis
# ============================================================
md("""## 9. 소주제 간 종합 연결 인사이트""")

code("""# 군집별 Waste Risk 비율 (소주제 3 연결)
cat_sales_period = {
    'Seafood': 7, 'Dairy': 14, 'Fruits & Vegetables': 10,
    'Bakery': 7, 'Beverages': 60, 'Grains & Pulses': 90, 'Oils & Fats': 90
}
df['Sales_Period'] = df['Catagory'].map(cat_sales_period)
df['Days_To_Deplete'] = df['Stock_Quantity'] / (df['Sales_Volume'] / 30).replace(0, np.nan)
df['Waste_Risk'] = (df['Days_To_Deplete'] > df['Days_To_Expiry']).astype(int)

risk_by_cluster = df.groupby('Cluster_Enhanced')['Waste_Risk'].mean()

fig, ax = plt.subplots(figsize=(10, 6))
colors_risk = ['#2ecc71' if v < 0.5 else '#e74c3c' for v in risk_by_cluster]
risk_by_cluster.plot(kind='bar', ax=ax, color=colors_risk, edgecolor='white')
ax.set_title('군집별 폐기 위험 비율 (소주제 3 연결)', fontsize=14)
ax.set_xlabel('Cluster')
ax.set_ylabel('Waste Risk 비율')
ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
for i, v in enumerate(risk_by_cluster):
    ax.text(i, v + 0.02, f'{v:.1%}', ha='center', fontsize=12, fontweight='bold')
plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'cluster_waste_risk.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")

print("\\n=== 군집별 Waste Risk 비율 ===")
for c, r in risk_by_cluster.items():
    print(f"  Cluster {c}: {r:.1%}")""")

code("""# 프로젝트 종합 연결 다이어그램
fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')

ax.text(8, 9.5, '머신러닝 기반 식료품 유통 재고 관리 최적화 시스템',
        fontsize=16, ha='center', fontweight='bold', color='#2c3e50')
ax.text(8, 9.0, '소주제 1~4 종합 연결 다이어그램',
        fontsize=12, ha='center', color='#7f8c8d')

topics = [
    (2, 7, '소주제 1\\n제품 중단 예측\\n(이진 분류)', '#3498db'),
    (6, 7, '소주제 2\\n판매량 예측\\n(회귀)', '#2ecc71'),
    (10, 7, '소주제 3\\n폐기 위험도 예측\\n(이진 분류)', '#e74c3c'),
    (14, 7, '소주제 4\\n발주 전략 군집화\\n(회귀+클러스터링)', '#9b59b6'),
]
for x, y, text, color in topics:
    bbox = dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.3, edgecolor=color)
    ax.text(x, y, text, fontsize=10, ha='center', va='center', bbox=bbox)

connections = [
    (2, 6, '중단 제품 →\\n판매량 영향', 6.3),
    (6, 10, 'Sales_Volume →\\nDaily_Sales 정밀화', 6.3),
    (10, 14, 'Waste_Risk →\\n군집별 Risk 비율', 6.3),
    (2, 14, 'Discontinued →\\n군집 분포 분석', 5.5),
]
for x1, x2, text, y_pos in connections:
    ax.annotate('', xy=(x2 - 0.5, y_pos), xytext=(x1 + 0.5, y_pos),
                arrowprops=dict(arrowstyle='->', color='#34495e', lw=1.5))
    ax.text((x1 + x2) / 2, y_pos + 0.3, text, fontsize=8, ha='center', color='#34495e')

ax.text(8, 3.8, '최종 액션 플랜', fontsize=14, ha='center',
        fontweight='bold', color='#2c3e50')
for cid in range(optimal_k):
    mask = df['Cluster_Enhanced'] == cid
    avg_turn = df.loc[mask, 'Inventory_Turnover_Rate'].mean()
    main_cat = df.loc[mask, 'Catagory'].mode()[0]
    n = mask.sum()
    if avg_turn > 60:
        strat = "JIT 소량 빈번 발주, 안전재고 최소화"
    elif avg_turn < 30:
        strat = "프로모션 소진, 재주문점 하향 조정"
    else:
        strat = "EOQ 기반 현행 유지, 미세 조정"
    ax.text(8, 3.0 - cid * 0.5,
            f'• Cluster {cid} ({n}개, {main_cat}): {strat}',
            fontsize=9, ha='center', color='#2c3e50')

plt.tight_layout()
fname = os.path.join(FIGURE_DIR, 'project_synthesis.png')
plt.savefig(fname, dpi=150, bbox_inches='tight')
plt.show()
print(f"저장 완료: {os.path.basename(fname)}")""")

# ============================================================
# 13. Model Save
# ============================================================
md("""## 10. 모델 저장""")

code("""best_regressor = results_enhanced[best_model_name]['model']
joblib.dump(best_regressor, os.path.join(MODEL_DIR, 'best_regressor_turnover_enhanced.pkl'))
joblib.dump(scaler_Ae, os.path.join(MODEL_DIR, 'scaler_turnover_enhanced.pkl'))
print(f"Phase A 최적 모델 저장: best_regressor_turnover_enhanced.pkl ({best_model_name})")

joblib.dump(km_enhanced_model, os.path.join(MODEL_DIR, 'kmeans_enhanced.pkl'))
joblib.dump(scaler_ce, os.path.join(MODEL_DIR, 'scaler_clustering_enhanced.pkl'))
print(f"Phase B 클러스터링 저장: kmeans_enhanced.pkl (K={optimal_k})")""")

# ============================================================
# 14. Conclusion
# ============================================================
md("""## 11. 결론 및 최종 액션 플랜""")

code("""print("=" * 70)
print("소주제 4: 최적 발주 전략 클러스터링 — Enhanced 결론 및 인사이트")
print("=" * 70)

print("\\n■ Phase A: 재고 회전율 예측")
print("-" * 60)
for mn in ['RandomForest', 'XGBoost']:
    bl = results_baseline[mn]
    en = results_enhanced[mn]
    print(f"  {mn:15s} | BL R²: {bl['r2']:.4f} → EN R²: {en['r2']:.4f}")
print(f"  최적: {best_model_name} Enhanced (R²: {best_result['r2']:.4f})")

print("\\n■ Phase B: 발주 패턴 클러스터링")
print("-" * 60)
print(f"  Baseline Silhouette (K={optimal_k}): {sil_b:.4f}")
print(f"  Enhanced Silhouette (K={optimal_k}): {sil_e:.4f}")
print(f"  변화: {sil_e - sil_b:+.4f}")

print("\\n■ 군집별 발주 전략 요약")
print("-" * 60)
for cid in range(optimal_k):
    mask = df['Cluster_Enhanced'] == cid
    subset = df[mask]
    avg_turn = subset['Inventory_Turnover_Rate'].mean()
    avg_eoq = subset['EOQ_Proxy'].mean()
    main_cat = subset['Catagory'].mode()[0]
    n = len(subset)
    if avg_turn > 60:
        strat = "Fast Mover → JIT 소량 빈번 발주"
    elif avg_turn < 30:
        strat = "Slow Mover → 프로모션 소진, 발주 축소"
    else:
        strat = "Balanced → EOQ 기반 유지"
    print(f"  Cluster {cid} ({n}개, {main_cat}): 회전율 {avg_turn:.1f}, EOQ {avg_eoq:.1f} → {strat}")

print("\\n■ 보강 데이터 기여")
print("-" * 60)
print("  ① Inventory Optimization → EOQ·안전재고 파생변수 설계 근거")
print("  ② FMCG Supply Chain → 업종 벤치마크 비교 (창고 운영 패턴)")
print("  ③ Retail Demand Forecasting → 동적 ROP·수요예측 개념 도입")

print("\\n■ 소주제 간 종합 연결")
print("-" * 60)
print("  소주제 1 → Discontinued 제품의 군집 분포 분석 가능")
print("  소주제 2 → Sales_Volume 예측 → Daily_Sales 정밀화 → ROP 고도화")
print("  소주제 3 → Waste_Risk 높은 군집 → 폐기 방지 우선 관리")
print("  소주제 4 → EOQ 기반 군집별 차별화된 발주 전략 최종 제안")

print("\\n■ 최종 액션 플랜")
print("-" * 60)
print("  1. Fast Mover 군집: JIT 방식 전환, 안전재고 최소화, 발주 빈도 ↑")
print("  2. Balanced 군집: EOQ 기반 현행 유지, 계절 수요 반영 미세 조정")
print("  3. Slow Mover 군집: 프로모션 소진 전략, 재주문점 하향, SKU 합리화 검토")
print("  4. 폐기 위험 높은 군집: 신선도 기반 동적 ROP 우선 적용")
print("  5. 수요 예측 모델(소주제 2) 연계 → 동적 재주문점 시스템 확장")""")

# ============================================================
# Build notebook
# ============================================================
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.13.0"
        }
    },
    "cells": cells
}

outpath = os.path.join(os.path.dirname(__file__), '..', 'notebooks',
                       '04_Reorder_Strategy_Clustering_Enhanced.ipynb')
with open(outpath, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"Notebook created: {len(cells)} cells → {outpath}")
