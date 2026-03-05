"""
자율주행 AI 분야 취업 동향 분석 - 메인 파이프라인

실행 방법:
    python main.py --phase all
    python main.py --phase crawl --source naver
    python main.py --phase visualize --skip-crawl
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import (
    DATA_RAW_DIR, DATA_PROCESSED_DIR, OUTPUT_CHARTS_DIR,
    OUTPUT_REPORTS_DIR, URL_LIST_DIR, NAVER_KEYWORDS, SARAMIN_KEYWORDS
)

logger = logging.getLogger(__name__)


def parse_args():
    """CLI 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="자율주행 AI 분야 취업 동향 분석 파이프라인"
    )
    parser.add_argument(
        "--phase", type=str, default="all",
        choices=["crawl", "process", "analyze", "visualize", "all"],
        help="실행할 단계 (기본: all)"
    )
    parser.add_argument(
        "--source", type=str, default="all",
        choices=["naver", "saramin", "wanted", "jobplanet", "all"],
        help="크롤링 소스 선택 (기본: all)"
    )
    parser.add_argument(
        "--skip-crawl", action="store_true",
        help="크롤링을 건너뛰고 기존 데이터로 분석"
    )
    return parser.parse_args()


def setup_logging():
    """로깅 설정 (파일 + 콘솔)"""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger.info(f"로그 파일: {log_file}")


# ============================================================
# Phase 1: 크롤링
# ============================================================
def run_crawling(source: str = "all"):
    """Phase 1: 데이터 크롤링"""
    print("\n" + "=" * 60)
    print("📥 Phase 1: 데이터 크롤링")
    print("=" * 60)

    # 1-1. Naver OpenAPI 크롤링
    if source in ["naver", "all"]:
        print("\n▶ Naver OpenAPI 크롤링 (블로그 + 뉴스)")
        try:
            from crawlers.naver_api_crawler import NaverAPICrawler
            crawler = NaverAPICrawler()
            blog_df, news_df = crawler.run_all()
            print(f"  ✅ 블로그: {len(blog_df)}건, 뉴스: {len(news_df)}건")
        except Exception as e:
            logger.error(f"Naver 크롤링 실패: {e}")
            print(f"  ❌ 실패: {e}")

    # 1-2. 사람인 채용공고 크롤링
    if source in ["saramin", "all"]:
        print("\n▶ 사람인 채용공고 크롤링")
        try:
            from crawlers.saramin_crawler import SaraminCrawler
            crawler = SaraminCrawler()
            df = crawler.run_all()
            print(f"  ✅ 채용공고: {len(df)}건")
        except Exception as e:
            logger.error(f"사람인 크롤링 실패: {e}")
            print(f"  ❌ 실패: {e}")

    # 1-3. 원티드 포지션 크롤링
    if source in ["wanted", "all"]:
        print("\n▶ 원티드 포지션 크롤링")
        try:
            from crawlers.wanted_crawler import WantedCrawler
            crawler = WantedCrawler()
            df = crawler.run_all()
            print(f"  ✅ 포지션: {len(df)}건")
        except Exception as e:
            logger.error(f"원티드 크롤링 실패: {e}")
            print(f"  ❌ 실패: {e}")

    # 1-4. 잡플래닛 크롤링
    if source in ["jobplanet", "all"]:
        print("\n▶ 잡플래닛 기업 리뷰/연봉/면접후기 크롤링")
        try:
            from crawlers.jobplanet_crawler import JobPlanetCrawler
            crawler = JobPlanetCrawler()
            try:
                crawler.run_all()
                print("  ✅ 잡플래닛 크롤링 완료")
            finally:
                crawler.close()
        except Exception as e:
            logger.error(f"잡플래닛 크롤링 실패: {e}")
            print(f"  ❌ 실패: {e}")


# ============================================================
# Phase 2: 데이터 전처리
# ============================================================
def run_processing():
    """Phase 2: 데이터 전처리"""
    print("\n" + "=" * 60)
    print("🔧 Phase 2: 데이터 전처리")
    print("=" * 60)

    try:
        from processors.data_cleaner import DataCleaner
        cleaner = DataCleaner()
        cleaner.process_all_raw_data()
        print("  ✅ 전처리 완료")
    except Exception as e:
        logger.error(f"데이터 전처리 실패: {e}")
        print(f"  ❌ 실패: {e}")


