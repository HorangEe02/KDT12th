# 🎮 e스포츠 경제 분석 프로젝트 - 보완 연구 지침서

## 📋 개요

이 문서는 기존 "e스포츠 vs 전통 스포츠: 경제적 규모 비교 분석" 프로젝트를 보완하기 위한 연구 지침입니다. 단순한 데이터 나열을 넘어 **"e스포츠가 왜 스포츠인가?"**라는 질문에 확답을 줄 수 있는 4가지 핵심 보완 전략을 구현합니다.

### 핵심 목표

기존 분석의 한계점인 "절대적 규모 비교"에서 벗어나, **구조적 동질성**과 **산업적 성숙도**를 증명하는 방향으로 분석을 확장합니다.

---

## 🔧 환경 설정

### 필수 라이브러리

```python
# 기본 데이터 처리
import pandas as pd
import numpy as np

# 시각화
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch
import matplotlib.gridspec as gridspec

# 통계 분석
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import statsmodels.api as sm

# 추가 시각화 (선택)
# pip install joypy  # 릿지라인 플롯용
# import joypy

# 한글 폰트 설정
import platform
if platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
elif platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False
```

### 출력 디렉토리

```python
import os
OUTPUT_DIR = 'output_enhanced'
os.makedirs(OUTPUT_DIR, exist_ok=True)
```

---

## 📊 보완 전략 1: 경제 구조의 동질성 증명

### 1.1 소득 불균형(Winner-Takes-All) 구조 분석

#### 분석 목적

전통 스포츠는 상위 1%가 전체 수익의 상당 부분을 차지하는 구조입니다. e스포츠에서도 이와 동일한 **로렌츠 곡선(Lorenz Curve)**이나 **지니 계수(Gini Coefficient)**가 나타나는지 분석하여, "돈이 흐르는 방식이 같다면 같은 산업군"임을 증명합니다.

#### 구현 지침

```python
def calculate_gini(earnings):
    """지니 계수 계산 함수"""
    sorted_earnings = np.sort(earnings)
    n = len(sorted_earnings)
    cumulative = np.cumsum(sorted_earnings)
    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_earnings))) / (n * np.sum(sorted_earnings)) - (n + 1) / n
    return gini

def plot_lorenz_curve(data_dict, title, save_path):
    """
    로렌츠 곡선 시각화
    
    Parameters:
    -----------
    data_dict : dict
        {'종목명': earnings_array, ...} 형태의 딕셔너리
    title : str
        그래프 제목
    save_path : str
        저장 경로
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = {'e스포츠': '#9B59B6', '축구': '#27AE60', 'NFL': '#E74C3C'}
    
    # 완전 평등선
    ax.plot([0, 1], [0, 1], 'k--', label='완전 평등선', alpha=0.7)
    
    for name, earnings in data_dict.items():
        sorted_data = np.sort(earnings)
        cumulative_share = np.cumsum(sorted_data) / np.sum(sorted_data)
        population_share = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        
        gini = calculate_gini(earnings)
        
        ax.plot(population_share, cumulative_share, 
                label=f'{name} (Gini: {gini:.3f})', 
                color=colors.get(name, 'gray'), linewidth=2)
    
    ax.set_xlabel('인구 누적 비율', fontsize=12)
    ax.set_ylabel('소득 누적 비율', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return fig
```

#### 데이터 준비

```python
# e스포츠 선수 상금 데이터
esports_earnings = esports_players_raw['TotalUSDPrize'].dropna().values

# NFL 연봉 데이터 (APY 또는 Total Value 컬럼 사용)
nfl_earnings = nfl_contracts_raw['APY'].dropna().values  # 또는 적절한 컬럼명

# 축구 선수 시장가치 데이터
football_earnings = football_valuations['market_value_in_eur'].dropna().values

# 로렌츠 곡선 및 지니 계수 분석
earnings_data = {
    'e스포츠': esports_earnings,
    '축구': football_earnings,
    'NFL': nfl_earnings
}

plot_lorenz_curve(
    earnings_data,
    '종목별 소득 불균형 구조 비교 (로렌츠 곡선)',
    f'{OUTPUT_DIR}/16_lorenz_curve_comparison.png'
)
```

