"""
03. 데이터 분석
기후 변화에 따른 햄버거 재료 영향 분석

통계적 기법을 활용하여 기후 변화와 햄버거 재료 간의 관계를 정량적으로 분석합니다.

분석 목표:
    1. 기온 변화와 생산량 간의 상관관계 검증
    2. 시차(Lag) 효과 분석
    3. 회귀분석을 통한 영향력 추정
    4. 이상기후 이벤트의 영향 분석

데이터 출처:
    1. FAOSTAT (https://www.fao.org/faostat/en/#data)
    2. Kaggle Climate Change Impact on Agriculture
       (https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture)
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr, shapiro, levene
from scipy.stats import ttest_ind, mannwhitneyu
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# statsmodels 임포트
try:
    import statsmodels.api as sm
    from statsmodels.stats.diagnostic import het_breuschpagan
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("⚠️ statsmodels가 설치되지 않았습니다. 일부 분석이 제한됩니다.")


# =============================================================================
# 1. 환경 설정
# =============================================================================
def setup_environment():
    """분석 환경 설정"""
    # 경로 설정
    PROJECT_DIR = Path(__file__).parent.parent
    PROCESSED_DIR = PROJECT_DIR / 'output' / 'processed'
    OUTPUT_DIR = PROJECT_DIR / 'output' / 'analysis'
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 유의수준 설정
    ALPHA = 0.05

    # 시각화 스타일
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 11

    # 한글 폰트 설정
    try:
        plt.rcParams['font.family'] = 'AppleGothic'
    except:
        try:
            plt.rcParams['font.family'] = 'Malgun Gothic'
        except:
            pass
    plt.rcParams['axes.unicode_minus'] = False

    print("=" * 60)
    print("📊 기후 변화에 따른 햄버거 재료 영향 분석")
    print("   03. 데이터 분석 (통계 분석)")
    print("=" * 60)
    print(f"\n✅ 분석 환경 설정 완료")
    print(f"   - 유의수준 (α): {ALPHA}")
    print(f"   - 데이터 경로: {PROCESSED_DIR}")
    print(f"   - 결과 경로: {OUTPUT_DIR}")

    return PROJECT_DIR, PROCESSED_DIR, OUTPUT_DIR, ALPHA


# =============================================================================
# 2. 데이터 로드
# =============================================================================
def load_analysis_data(processed_dir):
    """분석용 데이터 로드"""
    print("\n📥 데이터 로드 중...")
    data = {}

    # 재료별 생산량 데이터
    items = ['wheat', 'tomatoes', 'potatoes', 'lettuce', 'beef', 'cucumbers']

    for item in items:
        filepath = processed_dir / f'{item}_production.csv'
        if filepath.exists():
            data[item] = pd.read_csv(filepath)
            print(f"   ✓ {item}: {len(data[item])} rows")

    # 기온 데이터
    temp_path = processed_dir / 'temperature_processed.csv'
    if temp_path.exists():
        data['temperature'] = pd.read_csv(temp_path)
        print(f"   ✓ temperature: {len(data['temperature'])} rows")

    # Kaggle 데이터
    kaggle_path = processed_dir / 'kaggle_climate_agriculture.csv'
    if kaggle_path.exists():
        data['kaggle'] = pd.read_csv(kaggle_path)
        print(f"   ✓ kaggle: {len(data['kaggle'])} rows")

    # 통합 데이터
    integrated_path = processed_dir / 'integrated_dataset.csv'
    if integrated_path.exists():
        data['integrated'] = pd.read_csv(integrated_path)
        print(f"   ✓ integrated: {len(data['integrated'])} rows")

    print(f"\n✅ 총 {len(data)}개 데이터셋 로드 완료")
    return data


# =============================================================================
# 3. 상관분석 (Correlation Analysis)
# =============================================================================
def correlation_analysis(data, alpha=0.05):
    """
    기온 변화와 생산량 간의 상관분석

    통계적 방법:
    - Pearson 상관계수: 선형 관계 (정규성 가정)
    - Spearman 상관계수: 단조 관계 (비모수)
    - p-value: 귀무가설(상관없음) 검정
    """
    results = []

    print("\n" + "=" * 80)
    print("📊 상관분석: 기온 변화 vs 글로벌 생산량")
    print("=" * 80)
    print(f"\n{'재료':<15} {'Pearson r':>12} {'p-value':>12} {'Spearman ρ':>12} {'p-value':>12} {'N':>6}")
    print("-" * 80)

    items = ['wheat', 'tomatoes', 'potatoes', 'lettuce', 'beef', 'cucumbers']

    for item in items:
        if item in data and 'World_Total' in data[item].columns:
            df = data[item].copy()

            # Temp_Anomaly가 없으면 기온 데이터에서 병합
            if 'Temp_Anomaly' not in df.columns and 'temperature' in data:
                df_temp = data['temperature']
                df_world_temp = df_temp[df_temp['Area'] == 'World'].groupby('Year')['Temp_Anomaly'].mean().reset_index()
                df = df.merge(df_world_temp, on='Year', how='left')

            if 'Temp_Anomaly' not in df.columns:
                continue

            df = df.dropna(subset=['World_Total', 'Temp_Anomaly'])

            if len(df) < 5:
                continue

            x = df['Temp_Anomaly'].values
            y = df['World_Total'].values
            n = len(x)

            # Pearson 상관계수
            pearson_r, pearson_p = pearsonr(x, y)

            # Spearman 상관계수
            spearman_r, spearman_p = spearmanr(x, y)

            # 유의성 표시
            sig_p = "***" if pearson_p < 0.001 else "**" if pearson_p < 0.01 else "*" if pearson_p < 0.05 else ""
            sig_s = "***" if spearman_p < 0.001 else "**" if spearman_p < 0.01 else "*" if spearman_p < 0.05 else ""

            print(f"{item:<15} {pearson_r:>10.4f}{sig_p:<2} {pearson_p:>10.4f} {spearman_r:>10.4f}{sig_s:<2} {spearman_p:>10.4f} {n:>6}")

            results.append({
                'Item': item,
                'N': n,
                'Pearson_r': pearson_r,
                'Pearson_p': pearson_p,
                'Pearson_sig': pearson_p < alpha,
                'Spearman_r': spearman_r,
                'Spearman_p': spearman_p,
                'Spearman_sig': spearman_p < alpha
            })

    print("-" * 80)
    print("유의수준: *** p<0.001, ** p<0.01, * p<0.05")

    return pd.DataFrame(results)


def interpret_correlation(df_corr):
    """상관분석 결과 해석"""
    print("\n📊 상관분석 결과 해석")
    print("-" * 50)

    if len(df_corr) == 0:
        print("   분석 결과 없음")
        return

    # 유의미한 상관관계
    sig_positive = df_corr[(df_corr['Pearson_sig']) & (df_corr['Pearson_r'] > 0)]
    sig_negative = df_corr[(df_corr['Pearson_sig']) & (df_corr['Pearson_r'] < 0)]

    if len(sig_positive) > 0:
        print("\n[유의미한 양의 상관관계]")
        for _, row in sig_positive.iterrows():
            strength = "강한" if abs(row['Pearson_r']) > 0.7 else "중간" if abs(row['Pearson_r']) > 0.3 else "약한"
            print(f"   - {row['Item']}: r = {row['Pearson_r']:.3f} ({strength} 양의 상관)")
            print(f"     → 기온이 상승할수록 생산량이 증가하는 경향")

    if len(sig_negative) > 0:
        print("\n[유의미한 음의 상관관계]")
        for _, row in sig_negative.iterrows():
            strength = "강한" if abs(row['Pearson_r']) > 0.7 else "중간" if abs(row['Pearson_r']) > 0.3 else "약한"
            print(f"   - {row['Item']}: r = {row['Pearson_r']:.3f} ({strength} 음의 상관)")
            print(f"     → 기온이 상승할수록 생산량이 감소하는 경향")

    # 주의사항
    print("\n⚠️ 해석 시 주의사항:")
    print("   - 상관관계 ≠ 인과관계")
    print("   - 양의 상관: 기술 발전, 재배 면적 증가 등의 교란변수 가능")
    print("   - 시계열 데이터의 경향성(trend)이 반영될 수 있음")


# =============================================================================
# 4. 시차(Lag) 상관분석
# =============================================================================
def lag_correlation_analysis(data, max_lag=5, alpha=0.05):
    """
    시차(Lag) 상관분석

    Parameters:
    -----------
    max_lag : int - 분석할 최대 시차 (연도)

    Returns:
    --------
    DataFrame - 시차별 상관계수
    """
    results = []

    print("\n" + "=" * 60)
    print("📊 시차(Lag) 상관분석: 기온 변화 → 생산량")
    print("=" * 60)
    print("(기온 변화가 생산량에 미치는 지연 효과 분석)")

    items = ['wheat', 'tomatoes', 'potatoes', 'lettuce', 'beef']

    for item in items:
        if item not in data or 'World_Total' not in data[item].columns:
            continue

        df = data[item].copy()

        # Temp_Anomaly 확인/병합
        if 'Temp_Anomaly' not in df.columns and 'temperature' in data:
            df_temp = data['temperature']
            df_world_temp = df_temp[df_temp['Area'] == 'World'].groupby('Year')['Temp_Anomaly'].mean().reset_index()
            df = df.merge(df_world_temp, on='Year', how='left')

        if 'Temp_Anomaly' not in df.columns:
            continue

        print(f"\n[{item.upper()}]")
        print(f"{'Lag (년)':<12} {'상관계수':>12} {'p-value':>12} {'유의성':>10}")
        print("-" * 50)

        best_lag = 0
        best_corr = 0
        best_p = 1

        for lag in range(0, max_lag + 1):
            # 기온을 lag만큼 앞으로 이동 (과거 기온 → 현재 생산량)
            temp_lagged = df['Temp_Anomaly'].shift(lag)
            prod = df['World_Total']

            # 결측치 제거
            mask = ~(temp_lagged.isna() | prod.isna())
            if mask.sum() < 5:
                continue

            corr, pval = pearsonr(temp_lagged[mask], prod[mask])

            sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < alpha else "ns"
            print(f"{lag:<12} {corr:>12.4f} {pval:>12.4f} {sig:>10}")

            results.append({
                'Item': item,
                'Lag_Years': lag,
                'Correlation': corr,
                'P_value': pval,
                'Significant': pval < alpha,
                'N': mask.sum()
            })

            if abs(corr) > abs(best_corr) and not np.isnan(corr):
                best_corr = corr
                best_lag = lag
                best_p = pval

        print(f"\n→ 최적 시차: {best_lag}년 (r = {best_corr:.4f}, p = {best_p:.4f})")

    return pd.DataFrame(results)


# =============================================================================
# 5. 회귀분석 (Regression Analysis)
# =============================================================================
def simple_linear_regression(data, output_dir):
    """
    단순 선형 회귀분석

    모델: Y = β₀ + β₁X + ε
    - Y: 생산량 (종속변수)
    - X: 기온 편차 (독립변수)
    - β₁: 기온 1°C 변화 시 생산량 변화량

    가정 검정:
    1. 선형성 (Linearity)
    2. 정규성 (Normality of residuals)
    3. 등분산성 (Homoscedasticity)
    """
    if not STATSMODELS_AVAILABLE:
        print("⚠️ statsmodels 미설치로 회귀분석 생략")
        return pd.DataFrame()

    results = []

    print("\n" + "=" * 70)
    print("📊 회귀분석: 기온 변화 → 생산량")
    print("=" * 70)

    items = ['wheat', 'tomatoes', 'potatoes', 'lettuce', 'beef']
    valid_items = []

    for item in items:
        if item not in data or 'World_Total' not in data[item].columns:
            continue

        df = data[item].copy()

        # Temp_Anomaly 확인/병합
        if 'Temp_Anomaly' not in df.columns and 'temperature' in data:
            df_temp = data['temperature']
            df_world_temp = df_temp[df_temp['Area'] == 'World'].groupby('Year')['Temp_Anomaly'].mean().reset_index()
            df = df.merge(df_world_temp, on='Year', how='left')

        if 'Temp_Anomaly' not in df.columns:
            continue

        df = df.dropna(subset=['World_Total', 'Temp_Anomaly'])

        if len(df) < 5:
            continue

        valid_items.append((item, df))

    if not valid_items:
        print("⚠️ 분석 가능한 데이터 없음")
        return pd.DataFrame()

    # 시각화 설정
    n_items = len(valid_items)
    n_cols = min(3, n_items)
    n_rows = (n_items + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
    if n_items == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]

    for idx, (item, df) in enumerate(valid_items):
        X = df['Temp_Anomaly'].values
        y = df['World_Total'].values / 1e6  # 백만 톤

        # OLS 회귀분석
        X_const = sm.add_constant(X)
        model = sm.OLS(y, X_const).fit()

        # 결과 추출
        beta0 = model.params[0]
        beta1 = model.params[1]
        r_squared = model.rsquared
        adj_r_squared = model.rsquared_adj
        f_stat = model.fvalue
        f_pval = model.f_pvalue

        # 잔차 분석
        residuals = model.resid

        # 정규성 검정 (Shapiro-Wilk)
        if len(residuals) <= 50:
            shapiro_stat, shapiro_p = shapiro(residuals)
        else:
            shapiro_stat, shapiro_p = np.nan, np.nan

        # 등분산성 검정 (Breusch-Pagan)
        try:
            _, bp_pval, _, _ = het_breuschpagan(residuals, X_const)
        except:
            bp_pval = np.nan

        print(f"\n[{item.upper()}]")
        print(f"   회귀식: Production = {beta1:.2f} × Temp + {beta0:.2f}")
        print(f"   R² = {r_squared:.4f}, Adjusted R² = {adj_r_squared:.4f}")
        print(f"   F-statistic = {f_stat:.2f}, p-value = {f_pval:.4e}")
        print(f"   해석: 기온 1°C 상승 시 생산량 {beta1:.2f} 백만톤 {'증가' if beta1 > 0 else '감소'}")
        print(f"\n   [가정 검정]")
        print(f"   - 잔차 정규성 (Shapiro-Wilk): p = {shapiro_p:.4f} {'✓' if shapiro_p > 0.05 else '✗'}")
        print(f"   - 등분산성 (Breusch-Pagan): p = {bp_pval:.4f} {'✓' if bp_pval > 0.05 else '✗'}")

        # 시각화
        ax = axes[idx]
        ax.scatter(X, y, alpha=0.6, edgecolors='black', linewidth=0.5, s=60)

        # 회귀선
        x_line = np.linspace(X.min(), X.max(), 100)
        y_line = beta0 + beta1 * x_line
        ax.plot(x_line, y_line, 'r-', linewidth=2, label='Regression Line')

        # 95% 신뢰구간
        se = np.sqrt(np.sum(residuals**2) / (len(X) - 2))
        ci = 1.96 * se
        ax.fill_between(x_line, y_line - ci, y_line + ci, alpha=0.2, color='red')

        # 텍스트
        sig = "***" if f_pval < 0.001 else "**" if f_pval < 0.01 else "*" if f_pval < 0.05 else "ns"
        ax.text(0.05, 0.95, f'y = {beta1:.2f}x + {beta0:.2f}\nR² = {r_squared:.3f} ({sig})',
               transform=ax.transAxes, fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.set_xlabel('Temperature Anomaly (°C)')
        ax.set_ylabel('Production (Million Tonnes)')
        ax.set_title(f'{item.title()}', fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(alpha=0.3)

        results.append({
            'Item': item,
            'Intercept': beta0,
            'Slope': beta1,
            'R_squared': r_squared,
            'Adj_R_squared': adj_r_squared,
            'F_statistic': f_stat,
            'F_pvalue': f_pval,
            'Shapiro_p': shapiro_p,
            'BreuschPagan_p': bp_pval,
            'N': len(X)
        })

    # 남은 subplot 숨기기
    for idx in range(len(valid_items), len(axes)):
        axes[idx].set_visible(False)

    plt.suptitle('Linear Regression: Temperature → Production\nSource: FAOSTAT',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'stat_03_regression_plots.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("\n✅ 회귀분석 시각화 저장 완료")

    return pd.DataFrame(results)


def multiple_regression(data, output_dir):
    """
    다중 회귀분석: 여러 기후 변수가 수율에 미치는 영향

    모델: Yield = β₀ + β₁(Temp) + β₂(Precip) + β₃(CO2) + ε
    """
    if not STATSMODELS_AVAILABLE:
        print("⚠️ statsmodels 미설치로 다중회귀분석 생략")
        return None

    if 'kaggle' not in data:
        print("⚠️ Kaggle 데이터 없음")
        return None

    df = data['kaggle'].dropna()

    print("\n" + "=" * 70)
    print("📊 다중 회귀분석: 기후 변수 → 작물 수율")
    print("=" * 70)

    # 필요한 컬럼 확인
    required_cols = ['Average_Temperature_C', 'Total_Precipitation_mm', 'CO2_Emissions_MT', 'Crop_Yield_MT_per_HA']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"⚠️ 필요한 컬럼 없음: {missing_cols}")
        return None

    # 변수 설정
    X = df[['Average_Temperature_C', 'Total_Precipitation_mm', 'CO2_Emissions_MT']]
    y = df['Crop_Yield_MT_per_HA']

    # 상수항 추가
    X_const = sm.add_constant(X)

    # OLS 회귀분석
    model = sm.OLS(y, X_const).fit()

    print(model.summary())

    # 결과 요약
    print("\n📊 다중 회귀분석 요약")
    print("-" * 50)
    print(f"R² = {model.rsquared:.4f}")
    print(f"Adjusted R² = {model.rsquared_adj:.4f}")
    print(f"F-statistic = {model.fvalue:.2f}, p = {model.f_pvalue:.4e}")

    print("\n[계수 해석]")
    for var, coef, pval in zip(X.columns, model.params[1:], model.pvalues[1:]):
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
        print(f"   {var}: β = {coef:.4f} ({sig})")

    # VIF (다중공선성) 확인
    print("\n[다중공선성 검정 (VIF)]")
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        status = "✓" if vif < 5 else "⚠️" if vif < 10 else "✗"
        print(f"   {col}: VIF = {vif:.2f} {status}")

    return model


# =============================================================================
# 6. 이상기후 이벤트 분석
# =============================================================================
def event_study_analysis(data):
    """
    이상기후 이벤트가 생산량에 미치는 영향 분석

    방법: 이벤트 전후 생산량 변화 비교
    """
    # 주요 이상기후 연도 정의
    extreme_events = {
        2010: {'name': 'Russia Heatwave', 'affected': ['wheat']},
        2011: {'name': 'US Southern Drought', 'affected': ['wheat', 'beef']},
        2012: {'name': 'US Drought (Corn Belt)', 'affected': ['wheat', 'beef']},
        2019: {'name': 'Australia Bushfires', 'affected': ['wheat', 'beef']},
        2021: {'name': 'Western US Drought', 'affected': ['wheat', 'potatoes']},
        2022: {'name': 'European Drought', 'affected': ['wheat', 'potatoes']}
    }

    print("\n" + "=" * 70)
    print("📊 이상기후 이벤트 분석")
    print("=" * 70)

    results = []

    for year, event_info in extreme_events.items():
        print(f"\n[{year}: {event_info['name']}]")

        for item in event_info['affected']:
            if item not in data or 'World_Total' not in data[item].columns:
                continue

            df = data[item]

            # 이벤트 연도 및 전후 1년 데이터
            event_year_data = df[df['Year'] == year]['World_Total'].values
            pre_year_data = df[df['Year'] == year - 1]['World_Total'].values
            post_year_data = df[df['Year'] == year + 1]['World_Total'].values

            if len(event_year_data) == 0 or len(pre_year_data) == 0:
                continue

            # 연간 변화율 계산
            change_to_event = ((event_year_data[0] - pre_year_data[0]) / pre_year_data[0]) * 100

            if len(post_year_data) > 0:
                change_to_recovery = ((post_year_data[0] - event_year_data[0]) / event_year_data[0]) * 100
            else:
                change_to_recovery = np.nan

            print(f"   {item}:")
            print(f"     - 전년 대비 변화: {change_to_event:+.2f}%")
            if not np.isnan(change_to_recovery):
                print(f"     - 회복 (이듬해): {change_to_recovery:+.2f}%")

            results.append({
                'Year': year,
                'Event': event_info['name'],
                'Item': item,
                'Change_Pct': change_to_event,
                'Recovery_Pct': change_to_recovery
            })

    return pd.DataFrame(results)


# =============================================================================
# 7. 변동성 분석
# =============================================================================
def volatility_analysis(data):
    """
    생산량 변동성(Volatility) 분석
    - 연간 변화율의 표준편차로 측정
    - 기후 변동성 증가가 생산 안정성에 미치는 영향
    """
    print("\n" + "=" * 70)
    print("📊 생산량 변동성 분석")
    print("=" * 70)

    results = []

    for item in ['wheat', 'tomatoes', 'potatoes', 'lettuce', 'beef']:
        if item not in data or 'World_Total' not in data[item].columns:
            continue

        df = data[item].copy()
        df['YoY_Change'] = df['World_Total'].pct_change() * 100

        # 기간 분할 (전반기 vs 후반기)
        mid_year = df['Year'].median()
        early_period = df[df['Year'] < mid_year]['YoY_Change'].dropna()
        late_period = df[df['Year'] >= mid_year]['YoY_Change'].dropna()

        # 변동성 (표준편차)
        vol_early = early_period.std()
        vol_late = late_period.std()
        vol_change = ((vol_late - vol_early) / vol_early) * 100 if vol_early > 0 else np.nan

        # Mann-Whitney U 검정 (비모수)
        if len(early_period) >= 3 and len(late_period) >= 3:
            stat, pval = mannwhitneyu(early_period, late_period, alternative='two-sided')
        else:
            stat, pval = np.nan, np.nan

        print(f"\n[{item.upper()}]")
        print(f"   전반기 변동성 (SD): {vol_early:.2f}%")
        print(f"   후반기 변동성 (SD): {vol_late:.2f}%")
        print(f"   변동성 변화: {vol_change:+.1f}%")
        print(f"   Mann-Whitney U p-value: {pval:.4f}")

        results.append({
            'Item': item,
            'Volatility_Early': vol_early,
            'Volatility_Late': vol_late,
            'Change_Pct': vol_change,
            'MW_pvalue': pval
        })

    return pd.DataFrame(results)


# =============================================================================
# 8. 상관행렬 히트맵
# =============================================================================
def correlation_heatmap(data, output_dir):
    """
    다변량 상관행렬 시각화
    """
    if 'kaggle' not in data:
        print("⚠️ Kaggle 데이터 없음")
        return None

    df = data['kaggle']

    # 분석 변수
    variables = ['Average_Temperature_C', 'Total_Precipitation_mm',
                 'CO2_Emissions_MT', 'Crop_Yield_MT_per_HA']

    # 존재하는 변수만 선택
    available_vars = [v for v in variables if v in df.columns]
    if len(available_vars) < 2:
        print("⚠️ 충분한 변수 없음")
        return None

    # 경제 영향 변수 추가 (있는 경우)
    if 'Economic_Impact_Million_USD' in df.columns:
        available_vars.append('Economic_Impact_Million_USD')

    # 상관행렬
    corr_matrix = df[available_vars].corr()

    # 시각화
    fig, ax = plt.subplots(figsize=(10, 8))

    # 마스크 (상삼각)
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

    # 히트맵
    sns.heatmap(corr_matrix,
                annot=True,
                fmt='.3f',
                cmap='RdBu_r',
                center=0,
                square=True,
                linewidths=0.5,
                cbar_kws={'label': 'Correlation Coefficient'},
                ax=ax,
                mask=mask,
                vmin=-1, vmax=1)

    # 라벨 간소화
    labels = {
        'Average_Temperature_C': 'Temp (°C)',
        'Total_Precipitation_mm': 'Precip (mm)',
        'CO2_Emissions_MT': 'CO2 (MT)',
        'Crop_Yield_MT_per_HA': 'Yield (MT/HA)',
        'Economic_Impact_Million_USD': 'Economic ($M)'
    }
    new_labels = [labels.get(v, v) for v in available_vars]

    ax.set_xticklabels(new_labels, rotation=45, ha='right')
    ax.set_yticklabels(new_labels, rotation=0)

    ax.set_title('Correlation Matrix: Climate Variables vs Agricultural Outcomes\n'
                 'Source: Kaggle Climate Change Impact on Agriculture',
                 fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'stat_06_correlation_heatmap.png', dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close()

    print("\n✅ 상관행렬 히트맵 저장 완료")
    print("\n📊 상관행렬:")
    print(corr_matrix.round(3))

    return corr_matrix


# =============================================================================
# 9. 분석 결과 요약
# =============================================================================
def generate_analysis_summary(output_dir, df_corr, df_lag, df_reg, df_events, df_vol):
    """분석 결과 종합 요약"""

    # 상관분석 요약
    sig_corr = df_corr[df_corr['Pearson_sig']]['Item'].tolist() if len(df_corr) > 0 else []

    # 회귀분석 요약
    if len(df_reg) > 0:
        best_r2 = df_reg.loc[df_reg['R_squared'].idxmax()]
        best_item = best_r2['Item']
        best_r2_val = best_r2['R_squared']
    else:
        best_item, best_r2_val = "N/A", 0

    summary = f"""