# ============================================================
# Phase 3: 데이터 분석
# ============================================================
def run_analysis():
    """Phase 3: 데이터 분석"""
    print("\n" + "=" * 60)
    print("📊 Phase 3: 데이터 분석")
    print("=" * 60)

    import pandas as pd

    # 3-1. 텍스트 분석
    print("\n▶ 텍스트 분석")
    try:
        from processors.text_analyzer import TextAnalyzer
        analyzer = TextAnalyzer()

        # 채용공고 기술스택 빈도
        for filename in ["processed_saramin_jobs.csv", "processed_wanted_positions.csv"]:
            filepath = DATA_PROCESSED_DIR / filename
            if filepath.exists():
                df = pd.read_csv(filepath, encoding="utf-8-sig")
                tech_freq = analyzer.get_tech_stack_frequency(df)
                if not tech_freq.empty:
                    tech_freq.to_csv(DATA_PROCESSED_DIR / "tech_stack_freq.csv",
                                     index=False, encoding="utf-8-sig")
                    print(f"  ✅ 기술스택 빈도 분석 완료: {len(tech_freq)}개 기술")

                cert_freq = analyzer.get_certificate_frequency(df)
                if not cert_freq.empty:
                    cert_freq.to_csv(DATA_PROCESSED_DIR / "certificate_freq.csv",
                                     index=False, encoding="utf-8-sig")
                    print(f"  ✅ 자격증 빈도 분석 완료: {len(cert_freq)}개")
                break

        # 블로그 키워드 빈도
        blog_path = DATA_PROCESSED_DIR / "processed_naver_blog_results.csv"
        if blog_path.exists():
            blog_df = pd.read_csv(blog_path, encoding="utf-8-sig")
            texts = blog_df["제목"].dropna().tolist() + blog_df["본문요약"].dropna().tolist()
            word_freq = analyzer.get_word_frequency(texts, top_n=50)
            if not word_freq.empty:
                word_freq.to_csv(DATA_PROCESSED_DIR / "blog_word_freq.csv",
                                 index=False, encoding="utf-8-sig")
                print(f"  ✅ 블로그 키워드 빈도 분석 완료")

            # 키워드 트렌드
            trend = analyzer.get_keyword_trend(blog_df)
            if not trend.empty:
                trend.to_csv(DATA_PROCESSED_DIR / "keyword_trend.csv", encoding="utf-8-sig")
                print(f"  ✅ 키워드 트렌드 분석 완료")

    except Exception as e:
        logger.error(f"텍스트 분석 실패: {e}")
        print(f"  ❌ 텍스트 분석 실패: {e}")

    # 3-2. 연봉 분석
    print("\n▶ 연봉 분석")
    try:
        from processors.salary_analyzer import SalaryAnalyzer

        salary_files = list(DATA_PROCESSED_DIR.glob("*salary*")) + list(DATA_PROCESSED_DIR.glob("*saramin*"))
        for sf in salary_files:
            df = pd.read_csv(sf, encoding="utf-8-sig")
            if "연봉_만원" in df.columns:
                sa = SalaryAnalyzer(df)
                stats = sa.get_salary_stats()
                if stats:
                    print(f"  ✅ 연봉 통계: 평균 {stats.get('평균', 'N/A')}만원")

                by_company = sa.get_salary_by_company()
                if not by_company.empty:
                    by_company.to_csv(DATA_PROCESSED_DIR / "salary_by_company.csv",
                                      index=False, encoding="utf-8-sig")

                by_career = sa.get_salary_by_career()
                if not by_career.empty:
                    by_career.to_csv(DATA_PROCESSED_DIR / "salary_by_career.csv",
                                     index=False, encoding="utf-8-sig")

                by_tech = sa.get_salary_by_tech_stack()
                if not by_tech.empty:
                    by_tech.to_csv(DATA_PROCESSED_DIR / "salary_by_tech.csv",
                                    index=False, encoding="utf-8-sig")
                break

    except Exception as e:
        logger.error(f"연봉 분석 실패: {e}")
        print(f"  ❌ 연봉 분석 실패: {e}")


