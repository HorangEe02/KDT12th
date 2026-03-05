"""
=============================================================
의료 AI 분야 취업 동향 분석 - 전체 파이프라인 실행
=============================================================
크롤링 → 전처리 → 분석 → 시각화 → URL 목록 정리
=============================================================
실행 예시:
    python main.py --phase all
    python main.py --phase crawl --source naver
    python main.py --phase visualize --skip-crawl
=============================================================
"""

import os
import sys
import argparse
from datetime import datetime

import pandas as pd

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.settings import (
    DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUTS_CHARTS_DIR,
    URL_LIST_DIR, NAVER_BLOG_KEYWORDS, NAVER_NEWS_KEYWORDS,
)


# ============================================================
# Phase 1: 크롤링
# ============================================================
def run_crawling(source="all"):
    """데이터 크롤링 실행"""
    print("\n" + "=" * 60)
    print("📥 Phase 1: 데이터 크롤링")
    print("=" * 60)

    # 1-1. Naver OpenAPI 크롤링
    if source in ("all", "naver"):
        print("\n--- [1/4] Naver OpenAPI 크롤링 (블로그 + 뉴스) ---")
        try:
            from crawlers.naver_api_crawler import NaverAPICrawler
            crawler = NaverAPICrawler()
            crawler.run_all()
        except Exception as e:
            print(f"  ❌ Naver 크롤링 오류: {e}")

    # 1-2. 사람인 채용공고 크롤링
    if source in ("all", "saramin"):
        print("\n--- [2/4] 사람인 채용공고 크롤링 ---")
        try:
            from crawlers.saramin_crawler import SaraminCrawler
            crawler = SaraminCrawler()
            crawler.run_all()
        except Exception as e:
            print(f"  ❌ 사람인 크롤링 오류: {e}")

    # 1-3. 원티드 포지션 크롤링
    if source in ("all", "wanted"):
        print("\n--- [3/4] 원티드 포지션 크롤링 ---")
        try:
            from crawlers.wanted_crawler import WantedCrawler
            crawler = WantedCrawler(headless=True)
            try:
                crawler.run_all()
            finally:
                crawler.close()
        except Exception as e:
            print(f"  ❌ 원티드 크롤링 오류: {e}")

    # 1-4. 잡플래닛 기업 리뷰/연봉/면접후기 크롤링
    if source in ("all", "jobplanet"):
        print("\n--- [4/4] 잡플래닛 기업 크롤링 ---")
        try:
            from crawlers.jobplanet_crawler import JobPlanetCrawler
            crawler = JobPlanetCrawler(headless=True)
            try:
                crawler.run_all()
            finally:
                crawler.close()
        except Exception as e:
            print(f"  ❌ 잡플래닛 크롤링 오류: {e}")


# ============================================================
# Phase 2: 데이터 전처리
# ============================================================
def run_processing():
    """데이터 전처리 실행"""
    print("\n" + "=" * 60)
    print("🔧 Phase 2: 데이터 전처리")
    print("=" * 60)

    from processors.data_cleaner import DataCleaner
    cleaner = DataCleaner()
    cleaner.process_all_raw_data()


