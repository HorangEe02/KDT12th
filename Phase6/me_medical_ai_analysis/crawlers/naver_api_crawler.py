"""
=============================================================
Naver OpenAPI 크롤러 - 의료 AI 취업 동향 블로그/뉴스 수집
=============================================================
- 블로그, 뉴스 검색 API를 활용하여 의료 AI 취준 동향 데이터 수집
- 키워드별 최소 100개 이상 결과 확보 시도
- HTML 태그 제거, 날짜 형식 통일 처리
=============================================================
"""

import urllib.request
import urllib.parse
import json
import re
import os
import time
from datetime import datetime

import pandas as pd
from tqdm import tqdm

from config.settings import (
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
    NAVER_BLOG_KEYWORDS,
    NAVER_NEWS_KEYWORDS,
    DATA_RAW_DIR,
    URL_LIST_DIR,
    API_CALL_DELAY,
)


class NaverAPICrawler:
    """Naver OpenAPI를 활용한 블로그/뉴스 데이터 수집"""

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or NAVER_CLIENT_ID
        self.client_secret = client_secret or NAVER_CLIENT_SECRET
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        self.collected_urls = []

    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """HTML 태그 및 특수문자 제거"""
        if not isinstance(text, str):
            return ""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"&[a-zA-Z]+;", " ", clean)
        clean = re.sub(r"&#\d+;", " ", clean)
        return clean.strip()

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """날짜 형식을 YYYY-MM-DD로 통일"""
        if not isinstance(date_str, str):
            return ""
        # YYYYMMDD 형식
        if re.match(r"^\d{8}$", date_str):
            try:
                return datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
            except ValueError:
                return date_str
        # RFC 2822 (뉴스 pubDate)
        try:
            dt = datetime.strptime(date_str[:25].strip().rstrip(","), "%a, %d %b %Y %H:%M:%S")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, IndexError):
            pass
        return date_str

    def _call_api(self, search_type: str, params: dict) -> dict:
        """Naver 검색 API 호출"""
        base_url = f"https://openapi.naver.com/v1/search/{search_type}.json"
        url = base_url + "?" + urllib.parse.urlencode(params)

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", self.client_id)
        request.add_header("X-Naver-Client-Secret", self.client_secret)

        try:
            response = urllib.request.urlopen(request)
            if response.getcode() == 200:
                return json.loads(response.read().decode("utf-8"))
            else:
                print(f"    ⚠️ HTTP Error: {response.getcode()}")
                return None
        except urllib.error.URLError as e:
            print(f"    ❌ URL Error: {e}")
            return None
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return None

    def search_blog(self, query: str, display: int = 100, start: int = 1,
                    sort: str = "sim") -> pd.DataFrame:
        """
        Naver 블로그 검색 API 호출

        Parameters:
            query: 검색어
            display: 한 번에 가져올 결과 수 (최대 100)
            start: 시작 위치 (1~1000)
            sort: "sim"(정확도순) 또는 "date"(최신순)

        Returns:
            DataFrame: 블로그 검색 결과
        """
        params = {"query": query, "display": display, "start": start, "sort": sort}
        result = self._call_api("blog", params)

        if result is None or "items" not in result:
            return pd.DataFrame()

        rows = []
        for item in result["items"]:
            link = item.get("link", "")
            rows.append({
                "검색키워드": query,
                "제목": self._remove_html_tags(item.get("title", "")),
                "내용요약": self._remove_html_tags(item.get("description", "")),
                "블로거명": item.get("bloggername", ""),
                "블로그링크": item.get("bloggerlink", ""),
                "게시글링크": link,
                "게시일자": self._normalize_date(item.get("postdate", "")),
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "출처": "Naver Blog",
            })
            self.collected_urls.append({
                "번호": len(self.collected_urls) + 1,
                "URL": link,
                "소스": "Naver블로그",
                "검색키워드": query,
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "데이터유형": "블로그",
                "비고": "",
            })

        return pd.DataFrame(rows)

    def search_news(self, query: str, display: int = 100, start: int = 1,
                    sort: str = "date") -> pd.DataFrame:
        """
        Naver 뉴스 검색 API 호출

        Returns:
            DataFrame: 뉴스 검색 결과
        """
        params = {"query": query, "display": display, "start": start, "sort": sort}
        result = self._call_api("news", params)

        if result is None or "items" not in result:
            return pd.DataFrame()

        rows = []
        for item in result["items"]:
            link = item.get("originallink", "") or item.get("link", "")
            rows.append({
                "검색키워드": query,
                "제목": self._remove_html_tags(item.get("title", "")),
                "내용요약": self._remove_html_tags(item.get("description", "")),
                "원본링크": link,
                "네이버링크": item.get("link", ""),
                "게시일자": self._normalize_date(item.get("pubDate", "")),
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "출처": "Naver News",
            })
            self.collected_urls.append({
                "번호": len(self.collected_urls) + 1,
                "URL": link,
                "소스": "Naver뉴스",
                "검색키워드": query,
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "데이터유형": "뉴스",
                "비고": "",
            })

        return pd.DataFrame(rows)

    def search_all_keywords(self, keywords: list, search_type: str = "blog",
                            max_per_keyword: int = 30) -> pd.DataFrame:
        """
        키워드 리스트 전체를 순회하며 검색

        Parameters:
            keywords: 검색 키워드 리스트
            search_type: "blog" 또는 "news"
            max_per_keyword: 키워드당 최대 수집 건수 (기본: 30)

        Returns:
            DataFrame: 전체 결과 (중복 URL 제거)
        """
        all_dfs = []
        seen_links = set()

        search_func = self.search_blog if search_type == "blog" else self.search_news
        link_col = "게시글링크" if search_type == "blog" else "원본링크"

        for keyword in tqdm(keywords, desc=f"[{search_type}] 키워드 검색"):
            collected = 0
            start = 1

            while collected < max_per_keyword and start <= 1000:
                display = min(100, max_per_keyword - collected)
                df = search_func(keyword, display=display, start=start)

                if df.empty:
                    break

                # 중복 제거
                new_rows = []
                for _, row in df.iterrows():
                    link = row.get(link_col, "")
                    if link not in seen_links:
                        seen_links.add(link)
                        new_rows.append(row)
                        collected += 1

                if new_rows:
                    all_dfs.append(pd.DataFrame(new_rows))

                start += display
                time.sleep(API_CALL_DELAY)

        if not all_dfs:
            return pd.DataFrame()

        result = pd.concat(all_dfs, ignore_index=True)
        result["검색키워드"] = result["검색키워드"].astype(str)
        return result

    def save_data(self, df: pd.DataFrame, filename: str):
        """data/raw/ 폴더에 CSV/JSON 저장"""
        if df is None or df.empty:
            print("  ⚠️ 저장할 데이터가 없습니다.")
            return

        # CSV 저장
        csv_path = os.path.join(DATA_RAW_DIR, f"{filename}.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"  💾 CSV 저장: {csv_path} ({len(df)}건)")

        # JSON 저장
        json_path = os.path.join(DATA_RAW_DIR, f"{filename}.json")
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
        print(f"  💾 JSON 저장: {json_path}")

    def _save_url_list(self):
        """크롤링 URL 목록을 url_list/crawling_urls.csv에 추가"""
        if not self.collected_urls:
            return

        url_path = os.path.join(URL_LIST_DIR, "crawling_urls.csv")
        df_new = pd.DataFrame(self.collected_urls)

        if os.path.exists(url_path):
            df_existing = pd.read_csv(url_path, encoding="utf-8-sig")
            df_new["번호"] = range(len(df_existing) + 1, len(df_existing) + len(df_new) + 1)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new

        df_combined.to_csv(url_path, index=False, encoding="utf-8-sig")
        print(f"  📋 URL 목록 저장: {url_path} (총 {len(df_combined)}개)")

    def _run_crawl(self, blog_keywords, news_keywords, file_suffix="의료AI"):
        """블로그/뉴스 크롤링 내부 공통 로직

        Args:
            blog_keywords: 블로그 검색 키워드 리스트
            news_keywords: 뉴스 검색 키워드 리스트
            file_suffix: 저장 파일명 접미사

        Returns:
            tuple: (df_blog, df_news)
        """
        print("=" * 60)
        print("📌 Naver OpenAPI 크롤링 시작")
        print(f"📅 수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📋 블로그 키워드: {len(blog_keywords)}개")
        print(f"📋 뉴스 키워드:   {len(news_keywords)}개")
        print("=" * 60)

        # 블로그 크롤링
        print("\n📝 블로그 크롤링")
        df_blog = self.search_all_keywords(blog_keywords, "blog", max_per_keyword=30)
        self.save_data(df_blog, f"naver_blog_{file_suffix}")

        # 뉴스 크롤링
        print("\n📰 뉴스 크롤링")
        df_news = self.search_all_keywords(news_keywords, "news", max_per_keyword=30)
        self.save_data(df_news, f"naver_news_{file_suffix}")

        # URL 목록 저장
        self._save_url_list()

        # 결과 요약
        blog_count = len(df_blog) if not df_blog.empty else 0
        news_count = len(df_news) if not df_news.empty else 0
        print(f"\n✅ Naver 크롤링 완료!")
        print(f"  블로그: {blog_count}건")
        print(f"  뉴스:   {news_count}건")
        print(f"  총 URL: {len(self.collected_urls)}개")

        return df_blog, df_news

    def run_all(self, extra_blog_keywords=None, extra_news_keywords=None):
        """기본 키워드 + 추가 키워드로 크롤링 실행

        Args:
            extra_blog_keywords: 추가 블로그 키워드 리스트 (선택)
            extra_news_keywords: 추가 뉴스 키워드 리스트 (선택)

        사용 예시:
            # 기본 키워드만
            crawler.run_all()

            # 기본 + 추가 키워드
            crawler.run_all(
                extra_blog_keywords=["삼성서울병원 AI 취업", "서울아산병원 채용"],
                extra_news_keywords=["삼성서울병원 AI", "서울아산병원 인공지능"],
            )
        """
        blog_kw = list(NAVER_BLOG_KEYWORDS)
        news_kw = list(NAVER_NEWS_KEYWORDS)

        if extra_blog_keywords:
            blog_kw.extend(extra_blog_keywords)
            print(f"📌 추가 블로그 키워드 {len(extra_blog_keywords)}개 포함")
        if extra_news_keywords:
            news_kw.extend(extra_news_keywords)
            print(f"📌 추가 뉴스 키워드 {len(extra_news_keywords)}개 포함")

        return self._run_crawl(blog_kw, news_kw, file_suffix="의료AI")

    def run_custom(self, blog_keywords=None, news_keywords=None, file_suffix="의료AI_추가"):
        """지정한 키워드만으로 크롤링 (기본 키워드 제외)

        Args:
            blog_keywords: 블로그 검색 키워드 리스트
            news_keywords: 뉴스 검색 키워드 리스트
            file_suffix: 저장 파일명 접미사

        사용 예시:
            crawler.run_custom(
                blog_keywords=["삼성서울병원 AI 취업", "세브란스 의료AI"],
                news_keywords=["삼성서울병원 AI 채용", "세브란스 인공지능"],
                file_suffix="의료AI_대형병원",
            )
        """
        blog_kw = blog_keywords or []
        news_kw = news_keywords or []

        if not blog_kw and not news_kw:
            print("⚠️ 크롤링할 키워드가 없습니다.")
            return pd.DataFrame(), pd.DataFrame()

        return self._run_crawl(blog_kw, news_kw, file_suffix=file_suffix)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="네이버 OpenAPI 의료 AI 블로그/뉴스 크롤러")
    parser.add_argument(
        "--mode", choices=["all", "custom"], default="all",
        help="실행 모드: all(기본+추가), custom(추가만)",
    )
    parser.add_argument(
        "--extra-blog", nargs="+",
        help="추가 블로그 키워드 (예: --extra-blog '삼성서울병원 AI 취업' '아산병원 채용')",
    )
    parser.add_argument(
        "--extra-news", nargs="+",
        help="추가 뉴스 키워드 (예: --extra-news '삼성서울병원 AI' '아산병원 인공지능')",
    )
    parser.add_argument(
        "--suffix", type=str, default="의료AI_추가",
        help="저장 파일명 접미사 (--mode custom 시 사용)",
    )

    args = parser.parse_args()
    crawler = NaverAPICrawler()

    if args.mode == "all":
        crawler.run_all(
            extra_blog_keywords=args.extra_blog,
            extra_news_keywords=args.extra_news,
        )
    elif args.mode == "custom":
        if not args.extra_blog and not args.extra_news:
            print("⚠️ --extra-blog 또는 --extra-news 옵션으로 키워드를 지정해주세요.")
        else:
            crawler.run_custom(
                blog_keywords=args.extra_blog,
                news_keywords=args.extra_news,
                file_suffix=args.suffix,
            )