# ============================================================
# Phase 4: 시각화
# ============================================================
def run_visualization():
    """Phase 4: 시각화 생성 (총 29개)"""
    print("\n" + "=" * 60)
    print("🎨 Phase 4: 시각화 생성")
    print("=" * 60)

    import pandas as pd
    from collections import Counter

    # 데이터 로드 헬퍼
    def load_csv(name):
        path = DATA_PROCESSED_DIR / name
        if path.exists():
            return pd.read_csv(path, encoding="utf-8-sig")
        return None

    # ── 4-1. 워드클라우드 (5개) ──
    print("\n▶ 워드클라우드 생성 (5개)")
    try:
        from visualizations.wordcloud_viz import WordCloudVisualizer
        wc_viz = WordCloudVisualizer()

        wc_data = {}

        # 기술스택 빈도 → dict
        tech_df = load_csv("tech_stack_freq.csv")
        if tech_df is not None:
            wc_data["tech_freq"] = dict(zip(tech_df["기술스택"], tech_df["빈도"]))

        # 블로그 키워드 빈도
        blog_freq_df = load_csv("blog_word_freq.csv")
        if blog_freq_df is not None:
            wc_data["blog_freq"] = dict(zip(blog_freq_df["단어"], blog_freq_df["빈도"]))

        # 면접후기 키워드 (있으면)
        interview_df = load_csv("processed_jobplanet_interviews.csv")
        if interview_df is not None:
            from processors.text_analyzer import TextAnalyzer
            ta = TextAnalyzer()
            texts = interview_df["면접질문"].dropna().tolist() + interview_df["면접내용"].dropna().tolist()
            freq_df = ta.get_word_frequency(texts, top_n=50)
            if not freq_df.empty:
                wc_data["interview_freq"] = dict(zip(freq_df["단어"], freq_df["빈도"]))

        # 리뷰 장점/단점
        review_df = load_csv("processed_jobplanet_reviews.csv")
        if review_df is not None:
            from processors.text_analyzer import TextAnalyzer
            ta = TextAnalyzer()
            if "장점" in review_df.columns:
                pros_freq = ta.get_word_frequency(review_df["장점"].dropna().tolist(), top_n=50)
                if not pros_freq.empty:
                    wc_data["pros_freq"] = dict(zip(pros_freq["단어"], pros_freq["빈도"]))
            if "단점" in review_df.columns:
                cons_freq = ta.get_word_frequency(review_df["단점"].dropna().tolist(), top_n=50)
                if not cons_freq.empty:
                    wc_data["cons_freq"] = dict(zip(cons_freq["단어"], cons_freq["빈도"]))

        wc_viz.create_all(wc_data)
        print(f"  ✅ 워드클라우드 생성 완료 ({len(wc_data)}개)")

    except Exception as e:
        logger.error(f"워드클라우드 생성 실패: {e}")
        print(f"  ❌ 실패: {e}")

    # ── 4-2. 기본 차트 (8개) ──
    print("\n▶ 기본 차트 생성 (8개)")
    try:
        from visualizations.chart_viz import ChartVisualizer
        chart_viz = ChartVisualizer()
        chart_data = {}

        tech_df = load_csv("tech_stack_freq.csv")
        if tech_df is not None:
            chart_data["tech_freq_df"] = tech_df

        cert_df = load_csv("certificate_freq.csv")
        if cert_df is not None:
            chart_data["cert_data"] = cert_df

        # 경력 분포
        for name in ["processed_saramin_jobs.csv", "processed_wanted_positions.csv"]:
            df = load_csv(name)
            if df is not None and "경력구분" in df.columns:
                counts = df["경력구분"].value_counts().reset_index()
                counts.columns = ["경력구분", "건수"]
                chart_data["career_data"] = counts
                break

        # 연봉 데이터
        for name in ["processed_jobplanet_salaries.csv", "processed_saramin_jobs.csv"]:
            df = load_csv(name)
            if df is not None and "연봉_만원" in df.columns:
                company_col = "기업명" if "기업명" in df.columns else "회사명"
                if company_col in df.columns:
                    chart_data["salary_data"] = df
                    break

        # 기업 평점
        ratings_df = load_csv("processed_jobplanet_reviews.csv")
        if ratings_df is not None:
            chart_data["ratings_data"] = ratings_df

        # 지역 분포
        for name in ["processed_saramin_jobs.csv"]:
            df = load_csv(name)
            if df is not None and "근무지역" in df.columns:
                loc_counts = df["근무지역"].value_counts().head(10).reset_index()
                loc_counts.columns = ["지역", "건수"]
                chart_data["location_data"] = loc_counts
                break

        # 기업 규모 분포
        for name in ["processed_saramin_jobs.csv"]:
            df = load_csv(name)
            if df is not None and "기업규모" in df.columns:
                size_counts = df["기업규모"].value_counts().reset_index()
                size_counts.columns = ["기업규모", "건수"]
                chart_data["size_data"] = size_counts
                break

        # 블로그/뉴스 데이터 기반 월별 트렌드 (Naver 데이터 활용)
        blog_df_viz = load_csv("processed_naver_blog_results.csv")
        news_df_viz = load_csv("processed_naver_news_results.csv")
        trend_frames = []
        for df_viz in [blog_df_viz, news_df_viz]:
            if df_viz is not None:
                trend_frames.append(df_viz)
        if trend_frames:
            combined_trend = pd.concat(trend_frames, ignore_index=True)
            date_col = None
            for c in ["작성일", "발행일"]:
                if c in combined_trend.columns:
                    date_col = c
                    break
            if date_col:
                combined_trend[date_col] = pd.to_datetime(combined_trend[date_col], errors="coerce")
                combined_trend = combined_trend.dropna(subset=[date_col])
                monthly = combined_trend.set_index(date_col).resample("ME").size()
                if len(monthly) > 1:
                    trend_df = monthly.reset_index()
                    trend_df.columns = ["월", "건수"]
                    trend_df["월"] = trend_df["월"].dt.strftime("%Y-%m")
                    chart_data["trend_data"] = trend_df

        # 검색키워드별 분포 (소스 분포로 활용)
        if blog_df_viz is not None and "검색키워드" in blog_df_viz.columns:
            kw_counts = blog_df_viz["검색키워드"].value_counts().head(10).reset_index()
            kw_counts.columns = ["지역", "건수"]  # 지역 차트 재활용
            if "location_data" not in chart_data:
                chart_data["location_data"] = kw_counts

        chart_viz.create_all(chart_data)
        print(f"  ✅ 기본 차트 생성 완료 ({len(chart_data)}개)")

    except Exception as e:
        logger.error(f"기본 차트 생성 실패: {e}")
        print(f"  ❌ 실패: {e}")

    # ── 4-3. 고급 차트 (8개) ──
    print("\n▶ 고급 차트 생성 (8개)")
    try:
        from visualizations.advanced_viz import AdvancedVisualizer
        adv_viz = AdvancedVisualizer()
        adv_data = {}

        # 사용 가능한 데이터 전달
        if "salary_data" in chart_data:
            adv_data["scatter_data"] = chart_data["salary_data"]
        if ratings_df is not None:
            adv_data["violin_data"] = ratings_df

        # 키워드 트렌드 버블차트 (Naver 블로그 데이터 활용)
        keyword_trend_df = load_csv("keyword_trend.csv")
        if keyword_trend_df is not None:
            keyword_trend_df = keyword_trend_df.set_index(keyword_trend_df.columns[0])
            # 상위 10개 키워드만
            if len(keyword_trend_df.columns) > 10:
                top_kw = keyword_trend_df.sum().nlargest(10).index
                keyword_trend_df = keyword_trend_df[top_kw]
            adv_data["bubble_data"] = keyword_trend_df

        adv_viz.create_all(adv_data)
        print("  ✅ 고급 차트 생성 완료")

    except Exception as e:
        logger.error(f"고급 차트 생성 실패: {e}")
        print(f"  ❌ 실패: {e}")

    # ── 4-4. 인터랙티브 차트 (6개) ──
    print("\n▶ 인터랙티브 차트 생성 (6개)")
    try:
        from visualizations.interactive_viz import InteractiveVisualizer
        int_viz = InteractiveVisualizer()
        int_data = {}

        if tech_df is not None:
            int_data["tech_freq_df"] = tech_df

        # 키워드 트렌드 인터랙티브 라인차트
        if keyword_trend_df is not None:
            int_data["trend_data"] = keyword_trend_df

        int_viz.create_all(int_data)
        print("  ✅ 인터랙티브 차트 생성 완료")

    except Exception as e:
        logger.error(f"인터랙티브 차트 생성 실패: {e}")
        print(f"  ❌ 실패: {e}")

    # ── 4-5. 종합 대시보드 (2개) ──
    print("\n▶ 종합 대시보드 생성 (2개)")
    try:
        from visualizations.dashboard import AnalysisDashboard
        dashboard = AnalysisDashboard()
        dashboard.create_summary_dashboard()
        dashboard.create_plotly_dashboard()
        dashboard.generate_summary_stats()
        print("  ✅ 대시보드 생성 완료")

    except Exception as e:
        logger.error(f"대시보드 생성 실패: {e}")
        print(f"  ❌ 실패: {e}")