# ============================================================
# Phase 3: 데이터 분석
# ============================================================
def run_analysis():
    """데이터 분석 실행"""
    print("\n" + "=" * 60)
    print("📊 Phase 3: 데이터 분석")
    print("=" * 60)

    import glob

    # 전처리 데이터 로드
    processed_files = glob.glob(os.path.join(DATA_PROCESSED_DIR, "*.csv"))
    if not processed_files:
        # raw 데이터라도 사용
        processed_files = glob.glob(os.path.join(DATA_RAW_DIR, "*.csv"))

    all_data = {}
    for f in processed_files:
        name = os.path.basename(f).replace("_processed.csv", "").replace(".csv", "")
        try:
            all_data[name] = pd.read_csv(f, encoding="utf-8-sig")
            print(f"  📂 로드: {name} ({len(all_data[name])}건)")
        except Exception as e:
            print(f"  ⚠️ {name} 로드 실패: {e}")

    if not all_data:
        print("  ⚠️ 분석할 데이터가 없습니다.")
        return {}

    # 텍스트 분석
    print("\n  📈 텍스트 분석 시작...")
    from processors.text_analyzer import TextAnalyzer
    analyzer = TextAnalyzer()

    # 모든 텍스트 합치기
    all_texts = []
    for name, df in all_data.items():
        text_cols = ["제목", "내용요약", "자격요건", "우대사항", "주요업무",
                     "장점", "단점", "한줄평", "면접경험", "면접질문",
                     "기술스택태그", "혜택및복지", "회사소개", "포지션명",
                     "공고제목", "기술스택", "자격증", "복리후생", "직무분야"]
        for col in text_cols:
            if col in df.columns:
                all_texts.extend(df[col].dropna().tolist())

    # 단어 빈도
    word_freq = analyzer.get_word_frequency(all_texts, top_n=50)
    if not word_freq.empty:
        word_freq.to_csv(os.path.join(DATA_PROCESSED_DIR, "word_frequency.csv"),
                         index=False, encoding="utf-8-sig")
        print(f"  ✅ 단어 빈도 분석 완료: {len(word_freq)}개")

    # 기술스택 빈도
    combined_df = pd.concat(all_data.values(), ignore_index=True) if all_data else pd.DataFrame()
    tech_freq = analyzer.get_tech_stack_frequency(combined_df)
    if not tech_freq.empty:
        tech_freq.to_csv(os.path.join(DATA_PROCESSED_DIR, "tech_stack_frequency.csv"),
                         index=False, encoding="utf-8-sig")
        print(f"  ✅ 기술스택 빈도 분석 완료: {len(tech_freq)}개")
        print("\n  🔧 기술스택 TOP 10:")
        for _, row in tech_freq.head(10).iterrows():
            print(f"     {row.iloc[0]}: {int(row.iloc[1])}회")

    # 자격증 빈도
    cert_freq = analyzer.get_certificate_frequency(combined_df)
    if not cert_freq.empty:
        cert_freq.to_csv(os.path.join(DATA_PROCESSED_DIR, "certificate_frequency.csv"),
                         index=False, encoding="utf-8-sig")
        print(f"\n  ✅ 자격증 빈도 분석 완료: {len(cert_freq)}개")

    # 의료 도메인 빈도
    domain_freq = analyzer.get_medical_domain_frequency(combined_df)
    if not domain_freq.empty:
        domain_freq.to_csv(os.path.join(DATA_PROCESSED_DIR, "medical_domain_frequency.csv"),
                           index=False, encoding="utf-8-sig")
        print(f"  ✅ 의료 도메인 빈도 분석 완료: {len(domain_freq)}개")

    # 연봉 분석
    print("\n  💰 연봉 분석 시작...")
    from processors.salary_analyzer import SalaryAnalyzer
    salary_analyzer = SalaryAnalyzer(combined_df)
    salary_stats = salary_analyzer.get_salary_stats()
    print(f"  연봉 통계: {salary_stats}")

    return {
        "all_data": all_data,
        "combined_df": combined_df,
        "all_texts": all_texts,
        "tech_freq": tech_freq,
        "cert_freq": cert_freq,
        "domain_freq": domain_freq,
        "word_freq": word_freq,
    }


