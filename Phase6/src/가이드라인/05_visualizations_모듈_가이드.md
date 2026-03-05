# 05. visualizations 모듈 가이드

> 9개 시각화 모듈이 총 52개 이상의 차트를 생성한다.
> 모든 모듈이 **범용 차트 구조**이므로, 분야 전환 시 **차트 제목만 변경**하면 된다.

---

## 파일 구조

```
visualizations/
├── __init__.py                 ← 9개 클래스 import
├── wordcloud_viz.py            ← 워드클라우드 7종 (★★☆ 마스크 이미지 변경)
├── chart_viz.py                ← 기본 차트 11종 (★☆☆)
├── advanced_viz.py             ← 고급 차트 10종 (★☆☆)
├── interactive_viz.py          ← Plotly 인터랙티브 8종 (★☆☆)
├── dashboard.py                ← 종합 대시보드 + 9종 서브차트 (★☆☆)
├── content_trend_viz.py        ← 콘텐츠 트렌드 5종 (★☆☆)
├── cross_analysis_viz.py       ← 교차 분석 4종 (★☆☆)
├── jobplanet_deep_viz.py       ← 잡플래닛 심층 6종 (★☆☆)
└── wanted_viz.py               ← 원티드 전용 7종 (★☆☆)
```

---

## 공통 수정 사항 (모든 시각화 모듈)

| 항목 | 기존 | 변경 | 난이도 |
|------|------|------|--------|
| 차트 제목 | "의료 AI ..." | "{분야명} ..." | ★☆☆ |
| 파일명 | 유지 가능 | (선택) 분야명 포함 | ★☆☆ |
| 색상맵 | 유지 가능 | (선택) 분야 이미지에 맞게 | ★☆☆ |

---

## 1. wordcloud_viz.py - 워드클라우드 7종

### 클래스 구조

```python
class WordCloudVisualizer:
    STOPWORDS = { ... }       # ★ 불용어 세트 (분야별 추가 가능)

    def __init__(self, save_dir=None)

    # 개별 워드클라우드
    def generate_tech_stack_wordcloud(tech_data)       # 기술스택
    def generate_blog_keyword_wordcloud(blog_texts)    # 블로그 키워드
    def generate_interview_keyword_wordcloud(texts)    # 면접 키워드
    def generate_review_pros_wordcloud(pros_texts)     # 리뷰 장점
    def generate_review_cons_wordcloud(cons_texts)     # 리뷰 단점
    def generate_job_requirements_wordcloud(req_texts) # 채용 자격요건
    def generate_medical_domain_wordcloud(texts)       # 도메인 키워드 (★ 메서드명 변경)

    # 전체 실행
    def generate_all(data_dict) → None
```

### 생성 차트 목록

| 차트 | 파일명 | 색상맵 | 마스크 |
|------|--------|--------|--------|
| 기술스택 | `wc_tech_stack.png` | cool | O (cross.png) |
| 블로그 키워드 | `wc_blog_keywords.png` | viridis | O |
| 면접 키워드 | `wc_interview.png` | plasma | O |
| 리뷰 장점 | `wc_review_pros.png` | Greens | O |
| 리뷰 단점 | `wc_review_cons.png` | Reds | O |
| 도메인 키워드 | `wc_medical_domain.png` | YlGn | O |
| 채용 자격요건 | `wc_job_requirements.png` | coolwarm | O |

### 분야 전환 시 수정 포인트

```python
# [수정 1] 마스크 이미지 교체
# 기존: cross.png (의료 십자가)
# 변경: 분야를 상징하는 이미지
# → settings.py의 WORDCLOUD_MASK_PATH를 변경하면 자동 적용
# 마스크 이미지 요건: 흰 배경 + 검정 도형, PNG 형식

# [수정 2] 불용어 추가
STOPWORDS = {
    "있는", "하는", "있다", "합니다", "입니다", "등", "및", "또한",
    "위해", "통해", "대한", "관련", "이상", "이하", "필요", "해당",
    # 분야별 추가 (예: 핀테크에서 "금융"이 너무 빈번)
}

# [수정 3] 차트 제목
# 각 generate_*() 메서드 내부의 title 문자열 변경
# "의료 AI 채용공고 기술스택 워드클라우드" → "{분야명} 기술스택 워드클라우드"

# [수정 4] 메서드명 (선택)
# generate_medical_domain_wordcloud() → generate_domain_wordcloud()
```

