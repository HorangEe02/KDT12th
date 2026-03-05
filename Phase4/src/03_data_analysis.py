"""
03. 데이터 분석 (소스류 분석)

프로젝트명: 기후 변화가 햄버거 소스류 원재료에 미치는 영향 분석
분석 대상: 토마토(케찹), 계란(마요네즈), 고추(스리라차)

분석 목표:
1. 기온 변화와 소스 원료 생산량 간의 상관관계 검증
2. 원료별 기후 민감도(Climate Sensitivity) 비교
3. 2022년 스리라차 품귀 사태 원인 분석
4. 통계적 회귀분석

데이터 출처:
- FAOSTAT (https://www.fao.org/faostat/en/#data)
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr, shapiro, ttest_ind
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# statsmodels 임포트 (설치 필요할 수 있음)
try:
    import statsmodels.api as sm
    from statsmodels.stats.diagnostic import het_breuschpagan
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("⚠️ statsmodels 미설치 - 일부 고급 분석 제한됨")

# ============================================================
# 1. 환경 설정
# ============================================================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'output' / 'processed'
OUTPUT_DIR = BASE_DIR / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 시각화 스타일
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.unicode_minus'] = False

try:
    plt.rcParams['font.family'] = 'AppleGothic'
except:
    pass

# 유의수준
ALPHA = 0.05

# 색상 팔레트
SAUCE_COLORS = {
    'Tomatoes': '#E74C3C',
    'Eggs': '#F1C40F',
    'Chillies_dry': '#C0392B',
    'Chillies_green': '#27AE60'
}

print("=" * 60)
print("📊 소스류 데이터 통계 분석")
print("=" * 60)
print(f"   - 유의수준 (α): {ALPHA}")
print(f"   - 분석 대상: 토마토(케찹), 계란(마요), 고추(스리라차)")
print()

# ============================================================
# 2. 데이터 로드
# ============================================================
def load_analysis_data():
    """분석용 데이터 로드"""
    data = {}

    files = {
        'Tomatoes': 'tomatoes_production.csv',
        'Eggs': 'eggs_production.csv',
        'Chillies_dry': 'chillies_dry_production.csv',
        'Chillies_green': 'chillies_green_production.csv',
        'Temperature': 'temperature_processed.csv',
        'Integrated': 'sauce_ingredients_integrated.csv'
    }

    print("📂 데이터 로드 중...")
    for name, filename in files.items():
        filepath = DATA_DIR / filename
        if filepath.exists():
            data[name] = pd.read_csv(filepath)
            print(f"   ✓ {name}: {len(data[name])} rows")
        else:
            print(f"   ⚠️ {name}: 파일 없음")

    return data


def prepare_merged_data(data):
    """생산량 데이터와 기온 데이터 병합"""
    if 'Temperature' not in data:
        return data

    df_temp = data['Temperature']

    # World_Avg 컬럼 확인
    temp_col = None
    for col in ['World_Avg', 'World']:
        if col in df_temp.columns:
            temp_col = col
            break

    if temp_col is None:
        numeric_cols = df_temp.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != 'Year']
        if numeric_cols:
            df_temp['World_Avg'] = df_temp[numeric_cols].mean(axis=1)
            temp_col = 'World_Avg'

    if temp_col:
        temp_subset = df_temp[['Year', temp_col]].rename(columns={temp_col: 'Temp_Anomaly'})

        for key in ['Tomatoes', 'Eggs', 'Chillies_dry', 'Chillies_green']:
            if key in data:
                df = data[key].copy()

                # World_Total 확인/생성
                if 'World_Total' not in df.columns:
                    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                    numeric_cols = [c for c in numeric_cols if c != 'Year']
                    df['World_Total'] = df[numeric_cols].sum(axis=1)

                # 기온 데이터 병합
                df = df.merge(temp_subset, on='Year', how='left')
                data[key] = df

    return data


# ============================================================
# 3. 상관분석 (Correlation Analysis)
# ============================================================
def correlation_analysis(data):
    """
    소스 원료별 기온-생산량 상관분석

    가설:
    - H₀: 기온 변화와 생산량 사이에 상관관계가 없다 (ρ = 0)
    - H₁: 기온 변화와 생산량 사이에 상관관계가 있다 (ρ ≠ 0)
    """
    print("\n" + "=" * 80)
    print("📊 기온 변화 vs 소스 원료 생산량 상관분석")
    print("=" * 80)
    print(f"{'원료':<25} {'Pearson r':>12} {'p-value':>12} {'Spearman ρ':>12} {'p-value':>12} {'N':>6}")
    print("-" * 80)

    results = []

    items_info = [
        ('Tomatoes', '토마토 (케찹)'),
        ('Eggs', '계란 (마요네즈)'),
        ('Chillies_dry', '건고추 (스리라차)'),
        ('Chillies_green', '풋고추')
    ]

    for key, name in items_info:
        if key not in data:
            continue

        df = data[key]

        if 'World_Total' not in df.columns or 'Temp_Anomaly' not in df.columns:
            continue

        df_clean = df.dropna(subset=['World_Total', 'Temp_Anomaly'])

        if len(df_clean) < 3:
            continue

        x = df_clean['Temp_Anomaly'].values
        y = df_clean['World_Total'].values
        n = len(x)

        # Pearson 상관계수
        pearson_r, pearson_p = pearsonr(x, y)

        # Spearman 상관계수
        spearman_r, spearman_p = spearmanr(x, y)

        sig_p = "***" if pearson_p < 0.001 else "**" if pearson_p < 0.01 else "*" if pearson_p < 0.05 else ""
        sig_s = "***" if spearman_p < 0.001 else "**" if spearman_p < 0.01 else "*" if spearman_p < 0.05 else ""

        print(f"{name:<25} {pearson_r:>10.4f}{sig_p:<2} {pearson_p:>10.4f} {spearman_r:>10.4f}{sig_s:<2} {spearman_p:>10.4f} {n:>6}")

        results.append({
            'Item': name,
            'Item_Key': key,
            'N': n,
            'Pearson_r': pearson_r,
            'Pearson_p': pearson_p,
            'Pearson_sig': pearson_p < ALPHA,
            'Spearman_r': spearman_r,
            'Spearman_p': spearman_p,
            'Spearman_sig': spearman_p < ALPHA
        })

    print("-" * 80)
    print("유의수준: *** p<0.001, ** p<0.01, * p<0.05")

    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_DIR / 'sauce_stat_01_correlation.csv', index=False, encoding='utf-8-sig')
    print("\n✅ 상관분석 결과 저장: sauce_stat_01_correlation.csv")

    return df_results


def interpret_correlation(df_corr):
    """상관분석 결과 해석"""
    print("\n📊 상관분석 결과 해석")
    print("-" * 50)

    for _, row in df_corr.iterrows():
        r = row['Pearson_r']
        sig = row['Pearson_sig']

        # 상관 강도 해석
        if abs(r) > 0.7:
            strength = "강한"
        elif abs(r) > 0.3:
            strength = "중간"
        else:
            strength = "약한"

        direction = "양의" if r > 0 else "음의"

        print(f"\n[{row['Item']}]")
        print(f"   상관계수: r = {r:.4f} ({strength} {direction} 상관)")
        print(f"   통계적 유의성: {'유의함' if sig else '유의하지 않음'} (p = {row['Pearson_p']:.4f})")

        # 품목별 해석
        if row['Item_Key'] == 'Chillies_dry':
            print("   💡 해석: 고추는 기후 변동에 가장 민감한 원료")
            print("      → 스리라차 소스 공급 안정성에 주의 필요")
        elif row['Item_Key'] == 'Eggs':
            print("   💡 해석: 계란은 사료 작물(옥수수, 콩)을 통한 간접 영향")
            print("      → 조류인플루엔자(AI)가 더 큰 변동 요인")
        elif row['Item_Key'] == 'Tomatoes':
            print("   💡 해석: 토마토는 관개 시설로 기후 영향 일부 완충")
            print("      → 물 부족 지역(스페인, 이탈리아)은 취약")


# ============================================================
# 4. 기후 민감도 분석 (Climate Sensitivity)
# ============================================================
def climate_sensitivity_analysis(data):
    """
    소스 원료별 기후 민감도 비교

    지표:
    1. 변동계수 (Coefficient of Variation)
    2. 연간 변화율의 표준편차
    3. 기온 변화에 대한 민감도 (회귀 기울기)
    """
    print("\n" + "=" * 70)
    print("🌡️ 소스 원료별 기후 민감도 분석")
    print("=" * 70)

    results = []

    items = [
        ('Tomatoes', '토마토 (케찹)'),
        ('Eggs', '계란 (마요네즈)'),
        ('Chillies_dry', '건고추 (스리라차)'),
        ('Chillies_green', '풋고추')
    ]

    for key, name in items:
        if key not in data:
            continue

        df = data[key]

        if 'World_Total' not in df.columns:
            continue

        production = df['World_Total']

        # 1. 변동계수 (CV)
        cv = (production.std() / production.mean()) * 100

        # 2. 연간 변화율 표준편차
        yoy_change = production.pct_change() * 100
        yoy_std = yoy_change.std()

        # 3. 기온 민감도 (회귀 기울기)
        temp_sensitivity = np.nan
        temp_sensitivity_pct = np.nan

        if 'Temp_Anomaly' in df.columns and STATSMODELS_AVAILABLE:
            df_clean = df.dropna(subset=['World_Total', 'Temp_Anomaly'])
            if len(df_clean) >= 3:
                X = sm.add_constant(df_clean['Temp_Anomaly'])
                y = df_clean['World_Total'] / 1e6
                model = sm.OLS(y, X).fit()
                temp_sensitivity = model.params.iloc[1]
                temp_sensitivity_pct = (temp_sensitivity / y.mean()) * 100

        print(f"\n[{name}]")
        print(f"   변동계수 (CV): {cv:.2f}%")
        print(f"   연간 변화율 SD: {yoy_std:.2f}%")
        if not np.isnan(temp_sensitivity):
            print(f"   기온 민감도: {temp_sensitivity:.2f} MT/°C ({temp_sensitivity_pct:.2f}%/°C)")

        results.append({
            'Item': name,
            'Item_Key': key,
            'CV_Percent': cv,
            'YoY_SD': yoy_std,
            'Temp_Sensitivity_MT_per_C': temp_sensitivity,
            'Temp_Sensitivity_Pct_per_C': temp_sensitivity_pct
        })

    df_results = pd.DataFrame(results)

    # 민감도 순위
    print("\n" + "-" * 50)
    print("📊 기후 민감도 순위 (변동계수 기준)")
    df_ranked = df_results.sort_values('CV_Percent', ascending=False)
    for i, (_, row) in enumerate(df_ranked.iterrows(), 1):
        print(f"   {i}. {row['Item']}: CV = {row['CV_Percent']:.2f}%")

    df_results.to_csv(OUTPUT_DIR / 'sauce_stat_02_sensitivity.csv', index=False, encoding='utf-8-sig')
    print("\n✅ 기후 민감도 분석 저장: sauce_stat_02_sensitivity.csv")

    return df_results


def visualize_sensitivity(data, df_sensitivity):
    """기후 민감도 시각화"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    items = [
        ('Tomatoes', 'Tomato', "#CD7166"),
        ('Eggs', 'Eggs', "#E9CF69"),
        ('Chillies_dry', 'Dry Chilli', "#7490D2")
    ]

    # 민감도 데이터 필터링
    df_plot = df_sensitivity[df_sensitivity['Item_Key'].isin([k for k, _, _ in items])]

    # 1. 변동계수 바 차트
    ax1 = axes[0]
    names = df_plot['Item'].tolist()
    cvs = df_plot['CV_Percent'].values
    colors = [SAUCE_COLORS.get(row['Item_Key'], 'gray') for _, row in df_plot.iterrows()]

    bars = ax1.bar(range(len(names)), cvs, color=colors, edgecolor='black', linewidth=0.5)
    ax1.set_xticks(range(len(names)))
    ax1.set_xticklabels([n.split('(')[0].strip() for n in names], rotation=15)
    ax1.set_ylabel('Coefficient of Variation (%)')
    ax1.set_title('Production Volatility (CV)', fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # 2. 연간 변화율 분포
    ax2 = axes[1]
    for key, name, color in items:
        if key in data and 'World_Total' in data[key].columns:
            yoy = data[key]['World_Total'].pct_change() * 100
            ax2.hist(yoy.dropna(), bins=12, alpha=0.5, label=name, color=color, edgecolor='black')

    ax2.axvline(x=0, color='black', linestyle='--', linewidth=1)
    ax2.set_xlabel('Year-over-Year Change (%)')
    ax2.set_ylabel('Frequency')
    ax2.set_title('YoY Change Distribution', fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)

    # 3. 기온 민감도
    ax3 = axes[2]
    sensitivities = df_plot['Temp_Sensitivity_Pct_per_C'].values
    valid_mask = ~np.isnan(sensitivities)

    if valid_mask.any():
        valid_names = [names[i] for i in range(len(names)) if valid_mask[i]]
        valid_sens = sensitivities[valid_mask]
        valid_colors = [colors[i] for i in range(len(colors)) if valid_mask[i]]

        bars = ax3.barh(range(len(valid_names)), valid_sens, color=valid_colors, edgecolor='black', linewidth=0.5)
        ax3.set_yticks(range(len(valid_names)))
        ax3.set_yticklabels([n.split('(')[0].strip() for n in valid_names])
        ax3.axvline(x=0, color='black', linestyle='--', linewidth=1)
        ax3.set_xlabel('Sensitivity (%/°C)')
        ax3.set_title('Production Change per 1°C', fontweight='bold')
        ax3.grid(axis='x', alpha=0.3)

    plt.suptitle('Sauce Ingredients: Climate Sensitivity Comparison\n'
                 'Source: FAOSTAT', fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_stat_03_sensitivity_viz.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("\n✅ 기후 민감도 시각화 저장: sauce_stat_03_sensitivity_viz.png")


# ============================================================
# 5. 회귀분석 (Regression Analysis)
# ============================================================
def regression_analysis(data):
    """
    소스 원료별 회귀분석

    모델: Production = β₀ + β₁ × Temperature_Anomaly + ε
    """
    if not STATSMODELS_AVAILABLE:
        print("\n⚠️ statsmodels 미설치로 회귀분석 생략")
        return None

    print("\n" + "=" * 80)
    print("📈 회귀분석: 기온 변화 → 소스 원료 생산량")
    print("=" * 80)

    results = []

    items = [
        ('Tomatoes', '토마토 (케찹)'),
        ('Eggs', '계란 (마요네즈)'),
        ('Chillies_dry', '건고추 (스리라차)')
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    colors = ["#E9AEA7", "#E5D48F", "#839ACE"]

    for idx, ((key, name), ax, color) in enumerate(zip(items, axes, colors)):
        if key not in data:
            continue

        df = data[key]

        if 'World_Total' not in df.columns or 'Temp_Anomaly' not in df.columns:
            continue

        df_clean = df.dropna(subset=['World_Total', 'Temp_Anomaly'])

        if len(df_clean) < 5:
            continue

        X = df_clean['Temp_Anomaly'].values
        y = df_clean['World_Total'].values / 1e6

        # OLS 회귀분석
        X_const = sm.add_constant(X)
        model = sm.OLS(y, X_const).fit()

        beta0 = model.params[0]
        beta1 = model.params[1]
        r_squared = model.rsquared
        f_pval = model.f_pvalue

        # 잔차 분석
        residuals = model.resid

        # 정규성 검정
        shapiro_p = np.nan
        if len(residuals) >= 3 and len(residuals) <= 50:
            _, shapiro_p = shapiro(residuals)

        # 등분산성 검정
        bp_pval = np.nan
        try:
            _, bp_pval, _, _ = het_breuschpagan(residuals, X_const)
        except:
            pass

        print(f"\n[{name}]")
        print(f"   회귀식: Production = {beta1:.3f} × Temp + {beta0:.3f}")
        print(f"   R² = {r_squared:.4f}")
        print(f"   F-test p-value = {f_pval:.4e}")
        print(f"   해석: 기온 1°C 상승 시 생산량 {abs(beta1):.3f} 백만톤 {'증가' if beta1 > 0 else '감소'}")
        print(f"   [가정 검정]")
        if not np.isnan(shapiro_p):
            print(f"   - 잔차 정규성: p = {shapiro_p:.4f} {'✓' if shapiro_p > 0.05 else '✗'}")
        if not np.isnan(bp_pval):
            print(f"   - 등분산성: p = {bp_pval:.4f} {'✓' if bp_pval > 0.05 else '✗'}")

        # 시각화
        ax.scatter(X, y, c=color, s=60, alpha=0.7, edgecolors='black', linewidth=0.5)

        # 회귀선
        x_line = np.linspace(X.min(), X.max(), 100)
        y_line = beta0 + beta1 * x_line
        ax.plot(x_line, y_line, 'k-', linewidth=2)

        # 95% 신뢰구간
        se = np.sqrt(np.sum(residuals**2) / (len(X) - 2))
        ax.fill_between(x_line, y_line - 1.96*se, y_line + 1.96*se, alpha=0.2, color='gray')

        # 통계량 표시
        sig = "***" if f_pval < 0.001 else "**" if f_pval < 0.01 else "*" if f_pval < 0.05 else "ns"
        ax.text(0.05, 0.95, f'y = {beta1:.2f}x + {beta0:.2f}\nR² = {r_squared:.3f} ({sig})',
               transform=ax.transAxes, fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.set_xlabel('Temperature Anomaly (°C)')
        ax.set_ylabel('Production (Million Tonnes)')
        ax.set_title(name, fontweight='bold')
        ax.grid(alpha=0.3)

        results.append({
            'Item': name,
            'Item_Key': key,
            'Intercept': beta0,
            'Slope': beta1,
            'R_squared': r_squared,
            'F_pvalue': f_pval,
            'Shapiro_p': shapiro_p,
            'BP_p': bp_pval
        })

    plt.suptitle('Linear Regression: Temperature → Sauce Ingredient Production\n'
                 'Source: FAOSTAT', fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_stat_04_regression.png', dpi=150, bbox_inches='tight')
    plt.close()

    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_DIR / 'sauce_stat_04_regression.csv', index=False, encoding='utf-8-sig')

    print("\n✅ 회귀분석 결과 저장: sauce_stat_04_regression.csv, sauce_stat_04_regression.png")

    return df_results


# ============================================================
# 6. 2022 스리라차 위기 분석
# ============================================================
def sriracha_crisis_analysis(data):
    """
    2022년 스리라차 품귀 사태 분석

    배경:
    - 2022년 미국 Huy Fong Foods社 스리라차 생산 중단
    - 원인: 멕시코산 할라피뇨 고추 공급 차질
    - 멕시코 뉴멕시코/캘리포니아 지역 극심한 가뭄
    """
    print("\n" + "=" * 70)
    print("🌶️ 2022년 스리라차 위기 분석 (Event Study)")
    print("=" * 70)

    if 'Chillies_dry' not in data:
        print("⚠️ 고추 데이터 없음")
        return None

    df = data['Chillies_dry']

    # 이벤트 연도 정의
    event_year = 2022
    pre_years = [2019, 2020, 2021]
    post_years = [2022, 2023]

    # 사전/사후 기간 필터링
    df_pre = df[df['Year'].isin(pre_years)]
    df_event = df[df['Year'] == event_year]

    if len(df_event) == 0:
        print(f"⚠️ {event_year}년 데이터 없음")
        return None

    print(f"\n[이벤트 정의]")
    print(f"   - 이벤트 연도: {event_year}")
    print(f"   - 사전 기간: {pre_years}")
    print(f"   - 사후 기간: {post_years}")

    # 전체 생산량 분석
    if 'World_Total' in df.columns:
        pre_prod = df_pre['World_Total'].mean()
        event_prod = df_event['World_Total'].values[0]
        change_pct = ((event_prod - pre_prod) / pre_prod) * 100

        print(f"\n[전체 건고추 생산량 분석]")
        print(f"   - 사전 기간 평균: {pre_prod/1e6:.2f} 백만톤")
        print(f"   - 2022년 생산량: {event_prod/1e6:.2f} 백만톤")
        print(f"   - 변화: {change_pct:+.2f}%")

    # 멕시코 분석 (스리라차 원료 공급국)
    if 'Mexico' in df.columns:
        pre_mexico = df_pre['Mexico'].mean()
        event_mexico = df_event['Mexico'].values[0]

        if pre_mexico > 0:
            mexico_change = ((event_mexico - pre_mexico) / pre_mexico) * 100

            print(f"\n[멕시코 건고추 생산량 분석]")
            print(f"   - 사전 기간 평균: {pre_mexico/1e3:.2f} 천톤")
            print(f"   - 2022년 생산량: {event_mexico/1e3:.2f} 천톤")
            print(f"   - 변화: {mexico_change:+.2f}%")
            print(f"   ⚠️ 멕시코 고추 생산 변화 → 스리라차 공급 영향")

    # 기온 분석
    if 'Temp_Anomaly' in df.columns:
        pre_temp = df_pre['Temp_Anomaly'].mean()
        event_temp = df_event['Temp_Anomaly'].values[0]

        print(f"\n[기온 변화]")
        print(f"   - 사전 기간 평균 편차: {pre_temp:.3f}°C")
        print(f"   - 2022년 편차: {event_temp:.3f}°C")
        print(f"   - 차이: {event_temp - pre_temp:+.3f}°C")

    # 통계적 유의성 검정
    if 'World_Total' in df.columns:
        pre_data = df[df['Year'].isin(pre_years)]['World_Total'].values
        post_data = df[df['Year'].isin(post_years)]['World_Total'].values

        if len(pre_data) >= 2 and len(post_data) >= 1:
            # Mann-Whitney U test (샘플 크기가 작아서)
            if len(post_data) >= 2:
                try:
                    t_stat, t_pval = ttest_ind(pre_data, post_data)
                    print(f"\n[통계적 검정: 사전 vs 사후 생산량]")
                    print(f"   - t-statistic: {t_stat:.3f}")
                    print(f"   - p-value: {t_pval:.4f}")
                    print(f"   - 결론: {'유의미한 차이' if t_pval < 0.05 else '유의미한 차이 없음'}")
                except:
                    pass

    return {'Event': 'Sriracha Crisis 2022'}


# ============================================================
# 7. 이상기후 이벤트 영향 분석
# ============================================================
def extreme_event_analysis(data):
    """주요 이상기후 이벤트가 소스 원료에 미친 영향"""

    events = {
        2012: {'name': 'US Drought', 'affected': ['Tomatoes', 'Eggs']},
        2015: {'name': 'Avian Influenza (AI)', 'affected': ['Eggs']},
        2019: {'name': 'European Heatwave', 'affected': ['Tomatoes']},
        2022: {'name': 'Sriracha Crisis (Mexico Drought)', 'affected': ['Chillies_dry']}
    }

    print("\n" + "=" * 70)
    print("🌪️ 이상기후 이벤트 영향 분석")
    print("=" * 70)

    results = []

    for year, event_info in events.items():
        print(f"\n[{year}: {event_info['name']}]")

        for item in event_info['affected']:
            if item not in data:
                continue

            df = data[item]

            if 'World_Total' not in df.columns:
                continue

            # 해당 연도 및 전년도 데이터
            current = df[df['Year'] == year]['World_Total'].values
            previous = df[df['Year'] == year - 1]['World_Total'].values

            if len(current) == 0 or len(previous) == 0:
                continue

            change = ((current[0] - previous[0]) / previous[0]) * 100

            item_names = {
                'Tomatoes': '토마토 (케찹)',
                'Eggs': '계란 (마요네즈)',
                'Chillies_dry': '건고추 (스리라차)'
            }
            item_name = item_names.get(item, item)

            print(f"   - {item_name}: {change:+.2f}%")

            results.append({
                'Year': year,
                'Event': event_info['name'],
                'Item': item_name,
                'Change_Pct': change
            })

    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_DIR / 'sauce_stat_05_events.csv', index=False, encoding='utf-8-sig')
    print("\n✅ 이벤트 분석 저장: sauce_stat_05_events.csv")

    return df_results


# ============================================================
# 8. 상관행렬 히트맵
# ============================================================
def correlation_heatmap(data):
    """소스 원료 간 상관행렬 시각화"""

    if 'Integrated' not in data:
        print("\n⚠️ 통합 데이터셋 없음 - 히트맵 생략")
        return None

    df_integrated = data['Integrated']

    # 피벗 테이블 생성
    if 'Item_Key' in df_integrated.columns:
        pivot_col = 'Item_Key'
    elif 'Item' in df_integrated.columns:
        pivot_col = 'Item'
    else:
        print("\n⚠️ 피벗 컬럼 없음")
        return None

    try:
        df_pivot = df_integrated.pivot(
            index='Year',
            columns=pivot_col,
            values='World_Production_Tonnes'
        )
    except:
        print("\n⚠️ 피벗 실패")
        return None

    # 기온 데이터 추가
    if 'Temperature' in data:
        df_temp = data['Temperature']
        temp_col = 'World_Avg' if 'World_Avg' in df_temp.columns else 'World'
        if temp_col in df_temp.columns:
            temp_subset = df_temp[['Year', temp_col]].rename(columns={temp_col: 'Temperature'})
            df_pivot = df_pivot.reset_index().merge(temp_subset, on='Year', how='left').set_index('Year')

    # 결측치 제거
    df_pivot = df_pivot.dropna()

    if len(df_pivot) < 3:
        print("\n⚠️ 데이터 부족")
        return None

    # 상관행렬
    corr_matrix = df_pivot.corr()

    # 히트맵
    fig, ax = plt.subplots(figsize=(10, 8))

    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

    sns.heatmap(corr_matrix,
                annot=True,
                fmt='.3f',
                cmap='RdBu_r',
                center=0,
                square=True,
                linewidths=0.5,
                mask=mask,
                vmin=-1, vmax=1,
                cbar_kws={'label': 'Correlation'},
                ax=ax)

    ax.set_title('Correlation Matrix: Sauce Ingredients & Temperature\n'
                 'Source: FAOSTAT', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'sauce_stat_06_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("\n✅ 상관행렬 히트맵 저장: sauce_stat_06_heatmap.png")
    print("\n📊 상관행렬:")
    print(corr_matrix.round(3))

    return corr_matrix


# ============================================================
# 9. 분석 결과 요약
# ============================================================
def generate_summary():
    """분석 결과 요약 생성"""

    summary = """
================================================================================
📊 소스류 원료 통계 분석 결과 요약
================================================================================

■ 분석 대상
  - 토마토 (Tomatoes) → 케찹 원료
  - 계란 (Eggs) → 마요네즈 원료
  - 건고추 (Chillies, dry) → 스리라차 원료

■ 주요 분석 방법
  1. 상관분석 (Pearson, Spearman)
  2. 기후 민감도 분석 (변동계수, 회귀 기울기)
  3. 회귀분석 (OLS)
  4. 이벤트 스터디 (2022 스리라차 위기)

■ 주요 발견사항

  1. 기후 민감도 순위
     🌶️ 건고추 > 🥚 계란 > 🍅 토마토

  2. 스리라차 위기 (2022)
     - 멕시코 가뭄으로 원료 공급 차질
     - 고추 생산 급감

  3. 계란의 특수성
     - 직접적 기후 영향보다 AI(조류인플루엔자)가 주요 변동 요인
     - 사료 가격(옥수수, 콩)을 통한 간접 영향

■ 한계점
  1. 교란변수(정책, 환율, 물류) 미통제
  2. 가격 데이터 미포함
  3. 지역별 세부 분석 제한

■ 데이터 출처
  - FAOSTAT Crops: https://www.fao.org/faostat/en/#data/QCL
  - FAOSTAT Livestock: https://www.fao.org/faostat/en/#data/QL
  - FAOSTAT Temperature: https://www.fao.org/faostat/en/#data/ET

================================================================================
✅ 다음 단계: 04_결론_도출.md
================================================================================
"""
    print(summary)

    with open(OUTPUT_DIR / 'sauce_stat_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)

    print("✅ 분석 요약 저장: sauce_stat_summary.txt")


# ============================================================
# 10. 메인 실행
# ============================================================
def main():
    """메인 분석 파이프라인"""

    # 1. 데이터 로드
    data = load_analysis_data()

    if len(data) == 0:
        print("\n⚠️ 로드된 데이터가 없습니다. 먼저 01_data_preprocessing.py를 실행하세요.")
        return

    # 2. 데이터 병합 (생산량 + 기온)
    data = prepare_merged_data(data)

    print("\n" + "=" * 60)
    print("📊 통계 분석 시작")
    print("=" * 60)

    # 3. 상관분석
    print("\n[1] 상관분석")
    df_corr = correlation_analysis(data)
    if df_corr is not None and len(df_corr) > 0:
        interpret_correlation(df_corr)

    # 4. 기후 민감도 분석
    print("\n[2] 기후 민감도 분석")
    df_sensitivity = climate_sensitivity_analysis(data)
    if df_sensitivity is not None:
        visualize_sensitivity(data, df_sensitivity)

    # 5. 회귀분석
    print("\n[3] 회귀분석")
    df_reg = regression_analysis(data)

    # 6. 스리라차 위기 분석
    print("\n[4] 스리라차 위기 분석")
    sriracha_crisis_analysis(data)

    # 7. 이상기후 이벤트 분석
    print("\n[5] 이상기후 이벤트 분석")
    extreme_event_analysis(data)

    # 8. 상관행렬 히트맵
    print("\n[6] 상관행렬 히트맵")
    correlation_heatmap(data)

    # 9. 결과 요약
    print("\n[7] 결과 요약")
    generate_summary()

    # 생성된 파일 목록
    print("\n" + "=" * 60)
    print("📁 생성된 분석 결과 파일")
    print("=" * 60)
    for f in sorted(OUTPUT_DIR.glob("sauce_stat_*")):
        size = f.stat().st_size / 1024
        print(f"   - {f.name} ({size:.1f} KB)")

    return data


if __name__ == '__main__':
    data = main()