# ============================================================
# Phase 4: 시각화
# ============================================================
def run_visualization(analysis_results: dict = None):
    """시각화 생성"""
    print("\n" + "=" * 60)
    print("🎨 Phase 4: 시각화 생성")
    print("=" * 60)

    if analysis_results is None:
        analysis_results = run_analysis()

    tech_freq = analysis_results.get("tech_freq", pd.DataFrame())
    cert_freq = analysis_results.get("cert_freq", pd.DataFrame())
    all_texts = analysis_results.get("all_texts", [])
    all_data = analysis_results.get("all_data", {})
    combined_df = analysis_results.get("combined_df", pd.DataFrame())

    # 4-1. 워드클라우드
    print("\n--- [1/10] 워드클라우드 생성 ---")
    try:
        from visualizations.wordcloud_viz import WordCloudVisualizer
        wc_viz = WordCloudVisualizer()

        # 데이터 준비
        wc_data = {"blog": [], "interview": [], "review_pros": [],
                   "review_cons": [], "tech_stack": {}, "medical_domain": {}}

        for name, df in all_data.items():
            if "블로그" in name or "blog" in name.lower():
                for col in ["제목", "내용요약"]:
                    if col in df.columns:
                        wc_data["blog"].extend(df[col].dropna().tolist())
            if "면접" in name or "interview" in name.lower():
                for col in ["면접경험", "면접질문"]:
                    if col in df.columns:
                        wc_data["interview"].extend(df[col].dropna().tolist())
            if "리뷰" in name or "review" in name.lower():
                if "장점" in df.columns:
                    wc_data["review_pros"].extend(df["장점"].dropna().tolist())
                if "단점" in df.columns:
                    wc_data["review_cons"].extend(df["단점"].dropna().tolist())

        # 기술스택 딕셔너리
        if not tech_freq.empty:
            wc_data["tech_stack"] = dict(zip(tech_freq.iloc[:, 0], tech_freq.iloc[:, 1]))

        # 의료 도메인 텍스트
        wc_data["medical_domain"] = all_texts[:500] if all_texts else []

        # 채용 자격요건/우대사항/주요업무 텍스트 (원티드 + 사람인)
        job_req_texts = []
        for name, df in all_data.items():
            if "원티드" in name or "wanted" in name.lower() or "사람인" in name or "saramin" in name.lower():
                for col in ["자격요건", "우대사항", "주요업무"]:
                    if col in df.columns:
                        job_req_texts.extend(df[col].dropna().tolist())
        if job_req_texts:
            wc_data["job_requirements"] = job_req_texts

        wc_viz.generate_all(wc_data)
    except Exception as e:
        print(f"  ❌ 워드클라우드 생성 오류: {e}")

    # 4-2. 기본 차트
    print("\n--- [2/10] 기본 차트 생성 ---")
    try:
        from visualizations.chart_viz import ChartVisualizer
        chart_viz = ChartVisualizer()

        # 블로그/뉴스 데이터 로드 (키워드 분포 차트용)
        blog_df = None
        news_df = None
        for name, df in all_data.items():
            if "blog" in name.lower() or "블로그" in name:
                blog_df = df
            if "news" in name.lower() or "뉴스" in name:
                news_df = df

        chart_data = {
            "tech_freq": tech_freq if not tech_freq.empty else None,
            "cert_freq": cert_freq if not cert_freq.empty else None,
            "blog_df": blog_df,
            "news_df": news_df,
        }

        # 사람인/원티드 채용공고에서 경력/지역/학력 분포 추출
        for name, df in all_data.items():
            if "사람인" in name or "saramin" in name.lower() or "원티드" in name or "wanted" in name.lower():
                if "경력조건" in df.columns and chart_data.get("career") is None:
                    career_counts = df["경력조건"].dropna().value_counts().reset_index()
                    career_counts.columns = ["경력조건", "건수"]
                    chart_data["career"] = career_counts
                if "근무지역" in df.columns and chart_data.get("location") is None:
                    loc_counts = df["근무지역"].dropna().value_counts().head(15).reset_index()
                    loc_counts.columns = ["근무지역", "건수"]
                    chart_data["location"] = loc_counts
                if "학력조건" in df.columns and chart_data.get("education") is None:
                    edu_counts = df["학력조건"].dropna().value_counts().reset_index()
                    edu_counts.columns = ["학력조건", "건수"]
                    chart_data["education"] = edu_counts

        chart_viz.generate_all(chart_data)
    except Exception as e:
        print(f"  ❌ 기본 차트 생성 오류: {e}")

    # 4-3. 고급 차트
    print("\n--- [3/10] 고급 차트 생성 ---")
    try:
        from visualizations.advanced_viz import AdvancedVisualizer
        adv_viz = AdvancedVisualizer()
        adv_viz.generate_all({})
    except Exception as e:
        print(f"  ❌ 고급 차트 생성 오류: {e}")

    # 4-4. 인터랙티브 차트
    print("\n--- [4/10] 인터랙티브 차트 생성 ---")
    try:
        from visualizations.interactive_viz import InteractiveVisualizer
        inter_viz = InteractiveVisualizer()
        inter_data = {
            "tech_freq": tech_freq if not tech_freq.empty else None,
        }
        inter_viz.generate_all(inter_data)
    except Exception as e:
        print(f"  ❌ 인터랙티브 차트 생성 오류: {e}")

    # 4-5. 종합 대시보드
    print("\n--- [5/10] 종합 대시보드 생성 ---")
    try:
        from visualizations.dashboard import AnalysisDashboard
        dashboard = AnalysisDashboard()
        dashboard.create_summary_dashboard()
        dashboard.create_plotly_dashboard()
    except Exception as e:
        print(f"  ❌ 대시보드 생성 오류: {e}")

    # 4-6. 잡플래닛 심층 분석
    print("\n--- [6/10] 잡플래닛 심층 분석 ---")
    try:
        from visualizations.jobplanet_deep_viz import JobPlanetDeepVisualizer
        jp_viz = JobPlanetDeepVisualizer()
        jp_viz.generate_all()
    except Exception as e:
        print(f"  ❌ 잡플래닛 심층 분석 오류: {e}")

    # 4-7. 콘텐츠 트렌드 분석
    print("\n--- [7/10] 콘텐츠 트렌드 분석 ---")
    try:
        from visualizations.content_trend_viz import ContentTrendVisualizer
        ct_viz = ContentTrendVisualizer()
        ct_viz.generate_all()
    except Exception as e:
        print(f"  ❌ 콘텐츠 트렌드 분석 오류: {e}")

    # 4-8. 크로스 분석
    print("\n--- [8/10] 크로스 분석 ---")
    try:
        from visualizations.cross_analysis_viz import CrossAnalysisVisualizer
        ca_viz = CrossAnalysisVisualizer()
        ca_viz.generate_all()
    except Exception as e:
        print(f"  ❌ 크로스 분석 오류: {e}")

    # 4-9. 원티드 채용 포지션 분석
    print("\n--- [9/10] 원티드 채용 포지션 분석 ---")
    try:
        from visualizations.wanted_viz import WantedVisualizer
        w_viz = WantedVisualizer()
        w_viz.generate_all()
    except Exception as e:
        print(f"  ❌ 원티드 시각화 오류: {e}")

    # 4-10. 사람인 채용공고 분석
    print("\n--- [10/10] 사람인 채용공고 분석 ---")
    try:
        from visualizations.saramin_viz import SaraminVisualizer
        s_viz = SaraminVisualizer()
        s_viz.generate_all()
    except Exception as e:
        print(f"  ❌ 사람인 시각화 오류: {e}")


