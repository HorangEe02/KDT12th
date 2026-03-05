"""
=============================================================
잡플래닛 크롤러 - 마케팅 기업 리뷰/연봉/면접후기 크롤링
=============================================================
- Selenium을 활용한 잡플래닛 로그인 후 크롤링
- 수집 대상: 기업 리뷰, 연봉, 평점, 면접 후기
- 대상 기업: settings.py TARGET_COMPANIES + 추가 기업 지원
=============================================================
"""

import time
import os
import re
import json
import urllib.parse
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config.settings import (
    JOBPLANET_USER_ID, JOBPLANET_PASSWORD,
    TARGET_COMPANIES, DATA_RAW_DIR, URL_LIST_DIR,
    USER_AGENT, random_delay,
)


class JobPlanetCrawler:
    """잡플래닛 기업 리뷰/연봉/면접후기 크롤러"""

    BASE_URL = "https://www.jobplanet.co.kr"
    LOGIN_URL = "https://www.jobplanet.co.kr/users/sign_in"

    def __init__(self, driver_path=None, headless=False):
        self.driver = self._create_driver(headless)
        self.collected_urls = []

    def _create_driver(self, headless=False):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument(f"user-agent={USER_AGENT}")
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        return driver

    def _get_soup(self, url, wait=2):
        self.driver.get(url)
        time.sleep(wait)
        return BeautifulSoup(self.driver.page_source, "html.parser")

    @staticmethod
    def _safe_text(element):
        return element.get_text(strip=True) if element else ""

    @staticmethod
    def _try_selectors(soup_or_tag, selectors):
        for sel in selectors:
            el = soup_or_tag.select_one(sel)
            if el:
                return el
        return None

    def login(self) -> bool:
        print("잡플래닛 로그인 시도...")
        self.driver.get(self.LOGIN_URL)
        time.sleep(4)
        try:
            email_selectors = ["input[type='email']", "input[name='user[email]']", "input#user_email", "input[placeholder*='이메일']"]
            email_filled = False
            for sel in email_selectors:
                try:
                    el = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                    self.driver.execute_script(
                        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        el, JOBPLANET_USER_ID)
                    email_filled = True
                    break
                except Exception:
                    continue
            if not email_filled:
                print("  이메일 입력란을 찾을 수 없음")
                return False
            time.sleep(0.5)
            pw_selectors = ["input[type='password']", "input[name='user[password]']"]
            pw_filled = False
            for sel in pw_selectors:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    self.driver.execute_script(
                        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        el, JOBPLANET_PASSWORD)
                    pw_filled = True
                    break
                except Exception:
                    continue
            if not pw_filled:
                print("  비밀번호 입력란을 찾을 수 없음")
                return False
            time.sleep(0.5)
            btn_selectors = ["button[type='submit']", ".btn_sign_in", "input[type='submit']", "button.btn_sign_up"]
            for sel in btn_selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                    self.driver.execute_script("arguments[0].click();", btn)
                    break
                except Exception:
                    continue
            time.sleep(5)
            if "sign_in" not in self.driver.current_url:
                print("  로그인 성공!")
                return True
            else:
                print("  로그인 실패 - CAPTCHA 또는 인증 필요")
                return False
        except TimeoutException:
            print("  로그인 페이지 로딩 실패")
            return False

    def _search_company(self, company_name: str) -> str:
        search_name = re.sub(r'[（(].*?[）)]', '', company_name).strip()
        search_variants = [search_name]
        if "AI" in search_name:
            search_variants.append(search_name.replace("AI", "에이아이"))
            search_variants.append(search_name.replace("AI", "").strip())
        for query in search_variants:
            search_url = f"{self.BASE_URL}/search?query={urllib.parse.quote(query)}"
            self.driver.get(search_url)
            try:
                WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.grid a[href*='/companies/']")))
            except TimeoutException:
                continue
            time.sleep(2)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            grid = soup.select_one("ul.grid")
            if not grid:
                continue
            for a_tag in grid.find_all("a", href=re.compile(r"/companies/\d+")):
                href = a_tag.get("href", "")
                m = re.search(r"/companies/(\d+)", href)
                if not m:
                    continue
                cid = m.group(1)
                text = a_tag.get_text(strip=True)
                if query in text or search_name in text:
                    print(f"    -> 매칭: [{cid}] {text[:40]}")
                    return cid
        print(f"    '{company_name}' 검색 결과 매칭 실패")
        return None

    def crawl_company_info(self, company_id: str) -> dict:
        url = f"{self.BASE_URL}/companies/{company_id}"
        soup = self._get_soup(url)
        info = {}
        try:
            el = self._try_selectors(soup, [".rate_point .num", ".company_rating .num", ".total_rating"])
            if el:
                nums = re.findall(r"[\d.]+", self._safe_text(el))
                if nums:
                    info["전체평점"] = nums[0]
            el = self._try_selectors(soup, ["h1.name", "h1.company_name", "h1"])
            if el:
                info["기업명_잡플래닛"] = self._safe_text(el)
            for dt in soup.select("dt"):
                dd = dt.find_next_sibling("dd")
                if dd:
                    key, val = self._safe_text(dt), self._safe_text(dd)
                    if key and val:
                        info[key] = val
            for section in soup.select(".rating_item, .score_item, .company_grade_item, .chart_item"):
                label_el = self._try_selectors(section, [".rating_label", ".item_name", "dt", ".name"])
                value_el = self._try_selectors(section, [".rating_value", ".item_value", "dd", ".num"])
                if label_el and value_el:
                    label, value = self._safe_text(label_el), self._safe_text(value_el)
                    if label and value:
                        info[f"평점_{label}"] = value
        except Exception as e:
            info["크롤링_오류"] = str(e)
        self.collected_urls.append({
            "번호": len(self.collected_urls) + 1, "URL": url, "소스": "잡플래닛",
            "검색키워드": info.get("기업명_잡플래닛", ""),
            "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "데이터유형": "기업정보", "비고": "",
        })
        return info

    def crawl_company_reviews(self, company_id: str, max_pages: int = 3) -> pd.DataFrame:
        reviews = []
        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/companies/{company_id}/reviews?page={page}"
            soup = self._get_soup(url, wait=3)
            page_reviews = []
            for header in soup.find_all("div", class_=lambda c: c and "relative" in c and "flex" in c and "items-center" in c and "justify-between" in c):
                text = header.get_text(strip=True)
                if "전직원" not in text and "현직원" not in text:
                    continue
                card = header.parent
                if not card:
                    continue
                review = {}
                spans = header.find_all("span", class_=lambda c: c and "text-body2" in c)
                span_texts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]
                if len(span_texts) >= 1:
                    review["직종"] = span_texts[0]
                if len(span_texts) >= 2:
                    review["재직상태"] = span_texts[1]
                if len(span_texts) >= 3:
                    review["위치"] = span_texts[2]
                if len(span_texts) >= 4:
                    review["등록일"] = span_texts[3].replace("작성", "").strip()
                rating_div = card.select_one("div.block div.mb-\\[32px\\], div[class*='mb-[32px]']")
                if rating_div:
                    nums = re.findall(r"[\d.]+", self._safe_text(rating_div))
                    if nums:
                        review["별점"] = nums[0]
                body = card.select_one("p.new-body1")
                if body:
                    txt = self._safe_text(body)
                    if txt and "멤버십" not in txt:
                        review["한줄평"] = txt[:500]
                if review:
                    page_reviews.append(review)
            if not page_reviews:
                break
            reviews.extend(page_reviews)
            print(f"      리뷰 p{page}: {len(page_reviews)}건")
        self.collected_urls.append({
            "번호": len(self.collected_urls) + 1,
            "URL": f"{self.BASE_URL}/companies/{company_id}/reviews",
            "소스": "잡플래닛", "검색키워드": "", "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "데이터유형": "기업리뷰", "비고": "",
        })
        return pd.DataFrame(reviews) if reviews else pd.DataFrame()

    def crawl_company_salary(self, company_id: str) -> pd.DataFrame:
        url = f"{self.BASE_URL}/companies/{company_id}/salaries"
        soup = self._get_soup(url, wait=2.5)
        salary_info = {}
        try:
            el = self._try_selectors(soup, [".avg_salary", ".salary_avg", ".total_salary .num"])
            if el:
                salary_info["평균연봉"] = self._safe_text(el)
            rows = soup.select(".salary_item, .salary_row, tr[class*='salary'], .chart_row")
            details = []
            for row in rows:
                cols = row.select("td, .cell, span, div")
                texts = [self._safe_text(c) for c in cols if self._safe_text(c)]
                if len(texts) >= 2:
                    details.append({"구분": texts[0], "연봉": texts[-1]})
            if details:
                salary_info["상세"] = json.dumps(details, ensure_ascii=False)
        except Exception as e:
            salary_info["크롤링_오류"] = str(e)
        self.collected_urls.append({
            "번호": len(self.collected_urls) + 1, "URL": url, "소스": "잡플래닛",
            "검색키워드": "", "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "데이터유형": "연봉", "비고": "",
        })
        return pd.DataFrame([salary_info]) if salary_info else pd.DataFrame()

    def crawl_interview_reviews(self, company_id: str, max_pages: int = 2) -> pd.DataFrame:
        interviews = []
        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/companies/{company_id}/interviews?page={page}"
            soup = self._get_soup(url, wait=3)
            items = soup.select("section.content_ty4")
            if not items:
                break
            for item in items:
                interview = {}
                el = item.select_one(".content_top_ty2 .txt1")
                if el:
                    txt = self._safe_text(el)
                    parts = txt.split("|")
                    if parts:
                        interview["지원직무"] = re.sub(r'\s+', ' ', parts[0]).strip()
                el = item.select_one(".content_top_ty2 .txt2")
                if el:
                    interview["등록일"] = self._safe_text(el)
                for dt in item.select("dt.df_tit"):
                    dd = dt.find_next_sibling("dd")
                    if not dd:
                        continue
                    key = self._safe_text(dt)
                    if "면접난이도" in key:
                        lev = dd.select_one(".blo_txt2")
                        if lev:
                            interview["면접난이도"] = self._safe_text(lev)
                    elif "면접일자" in key:
                        interview["면접일자"] = self._safe_text(dd)
                    elif "면접경로" in key:
                        interview["면접경로"] = self._safe_text(dd)
                body = item.select_one(".content_body_ty1")
                if body:
                    cover = body.select_one(".cover_wrap, .cover_ad_blind")
                    if not cover:
                        interview["면접경험"] = self._safe_text(body)[:500]
                if interview:
                    interviews.append(interview)
            print(f"      면접후기 p{page}: {len(items)}건")
        self.collected_urls.append({
            "번호": len(self.collected_urls) + 1,
            "URL": f"{self.BASE_URL}/companies/{company_id}/interviews",
            "소스": "잡플래닛", "검색키워드": "", "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "데이터유형": "면접후기", "비고": "",
        })
        return pd.DataFrame(interviews) if interviews else pd.DataFrame()

    def save_data(self, df: pd.DataFrame, filename: str):
        if df is None or df.empty:
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

    def _build_company_list(self, extra_companies=None, include_target=True):
        companies = {}
        if include_target:
            companies.update(TARGET_COMPANIES)
        if extra_companies is None:
            return companies
        if isinstance(extra_companies, dict):
            companies.update(extra_companies)
        elif isinstance(extra_companies, list):
            for item in extra_companies:
                if isinstance(item, str):
                    companies[item] = {"company_id": None, "category": "추가_마케팅기업", "비고": "추가 크롤링 대상"}
                elif isinstance(item, dict):
                    name = item.get("name", item.get("기업명", ""))
                    if not name:
                        continue
                    companies[name] = {"company_id": item.get("company_id"), "category": item.get("category", "추가_마케팅기업"), "비고": item.get("비고", "추가 크롤링 대상")}
        return companies

    def _crawl_companies(self, companies: dict, file_suffix: str = "마케팅"):
        all_company_data, all_reviews, all_salary, all_interviews = [], [], [], []
        items = list(companies.items())
        for idx, (name, info) in enumerate(tqdm(items, desc="기업 크롤링"), 1):
            print(f"\n[{idx}/{len(items)}] {name} ({info.get('category', '')})")
            cid = info.get("company_id")
            if not cid:
                print(f"  -> 잡플래닛에서 검색 중...")
                cid = self._search_company(name)
                if cid is None:
                    print(f"  기업을 찾을 수 없음 - 건너뜀")
                    continue
                print(f"  -> 검색 결과 ID: {cid}")
            print("  기업 정보 수집 중...")
            company_info = self.crawl_company_info(cid)
            company_info["기업명"] = name
            company_info["분야"] = info.get("category", "")
            all_company_data.append(company_info)
            print("  리뷰 수집 중...")
            df_review = self.crawl_company_reviews(cid)
            if not df_review.empty:
                df_review["기업명"] = name
                df_review["분야"] = info.get("category", "")
                all_reviews.append(df_review)
            print("  연봉 정보 수집 중...")
            df_salary = self.crawl_company_salary(cid)
            if not df_salary.empty:
                df_salary["기업명"] = name
                all_salary.append(df_salary)
            print("  면접 후기 수집 중...")
            df_interview = self.crawl_interview_reviews(cid)
            if not df_interview.empty:
                df_interview["기업명"] = name
                df_interview["분야"] = info.get("category", "")
                all_interviews.append(df_interview)
            print(f"  완료")
            random_delay(3, 6)
        return all_company_data, all_reviews, all_salary, all_interviews

    def _save_results(self, all_company_data, all_reviews, all_salary, all_interviews, file_suffix="마케팅"):
        if all_company_data:
            self.save_data(pd.DataFrame(all_company_data), f"잡플래닛_기업정보_{file_suffix}")
        if all_reviews:
            self.save_data(pd.concat(all_reviews, ignore_index=True), f"잡플래닛_리뷰_{file_suffix}")
        if all_salary:
            self.save_data(pd.concat(all_salary, ignore_index=True), f"잡플래닛_연봉_{file_suffix}")
        if all_interviews:
            self.save_data(pd.concat(all_interviews, ignore_index=True), f"잡플래닛_면접후기_{file_suffix}")
        self._save_url_list()
        print(f"\n잡플래닛 크롤링 완료!")
        print(f"  기업정보: {len(all_company_data)}건")
        print(f"  리뷰: {sum(len(df) for df in all_reviews)}건")
        print(f"  면접후기: {sum(len(df) for df in all_interviews)}건")

    def run_all(self, extra_companies=None):
        companies = self._build_company_list(extra_companies, include_target=True)
        print("=" * 60)
        print("잡플래닛 크롤링 시작")
        print(f"수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"대상 기업: {len(companies)}개")
        print("=" * 60)
        if not self.login():
            print("  로그인 실패 - 로그인 없이 크롤링을 시도합니다.")
        results = self._crawl_companies(companies)
        self._save_results(*results)

    def run_custom(self, companies, file_suffix="마케팅_추가"):
        company_list = self._build_company_list(companies, include_target=False)
        if not company_list:
            print("크롤링할 기업이 없습니다.")
            return
        print("=" * 60)
        print("잡플래닛 추가 기업 크롤링 시작")
        print(f"대상 기업: {len(company_list)}개")
        print("=" * 60)
        if not self.login():
            print("  로그인 실패 - 로그인 없이 크롤링을 시도합니다.")
        results = self._crawl_companies(company_list, file_suffix)
        self._save_results(*results, file_suffix=file_suffix)

    def run_single(self, company_name, company_id=None, category="추가_마케팅기업"):
        companies = {company_name: {"company_id": company_id, "category": category, "비고": "단일 기업 크롤링"}}
        self.run_custom(companies, file_suffix=f"마케팅_{company_name}")

    def close(self):
        if self.driver:
            self.driver.quit()
            print("브라우저 종료")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="잡플래닛 마케팅 기업 크롤러")
    parser.add_argument("--mode", choices=["all", "custom", "single"], default="all")
    parser.add_argument("--extra", nargs="+")
    parser.add_argument("--company", type=str)
    parser.add_argument("--company-id", type=str)
    parser.add_argument("--suffix", type=str, default="마케팅_추가")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    crawler = JobPlanetCrawler(headless=args.headless)
    try:
        if args.mode == "all":
            crawler.run_all(extra_companies=args.extra)
        elif args.mode == "custom":
            if not args.extra:
                print("--extra 옵션으로 기업명을 지정해주세요.")
            else:
                crawler.run_custom(args.extra, file_suffix=args.suffix)
        elif args.mode == "single":
            if not args.company:
                print("--company 옵션으로 기업명을 지정해주세요.")
            else:
                crawler.run_single(args.company, company_id=args.company_id)
    finally:
        crawler.close()
