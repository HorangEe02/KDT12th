"""
Naver OpenAPI 크롤러
블로그 및 뉴스 검색 API를 활용하여 자율주행 관련 데이터 수집
"""

import re
import time
import logging
import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import (
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NAVER_KEYWORDS,
    DATA_RAW_DIR, URL_LIST_DIR, API_CALL_DELAY, MAX_RETRIES
)

logger = logging.getLogger(__name__)


class NaverAPICrawler:
    """Naver OpenAPI를 활용한 블로그/뉴스 데이터 수집 크롤러"""

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or NAVER_CLIENT_ID
        self.client_secret = client_secret or NAVER_CLIENT_SECRET
        self.headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        self.collected_urls = []

        if not self.client_id or not self.client_secret:
            logger.warning("Naver API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")

    @staticmethod
    def _clean_html(text: str) -> str:
        """HTML 태그 및 특수문자 제거"""
        if not text or not isinstance(text, str):
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&quot;", '"').replace("&apos;", "'")
        return text.strip()

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """날짜 형식을 YYYY-MM-DD로 통일"""
        if not date_str:
            return ""
        # yyyymmdd 형식 (블로그)
        if re.match(r"^\d{8}$", date_str):
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        # RFC 2822 형식 (뉴스: "Mon, 15 Jan 2024 00:00:00 +0900")
        try:
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass
        return date_str

    def search_blog(self, query: str, display: int = 100, start: int = 1, sort: str = "sim") -> pd.DataFrame:
        """Naver 블로그 검색 API 호출"""
        url = "https://openapi.naver.com/v1/search/blog.json"
        params = {"query": query, "display": display, "start": start, "sort": sort}
        results = []

        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("items", []):
                    results.append({
                        "제목": self._clean_html(item.get("title", "")),
                        "블로거명": item.get("bloggername", ""),
                        "블로그링크": item.get("bloggerlink", ""),
                        "링크": item.get("link", ""),
                        "본문요약": self._clean_html(item.get("description", "")),
                        "작성일": self._normalize_date(item.get("postdate", "")),
                        "검색키워드": query,
                        "소스": "Naver블로그",
                    })
                    self.collected_urls.append(item.get("link", ""))

                logger.info(f"블로그 검색 완료: '{query}' → {len(data.get('items', []))}건")
                break

            except requests.exceptions.RequestException as e:
                logger.warning(f"블로그 검색 실패 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(1)

        return pd.DataFrame(results)

    def search_news(self, query: str, display: int = 100, start: int = 1, sort: str = "date") -> pd.DataFrame:
        """Naver 뉴스 검색 API 호출"""
        url = "https://openapi.naver.com/v1/search/news.json"
        params = {"query": query, "display": display, "start": start, "sort": sort}
        results = []

        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("items", []):
                    results.append({
                        "제목": self._clean_html(item.get("title", "")),
                        "원문링크": item.get("originallink", ""),
                        "링크": item.get("link", ""),
                        "본문요약": self._clean_html(item.get("description", "")),
                        "발행일": self._normalize_date(item.get("pubDate", "")),
                        "검색키워드": query,
                        "소스": "Naver뉴스",
                    })
                    self.collected_urls.append(item.get("link", ""))

                logger.info(f"뉴스 검색 완료: '{query}' → {len(data.get('items', []))}건")
                break

            except requests.exceptions.RequestException as e:
                logger.warning(f"뉴스 검색 실패 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(1)

        return pd.DataFrame(results)

    def search_all_keywords(self, keywords: list, search_type: str = "blog") -> pd.DataFrame:
        """키워드 리스트 전체를 순회하며 검색"""
        all_results = []
        search_func = self.search_blog if search_type == "blog" else self.search_news

        for keyword in tqdm(keywords, desc=f"Naver {search_type} 검색"):
            # 각 키워드당 최소 100개 확보 시도 (start=1, 101)
            for start in [1, 101]:
                df = search_func(keyword, display=100, start=start)
                if not df.empty:
                    all_results.append(df)
                time.sleep(API_CALL_DELAY)

        if not all_results:
            return pd.DataFrame()

        combined = pd.concat(all_results, ignore_index=True)
        # 중복 URL 제거
        link_col = "링크" if "링크" in combined.columns else combined.columns[0]
        before = len(combined)
        combined = combined.drop_duplicates(subset=[link_col])
        logger.info(f"중복 제거: {before} → {len(combined)}건")

        return combined

    def save_data(self, df: pd.DataFrame, filename: str):
        """데이터 저장 및 URL 목록 기록"""
        if df.empty:
            logger.warning(f"저장할 데이터가 없습니다: {filename}")
            return

        # CSV 저장
        filepath = DATA_RAW_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"데이터 저장 완료: {filepath} ({len(df)}건)")

        # URL 목록 추가
        url_file = URL_LIST_DIR / "crawling_urls.csv"
        existing = pd.read_csv(url_file) if url_file.stat().st_size > 50 else pd.DataFrame()
        start_num = len(existing) + 1 if not existing.empty else 1

        url_records = []
        for i, url in enumerate(self.collected_urls):
            url_records.append({
                "번호": start_num + i,
                "URL": url,
                "소스": "Naver블로그" if "blog" in filename else "Naver뉴스",
                "검색키워드": "",
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "데이터유형": "블로그" if "blog" in filename else "뉴스",
                "비고": "",
            })

        if url_records:
            url_df = pd.DataFrame(url_records)
            url_df.to_csv(url_file, mode="a", header=False, index=False, encoding="utf-8-sig")
            logger.info(f"URL 목록 추가: {len(url_records)}건")

        self.collected_urls = []

    def run_all(self):
        """전체 키워드에 대해 블로그 + 뉴스 검색 실행"""
        logger.info("=" * 50)
        logger.info("Naver OpenAPI 크롤링 시작")
        logger.info("=" * 50)

        # 블로그 검색
        logger.info("▶ 블로그 검색 시작")
        blog_df = self.search_all_keywords(NAVER_KEYWORDS, search_type="blog")
        self.save_data(blog_df, "naver_blog_results.csv")

        # 뉴스 검색
        logger.info("▶ 뉴스 검색 시작")
        news_df = self.search_all_keywords(NAVER_KEYWORDS, search_type="news")
        self.save_data(news_df, "naver_news_results.csv")

        logger.info(f"Naver 크롤링 완료 - 블로그: {len(blog_df)}건, 뉴스: {len(news_df)}건")
        return blog_df, news_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    crawler = NaverAPICrawler()
    crawler.run_all()