#### 시각화: 바이올린 플롯 + 로그 스케일

```python
def plot_income_distribution_violin_log(data_dict, save_path):
    """
    로그 스케일 바이올린 플롯으로 소득 분포 비교
    두 집단의 소득 분포 곡선을 겹쳐서 부의 집중도 패턴 비교
    """
    # 데이터프레임 준비
    df_list = []
    for name, earnings in data_dict.items():
        temp_df = pd.DataFrame({
            'earnings': earnings,
            'sport': name
        })
        df_list.append(temp_df)
    
    combined_df = pd.concat(df_list, ignore_index=True)
    combined_df['log_earnings'] = np.log10(combined_df['earnings'] + 1)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    palette = {'e스포츠': '#9B59B6', '축구': '#27AE60', 'NFL': '#E74C3C'}
    
    sns.violinplot(
        data=combined_df, 
        x='sport', 
        y='log_earnings',
        palette=palette,
        inner='quartile',
        ax=ax
    )
    
    ax.set_xlabel('종목', fontsize=12)
    ax.set_ylabel('소득 (로그 스케일, USD)', fontsize=12)
    ax.set_title('종목별 소득 분포 비교\n(부의 집중도가 스포츠 산업의 전형적 패턴을 따름)', 
                 fontsize=14, fontweight='bold')
    
    # Y축 레이블을 실제 금액으로 표시
    y_ticks = ax.get_yticks()
    ax.set_yticklabels([f'${10**y:,.0f}' for y in y_ticks])
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return fig
```

#### 기대 결과물

로렌츠 곡선 비교 그래프 (16_lorenz_curve_comparison.png)와 지니 계수 비교 테이블을 생성합니다. e스포츠의 지니 계수가 전통 스포츠와 유사한 범위(0.6~0.8)에 있다면, 이는 e스포츠가 전통 스포츠와 동일한 **"승자독식(Winner-Takes-All)"** 경제 구조를 가지고 있음을 의미합니다.

---

### 1.2 시청자당 매출 효율성(ARPU) 비교

#### 분석 목적

전체 매출은 낮더라도, 시청자 1인당 발생하는 수익 모델의 효율성을 비교하여 e스포츠의 **'비즈니스적 완성도'**를 강조합니다.

#### 구현 지침

```python
def calculate_arpu(revenue, viewers):
    """시청자당 매출(ARPU) 계산"""
    return revenue / viewers if viewers > 0 else 0

def plot_arpu_bubble_chart(data, save_path):
    """
    ARPU 버블 차트
    X축: 시청자 수 (백만 명)
    Y축: 매출액 (억 달러)
    버블 크기: 성장률 (%)
    
    Parameters:
    -----------
    data : pd.DataFrame
        columns: ['sport', 'viewers_million', 'revenue_billion', 'growth_rate', 'year']
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    
    colors = {'e스포츠': '#9B59B6', '축구': '#27AE60', 'NFL': '#E74C3C', 'NBA': '#3498DB'}
    
    for sport in data['sport'].unique():
        sport_data = data[data['sport'] == sport]
        
        # 성장률을 버블 크기로 변환 (최소 크기 보장)
        sizes = (sport_data['growth_rate'].abs() + 5) * 30
        
        scatter = ax.scatter(
            sport_data['viewers_million'],
            sport_data['revenue_billion'],
            s=sizes,
            c=colors.get(sport, 'gray'),
            alpha=0.6,
            label=sport,
            edgecolors='white',
            linewidth=2
        )
    
    ax.set_xlabel('시청자 수 (백만 명)', fontsize=12)
    ax.set_ylabel('매출액 (십억 달러)', fontsize=12)
    ax.set_title('종목별 시청자당 매출 효율성 비교\n(버블 크기 = 성장률)', 
                 fontsize=14, fontweight='bold')
    
    ax.legend(title='종목', loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # ARPU 등고선 추가 (선택사항)
    x_range = np.linspace(1, ax.get_xlim()[1], 100)
    for arpu in [0.5, 1.0, 2.0, 5.0]:
        y_range = arpu * x_range / 1000  # 단위 조정
        ax.plot(x_range, y_range, '--', alpha=0.3, color='gray')
        ax.annotate(f'ARPU=${arpu}', xy=(x_range[-1], y_range[-1]), fontsize=8, alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return fig
```

