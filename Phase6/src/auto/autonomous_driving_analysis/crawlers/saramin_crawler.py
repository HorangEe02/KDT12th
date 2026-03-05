"""
사람인 채용공고 크롤러
자율주행 관련 채용 공고의 상세 정보를 크롤링
"""

import re
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from urllib.parse import quote

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import (
    SARAMIN_KEYWORDS, TECH_STACK_KEYWORDS, CERTIFICATE_KEYWORDS,
    DATA_RAW_DIR, URL_LIST_DIR, USER_AGENT,
    CRAWL_DELAY_MIN, CRAWL_DELAY_MAX, MAX_RETRIES
)

logger = logging.getLogger(__name__)


class SaraminCrawler:
    """사람인 채용공고 크롤링"""

    BASE_URL = "https://www.saramin.co.kr"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": self.BASE_URL,
        })
        self.collected_urls = []

    def search_jobs(self, keyword: str, pages: int = 5) -> list:
        """키워드로 채용 공고 검색, URL 목록 반환"""
        urls = []

        for page in range(1, pages + 1):
            search_url = (
                f"{self.BASE_URL}/zf_user/search/recruit"
                f"?searchType=search&searchword={quote(keyword)}&recruitPage={page}"
            )

            for attempt in range(MAX_RETRIES):
                try:
                    resp = self.session.get(search_url, timeout=15)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "html.parser")

                    # 채용공고 목록에서 링크 추출
                    job_items = soup.select(".item_recruit .job_tit a")
                    if not job_items:
                        # 대체 셀렉터
                        job_items = soup.select("a[href*='/zf_user/jobs/relay/view']")

                    for item in job_items:
                        href = item.get("href", "")
                        if href:
                            full_url = href if href.startswith("http") else self.BASE_URL + href
                            urls.append(full_url)

                    logger.info(f"검색 '{keyword}' 페이지 {page}: {len(job_items)}건 발견")
                    break

                except requests.exceptions.RequestException as e:
                    logger.warning(f"검색 실패 (시도 {attempt + 1}): {e}")
                    time.sleep(2)

            time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

        return list(set(urls))  # 중복 제거

    def parse_job_detail(self, url: str) -> dict:
        """개별 채용 공고 상세 페이지 파싱"""
        result = {"URL": url}

        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # 공고 제목
                title_tag = soup.select_one(".tit_job") or soup.select_one("h1.title")
                result["공고제목"] = title_tag.get_text(strip=True) if title_tag else ""

                # 회사명
                company_tag = soup.select_one(".company_name") or soup.select_one(".corp_name a")
                result["회사명"] = company_tag.get_text(strip=True) if company_tag else ""

                # 상세 정보 추출 (요약 섹션)
                summary_items = soup.select(".jv_summary .cont")
                summary_labels = soup.select(".jv_summary .tit")

                for label, cont in zip(summary_labels, summary_items):
                    label_text = label.get_text(strip=True)
                    cont_text = cont.get_text(strip=True)

                    if "경력" in label_text:
                        result["경력조건"] = cont_text
                    elif "학력" in label_text:
                        result["학력조건"] = cont_text
                    elif "근무지" in label_text or "지역" in label_text:
                        result["근무지역"] = cont_text
                    elif "급여" in label_text or "연봉" in label_text:
                        result["연봉정보"] = cont_text
                    elif "마감" in label_text:
                        result["마감일"] = cont_text

                # 직무 분야
                job_sector = soup.select_one(".job_sector")
                result["직무분야"] = job_sector.get_text(strip=True) if job_sector else ""

                # 자격요건 / 우대사항 / 복리후생
                detail_sections = soup.select(".jv_detail .cont")
                detail_titles = soup.select(".jv_detail .tit_detail")

                full_text = ""
                for dtitle, dcont in zip(detail_titles, detail_sections):
                    dtitle_text = dtitle.get_text(strip=True)
                    dcont_text = dcont.get_text(strip=True)

                    if "자격" in dtitle_text or "요건" in dtitle_text:
                        result["자격요건"] = dcont_text
                    elif "우대" in dtitle_text:
                        result["우대사항"] = dcont_text
                    elif "복리" in dtitle_text or "혜택" in dtitle_text:
                        result["복리후생"] = dcont_text
                    elif "업무" in dtitle_text or "담당" in dtitle_text:
                        result["주요업무"] = dcont_text

                    full_text += " " + dcont_text

                # 기술스택 추출
                result["기술스택"] = ", ".join(self.extract_tech_stack(full_text))
                result["자격증"] = ", ".join(self.extract_certificates(full_text))

                # 기업 규모 (가능한 경우)
                size_tag = soup.select_one(".company_info .info") or soup.select_one(".corp_info_detail")
                result["기업규모"] = size_tag.get_text(strip=True) if size_tag else ""

                self.collected_urls.append(url)
                logger.info(f"파싱 완료: {result.get('공고제목', 'N/A')}")
                return result

            except requests.exceptions.RequestException as e:
                logger.warning(f"상세 파싱 실패 (시도 {attempt + 1}): {e}")
                time.sleep(2)
            except Exception as e:
                logger.error(f"파싱 중 오류: {e}")
                break

        return result

    def extract_tech_stack(self, text: str) -> list:
        """텍스트에서 기술스택 키워드 추출"""
        if not text:
            return []
        found = []
        text_upper = text.upper()
        for tech in TECH_STACK_KEYWORDS:
            # 대소문자 무관 매칭
            if tech.upper() in text_upper:
                found.append(tech)
            # 한글 키워드는 원본 매칭
            elif tech in text:
                found.append(tech)
        return list(set(found))

    def extract_certificates(self, text: str) -> list:
        """텍스트에서 자격증 키워드 추출"""
        if not text:
            return []
        found = []
        for cert in CERTIFICATE_KEYWORDS:
            if cert in text:
                found.append(cert)
        return list(set(found))

    def crawl_all(self, keywords: list = None) -> pd.DataFrame:
        """전체 키워드에 대해 크롤링 파이프라인 실행"""
        keywords = keywords or SARAMIN_KEYWORDS
        all_results = []
        all_urls = set()

        for keyword in tqdm(keywords, desc="사람인 채용공고 크롤링"):
            job_urls = self.search_jobs(keyword, pages=3)
            logger.info(f"'{keyword}': {len(job_urls)}개 공고 발견")

            for url in job_urls:
                if url in all_urls:
                    continue
                all_urls.add(url)

                detail = self.parse_job_detail(url)
                if detail.get("공고제목"):
                    detail["검색키워드"] = keyword
                    all_results.append(detail)

                time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

        df = pd.DataFrame(all_results)
        logger.info(f"사람인 크롤링 완료: 총 {len(df)}건")
        return df

    def save_data(self, df: pd.DataFrame, filename: str = "saramin_jobs.csv"):
        """데이터 저장"""
        if df.empty:
            logger.warning("저장할 데이터가 없습니다.")
            return

        filepath = DATA_RAW_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"저장 완료: {filepath} ({len(df)}건)")

        # URL 목록 추가
        url_file = URL_LIST_DIR / "crawling_urls.csv"
        existing = pd.read_csv(url_file) if url_file.stat().st_size > 50 else pd.DataFrame()
        start_num = len(existing) + 1 if not existing.empty else 1

        url_records = []
        for i, url in enumerate(self.collected_urls):
            url_records.append({
                "번호": start_num + i,
                "URL": url,
                "소스": "사람인",
                "검색키워드": "",
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "데이터유형": "채용공고",
                "비고": "",
            })

        if url_records:
            url_df = pd.DataFrame(url_records)
            url_df.to_csv(url_file, mode="a", header=False, index=False, encoding="utf-8-sig")
            logger.info(f"URL 목록 추가: {len(url_records)}건")

        self.collected_urls = []

    def run_all(self):
        """전체 실행"""
        logger.info("=" * 50)
        logger.info("사람인 채용공고 크롤링 시작")
        logger.info("=" * 50)

        df = self.crawl_all()
        self.save_data(df)
        return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    crawler = SaraminCrawler()
    crawler.run_all()