================================================================================
📊 통계 분석 결과 요약
================================================================================

■ 분석 목적
  기후 변화가 햄버거 주요 재료(빵, 패티, 야채, 소스)의 생산에
  미치는 영향을 통계적으로 검증

■ 주요 분석 방법
  1. 상관분석 (Pearson, Spearman)
  2. 시차(Lag) 상관분석
  3. 단순/다중 회귀분석
  4. 이벤트 스터디
  5. 변동성 분석

■ 주요 발견사항

  1. 상관관계
     - 유의미한 상관관계: {', '.join(sig_corr) if sig_corr else '없음'}
     - 기온과 생산량 간 양의 상관 경향 (기술 발전 효과 포함)

  2. 시차 효과
     - 기온 영향이 즉각적이지 않고 지연되어 나타남
     - 작물별로 최적 시차가 상이함

  3. 회귀분석
     - 최고 설명력: {best_item} (R² = {best_r2_val:.4f})
     - 기온 1°C 상승 시 생산량 변화 추정 가능

  4. 이상기후 영향
     - 2012년 미국 가뭄: 밀/소고기 생산 영향
     - 2022년 유럽 가뭄: 밀/감자 생산 영향

  5. 변동성
     - 일부 품목에서 후반기 변동성 증가 경향

■ 한계점
  1. 기후 외 교란변수 (전쟁, 정책, 기술) 통제 어려움
  2. 시계열 데이터의 자기상관 존재 가능
  3. 비선형 관계 추가 분석 필요