#### 데이터 준비 예시

```python
# ARPU 분석용 데이터 (실제 데이터로 대체 필요)
arpu_data = pd.DataFrame({
    'sport': ['e스포츠', 'e스포츠', 'e스포츠', 'NFL', 'NFL', 'NFL', '축구', '축구', '축구'],
    'year': [2020, 2022, 2024, 2020, 2022, 2024, 2020, 2022, 2024],
    'viewers_million': [495, 640, 800, 150, 160, 170, 3500, 3800, 4000],
    'revenue_billion': [0.95, 1.38, 1.87, 12.0, 14.0, 18.0, 28.0, 32.0, 35.0],
    'growth_rate': [15.2, 22.5, 37.3, 3.5, 5.2, 6.0, 2.1, 3.8, 4.2]
})

# ARPU 계산
arpu_data['arpu'] = arpu_data['revenue_billion'] * 1000 / arpu_data['viewers_million']

print("종목별 ARPU 비교:")
print(arpu_data.groupby('sport')['arpu'].mean().sort_values(ascending=False))
```

#### 기대 결과물

버블 차트 (17_arpu_bubble_chart.png)를 생성합니다. e스포츠가 "작지만 가장 효율적이고 빠르게 성장하는 스포츠"임을 시각적으로 증명합니다.

---

## 📊 보완 전략 2: 인지적 부하로 신체 활동 재정의

### 2.1 APM(분당 작업 수)을 신체 활동량으로 치환

#### 분석 목적

기존 분석에서 '신체적 영향 미미(8점)'로 평가된 부분을 반박합니다. 축구 선수가 90분간 10km를 뛴다면, e스포츠 선수는 30분간 수천 번의 정밀한 손가락 근육 조절을 수행합니다. 이를 **'단위 시간당 신경-근육 협응 횟수'**로 재정의합니다.

#### 구현 지침: 불렛 차트(Bullet Chart)

```python
def plot_bullet_chart(data, save_path):
    """
    불렛 차트: 프로게이머 vs 일반인 vs 다른 스포츠 선수의 반응 속도/작업량 비교
    
    Parameters:
    -----------
    data : list of dict
        각 딕셔너리는 {'category', 'value', 'target', 'ranges'} 포함
    """
    fig, axes = plt.subplots(len(data), 1, figsize=(12, 3 * len(data)))
    
    if len(data) == 1:
        axes = [axes]
    
    colors = {
        'background': ['#f0f0f0', '#d9d9d9', '#bdbdbd'],
        'bar': '#9B59B6',
        'target': '#E74C3C'
    }
    
    for ax, item in zip(axes, data):
        category = item['category']
        value = item['value']
        target = item['target']
        ranges = item['ranges']  # [low, medium, high] 범위
        
        # 배경 범위 그리기
        for i, (start, end) in enumerate(zip([0] + ranges[:-1], ranges)):
            ax.barh(0, end - start, left=start, height=0.5, 
                    color=colors['background'][i], edgecolor='none')
        
        # 실제 값 막대
        ax.barh(0, value, height=0.25, color=colors['bar'], label='프로게이머')
        
        # 타겟 라인 (다른 스포츠 기준)
        ax.axvline(target, color=colors['target'], linewidth=3, label='전통 스포츠 기준')
        
        ax.set_xlim(0, max(ranges))
        ax.set_yticks([])
        ax.set_xlabel(item.get('unit', ''), fontsize=10)
        ax.set_title(category, fontsize=12, fontweight='bold', loc='left')
        
        # 범례 (첫 번째 차트에만)
        if ax == axes[0]:
            ax.legend(loc='upper right')
    
    plt.suptitle('e스포츠 선수의 신경-근육 협응 능력 비교\n(일반인 배경 위에 프로게이머 수치 표시)', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return fig
```

