"""
=============================================================
사람인 크롤러 - 마케팅 관련 채용 공고 크롤링
=============================================================
- requests + BeautifulSoup 기반 크롤링
- 검색 결과 카드에서 데이터 추출
- 수집 대상: 공고제목, 회사명, 경력조건, 학력조건, 근무지역,
             고용형태, 직무분야, 마감일, 기술스택, 자격증
=============================================================
"""

import re
import os
import time
from datetime import datetime
from urllib.parse import quote, urlencode

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

from config.settings import (
    SARAMIN_KEYWORDS,
    TECH_STACK_KEYWORDS,
    CERTIFICATE_KEYWORDS,
    DATA_RAW_DIR,
    URL_LIST_DIR,
    USER_AGENT,
    random_delay,
)


class SaraminCrawler:
    """사람인 채용공고 크롤러 (검색 결과 카드 기반)"""

    BASE_URL = "https://www.saramin.co.kr"
    SEARCH_URL = "https://www.saramin.co.kr/zf_user/search/recruit"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Referer": "https://www.saramin.co.kr/",
        })
        self.collected_urls = []
        self.max_retries = 3

    def _get_page(self, url: str, retries: int = 0) -> BeautifulSoup:
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            if retries < self.max_retries:
                print(f"    재시도 ({retries + 1}/{self.max_retries}): {e}")
                time.sleep(3)
                return self._get_page(url, retries + 1)
            print(f"    요청 실패: {e}")
            return None

    def _parse_condition_spans(self, spans: list) -> dict:
        result = {}
        for text in spans:
            text = text.strip()
            if not text:
                continue
            if re.search(r"(신입|경력|년↑|년이상)", text):
                result["경력조건"] = text
            elif re.search(r"(대졸|초대졸|석사|박사|학력|고졸|↑)", text):
                result["학력조건"] = text
            elif re.search(r"(정규직|계약직|인턴|파견|아르바이트|프리랜서|위촉직)", text):
                result["고용형태"] = text
            elif "근무지역" not in result:
                result["근무지역"] = text
        return result

    def search_and_parse(self, keyword: str, pages: int = 5) -> list:
        jobs = []
        for page in range(1, pages + 1):
            params = urlencode({"searchType": "search", "searchword": keyword, "recruitPage": page})
            url = f"{self.SEARCH_URL}?{params}"
            soup = self._get_page(url)
            if soup is None:
                break
            cards = soup.select(".item_recruit")
            if not cards:
                break
            for card in cards:
                job = self._parse_card(card, keyword)
                if job:
                    jobs.append(job)
            page_nav = soup.select(".pagination a, .btn_next")
            has_next = any(str(page + 1) in (a.get("href", "") or a.get_text(strip=True)) for a in page_nav)
            if len(cards) < 40 and not has_next:
                break
            random_delay(2, 4)
        return jobs

    def _parse_card(self, card, keyword: str) -> dict:
        job = {}
        title_el = card.select_one(".job_tit a")
        if not title_el:
            return None
        job["공고제목"] = title_el.get_text(strip=True)
        href = title_el.get("href", "")
        if href.startswith("/"):
            href = self.BASE_URL + href
        job["공고URL"] = href
        corp_el = card.select_one(".corp_name a")
        if corp_el:
            job["회사명"] = corp_el.get_text(strip=True)
        cond_spans = card.select(".job_condition > span")
        cond_texts = [s.get_text(strip=True) for s in cond_spans]
        parsed = self._parse_condition_spans(cond_texts)
        job.update(parsed)
        sector_els = card.select(".job_sector a")
        sectors = [s.get_text(strip=True) for s in sector_els if s.get_text(strip=True)]
        if sectors:
            job["직무분야"] = ", ".join(sectors)
        date_el = card.select_one(".job_date .date")
        if date_el:
            job["마감일"] = date_el.get_text(strip=True)
        day_el = card.select_one(".job_day")
        if day_el:
            job["등록일"] = day_el.get_text(strip=True).replace("등록일 ", "").replace("수정일 ", "")
        badges = card.select(".area_badge .badge")
        badge_texts = [b.get_text(strip=True) for b in badges if b.get_text(strip=True)]
        if badge_texts:
            job["배지"] = ", ".join(badge_texts)
        full_text = job.get("공고제목", "") + " " + job.get("직무분야", "")
        tech_list = self.extract_tech_stack(full_text)
        if tech_list:
            job["기술스택"] = ", ".join(tech_list)
        cert_list = self.extract_certificates(full_text)
        if cert_list:
            job["자격증"] = ", ".join(cert_list)
        job["검색키워드"] = keyword
        job["수집일시"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.collected_urls.append({
            "번호": len(self.collected_urls) + 1,
            "URL": job["공고URL"], "소스": "사람인", "검색키워드": keyword,
            "수집일시": job["수집일시"], "데이터유형": "채용공고", "비고": job.get("회사명", ""),
        })
        return job

    def extract_tech_stack(self, text: str) -> list:
        if not isinstance(text, str):
            return []
        found = []
        for tech in TECH_STACK_KEYWORDS:
            pattern = re.escape(tech)
            if re.search(rf"\b{pattern}\b" if tech.isascii() else pattern, text, re.IGNORECASE):
                found.append(tech)
        return found

    def extract_certificates(self, text: str) -> list:
        if not isinstance(text, str):
            return []
        found = []
        for cert in CERTIFICATE_KEYWORDS:
            if cert.lower() in text.lower():
                found.append(cert)
        return found

    def crawl_all(self, keywords: list = None) -> pd.DataFrame:
        keywords = keywords or SARAMIN_KEYWORDS
        all_jobs = []
        seen_urls = set()
        for keyword in tqdm(keywords, desc="사람인 키워드 검색"):
            print(f"\n  키워드: '{keyword}'")
            jobs = self.search_and_parse(keyword, pages=5)
            new_count = 0
            for job in jobs:
                url = job.get("공고URL", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                all_jobs.append(job)
                new_count += 1
            print(f"    -> 공고 {len(jobs)}개 발견, 신규 {new_count}개 추가")
            random_delay(1, 2)
        if not all_jobs:
            return pd.DataFrame()
        df = pd.DataFrame(all_jobs)
        col_order = [
            "공고URL", "공고제목", "회사명", "경력조건", "학력조건",
            "근무지역", "고용형태", "직무분야", "마감일", "등록일",
            "기술스택", "자격증", "배지", "검색키워드", "수집일시",
        ]
        existing_cols = [c for c in col_order if c in df.columns]
        extra_cols = [c for c in df.columns if c not in col_order]
        df = df[existing_cols + extra_cols]
        return df

    def save_data(self, df: pd.DataFrame, filename: str):
        if df is None or df.empty:
            print("  저장할 데이터가 없습니다.")
            return
        path = os.path.join(DATA_RAW_DIR, f"{filename}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  저장: {path} ({len(df)}건)")

    def _save_url_list(self):
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
        print(f"  URL 목록 저장: {url_path} (총 {len(df_combined)}개)")

    def _run_crawl(self, keywords, file_suffix="마케팅"):
        print("=" * 60)
        print("사람인 채용공고 크롤링 시작")
        print(f"수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"검색 키워드: {len(keywords)}개")
        print("=" * 60)
        df = self.crawl_all(keywords=keywords)
        self.save_data(df, f"사람인_채용공고_{file_suffix}")
        self._save_url_list()
        count = len(df) if not df.empty else 0
        print(f"\n사람인 크롤링 완료! (총 {count}건)")
        return df

    def run_all(self, extra_keywords=None):
        keywords = list(SARAMIN_KEYWORDS)
        if extra_keywords:
            keywords.extend(extra_keywords)
        return self._run_crawl(keywords, file_suffix="마케팅")

    def run_custom(self, keywords, file_suffix="마케팅_추가"):
        if not keywords:
            print("크롤링할 키워드가 없습니다.")
            return pd.DataFrame()
        return self._run_crawl(keywords, file_suffix=file_suffix)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="사람인 마케팅 채용공고 크롤러")
    parser.add_argument("--mode", choices=["all", "custom"], default="all")
    parser.add_argument("--extra", nargs="+")
    parser.add_argument("--suffix", type=str, default="마케팅_추가")
    args = parser.parse_args()
    crawler = SaraminCrawler()
    if args.mode == "all":
        crawler.run_all(extra_keywords=args.extra)
    elif args.mode == "custom":
        if not args.extra:
            print("--extra 옵션으로 키워드를 지정해주세요.")
        else:
            crawler.run_custom(args.extra, file_suffix=args.suffix)