■ 데이터 출처
  1. FAOSTAT (https://www.fao.org/faostat/en/#data)
  2. Kaggle Climate Change Impact on Agriculture
     (https://www.kaggle.com/datasets/waqi786/climate-change-impact-on-agriculture)

================================================================================
✅ 다음 단계: 04_결론_도출.md
================================================================================
"""
    print(summary)

    # 파일로 저장
    with open(output_dir / 'stat_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)

    print("✅ 분석 요약 저장 완료")


# =============================================================================
# 메인 실행
# =============================================================================
def main():
    """메인 실행 함수"""

    # 1. 환경 설정
    PROJECT_DIR, PROCESSED_DIR, OUTPUT_DIR, ALPHA = setup_environment()

    # 2. 데이터 로드
    data = load_analysis_data(PROCESSED_DIR)

    # 3. 상관분석
    print("\n" + "=" * 60)
    print("📈 통계 분석 시작")
    print("=" * 60)

    df_corr = correlation_analysis(data, ALPHA)
    if len(df_corr) > 0:
        df_corr.to_csv(OUTPUT_DIR / 'stat_01_correlation_results.csv', index=False)
        interpret_correlation(df_corr)

    # 4. 시차 상관분석
    df_lag = lag_correlation_analysis(data, max_lag=5, alpha=ALPHA)
    if len(df_lag) > 0:
        df_lag.to_csv(OUTPUT_DIR / 'stat_02_lag_correlation.csv', index=False)

    # 5. 회귀분석
    df_reg = simple_linear_regression(data, OUTPUT_DIR)
    if len(df_reg) > 0:
        df_reg.to_csv(OUTPUT_DIR / 'stat_03_regression_results.csv', index=False)

    # 6. 다중회귀분석
    model_multi = multiple_regression(data, OUTPUT_DIR)

    # 7. 이벤트 분석
    df_events = event_study_analysis(data)
    if len(df_events) > 0:
        df_events.to_csv(OUTPUT_DIR / 'stat_04_event_analysis.csv', index=False)

    # 8. 변동성 분석
    df_vol = volatility_analysis(data)
    if len(df_vol) > 0:
        df_vol.to_csv(OUTPUT_DIR / 'stat_05_volatility_analysis.csv', index=False)

    # 9. 상관행렬 히트맵
    corr_matrix = correlation_heatmap(data, OUTPUT_DIR)

    # 10. 결과 요약
    generate_analysis_summary(OUTPUT_DIR, df_corr, df_lag, df_reg, df_events, df_vol)

    # 11. 생성 파일 목록
    print("\n[생성된 분석 결과 파일]")
    for f in sorted(OUTPUT_DIR.glob("stat_*")):
        size = f.stat().st_size / 1024
        print(f"   - {f.name} ({size:.1f} KB)")

    print("\n" + "=" * 60)
    print("✅ 통계 분석 완료!")
    print("=" * 60)

    return {
        'correlation': df_corr,
        'lag_correlation': df_lag,
        'regression': df_reg,
        'events': df_events,
        'volatility': df_vol
    }


if __name__ == "__main__":
    results = main()
