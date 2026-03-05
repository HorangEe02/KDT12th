"""
STEP 11: 대구 인구유지 전략 보고서 생성 (v2 신규)
실행: python src/subtopic2/s2_step11_daegu_strategy.py
의존: STEP 10 완료
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import math
from s2_step0_config import get_connection, DB_NAME, S2_OUTPUT_DIR


def query_to_df(sql):
    conn = get_connection(DB_NAME, for_pandas=True)
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


def fmt_val(v, name=""):
    """nan/None 값을 보고서용 텍스트로 변환"""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "데이터 없음(추정치 활용)"
    return f"{v:,.2f}" if isinstance(v, float) else str(v)


def generate_report():
    print("\n" + "=" * 70)
    print("대구 인구유지 전략 보고서 생성")
    print("=" * 70)

    # 스코어카드 전체 조회
    df_sc = query_to_df("""
        SELECT comparison_axis, metric_category,
               daegu_metric_name, daegu_value,
               us_city_name, us_metric_name, us_value,
               gap_direction, correlation_insight, strategy_implication
        FROM pop_housing_4axis_scorecard
        ORDER BY FIELD(comparison_axis, '종합', '산업', '기후', '변모'), metric_category
    """)

    # 축별 요약 조회
    df_sum = query_to_df("""
        SELECT comparison_axis, us_city_name,
               pop_trend, housing_demand_trend, market_temp_trend, price_trend,
               causal_pathway, daegu_comparison, policy_lesson
        FROM pop_housing_axis_summary
        ORDER BY FIELD(comparison_axis, '종합', '산업', '기후', '변모')
    """)

    report = []
    report.append("# 대구광역시 인구유지 전략 보고서")
    report.append("> 소주제 2: 인구 이동과 주택 수요 — 미국 4개 유사 도시 비교 분석 기반\n")
    report.append("---\n")

    # 요약 표
    report.append("## Executive Summary\n")
    report.append("| 비교축 | 미국 도시 | 인구 추세 | 부동산 수요 | 시장 온도 | 가격 추세 |")
    report.append("|--------|----------|----------|-----------|----------|----------|")
    for _, row in df_sum.iterrows():
        report.append(f"| {row['comparison_axis']} | {row['us_city_name']} | "
                     f"{row['pop_trend']} | {row['housing_demand_trend']} | "
                     f"{row['market_temp_trend']} | {row['price_trend']} |")
    report.append(f"| **대구** | - | **유출(-)** | **수요 감소** | **냉각** | **정체** |\n")

    # 축별 상세
    for axis in ['종합', '산업', '기후', '변모']:
        axis_sc = df_sc[df_sc['comparison_axis'] == axis]
        axis_sm = df_sum[df_sum['comparison_axis'] == axis]

        if axis_sc.empty and axis_sm.empty:
            continue

        us_city = axis_sc.iloc[0]['us_city_name'] if not axis_sc.empty else ''
        report.append(f"## {axis} 비교: 대구 vs {us_city}\n")

        # 인과 경로
        if not axis_sm.empty:
            sm = axis_sm.iloc[0]
            report.append(f"### 인과 경로\n")
            report.append(f"```\n{sm['causal_pathway']}\n```\n")
            report.append(f"### 대구와의 차이\n{sm['daegu_comparison']}\n")

        # 지표별 비교
        for _, row in axis_sc.iterrows():
            dg_val = fmt_val(row['daegu_value'], row['daegu_metric_name'])
            us_val = fmt_val(row['us_value'], row['us_metric_name'])
            report.append(f"### {row['metric_category']}")
            report.append(f"- **대구:** {row['daegu_metric_name']} = {dg_val}")
            report.append(f"- **{us_city}:** {row['us_metric_name']} = {us_val}")
            report.append(f"- **격차:** {row['gap_direction']}")
            report.append(f"\n**인사이트:** {row['correlation_insight']}\n")
            report.append(f"**전략 시사점:** {row['strategy_implication']}\n")

        # 정책 교훈
        if not axis_sm.empty:
            report.append(f"### 정책 교훈\n{axis_sm.iloc[0]['policy_lesson']}\n")

        report.append("---\n")

    # 종합 전략
    report.append("## 대구 인구유지 + 부동산 활성화 종합 전략\n")
    report.append("""