---

## 2. chart_viz.py - 기본 차트 11종

### 클래스 구조

```python
class ChartVisualizer:
    def __init__(self, save_dir=None)

    def plot_tech_stack_bar(tech_freq_df)           # 기술스택 TOP15 수평 막대
    def plot_career_donut(career_data)               # 경력 분포 도넛
    def plot_salary_boxplot(salary_data)              # 연봉 박스플롯
    def plot_company_ratings_grouped_bar(data)        # 기업별 평점 그룹 막대
    def plot_certificate_bar(cert_freq_df)            # 자격증 빈도 막대
    def plot_monthly_trend_line(monthly_data)         # 월별 추이 라인
    def plot_company_size_pie(size_data)              # 기업 규모 파이
    def plot_location_bar(location_data)              # 지역 분포 막대
    def plot_education_bar(education_data)            # 학력 요건 막대
    def plot_medical_domain_pie(domain_data)          # 도메인 파이 (★ 제목/메서드명)
    def plot_keyword_distribution(blog_df, news_df)   # 키워드 분포

    def generate_all(data_dict) → None
```

### 생성 차트 목록

| 차트 | 파일명 | 차트유형 | 사용 이유 |
|------|--------|---------|----------|
| 기술스택 TOP15 | `chart_tech_stack_top15.png` | 수평 막대 | 순위 비교에 효과적, 긴 기술명 수용 |
| 경력 분포 | `chart_career_donut.png` | 도넛 | 비율 표시, 중앙에 총건수 표시 |
| 연봉 분포 | `chart_salary_boxplot.png` | 박스플롯 | 중앙값, 사분위수, 이상값 동시 표현 |
| 기업 평점 | `chart_company_ratings.png` | 그룹 막대 | 기업별 다차원 평가 비교 |
| 자격증 빈도 | `chart_certificate_freq.png` | 수평 막대 | 적은 항목수에서 빈도 차이 명확 |
| 월별 추이 | `chart_monthly_trend.png` | 라인 | 시간에 따른 변화 추적 |
| 기업 규모 | `chart_company_size.png` | 파이 | 전체 대비 비율 표현 |
| 지역 분포 | `chart_location.png` | 막대 | 카테고리별 비교 |
| 학력 요건 | `chart_education.png` | 막대 | 카테고리별 비교 |
| 도메인 분포 | `chart_medical_domain.png` | 파이 | 도메인 카테고리 비율 |
| 키워드 분포 | `chart_keyword_distribution.png` | 분포 | 블로그 vs 뉴스 비교 |

### 분야 전환 시 수정

각 `plot_*()` 메서드의 `title` 문자열에서 "의료 AI" → "{분야명}"으로 변경.
`plot_medical_domain_pie()` → `plot_domain_pie()`로 메서드명 변경 (선택).

---

## 3. advanced_viz.py - 고급 차트 10종

### 클래스 구조

```python
class AdvancedVisualizer:
    def __init__(self, save_dir=None, data_path=None)

    def plot_keyword_tech_heatmap()          # 키워드-기술 히트맵
    def plot_company_radar()                  # 기업 레이더 차트
    def plot_job_treemap()                    # 직무 트리맵 (squarify)
    def plot_tech_network()                   # 기술 네트워크 (networkx)
    def plot_tech_category_stacked_bar()      # 기술 카테고리 누적 막대
    def plot_review_violin()                  # 리뷰 바이올린 플롯
    def plot_keyword_bubble()                 # 키워드 버블 차트
    def plot_domain_keyword_heatmap()         # 도메인-키워드 히트맵
    def plot_company_interview_comparison()   # 기업 면접 비교
    def plot_word_freq_bubble()               # 단어 빈도 버블

    def generate_all(data_dict=None) → None
```

### 생성 차트 목록