# ============================================================
# Phase 5: URL 목록 정리
# ============================================================
def organize_url_list():
    """크롤링 URL 목록 정리 및 검증"""
    print("\n" + "=" * 60)
    print("📋 Phase 5: 크롤링 URL 목록 정리")
    print("=" * 60)

    url_path = os.path.join(URL_LIST_DIR, "crawling_urls.csv")

    if os.path.exists(url_path):
        df = pd.read_csv(url_path, encoding="utf-8-sig")
        # 중복 제거
        before = len(df)
        df = df.drop_duplicates(subset=["URL"], keep="first").reset_index(drop=True)
        df["번호"] = range(1, len(df) + 1)
        df.to_csv(url_path, index=False, encoding="utf-8-sig")

        print(f"  총 URL: {len(df)}개 (중복 제거: {before - len(df)}개)")

        # 소스별 현황
        if "소스" in df.columns:
            print("\n  📋 소스별 URL 현황:")
            for source, count in df["소스"].value_counts().items():
                print(f"     {source}: {count}개")

        if len(df) >= 100:
            print(f"\n  ✅ URL {len(df)}개 확보 → 100개 요구사항 충족!")
        else:
            print(f"\n  ⚠️ URL {len(df)}개 → 100개 미달 (추가 크롤링 필요)")
    else:
        print("  ⚠️ URL 목록 파일이 없습니다.")


# ============================================================
# 메인 실행
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="의료 AI 분야 취업 동향 분석")
    parser.add_argument("--phase", type=str, default="all",
                        choices=["crawl", "process", "analyze", "visualize", "all"],
                        help="실행할 단계 (기본: all)")
    parser.add_argument("--source", type=str, default="all",
                        choices=["naver", "saramin", "wanted", "jobplanet", "all"],
                        help="크롤링 소스 (기본: all)")
    parser.add_argument("--skip-crawl", action="store_true",
                        help="크롤링 스킵하고 기존 데이터로 분석만 실행")

    args = parser.parse_args()

    print("=" * 60)
    print("🏥 의료 AI 분야 취업 동향 분석 시작")
    print(f"📅 실행 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 실행 단계: {args.phase}")
    if args.phase in ("crawl", "all"):
        print(f"🔗 크롤링 소스: {args.source}")
    if args.skip_crawl:
        print("⏭️ 크롤링 단계 스킵")
    print("=" * 60)

    analysis_results = None

    # Phase 1: 크롤링
    if args.phase in ("crawl", "all") and not args.skip_crawl:
        run_crawling(args.source)

    # Phase 2: 전처리
    if args.phase in ("process", "all"):
        run_processing()

    # Phase 3: 분석
    if args.phase in ("analyze", "visualize", "all"):
        analysis_results = run_analysis()

    # Phase 4: 시각화
    if args.phase in ("visualize", "all"):
        run_visualization(analysis_results)

    # Phase 5: URL 정리
    if args.phase in ("all",):
        organize_url_list()

    # 완료 메시지
    print("\n" + "=" * 60)
    print("✅ 전체 분석 완료!")
    print(f"📁 결과 저장 위치: {os.path.abspath(os.path.join(PROJECT_ROOT, 'outputs'))}")
    print(f"📊 차트 저장 위치: {os.path.abspath(OUTPUTS_CHARTS_DIR)}")
    print(f"🔗 URL 목록: {os.path.abspath(os.path.join(URL_LIST_DIR, 'crawling_urls.csv'))}")
    print("=" * 60)


if __name__ == "__main__":
    main()