| # | 전략 | 벤치마크 | 인구 효과 | 부동산 효과 | 우선순위 |
|---|------|---------|----------|-----------|---------|
| 1 | **주택가격 경쟁력 마케팅** | Dallas, Phoenix | 수도권 유출 인구 흡수 | 거래량 증가, 시장 안정 | 단기 |
| 2 | **원격근무자 유치 프로그램** | Phoenix | 서울 소득+대구 주거비 | 수요 증가, 가격 완만 상승 | 단기 |
| 3 | **앵커 기업 유치** | Charlotte, Dallas | 고소득 일자리 → 인구유입 | 신규건설 증가, 가격 상승 | 중기 |
| 4 | **산학 클러스터 구축** | Atlanta, Charlotte | 전문직 유입 | 고급 주택 수요 증가 | 중기 |
| 5 | **교통 인프라 혁신** | Atlanta | 광역 생활권 확대 | 외곽 개발 활성화 | 중기 |
| 6 | **의료·바이오 특구** | Atlanta | 은퇴+전문직 유입 | 다양한 수요 창출 | 장기 |
| 7 | **산업 전환 완성** | Charlotte | 인구 안정화+유입 전환 | 시장 과열→가격 급등 | 장기 |

### 인구-부동산 선순환 모델

```
[현재] 인구유출 → 수요 감소 → 시장냉각 → 가격정체 → 매력도 하락 → 추가유출 (악순환)
                     | (전략 투입)
[목표] 기업유치+가격경쟁력 → 인구유입 전환 → 수요 증가 → 시장활성화 → 가격상승 → 투자매력 상승 (선순환)
```

### 핵심 KPI (인구유입 전환 신호)

| 지표 | 현재 (대구) | 목표 (5년 후) | 벤치마크 |
|------|-----------|-------------|---------|
| 인구변동률 | -0.5~-1.0% | 0% (유출 중단) | Dallas +1.5% |
| 시장온도지수 | 없음(추정 30~40) | 45~50 | Dallas 55~65 |
| 연간 거래건수 | 감소 추세 | 10% 증가 | Atlanta 패턴 |
| 주택구매 필요소득 | 낮음 | 완만 상승 | Charlotte 패턴 |

---

## 분석 시각화 자료

| # | 시각화 | 파일명 | 핵심 내용 |
|---|--------|--------|----------|
| V7 | 인구성장률 대조 | `s2_viz7_pop_growth_contrast.png` | 대구 자연증감률(+2.7→-3.4) vs 미국 4도시 ZHVI 상승 |
| V8 | 4축 경로 대시보드 | `s2_viz8_4axis_pathway.png` | 도시별 Sales Count + Market Temp 추이 |
| V9 | 시장온도 산점도 | `s2_viz9_pop_vs_market_temp.png` | ZHVI 변동률↔시장온도 양의 상관(slope=0.8) |
| V10 | 대구 vs 미국 이중축 | `s2_viz10_daegu_vs_us_dual.png` | 미국 ZHVI 상승 vs 대구 자연증감 감소+아파트가격 |
| V11 | Phoenix 과열 사이클 | `s2_viz11_phoenix_cycle.png` | 시장온도 77(2021) 과열→조정, ZHVI 버블·폭락 사이클 |
| V12 | 전략 로드맵 | `s2_viz12_strategy_roadmap.png` | 0→3→7→15년차 단계별 인구·부동산 전략 |

---

*본 보고서는 미국 Census, Zillow, 대구 부동산 실거래가, 한국 인구통계 데이터를 기반으로 작성되었습니다.*
""")

    # 저장
    path = os.path.join(S2_OUTPUT_DIR, 's2_daegu_population_strategy_report.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n[OK] 보고서 저장: {path}")
    return path


if __name__ == '__main__':
    path = generate_report()
    print(f"\n[DONE] S2 STEP 11 완료: {path}")
