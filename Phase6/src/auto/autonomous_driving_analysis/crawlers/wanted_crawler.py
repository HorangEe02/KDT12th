"""
원티드 크롤러
자율주행 관련 포지션 및 기술스택 태그 크롤링 (Selenium 활용)
"""

import time
import random
import logging
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from urllib.parse import quote

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import (
    DATA_RAW_DIR, URL_LIST_DIR, USER_AGENT,
    CRAWL_DELAY_MIN, CRAWL_DELAY_MAX, MAX_RETRIES
)

logger = logging.getLogger(__name__)

# Selenium 임포트 (설치 안 되어 있을 수 있음)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium이 설치되지 않았습니다. pip install selenium webdriver-manager")


class WantedCrawler:
    """원티드 포지션 크롤링 (Selenium 기반)"""

    BASE_URL = "https://www.wanted.co.kr"
    SEARCH_KEYWORDS = ["자율주행", "ADAS", "자율주행 엔지니어", "ROS 개발자", "자율주행 AI"]

    def __init__(self):
        self.driver = None
        self.collected_urls = []

        if SELENIUM_AVAILABLE:
            self._init_driver()
        else:
            logger.error("Selenium을 사용할 수 없습니다.")

    def _init_driver(self):
        """Chrome WebDriver 초기화 (headless)"""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument(f"user-agent={USER_AGENT}")
            options.add_argument("--window-size=1920,1080")

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            logger.info("Chrome WebDriver 초기화 완료")
        except Exception as e:
            logger.error(f"WebDriver 초기화 실패: {e}")
            self.driver = None

    def search_positions(self, keyword: str) -> list:
        """원티드 검색 페이지에서 포지션 목록 수집"""
        if not self.driver:
            logger.error("WebDriver가 초기화되지 않았습니다.")
            return []

        urls = []
        search_url = f"{self.BASE_URL}/search?query={quote(keyword)}&tab=position"

        try:
            self.driver.get(search_url)
            time.sleep(3)

            # 무한 스크롤 처리 (최대 10회)
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for scroll in range(10):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # 포지션 카드 URL 추출
            position_cards = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/wd/']")
            if not position_cards:
                position_cards = self.driver.find_elements(By.CSS_SELECTOR, "a[data-position-id]")

            for card in position_cards:
                href = card.get_attribute("href")
                if href and "/wd/" in href:
                    urls.append(href)

            urls = list(set(urls))
            logger.info(f"원티드 검색 '{keyword}': {len(urls)}개 포지션 발견")

        except Exception as e:
            logger.error(f"검색 실패 '{keyword}': {e}")

        return urls

    def parse_position_detail(self, url: str) -> dict:
        """포지션 상세 페이지 파싱"""
        result = {"URL": url}

        if not self.driver:
            return result

        for attempt in range(MAX_RETRIES):
            try:
                self.driver.get(url)
                time.sleep(2)

                # 포지션명
                try:
                    title = self.driver.find_element(By.CSS_SELECTOR, "h1, .JobHeader_title__HttDA, section h2")
                    result["포지션명"] = title.text.strip()
                except Exception:
                    result["포지션명"] = ""

                # 회사명
                try:
                    company = self.driver.find_element(
                        By.CSS_SELECTOR,
                        ".JobHeader_companyName__3gMkp, a[href*='/company/'] h6, .company-name"
                    )
                    result["회사명"] = company.text.strip()
                except Exception:
                    result["회사명"] = ""

                # 기술스택 태그
                try:
                    tech_tags = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".SkillItem_skillItem__Y5PDB, .skill-tag, span[class*='skill']"
                    )
                    result["기술스택태그"] = ", ".join([t.text.strip() for t in tech_tags if t.text.strip()])
                except Exception:
                    result["기술스택태그"] = ""

                # 상세 섹션 추출 (주요업무, 자격요건, 우대사항, 혜택)
                try:
                    sections = self.driver.find_elements(By.CSS_SELECTOR, "section.JobDescription_JobDescription__VWfcb > div")
                    if not sections:
                        sections = self.driver.find_elements(By.CSS_SELECTOR, ".job-description section")

                    section_texts = {}
                    for sec in sections:
                        try:
                            heading = sec.find_element(By.CSS_SELECTOR, "h6, h3, strong").text.strip()
                            body = sec.text.replace(heading, "").strip()
                            section_texts[heading] = body
                        except Exception:
                            continue

                    for key, val in section_texts.items():
                        if "업무" in key:
                            result["주요업무"] = val
                        elif "자격" in key or "요건" in key:
                            result["자격요건"] = val
                        elif "우대" in key:
                            result["우대사항"] = val
                        elif "혜택" in key or "복지" in key:
                            result["혜택및복지"] = val

                except Exception:
                    pass

                # 경력/연봉 정보
                try:
                    info_items = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".JobHeader_pcInfoContainer__jMFgF span, .summary-item"
                    )
                    for item in info_items:
                        text = item.text.strip()
                        if "경력" in text or "신입" in text:
                            result["경력조건"] = text
                        elif "만원" in text or "억" in text:
                            result["연봉정보"] = text
                except Exception:
                    pass

                self.collected_urls.append(url)
                logger.info(f"파싱 완료: {result.get('포지션명', 'N/A')}")
                return result

            except Exception as e:
                logger.warning(f"상세 파싱 실패 (시도 {attempt + 1}): {e}")
                time.sleep(2)

        return result

    def crawl_all(self) -> pd.DataFrame:
        """자율주행 관련 키워드로 전체 포지션 크롤링"""
        all_results = []
        all_urls = set()

        for keyword in tqdm(self.SEARCH_KEYWORDS, desc="원티드 포지션 크롤링"):
            position_urls = self.search_positions(keyword)

            for url in position_urls:
                if url in all_urls:
                    continue
                all_urls.add(url)

                detail = self.parse_position_detail(url)
                if detail.get("포지션명"):
                    detail["검색키워드"] = keyword
                    all_results.append(detail)

                time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

        df = pd.DataFrame(all_results)
        logger.info(f"원티드 크롤링 완료: 총 {len(df)}건")
        return df

    def save_data(self, df: pd.DataFrame, filename: str = "wanted_positions.csv"):
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
                "소스": "원티드",
                "검색키워드": "",
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "데이터유형": "채용공고",
                "비고": "",
            })

        if url_records:
            url_df = pd.DataFrame(url_records)
            url_df.to_csv(url_file, mode="a", header=False, index=False, encoding="utf-8-sig")

        self.collected_urls = []

    def close(self):
        """WebDriver 종료"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver 종료")

    def run_all(self):
        """전체 실행"""
        logger.info("=" * 50)
        logger.info("원티드 포지션 크롤링 시작")
        logger.info("=" * 50)

        try:
            df = self.crawl_all()
            self.save_data(df)
            return df
        finally:
            self.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    crawler = WantedCrawler()
    crawler.run_all()