# ============================================================
# Phase 5: URL 목록 정리
# ============================================================
def organize_url_list():
    """Phase 5: 크롤링 URL 목록 정리 및 검증"""
    print("\n" + "=" * 60)
    print("📋 Phase 5: 크롤링 URL 목록 정리")
    print("=" * 60)

    import pandas as pd

    url_file = URL_LIST_DIR / "crawling_urls.csv"
    if not url_file.exists():
        print("  ⚠️ URL 목록 파일이 없습니다.")
        return

    try:
        df = pd.read_csv(url_file, encoding="utf-8-sig")

        # 중복 제거
        before = len(df)
        df = df.drop_duplicates(subset=["URL"]).reset_index(drop=True)
        df["번호"] = range(1, len(df) + 1)

        # 저장
        df.to_csv(url_file, index=False, encoding="utf-8-sig")

        total = len(df)
        print(f"\n  📊 URL 목록 통계:")
        print(f"     총 URL 수: {total}개")

        if "소스" in df.columns:
            print(f"     소스별 분포:")
            for source, count in df["소스"].value_counts().items():
                print(f"       - {source}: {count}개")

        if total >= 100:
            print(f"\n  ✅ URL 100개 이상 확보 완료! ({total}개)")
        else:
            print(f"\n  ⚠️ URL {total}개 / 목표 100개 (부족: {100 - total}개)")

    except Exception as e:
        logger.error(f"URL 목록 정리 실패: {e}")
        print(f"  ❌ 실패: {e}")