#### 데이터 준비 예시

```python
# 불렛 차트 데이터 (연구 자료 기반으로 실제 값 입력)
bullet_data = [
    {
        'category': 'APM (분당 작업 수)',
        'value': 400,           # 프로게이머 (스타크래프트 기준)
        'target': 60,           # 일반인 평균
        'ranges': [100, 200, 500],  # [하, 중, 상]
        'unit': 'Actions per Minute'
    },
    {
        'category': '반응 속도 (ms)',
        'value': 150,           # 프로게이머
        'target': 250,          # 일반인 평균
        'ranges': [100, 200, 400],
        'unit': 'Milliseconds (낮을수록 좋음)'
    },
    {
        'category': '정밀도 (마우스 정확도 %)',
        'value': 98,            # 프로게이머
        'target': 85,           # 야구 타격 정밀도 비유
        'ranges': [70, 85, 100],
        'unit': 'Accuracy %'
    },
    {
        'category': '동시 정보 처리 (개체 수)',
        'value': 12,            # LoL 프로게이머 (맵 전체 인식)
        'target': 7,            # 일반인 평균 작업 기억 용량
        'ranges': [5, 8, 15],
        'unit': 'Objects tracked simultaneously'
    }
]

plot_bullet_chart(bullet_data, f'{OUTPUT_DIR}/18_cognitive_load_bullet_chart.png')
```

#### 기대 결과물

불렛 차트 (18_cognitive_load_bullet_chart.png)를 생성합니다. 프로게이머의 APM, 반응 속도, 정밀도가 일반인은 물론 일부 전통 스포츠 선수보다 높은 수준임을 시각화합니다.

---

### 2.2 피크 연령(Peak Age)의 재해석

#### 분석 목적

e스포츠 선수의 낮은 연령대를 '짧은 수명'이 아닌, 체조나 수영처럼 **'극도의 순발력을 요구하는 종목의 특성'**으로 연결합니다.

#### 구현 지침: 릿지라인 플롯(Ridgeline Plot)

```python
def plot_ridgeline_age_distribution(data, save_path):
    """
    릿지라인 플롯: 종목별 선수 연령 분포 층층이 비교
    
    Parameters:
    -----------
    data : dict
        {'종목명': age_array, ...}
    """
    # joypy 라이브러리가 없는 경우 대체 구현
    try:
        import joypy
        
        # 데이터프레임 준비
        df_list = []
        for sport, ages in data.items():
            temp_df = pd.DataFrame({'age': ages, 'sport': sport})
            df_list.append(temp_df)
        combined_df = pd.concat(df_list, ignore_index=True)
        
        fig, axes = joypy.joyplot(
            combined_df, 
            by='sport', 
            column='age',
            colormap=plt.cm.viridis,
            figsize=(12, 8),
            title='종목별 선수 피크 연령 분포 비교\n(e스포츠는 초정밀 순발력 스포츠 군집에 속함)'
        )
        
    except ImportError:
        # joypy가 없는 경우 KDE 플롯으로 대체
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = {
            'e스포츠': '#9B59B6',
            '체조': '#3498DB',
            '수영': '#1ABC9C',
            '축구': '#27AE60',
            '사격': '#F39C12',
            '골프': '#E74C3C'
        }
        
        for i, (sport, ages) in enumerate(data.items()):
            ages = np.array(ages)
            
            # KDE 계산
            kde = stats.gaussian_kde(ages)
            x_range = np.linspace(ages.min() - 5, ages.max() + 5, 200)
            density = kde(x_range)
            
            # 오프셋 적용하여 층층이 쌓기
            offset = i * 0.15
            ax.fill_between(x_range, offset, density + offset, 
                           alpha=0.6, color=colors.get(sport, 'gray'),
                           label=f'{sport} (평균: {ages.mean():.1f}세)')
            ax.plot(x_range, density + offset, color=colors.get(sport, 'gray'), linewidth=1.5)
        
        ax.set_xlabel('연령 (세)', fontsize=12)
        ax.set_ylabel('밀도 (오프셋 적용)', fontsize=12)
        ax.set_title('종목별 선수 피크 연령 분포 비교\n(e스포츠는 초정밀 순발력 스포츠 군집에 속함)', 
                     fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.set_yticks([])
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return fig
```

