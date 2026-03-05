"""
STEP 9: 대구 발전전략 종합 도출 (v2 신규)
- city_axis_scorecard → Markdown 보고서 자동 생성
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from step0_setup import *


def generate_strategy_report():
    """city_axis_scorecard → 대구 발전전략 종합 보고서 생성"""

    print("\n" + "=" * 70)
    print("대구 생존 전략 보고서 생성")
    print("=" * 70)

    df = query_to_df("""
        SELECT comparison_axis, metric_category,
               daegu_metric_name, daegu_value,
               us_city_name, us_metric_name, us_value,
               gap_ratio, insight, strategy_implication
        FROM city_axis_scorecard
        ORDER BY FIELD(comparison_axis, '종합', '산업', '기후', '변모'),
                 metric_category
    """)

    if df.empty:
        print("  [WARN] 스코어카드 데이터 없음. STEP 8을 먼저 실행하세요.")
        return None

    report = []
    report.append("# 대구광역시 생존 전략 보고서")
    report.append("> 미국 4개 유사 도시 비교 분석 기반\n")
    report.append("---\n")

    axis_info = {
        '종합': ('Dallas', '내륙 대도시, 보수적 성향, 무더운 여름'),
        '산업': ('Atlanta', '자동차·배터리 허브, 교통 요충지'),
        '기후': ('Phoenix', '분지 지형, 극심한 폭염'),
        '변모': ('Charlotte', '섬유→에너지/금융/첨단 도시 변모'),
    }

    for axis in ['종합', '산업', '기후', '변모']:
        axis_df = df[df['comparison_axis'] == axis]
        if axis_df.empty:
            continue

        us_city = axis_info[axis][0]
        common = axis_info[axis][1]

        report.append(f"## {axis} 비교: 대구 vs {us_city}")
        report.append(f"**공통점:** {common}\n")

        for _, row in axis_df.iterrows():
            category = row['metric_category'] if row['metric_category'] else '기타'
            report.append(f"### {category}")

            daegu_val = row['daegu_value']
            us_val = row['us_value']
            report.append(f"- **대구:** {row['daegu_metric_name']} = {daegu_val if daegu_val is not None else 'N/A'}")
            report.append(f"- **{row['us_city_name']}:** {row['us_metric_name']} = {us_val if us_val is not None else 'N/A'}")
            if row['gap_ratio']:
                report.append(f"- **격차 비율:** {row['gap_ratio']}")
            report.append(f"\n**인사이트:** {row['insight']}\n")
            report.append(f"**대구 전략 시사점:** {row['strategy_implication']}\n")
            report.append("---\n")

    # 종합 전략
    report.append("## 대구 인구유지 종합 전략\n")
    report.append("### 미국 4개 도시에서 배운 5대 핵심 전략\n")
    report.append("""
| # | 전략 | 벤치마크 도시 | 대구 적용 방안 |
|---|------|-------------|--------------|
| 1 | **주택 가격 경쟁력 마케팅** | Dallas, Phoenix | 수도권 대비 1/3~1/4 가격을 적극 홍보, 원격근무자 유치 |
| 2 | **앵커 기업 유치** | Charlotte, Dallas | 대기업 지역본사/R&D센터 유치 인센티브 (세제 혜택+부지 제공) |
| 3 | **교통 인프라 혁신** | Atlanta | KTX 30분 생활권 확대, 대구공항 국제선 확충, 광역교통망 |
| 4 | **산학 협력 생태계** | Charlotte, Atlanta | 경북대+DGIST+영남대 중심 산학클러스터, 스타트업 지원 |
| 5 | **기후 핸디캡 극복** | Phoenix | 도시 냉방 인프라, 실내 문화시설, 그린 인프라 투자 |

### 타임라인 제안

```
단기 (1~3년): 원격근무자 유치 + 주택 가격 경쟁력 마케팅
중기 (3~7년): 앵커 기업 유치 + 교통 인프라 착공
장기 (7~15년): 산업 전환 완성 + 인구 안정화
```

### Charlotte에서 배운 교훈
Charlotte의 산업 전환은 약 30년이 소요되었습니다.
대구는 1990년대부터 전환을 시작했으므로, 2025년 현재 약 30년째입니다.
Charlotte가 전환 완성기(2000년대 중반)에 보인 신호들:
- 신규건설 판매건수 급증
- 시장온도지수 상승 (판매자 우위)
- 주택구매 필요소득 증가 (고소득 유입)

대구가 이 신호들을 보이기 시작한다면, 전환 성공의 초기 징후로 볼 수 있습니다.
""")

    # 파일 저장
    report_path = os.path.join(OUTPUT_DIR, 'daegu_strategy_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n  [OK] 보고서 저장: {report_path}")

    # CSV 백업도 저장
    csv_path = os.path.join(OUTPUT_DIR, 'S4_SCORECARD.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"  [OK] 스코어카드 CSV: {csv_path}")

    return report_path


def run():
    print("=" * 60)
    print("STEP 9: 대구 발전전략 보고서")
    print("=" * 60)
    generate_strategy_report()
    print("\n  STEP 9 완료!")


if __name__ == '__main__':
    run()