| 차트 | 파일명 | 차트유형 | 사용 이유 |
|------|--------|---------|----------|
| 키워드-기술 히트맵 | `adv_keyword_tech_heatmap.png` | 히트맵 | 2D 행렬의 동시출현 빈도 |
| 기업 레이더 | `adv_company_radar.png` | 레이더 | 다차원 평가 한눈에 비교 |
| 직무 트리맵 | `adv_job_treemap.png` | 트리맵 | 면적으로 비중 표현 |
| 기술 네트워크 | `adv_tech_network.png` | 네트워크 | 기술 간 동시출현 관계 |
| 기술 카테고리 | `adv_tech_category_stacked.png` | 누적 막대 | 절대량 + 비율 동시 표현 |
| 리뷰 바이올린 | `adv_review_violin.png` | 바이올린 | 분포 밀도 상세 표현 |
| 키워드 버블 | `adv_keyword_bubble.png` | 버블 | 3차원 데이터 표현 |
| 도메인 히트맵 | `adv_domain_keyword_heatmap.png` | 히트맵 | 카테고리-키워드 관계 |
| 면접 비교 | `adv_company_interview_comparison.png` | 그룹 막대 | 기업별 면접 특성 비교 |
| 단어 빈도 버블 | `adv_word_freq_bubble.png` | 버블 | 빈도의 시각적 비교 |

### 분야 전환 시 수정

- 각 메서드의 `title` 문자열 변경
- `_load_all_data()`에서 파일명 매칭 패턴 변경 (분야명 접미사)

---

## 4. interactive_viz.py - Plotly 인터랙티브 8종

### 클래스 구조

```python
class InteractiveVisualizer:
    def __init__(self, save_dir=None)

    def plot_salary_boxplot(salary_data)             # 인터랙티브 연봉 박스플롯
    def plot_tech_stack_bar(tech_data)                # 인터랙티브 기술스택 막대
    def plot_company_radar(company_data)              # 인터랙티브 기업 레이더
    def plot_trend_line(trend_data)                   # 인터랙티브 추이 라인
    def plot_sankey(flow_data)                        # 생키 다이어그램
    def plot_tech_cooccurrence_heatmap(cooc_data)     # 기술 동시출현 히트맵
    def plot_company_positioning_scatter(data)         # 기업 포지셔닝 산점도
    def plot_domain_sunburst(domain_data)             # 도메인 선버스트

    def generate_all(data_dict) → None
```

### 생성 결과

- HTML 파일로 저장 (브라우저에서 인터랙티브 탐색 가능)
- 호버 툴팁, 줌/팬, 범례 토글, PNG 내보내기 기능
- 분야 전환 시: 차트 제목만 변경

---

## 5. dashboard.py - 종합 대시보드

### 클래스 구조

```python
class AnalysisDashboard:
    def __init__(self, processed_data_path=None)

    def generate_summary_stats() → dict          # 요약 통계
    def save_individual_charts() → None           # 개별 서브차트 9종 PNG 저장
    def create_summary_dashboard() → None         # 3×3 matplotlib 대시보드
    def create_plotly_dashboard() → None          # Plotly 인터랙티브 대시보드
```

### 생성 차트 목록

| 차트 | 파일명 | 설명 |
|------|--------|------|
| 종합 대시보드 | `dashboard_summary.png` | 3×3 서브플롯 종합 |
| 인터랙티브 대시보드 | `dashboard_interactive.html` | Plotly HTML |
| 서브차트 1 | `dashboard_01_tech_stack.png` | 기술스택 |
| 서브차트 2 | `dashboard_02_review_status.png` | 리뷰 현황 |
| 서브차트 3 | `dashboard_03_interview_difficulty.png` | 면접 난이도 |
| 서브차트 4 | `dashboard_04_company_ratings.png` | 기업 평점 |
| 서브차트 5 | `dashboard_05_monthly_trend.png` | 월별 추이 |
| 서브차트 6 | `dashboard_06_company_size.png` | 기업 규모 |
| 서브차트 7 | `dashboard_07_medical_domain.png` | 도메인 분포 |
| 서브차트 8 | `dashboard_08_certificate_freq.png` | 자격증 빈도 |
| 서브차트 9 | `dashboard_09_key_stats.png` | 핵심 통계 |

### 분야 전환 시 수정

- 대시보드 제목 문자열 변경
- `_load_all_data()`의 파일명 매칭 패턴 변경

---

## 6. content_trend_viz.py - 콘텐츠 트렌드 5종

### 생성 차트