#### 데이터 준비 예시

```python
# 종목별 선수 연령 데이터 (실제 데이터로 대체 필요)
# e스포츠 데이터는 esports_players_raw에서 추출 가능
age_data = {
    'e스포츠': np.random.normal(22, 3, 500).clip(16, 35),      # 평균 22세
    '체조': np.random.normal(20, 4, 300).clip(14, 30),          # 평균 20세
    '수영': np.random.normal(23, 4, 400).clip(16, 32),          # 평균 23세
    '축구': np.random.normal(27, 4, 600).clip(18, 40),          # 평균 27세
    '사격': np.random.normal(32, 6, 200).clip(20, 50),          # 평균 32세
    '골프': np.random.normal(35, 8, 250).clip(20, 55)           # 평균 35세
}

# 실제 e스포츠 데이터가 있다면:
# if 'Age' in esports_players_raw.columns:
#     age_data['e스포츠'] = esports_players_raw['Age'].dropna().values

plot_ridgeline_age_distribution(age_data, f'{OUTPUT_DIR}/19_peak_age_ridgeline.png')
```

#### 기대 결과물

릿지라인 플롯 (19_peak_age_ridgeline.png)을 생성합니다. e스포츠가 체조, 수영과 함께 **'초정밀 순발력 스포츠'** 군집에 속함을 시각화합니다.

---

## 📊 보완 전략 3: 성장 궤적의 동질성 (Convergence)

### 3.1 역사적 시점 동기화(Point-in-Time) 비교

#### 분석 목적

현재의 NFL과 현재의 e스포츠를 비교하는 것이 아니라, **'산업화 초기 단계의 NFL'과 '현재의 e스포츠'**의 성장 곡선을 비교합니다. 이를 통해 "e스포츠는 전통 스포츠가 50년에 걸쳐 이룬 성장을 10년 만에 압축적으로 재현하고 있다"는 결론을 도출합니다.

#### 구현 지침: 이중 회귀선(Dual Regression) 산점도

