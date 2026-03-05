# 06. outputs 디렉토리 가이드

> 시각화 결과와 분석 보고서가 저장되는 디렉토리이다.
> 분야 전환 시 별도 수정 없이, 시각화 모듈 실행 시 자동으로 파일이 생성된다.

---

## 디렉토리 구조

```
outputs/
├── charts/                  ← 시각화 결과 (52개 파일)
│   │
│   │  [워드클라우드 - wordcloud_viz.py]
│   ├── wc_tech_stack.png
│   ├── wc_blog_keywords.png
│   ├── wc_blog_keywords_only.png
│   ├── wc_medical_domain.png
│   ├── wc_job_requirements.png
│   │
│   │  [기본 차트 - chart_viz.py]
│   ├── chart_tech_stack_top15.png
│   ├── chart_certificate_freq.png
│   ├── chart_keyword_distribution.png
│   │
│   │  [콘텐츠 트렌드 - content_trend_viz.py]
│   ├── content_01_blog_vs_news_monthly.png
│   ├── content_02_news_source_top15.png
│   ├── content_03_active_bloggers_top15.png
│   ├── content_04_keyword_monthly_heatmap.png
│   ├── content_05_weekday_pattern.png
│   │
│   │  [교차 분석 - cross_analysis_viz.py]
│   ├── cross_01_tech_category_donut.png
│   ├── cross_02_field_avg_rating.png
│   ├── cross_03_status_rating_boxplot.png
│   ├── cross_04_interview_position.png
│   │
│   │  [대시보드 - dashboard.py]
│   ├── dashboard_summary.png              ← 3×3 종합 대시보드
│   ├── dashboard_interactive.html         ← Plotly 인터랙티브
│   ├── dashboard_01_tech_stack.png
│   ├── dashboard_02_review_status.png
│   ├── dashboard_03_interview_difficulty.png
│   ├── dashboard_04_company_ratings.png
│   ├── dashboard_05_monthly_trend.png
│   ├── dashboard_06_company_size.png
│   ├── dashboard_07_medical_domain.png
│   ├── dashboard_08_certificate_freq.png
│   ├── dashboard_09_key_stats.png
│   │
│   │  [잡플래닛 심층 - jobplanet_deep_viz.py]
│   ├── jobplanet_01_job_type_dist.png
│   ├── jobplanet_02_location_dist.png
│   ├── jobplanet_03_interview_route.png
│   ├── jobplanet_04_difficulty_heatmap.png
│   ├── jobplanet_05_company_jobtype_stacked.png
│   ├── jobplanet_06_rating_vs_difficulty.png
│   │
│   │  [원티드 전용 - wanted_viz.py]
│   ├── wanted_01_requirements_wordcloud.png
│   ├── wanted_02_job_category_dist.png
│   ├── wanted_03_industry_dist.png
│   ├── wanted_04_location_dist.png
│   ├── wanted_05_tech_stack_dist.png
│   ├── wanted_06_career_range_dist.png
│   ├── wanted_07_company_positions.png
│   │
│   │  [고급 차트 - advanced_viz.py]
│   ├── adv_keyword_tech_heatmap.png
│   ├── adv_company_radar.png
│   ├── adv_job_treemap.png
│   ├── adv_tech_network.png
│   ├── adv_tech_category_stacked.png
│   ├── adv_review_violin.png
│   ├── adv_keyword_bubble.png
│   ├── adv_domain_keyword_heatmap.png
│   ├── adv_company_interview_comparison.png
│   ├── adv_word_freq_bubble.png
│   │
│   │  [인터랙티브 - interactive_viz.py]
│   └── interactive_tech_stack_bar.html
│
└── reports/                 ← 분석 보고서
    ├── 의료AI_취업동향_분석_결과보고서.md
    ├── 다른_분야_적용_가이드라인.md
    └── 가이드라인/           ← 모듈별 분리 가이드
        ├── 00_프로젝트_개요_가이드.md
        ├── 01_config_모듈_가이드.md
        ├── 02_crawlers_모듈_가이드.md
        ├── 03_processors_모듈_가이드.md
        ├── 04_data_디렉토리_가이드.md
        ├── 05_visualizations_모듈_가이드.md
        ├── 06_outputs_디렉토리_가이드.md
        └── 07_main_실행_및_프롬프트_가이드.md
```

---

## 차트 분류별 통계

| 시각화 모듈 | PNG | HTML | 합계 |
|------------|-----|------|------|
| wordcloud_viz.py | 5 | - | 5 |
| chart_viz.py | 3 | - | 3 |
| content_trend_viz.py | 5 | - | 5 |
| cross_analysis_viz.py | 4 | - | 4 |
| dashboard.py | 10 | 1 | 11 |
| jobplanet_deep_viz.py | 6 | - | 6 |
| wanted_viz.py | 7 | - | 7 |
| advanced_viz.py | 10 | - | 10 |
| interactive_viz.py | - | 1 | 1 |
| **합계** | **50** | **2** | **52** |

---

## 파일 형식

### PNG 파일 (50개)
- **해상도**: 300 DPI
- **배경**: 흰색 (facecolor="white")
- **여백**: tight layout (bbox_inches="tight")
- 보고서 삽입, 인쇄, 프레젠테이션에 적합

### HTML 파일 (2개)
- **dashboard_interactive.html**: Plotly 종합 대시보드
- **interactive_tech_stack_bar.html**: Plotly 기술스택 막대
- 브라우저에서 열면 인터랙티브 탐색 가능
- 호버 툴팁, 줌/팬, 범례 토글, PNG 내보내기 기능

---

## 분야 전환 시 변경 사항

**별도 수정 불필요**. 시각화 모듈을 실행하면 동일한 파일명으로 `outputs/charts/`에 자동 저장된다.

디렉토리 자체는 `settings.py`에서 `os.makedirs(exist_ok=True)`로 자동 생성되므로 수동 생성 불필요.

---

## 활용 방법

### 보고서에 차트 삽입 (Markdown)

```markdown
![기술스택 워드클라우드](../charts/wc_tech_stack.png)
![기술스택 TOP15](../charts/chart_tech_stack_top15.png)
![종합 대시보드](../charts/dashboard_summary.png)
```

### HTML 대시보드 공유

```bash
# 브라우저에서 직접 열기
open outputs/charts/dashboard_interactive.html

# 또는 간단한 HTTP 서버로 공유
cd outputs/charts
python -m http.server 8080
```