| 차트 | 파일명 | 차트유형 | 사용 이유 |
|------|--------|---------|----------|
| 블로그 vs 뉴스 월별 | `content_01_blog_vs_news_monthly.png` | 이중 라인 | 블로그/뉴스 관심도 추이 비교 |
| 뉴스 출처 Top15 | `content_02_news_source_top15.png` | 수평 막대 | 주요 보도 매체 식별 |
| 활발한 블로거 Top15 | `content_03_active_bloggers_top15.png` | 수평 막대 | 핵심 정보 소스 식별 |
| 키워드 월별 히트맵 | `content_04_keyword_monthly_heatmap.png` | 히트맵 | 시간-키워드 2D 트렌드 |
| 요일별 패턴 | `content_05_weekday_pattern.png` | 막대 | 콘텐츠 게시 패턴 |

### 분야 전환: 차트 제목, 파일명 매칭 패턴만 변경

---

## 7. cross_analysis_viz.py - 교차 분석 4종

### 생성 차트

| 차트 | 파일명 | 차트유형 | 사용 이유 |
|------|--------|---------|----------|
| 기술 카테고리 도넛 | `cross_01_tech_category_donut.png` | 도넛 | 기술 카테고리 비율 |
| 분야별 평균 평점 | `cross_02_field_avg_rating.png` | 그룹 막대 | 카테고리별 평점 비교 |
| 재직상태별 평점 | `cross_03_status_rating_boxplot.png` | 박스플롯 | 현직/전직 평점 분포 비교 |
| 면접 포지션 | `cross_04_interview_position.png` | 분포 | 직종별 면접 분포 |

### 분야 전환: 차트 제목, 카테고리명만 변경

---

## 8. jobplanet_deep_viz.py - 잡플래닛 심층 6종

### 생성 차트

| 차트 | 파일명 | 차트유형 | 사용 이유 |
|------|--------|---------|----------|
| 직종 분포 | `jobplanet_01_job_type_dist.png` | 막대/파이 | 직군별 리뷰 분포 |
| 지역 분포 | `jobplanet_02_location_dist.png` | 막대 | 기업 지리적 분포 |
| 면접 경로 | `jobplanet_03_interview_route.png` | 파이 | 면접 도달 경로 비율 |
| 난이도 히트맵 | `jobplanet_04_difficulty_heatmap.png` | 히트맵 | 기업×직종 난이도 |
| 기업별 직종 | `jobplanet_05_company_jobtype_stacked.png` | 누적 막대 | 인력 구조 비교 |
| 평점 vs 난이도 | `jobplanet_06_rating_vs_difficulty.png` | 산점도 | 두 변수 상관관계 |

### 분야 전환: 차트 제목만 변경 (잡플래닛 구조는 분야 무관)

---

## 9. wanted_viz.py - 원티드 전용 7종

### 생성 차트

| 차트 | 파일명 | 차트유형 | 사용 이유 |
|------|--------|---------|----------|
| 자격요건 워드클라우드 | `wanted_01_requirements_wordcloud.png` | 워드클라우드 | 핵심 요건 직관적 파악 |
| 직무 카테고리 | `wanted_02_job_category_dist.png` | 막대/파이 | 하위 카테고리 비율 |
| 산업 분포 | `wanted_03_industry_dist.png` | 막대 | 산업별 채용 분포 |
| 지역 분포 | `wanted_04_location_dist.png` | 막대 | 근무지 분포 |
| 기술 스택 | `wanted_05_tech_stack_dist.png` | 수평 막대 | 요구 기술 순위 |
| 경력 범위 | `wanted_06_career_range_dist.png` | 막대 | 경력 요건 분포 |
| 기업별 포지션 | `wanted_07_company_positions.png` | 수평 막대 | 활발한 채용 기업 |

### 분야 전환: 차트 제목, 카테고리명만 변경

---

## 전체 수정 체크리스트

- [ ] wordcloud_viz.py: 마스크 이미지 교체 (settings.py의 WORDCLOUD_MASK_PATH)
- [ ] wordcloud_viz.py: STOPWORDS에 분야별 불용어 추가
- [ ] wordcloud_viz.py: `generate_medical_domain_wordcloud()` → `generate_domain_wordcloud()`
- [ ] 모든 9개 파일: 차트 제목에서 "의료 AI" → "{분야명}" 교체
- [ ] chart_viz.py: `plot_medical_domain_pie()` → `plot_domain_pie()` (선택)
- [ ] advanced_viz.py / dashboard.py: `_load_all_data()` 파일명 매칭 패턴 변경
- [ ] (선택) 색상맵을 분야 이미지에 맞게 변경