```python
def plot_dual_regression_growth(traditional_data, esports_data, save_path):
    """
    이중 회귀선 산점도: 전통 스포츠 성장기 vs e스포츠 최근 10년 비교
    
    Parameters:
    -----------
    traditional_data : pd.DataFrame
        columns: ['years_since_start', 'revenue', 'sport']
        (산업화 시작 후 경과 연수 기준)
    esports_data : pd.DataFrame
        columns: ['years_since_start', 'revenue']
    """
    fig, ax = plt.subplots(figsize=(14, 10))
    
    colors = {'NFL (1960-2010)': '#E74C3C', '축구 (1970-2020)': '#27AE60', 'e스포츠 (2010-2024)': '#9B59B6'}
    
    results = {}
    
    for sport, color in colors.items():
        if 'e스포츠' in sport:
            data = esports_data
        else:
            data = traditional_data[traditional_data['sport'] == sport.split(' ')[0]]
        
        x = data['years_since_start'].values
        y = data['revenue'].values
        
        # 산점도
        ax.scatter(x, y, color=color, alpha=0.6, s=80, label=f'{sport} 데이터')
        
        # 회귀 분석
        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()
        
        # 회귀선
        x_pred = np.linspace(x.min(), x.max(), 100)
        y_pred = model.predict(sm.add_constant(x_pred))
        ax.plot(x_pred, y_pred, color=color, linewidth=2.5, linestyle='--',
                label=f'{sport} 회귀선 (β={model.params[1]:.2f})')
        
        results[sport] = {
            'slope': model.params[1],
            'r_squared': model.rsquared,
            'growth_rate': (y[-1] / y[0]) ** (1 / len(y)) - 1 if y[0] > 0 else 0
        }
    
    ax.set_xlabel('산업화 시작 후 경과 연수', fontsize=12)
    ax.set_ylabel('매출 (십억 달러)', fontsize=12)
    ax.set_title('성장 궤적 동질성 분석: 역사적 시점 동기화 비교\n"e스포츠는 전통 스포츠가 50년에 걸쳐 이룬 성장을 10년 만에 압축 재현"', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # 결과 테이블 추가
    text_str = "회귀 분석 결과:\n"
    for sport, res in results.items():
        text_str += f"{sport}: β={res['slope']:.2f}, R²={res['r_squared']:.3f}\n"
    
    ax.text(0.98, 0.02, text_str, transform=ax.transAxes, fontsize=10,
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return fig, results
```

#### 데이터 준비 예시

```python
# 전통 스포츠: 산업화 초기부터의 성장 데이터 (실제 데이터로 대체 필요)
traditional_growth = pd.DataFrame({
    'sport': ['NFL'] * 10 + ['축구'] * 10,
    'years_since_start': list(range(0, 50, 5)) * 2,
    'revenue': [
        # NFL (1960-2010, 10년 단위)
        0.05, 0.2, 0.5, 1.5, 3.0, 5.0, 7.0, 9.0, 11.0, 14.0,
        # 축구 (1970-2020, 10년 단위)  
        0.1, 0.3, 0.8, 2.0, 5.0, 10.0, 15.0, 20.0, 28.0, 35.0
    ]
})

# e스포츠: 최근 10년 데이터 (global_esports_market에서 추출)
esports_growth = pd.DataFrame({
    'years_since_start': range(0, 15),  # 2010-2024
    'revenue': [0.1, 0.15, 0.2, 0.3, 0.45, 0.6, 0.8, 0.95, 1.1, 1.3, 1.5, 1.7, 1.87, 2.1, 2.4]
})

# 시각화
plot_dual_regression_growth(
    traditional_growth, 
    esports_growth,
    f'{OUTPUT_DIR}/20_dual_regression_growth.png'
)
```

#### 기대 결과물

이중 회귀선 산점도 (20_dual_regression_growth.png)를 생성합니다. 두 회귀선의 **기울기(β)**를 비교하여 e스포츠의 압축 성장을 정량적으로 증명합니다.

---

## 📊 보완 전략 4: 포지션별 역량 분석 (Role Specialization)

### 4.1 역량 레이더 차트: 축구 vs e스포츠 포지션 매칭

#### 분석 목적

단순히 '게임을 잘한다'가 아니라, 스포츠처럼 **'분업화된 전문성'**이 있음을 보여줍니다. 축구의 포지션(GK, DF, MF, FW)별 필요 역량과 e스포츠(LoL)의 라인별(탑, 정글, 미드, 원딜, 서폿) 필요 역량을 매칭합니다.

#### 구현 지침: 레이더 차트 중첩