# ============================================================
# 메인 실행
# ============================================================
def main():
    args = parse_args()
    setup_logging()

    start_time = datetime.now()

    print("=" * 60)
    print("🚗 자율주행 AI 분야 취업 동향 분석 시작")
    print(f"⏰ 시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📌 실행 단계: {args.phase}")
    if args.phase == "crawl":
        print(f"📌 크롤링 소스: {args.source}")
    if args.skip_crawl:
        print("📌 크롤링 건너뛰기 모드")
    print("=" * 60)

    # Phase 1: 크롤링
    if args.phase in ["crawl", "all"] and not args.skip_crawl:
        run_crawling(args.source)

    # Phase 2: 전처리
    if args.phase in ["process", "all"]:
        run_processing()

    # Phase 3: 분석
    if args.phase in ["analyze", "all"]:
        run_analysis()

    # Phase 4: 시각화
    if args.phase in ["visualize", "all"]:
        run_visualization()

    # Phase 5: URL 정리
    if args.phase == "all":
        organize_url_list()

    end_time = datetime.now()
    elapsed = end_time - start_time

    print("\n" + "=" * 60)
    print("✅ 전체 분석 완료!")
    print(f"⏰ 종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ 소요 시간: {elapsed}")
    print(f"📁 결과 저장 위치: {OUTPUT_CHARTS_DIR.parent}")
    print(f"📊 차트 저장 위치: {OUTPUT_CHARTS_DIR}")
    print(f"🔗 URL 목록: {URL_LIST_DIR / 'crawling_urls.csv'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
