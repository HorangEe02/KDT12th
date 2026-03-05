"""
잡플래닛 크롤러
자율주행 관련 기업의 리뷰, 연봉, 면접 후기 크롤링 (Selenium 활용)
"""

import time
import random
import logging
import pandas as pd
from datetime import datetime
from tqdm import tqdm

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import (
    TARGET_COMPANIES, DATA_RAW_DIR, URL_LIST_DIR, USER_AGENT,
    CRAWL_DELAY_MIN, CRAWL_DELAY_MAX, MAX_RETRIES,
    JOBPLANET_USER_ID, JOBPLANET_PASSWORD
)

logger = logging.getLogger(__name__)

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
    logger.warning("Selenium이 설치되지 않았습니다.")


class JobPlanetCrawler:
    """잡플래닛 기업 리뷰/연봉/면접후기 크롤러"""

    BASE_URL = "https://www.jobplanet.co.kr"

    def __init__(self, driver_path: str = None):
        self.driver = None
        self.collected_urls = []
        self.logged_in = False

        if SELENIUM_AVAILABLE:
            self._init_driver(driver_path)
            if self.driver and JOBPLANET_USER_ID and JOBPLANET_PASSWORD:
                self._login()

    def _init_driver(self, driver_path: str = None):
        """Chrome WebDriver 초기화 (Cloudflare 우회 옵션 포함)"""
        try:
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(f"user-agent={USER_AGENT}")
            options.add_argument("--window-size=1920,1080")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            if driver_path:
                service = Service(driver_path)
            else:
                service = Service(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            self.driver.implicitly_wait(10)
            logger.info("잡플래닛 WebDriver 초기화 완료")
        except Exception as e:
            logger.error(f"WebDriver 초기화 실패: {e}")

    def _login(self):
        """잡플래닛 로그인"""
        try:
            self.driver.get(f"{self.BASE_URL}/users/sign_in")
            time.sleep(3)

            # 이메일 입력
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='user[email]'], #user_email"))
            )
            email_input.clear()
            email_input.send_keys(JOBPLANET_USER_ID)

            # 비밀번호 입력
            pw_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='user[password]'], #user_password")
            pw_input.clear()
            pw_input.send_keys(JOBPLANET_PASSWORD)

            # 로그인 버튼 클릭
            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .btn_sign_in")
            login_btn.click()

            time.sleep(3)
            self.logged_in = True
            logger.info("잡플래닛 로그인 성공")

        except Exception as e:
            logger.warning(f"잡플래닛 로그인 실패: {e}")
            self.logged_in = False

    def crawl_company_reviews(self, company_id: str, company_name: str = "", pages: int = 3) -> pd.DataFrame:
        """기업 리뷰 페이지 크롤링"""
        results = []
        if not self.driver:
            return pd.DataFrame()

        for page in range(1, pages + 1):
            url = f"{self.BASE_URL}/companies/{company_id}/reviews?page={page}"
            self.collected_urls.append(url)

            for attempt in range(MAX_RETRIES):
                try:
                    self.driver.get(url)
                    time.sleep(3)

                    # 리뷰 아이템 추출
                    review_items = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".content_ty4, .review_item, article[class*='Review']"
                    )

                    for item in review_items:
                        review = {"회사명": company_name, "회사ID": company_id}

                        try:
                            title = item.find_element(By.CSS_SELECTOR, ".us_label, h2, .review_title")
                            review["리뷰제목"] = title.text.strip()
                        except Exception:
                            review["리뷰제목"] = ""

                        # 장점/단점
                        try:
                            sections = item.find_elements(By.CSS_SELECTOR, ".tc_list, .review_content div")
                            texts = [s.text.strip() for s in sections]
                            if len(texts) >= 2:
                                review["장점"] = texts[0]
                                review["단점"] = texts[1]
                            elif len(texts) == 1:
                                review["장점"] = texts[0]
                                review["단점"] = ""
                        except Exception:
                            review["장점"] = ""
                            review["단점"] = ""

                        # 평점들
                        try:
                            ratings = item.find_elements(By.CSS_SELECTOR, ".star_score, .rating")
                            rating_names = ["총점", "승진기회", "워라밸", "급여", "사내문화", "경영진"]
                            for idx, r in enumerate(ratings[:6]):
                                name = rating_names[idx] if idx < len(rating_names) else f"평점{idx}"
                                try:
                                    score_text = r.text.strip() or r.get_attribute("style") or ""
                                    # width 퍼센트에서 점수 추출 (예: width: 80% → 4.0)
                                    if "width" in score_text:
                                        import re
                                        pct = re.search(r"(\d+)%", score_text)
                                        review[name] = round(int(pct.group(1)) / 20, 1) if pct else ""
                                    else:
                                        review[name] = score_text
                                except Exception:
                                    review[name] = ""
                        except Exception:
                            pass

                        # 작성일, 재직상태, 직무
                        try:
                            meta = item.find_elements(By.CSS_SELECTOR, ".content_top_ty2 span, .review_meta span")
                            for m in meta:
                                text = m.text.strip()
                                if "현직" in text or "전직" in text:
                                    review["재직상태"] = text
                                elif any(c.isdigit() for c in text) and ("." in text or "-" in text):
                                    review["작성일"] = text
                                else:
                                    review["직무"] = text
                        except Exception:
                            pass

                        results.append(review)

                    logger.info(f"리뷰 크롤링: {company_name} 페이지 {page} → {len(review_items)}건")
                    break

                except Exception as e:
                    logger.warning(f"리뷰 크롤링 실패 (시도 {attempt + 1}): {e}")
                    time.sleep(2)

            time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

        return pd.DataFrame(results)

    def crawl_company_salary(self, company_id: str, company_name: str = "") -> pd.DataFrame:
        """연봉 정보 크롤링"""
        results = []
        if not self.driver:
            return pd.DataFrame()

        url = f"{self.BASE_URL}/companies/{company_id}/salaries"
        self.collected_urls.append(url)

        for attempt in range(MAX_RETRIES):
            try:
                self.driver.get(url)
                time.sleep(3)

                salary_items = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".salary_item, .salary_row, tr[class*='salary']"
                )

                for item in salary_items:
                    salary = {"회사명": company_name, "회사ID": company_id}

                    try:
                        cells = item.find_elements(By.CSS_SELECTOR, "td, .cell, span")
                        texts = [c.text.strip() for c in cells if c.text.strip()]

                        if len(texts) >= 3:
                            salary["직무"] = texts[0]
                            salary["연차"] = texts[1]
                            salary["연봉_만원"] = texts[2]
                        if len(texts) >= 4:
                            salary["성과급여부"] = texts[3]
                    except Exception:
                        pass

                    results.append(salary)

                logger.info(f"연봉 크롤링: {company_name} → {len(salary_items)}건")
                break

            except Exception as e:
                logger.warning(f"연봉 크롤링 실패 (시도 {attempt + 1}): {e}")
                time.sleep(2)

        return pd.DataFrame(results)

    def crawl_interview_reviews(self, company_id: str, company_name: str = "", pages: int = 3) -> pd.DataFrame:
        """면접 후기 크롤링"""
        results = []
        if not self.driver:
            return pd.DataFrame()

        for page in range(1, pages + 1):
            url = f"{self.BASE_URL}/companies/{company_id}/interviews?page={page}"
            self.collected_urls.append(url)

            for attempt in range(MAX_RETRIES):
                try:
                    self.driver.get(url)
                    time.sleep(3)

                    interview_items = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".content_ty4, .interview_item, article[class*='Interview']"
                    )

                    for item in interview_items:
                        interview = {"회사명": company_name, "회사ID": company_id}

                        # 면접 경험 (긍정/보통/부정)
                        try:
                            exp = item.find_element(By.CSS_SELECTOR, ".experience, .interview_result")
                            interview["면접경험"] = exp.text.strip()
                        except Exception:
                            interview["면접경험"] = ""

                        # 면접 난이도
                        try:
                            diff = item.find_element(By.CSS_SELECTOR, ".difficulty, .interview_difficulty")
                            interview["면접난이도"] = diff.text.strip()
                        except Exception:
                            interview["면접난이도"] = ""

                        # 면접 질문
                        try:
                            questions = item.find_elements(By.CSS_SELECTOR, ".interview_question, .question_content")
                            interview["면접질문"] = " | ".join([q.text.strip() for q in questions])
                        except Exception:
                            interview["면접질문"] = ""

                        # 면접 내용 전체
                        try:
                            content = item.find_element(By.CSS_SELECTOR, ".tc_list, .content_body")
                            interview["면접내용"] = content.text.strip()
                        except Exception:
                            interview["면접내용"] = ""

                        # 합격 여부
                        try:
                            result_el = item.find_element(By.CSS_SELECTOR, ".result, .pass_fail")
                            interview["합격여부"] = result_el.text.strip()
                        except Exception:
                            interview["합격여부"] = ""

                        # 지원 경로
                        try:
                            route = item.find_element(By.CSS_SELECTOR, ".route, .apply_route")
                            interview["지원경로"] = route.text.strip()
                        except Exception:
                            interview["지원경로"] = ""

                        results.append(interview)

                    logger.info(f"면접후기 크롤링: {company_name} 페이지 {page} → {len(interview_items)}건")
                    break

                except Exception as e:
                    logger.warning(f"면접후기 크롤링 실패 (시도 {attempt + 1}): {e}")
                    time.sleep(2)

            time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

        return pd.DataFrame(results)

    def crawl_company_info(self, company_id: str) -> dict:
        """기업 기본 정보 크롤링"""
        info = {"회사ID": company_id}
        if not self.driver:
            return info

        url = f"{self.BASE_URL}/companies/{company_id}"
        self.collected_urls.append(url)

        try:
            self.driver.get(url)
            time.sleep(3)

            # 기업명
            try:
                name = self.driver.find_element(By.CSS_SELECTOR, "h1.name, .company_name")
                info["기업명"] = name.text.strip()
            except Exception:
                pass

            # 기본 정보 (업종, 사원수, 설립연도 등)
            try:
                info_items = self.driver.find_elements(By.CSS_SELECTOR, ".company_info li, .info_item")
                for item in info_items:
                    text = item.text.strip()
                    if "업종" in text:
                        info["업종"] = text.replace("업종", "").strip()
                    elif "사원" in text or "명" in text:
                        info["사원수"] = text
                    elif "설립" in text:
                        info["설립연도"] = text
            except Exception:
                pass

            # 평균 연봉, 총 평점
            try:
                rating = self.driver.find_element(By.CSS_SELECTOR, ".rate_star, .total_rating")
                info["총평점"] = rating.text.strip()
            except Exception:
                pass

            try:
                avg_sal = self.driver.find_element(By.CSS_SELECTOR, ".avg_salary, .salary_info")
                info["평균연봉"] = avg_sal.text.strip()
            except Exception:
                pass

        except Exception as e:
            logger.error(f"기업정보 크롤링 실패: {e}")

        return info

    def save_data(self, df: pd.DataFrame, filename: str):
        """데이터 저장"""
        if df.empty:
            logger.warning(f"저장할 데이터가 없습니다: {filename}")
            return

        filepath = DATA_RAW_DIR / filename
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"저장 완료: {filepath} ({len(df)}건)")

        # URL 목록 추가
        url_file = URL_LIST_DIR / "crawling_urls.csv"
        existing = pd.read_csv(url_file) if url_file.stat().st_size > 50 else pd.DataFrame()
        start_num = len(existing) + 1 if not existing.empty else 1

        url_records = []
        data_type_map = {
            "review": "기업리뷰",
            "salary": "연봉정보",
            "interview": "면접후기",
        }
        data_type = "기업리뷰"
        for key, val in data_type_map.items():
            if key in filename:
                data_type = val
                break

        for i, url in enumerate(self.collected_urls):
            url_records.append({
                "번호": start_num + i,
                "URL": url,
                "소스": "잡플래닛",
                "검색키워드": "",
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "데이터유형": data_type,
                "비고": "",
            })

        if url_records:
            url_df = pd.DataFrame(url_records)
            url_df.to_csv(url_file, mode="a", header=False, index=False, encoding="utf-8-sig")

        self.collected_urls = []

    def run_all(self):
        """전체 기업에 대해 크롤링 실행"""
        logger.info("=" * 50)
        logger.info("잡플래닛 크롤링 시작")
        logger.info("=" * 50)

        all_reviews = []
        all_salaries = []
        all_interviews = []
        all_company_info = []

        for company_name, info in tqdm(TARGET_COMPANIES.items(), desc="잡플래닛 기업 크롤링"):
            company_id = info["jobplanet_id"]
            logger.info(f"▶ {company_name} 크롤링 시작 (ID: {company_id})")

            # 기업 정보
            company_info = self.crawl_company_info(company_id)
            company_info["기업명"] = company_name
            company_info["카테고리"] = info["category"]
            all_company_info.append(company_info)

            # 리뷰
            reviews_df = self.crawl_company_reviews(company_id, company_name)
            if not reviews_df.empty:
                all_reviews.append(reviews_df)

            # 연봉
            salary_df = self.crawl_company_salary(company_id, company_name)
            if not salary_df.empty:
                all_salaries.append(salary_df)

            # 면접후기
            interview_df = self.crawl_interview_reviews(company_id, company_name)
            if not interview_df.empty:
                all_interviews.append(interview_df)

            time.sleep(random.uniform(CRAWL_DELAY_MIN, CRAWL_DELAY_MAX))

        # 전체 데이터 병합 및 저장
        if all_reviews:
            reviews_combined = pd.concat(all_reviews, ignore_index=True)
            self.save_data(reviews_combined, "jobplanet_reviews.csv")

        if all_salaries:
            salaries_combined = pd.concat(all_salaries, ignore_index=True)
            self.save_data(salaries_combined, "jobplanet_salaries.csv")

        if all_interviews:
            interviews_combined = pd.concat(all_interviews, ignore_index=True)
            self.save_data(interviews_combined, "jobplanet_interviews.csv")

        # 기업 정보 저장
        if all_company_info:
            info_df = pd.DataFrame(all_company_info)
            self.save_data(info_df, "jobplanet_company_info.csv")

        logger.info("잡플래닛 크롤링 완료")

    def close(self):
        """WebDriver 종료"""
        if self.driver:
            self.driver.quit()
            logger.info("잡플래닛 WebDriver 종료")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    crawler = JobPlanetCrawler()
    try:
        crawler.run_all()
    finally:
        crawler.close()