```python
def plot_role_comparison_radar(football_roles, esports_roles, save_path):
    """
    레이더 차트 중첩: 축구 포지션 vs e스포츠 포지션 역량 비교
    
    Parameters:
    -----------
    football_roles : dict
        {'포지션명': {'역량1': 점수, '역량2': 점수, ...}, ...}
    esports_roles : dict
        동일 구조
    """
    # 공통 역량 카테고리 (두 스포츠에서 비교 가능한 항목)
    categories = ['시야/맵 리딩', '순발력/반응속도', '팀워크/의사소통', 
                  '전술 이해도', '개인기/메카닉', '리더십/콜링']
    
    # 매칭되는 포지션 쌍
    position_pairs = [
        ('미드필더', '정글러', '넓은 시야와 조율 능력'),
        ('공격수', '원딜', '높은 딜링과 마무리'),
        ('수비수', '탑', '라인 유지와 안정성'),
        ('골키퍼', '서포터', '팀 보호와 시야 확보')
    ]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 16), subplot_kw=dict(projection='polar'))
    axes = axes.flatten()
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # 닫힌 다각형을 위해
    
    for ax, (fb_pos, es_pos, description) in zip(axes, position_pairs):
        # 축구 포지션 데이터
        fb_values = [football_roles[fb_pos].get(cat, 50) for cat in categories]
        fb_values += fb_values[:1]
        
        # e스포츠 포지션 데이터
        es_values = [esports_roles[es_pos].get(cat, 50) for cat in categories]
        es_values += es_values[:1]
        
        # 플로팅
        ax.plot(angles, fb_values, 'o-', linewidth=2, label=f'축구: {fb_pos}', color='#27AE60')
        ax.fill(angles, fb_values, alpha=0.25, color='#27AE60')
        
        ax.plot(angles, es_values, 'o-', linewidth=2, label=f'e스포츠: {es_pos}', color='#9B59B6')
        ax.fill(angles, es_values, alpha=0.25, color='#9B59B6')
        
        # 카테고리 레이블
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=9)
        ax.set_ylim(0, 100)
        
        ax.set_title(f'{fb_pos} ↔ {es_pos}\n"{description}"', fontsize=11, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.suptitle('포지션별 역량 비교: 전술적 복잡성과 역할 분담이 전문 스포츠 수준임', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return fig
```

#### 데이터 준비 예시

```python
# 축구 포지션별 역량 (0-100 점수)
football_roles = {
    '미드필더': {
        '시야/맵 리딩': 90, '순발력/반응속도': 75, '팀워크/의사소통': 85,
        '전술 이해도': 95, '개인기/메카닉': 80, '리더십/콜링': 85
    },
    '공격수': {
        '시야/맵 리딩': 70, '순발력/반응속도': 95, '팀워크/의사소통': 70,
        '전술 이해도': 75, '개인기/메카닉': 95, '리더십/콜링': 60
    },
    '수비수': {
        '시야/맵 리딩': 80, '순발력/반응속도': 80, '팀워크/의사소통': 85,
        '전술 이해도': 90, '개인기/메카닉': 70, '리더십/콜링': 75
    },
    '골키퍼': {
        '시야/맵 리딩': 95, '순발력/반응속도': 90, '팀워크/의사소통': 80,
        '전술 이해도': 85, '개인기/메카닉': 75, '리더십/콜링': 90
    }
}

# e스포츠(LoL) 포지션별 역량
esports_roles = {
    '정글러': {
        '시야/맵 리딩': 95, '순발력/반응속도': 85, '팀워크/의사소통': 90,
        '전술 이해도': 95, '개인기/메카닉': 80, '리더십/콜링': 90
    },
    '원딜': {
        '시야/맵 리딩': 75, '순발력/반응속도': 95, '팀워크/의사소통': 75,
        '전술 이해도': 70, '개인기/메카닉': 98, '리더십/콜링': 55
    },
    '탑': {
        '시야/맵 리딩': 75, '순발력/반응속도': 85, '팀워크/의사소통': 70,
        '전술 이해도': 85, '개인기/메카닉': 90, '리더십/콜링': 65
    },
    '서포터': {
        '시야/맵 리딩': 98, '순발력/반응속도': 80, '팀워크/의사소통': 95,
        '전술 이해도': 90, '개인기/메카닉': 70, '리더십/콜링': 95
    }
}

plot_role_comparison_radar(
    football_roles, 
    esports_roles,
    f'{OUTPUT_DIR}/21_role_specialization_radar.png'
)
```

#### 기대 결과물

레이더 차트 중첩 (21_role_specialization_radar.png)을 생성합니다. 축구 미드필더의 역량 프로필과 e스포츠 정글러의 역량 프로필이 유사함을 시각화하여, **"전술적 복잡성과 역할 분담이 전문 스포츠 수준"**임을 증명합니다.

---

## 📋 실행 체크리스트

### 사전 준비

아래 항목들을 실행 전에 확인하세요.

1. [ ] 필수 라이브러리 설치 완료 (pandas, numpy, matplotlib, seaborn, scipy, statsmodels)
2. [ ] 선택 라이브러리 설치 (joypy - 릿지라인 플롯용)
3. [ ] 기존 데이터 파일 경로 확인 (../data/ 또는 적절한 경로)
4. [ ] 출력 디렉토리 생성 (output_enhanced/)

### 실행 순서

분석은 아래 순서로 진행하는 것을 권장합니다.

1. [ ] **환경 설정**: 라이브러리 로드 및 폰트 설정
2. [ ] **데이터 로드**: 기존 노트북의 데이터 로드 셀 실행
3. [ ] **보완 전략 1.1**: 로렌츠 곡선 및 지니 계수 분석
4. [ ] **보완 전략 1.2**: ARPU 버블 차트
5. [ ] **보완 전략 2.1**: 인지적 부하 불렛 차트
6. [ ] **보완 전략 2.2**: 피크 연령 릿지라인 플롯
7. [ ] **보완 전략 3.1**: 이중 회귀선 성장 궤적 분석
8. [ ] **보완 전략 4.1**: 포지션별 역량 레이더 차트
9. [ ] **종합 결론**: 업데이트된 평가 점수 산출

### 예상 출력 파일

| 파일명 | 설명 | 보완 전략 |
|--------|------|----------|
| 16_lorenz_curve_comparison.png | 로렌츠 곡선 비교 | 1.1 |
| 17_arpu_bubble_chart.png | ARPU 버블 차트 | 1.2 |
| 18_cognitive_load_bullet_chart.png | 인지적 부하 불렛 차트 | 2.1 |
| 19_peak_age_ridgeline.png | 피크 연령 릿지라인 플롯 | 2.2 |
| 20_dual_regression_growth.png | 이중 회귀선 성장 궤적 | 3.1 |
| 21_role_specialization_radar.png | 포지션별 역량 레이더 | 4.1 |

---

## 📝 업데이트된 평가 기준 제안

기존 평가 항목에 다음 항목들을 추가하거나 수정하는 것을 권장합니다.

| 평가 항목 | 기존 점수 | 보완 후 예상 점수 | 근거 |
|-----------|----------|------------------|------|
| 신체적 활동 | 8 | **45** | APM, 반응속도 등 인지적 부하 정량화 |
| 경제 구조 동질성 | (신규) | **75** | 지니 계수가 전통 스포츠와 유사 |
| 역할 전문화 | (신규) | **85** | 포지션별 역량 프로필 유사성 |
| 산업 성숙도 | (신규) | **70** | 압축 성장으로 50년 → 10년 |

---

## 🔗 참고 자료

다음 자료들을 데이터 수집 및 분석 근거로 활용하세요.

1. **APM 및 반응속도 연구**: "The cognitive demands of esports" (2020) 등 학술 논문
2. **스포츠 경제학**: Szymanski, S. "The Economics of Sport" - 지니 계수, ARPU 관련
3. **NFL 역사적 성장 데이터**: Forbes NFL Valuations, Statista
4. **e스포츠 시장 보고서**: Newzoo Global Esports Report 2024

---

**작성일**: 2025년 1월  
**목적**: Claude Code 실행을 위한 보완 연구 지침서  
**버전**: v1.0
