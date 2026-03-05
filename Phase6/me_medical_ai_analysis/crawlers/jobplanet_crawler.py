"""
=============================================================
잡플래닛 크롤러 - 의료 AI 기업 리뷰/연봉/면접후기 크롤링
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
    JOBPLANET_USER_ID,
    JOBPLANET_PASSWORD,
    TARGET_COMPANIES,
    DATA_RAW_DIR,
    URL_LIST_DIR,
    USER_AGENT,
    random_delay,
)


class JobPlanetCrawler:
    """잡플래닛 기업 리뷰/연봉/면접후기 크롤러"""

    BASE_URL = "https://www.jobplanet.co.kr"
    LOGIN_URL = "https://www.jobplanet.co.kr/users/sign_in"

    def __init__(self, driver_path=None, headless=False):
        self.driver = self._create_driver(headless)
        self.collected_urls = []

    def _create_driver(self, headless=False):
        """Chrome WebDriver 생성"""
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
        """URL 이동 후 BeautifulSoup 객체 반환"""
        self.driver.get(url)
        time.sleep(wait)
        return BeautifulSoup(self.driver.page_source, "html.parser")

    @staticmethod
    def _safe_text(element):
        """element가 None이어도 안전하게 텍스트 반환"""
        return element.get_text(strip=True) if element else ""

    @staticmethod
    def _try_selectors(soup_or_tag, selectors):
        """여러 CSS 셀렉터를 순서대로 시도"""
        for sel in selectors:
            el = soup_or_tag.select_one(sel)
            if el:
                return el
        return None

    def login(self) -> bool:
        """잡플래닛 로그인 (JavaScript 기반)"""
        print("🔐 잡플래닛 로그인 시도...")
        self.driver.get(self.LOGIN_URL)
        time.sleep(4)

        try:
            # 이메일 입력 (여러 셀렉터 시도)
            email_selectors = [
                "input[type='email']",
                "input[name='user[email]']",
                "input#user_email",
                "input[placeholder*='이메일']",
            ]
            email_filled = False
            for sel in email_selectors:
                try:
                    el = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                    )
                    self.driver.execute_script(
                        "arguments[0].value = arguments[1]; "
                        "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); "
                        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        el, JOBPLANET_USER_ID,
                    )
                    email_filled = True
                    break
                except Exception:
                    continue

            if not email_filled:
                print("  ❌ 이메일 입력란을 찾을 수 없음")
                return False

            time.sleep(0.5)

            # 비밀번호 입력
            pw_selectors = [
                "input[type='password']",
                "input[name='user[password]']",
            ]
            pw_filled = False
            for sel in pw_selectors:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    self.driver.execute_script(
                        "arguments[0].value = arguments[1]; "
                        "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); "
                        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        el, JOBPLANET_PASSWORD,
                    )
                    pw_filled = True
                    break
                except Exception:
                    continue

            if not pw_filled:
                print("  ❌ 비밀번호 입력란을 찾을 수 없음")
                return False

            time.sleep(0.5)

            # 로그인 버튼 클릭 (JavaScript)
            btn_selectors = [
                "button[type='submit']",
                ".btn_sign_in",
                "input[type='submit']",
                "button.btn_sign_up",
            ]
            for sel in btn_selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                    self.driver.execute_script("arguments[0].click();", btn)
                    break
                except Exception:
                    continue

            time.sleep(5)

            if "sign_in" not in self.driver.current_url:
                print("  ✅ 로그인 성공!")
                return True
            else:
                print("  ⚠️ 로그인 실패 - CAPTCHA 또는 인증 필요")
                return False

        except TimeoutException:
            print("  ❌ 로그인 페이지 로딩 실패")
            return False

    def _search_company(self, company_name: str) -> str:
        """기업명으로 검색하여 company_id 반환 (ul.grid 내 실제 검색 결과만 사용)"""
        # 괄호 내용 제거 (예: "네이버클라우드(의료)" → "네이버클라우드")
        search_name = re.sub(r'[（(].*?[）)]', '', company_name).strip()

        # 여러 검색어 시도 (원본, AI→에이아이 치환)
        search_variants = [search_name]
        if "AI" in search_name:
            search_variants.append(search_name.replace("AI", "에이아이"))
            search_variants.append(search_name.replace("AI", "").strip())

        for query in search_variants:
            search_url = f"{self.BASE_URL}/search?query={urllib.parse.quote(query)}"
            self.driver.get(search_url)

            # 검색 결과 그리드 로딩 대기
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "ul.grid a[href*='/companies/']")
                    )
                )
            except TimeoutException:
                continue
            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            # 실제 검색 결과는 ul.grid 내부에만 있음 (사이드바/광고 제외)
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

                # 기업명 매칭 (검색어가 텍스트에 포함)
                if query in text or search_name in text:
                    print(f"    → 매칭: [{cid}] {text[:40]}")
                    return cid

        print(f"    ⚠️ '{company_name}' 검색 결과 매칭 실패")
        return None

    def crawl_company_info(self, company_id: str) -> dict:
        """기업 기본 정보 크롤링"""
        url = f"{self.BASE_URL}/companies/{company_id}"
        soup = self._get_soup(url)
        info = {}

        try:
            el = self._try_selectors(soup, [
                ".rate_point .num", ".company_rating .num", ".total_rating",
            ])
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

            for section in soup.select(
                ".rating_item, .score_item, .company_grade_item, .chart_item"
            ):
                label_el = self._try_selectors(section, [".rating_label", ".item_name", "dt", ".name"])
                value_el = self._try_selectors(section, [".rating_value", ".item_value", "dd", ".num"])
                if label_el and value_el:
                    label, value = self._safe_text(label_el), self._safe_text(value_el)
                    if label and value:
                        info[f"평점_{label}"] = value

        except Exception as e:
            info["크롤링_오류"] = str(e)

        self.collected_urls.append({
            "번호": len(self.collected_urls) + 1,
            "URL": url, "소스": "잡플래닛", "검색키워드": info.get("기업명_잡플래닛", ""),
            "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "데이터유형": "기업정보", "비고": "",
        })

        return info

    def crawl_company_reviews(self, company_id: str, max_pages: int = 3) -> pd.DataFrame:
        """기업 리뷰 크롤링 (React/Tailwind 신규 레이아웃 대응)"""
        reviews = []

        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/companies/{company_id}/reviews?page={page}"
            soup = self._get_soup(url, wait=3)

            page_reviews = []

            # 리뷰 카드 탐색: 헤더에 "전직원"/"현직원" 포함된 div 찾기
            for header in soup.find_all("div", class_=lambda c: c and "relative" in c
                                        and "flex" in c and "items-center" in c
                                        and "justify-between" in c):
                text = header.get_text(strip=True)
                if "전직원" not in text and "현직원" not in text:
                    continue

                card = header.parent
                if not card:
                    continue

                review = {}

                # 직종, 재직상태, 위치, 날짜 추출 (span.text-body2 요소들)
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

                # 별점 (block 스타일 div 내 숫자)
                rating_div = card.select_one("div.block div.mb-\\[32px\\], div[class*='mb-[32px]']")
                if rating_div:
                    nums = re.findall(r"[\d.]+", self._safe_text(rating_div))
                    if nums:
                        review["별점"] = nums[0]

                # 리뷰 내용은 멤버십 벽 뒤에 있어 수집 제한
                # 블러되지 않은 일부 텍스트 시도
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
        """연봉 정보 크롤링"""
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
            "번호": len(self.collected_urls) + 1,
            "URL": url, "소스": "잡플래닛", "검색키워드": "",
            "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "데이터유형": "연봉", "비고": "",
        })

        return pd.DataFrame([salary_info]) if salary_info else pd.DataFrame()

    def crawl_interview_reviews(self, company_id: str, max_pages: int = 2) -> pd.DataFrame:
        """면접 후기 크롤링 (content_ty4 레거시 레이아웃 대응)"""
        interviews = []

        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/companies/{company_id}/interviews?page={page}"
            soup = self._get_soup(url, wait=3)

            # 면접 카드: section.content_ty4 (레거시 레이아웃)
            items = soup.select("section.content_ty4")
            if not items:
                break

            for item in items:
                interview = {}

                # 지원직무 + 직급 (.content_top_ty2 .txt1)
                el = item.select_one(".content_top_ty2 .txt1")
                if el:
                    txt = self._safe_text(el)
                    # "금융/재무 / 주임/계장|2026. 02. 03" 에서 분리
                    parts = txt.split("|")
                    if parts:
                        # 내부 공백/줄바꿈 정리
                        interview["지원직무"] = re.sub(r'\s+', ' ', parts[0]).strip()

                # 등록일 (.content_top_ty2 .txt2)
                el = item.select_one(".content_top_ty2 .txt2")
                if el:
                    interview["등록일"] = self._safe_text(el)

                # dt/dd 쌍에서 면접난이도, 면접일자, 면접경로 추출
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

                # 면접경험 (멤버십 벽 뒤이므로 제한적)
                body = item.select_one(".content_body_ty1")
                if body:
                    # 블라인드 커버가 없는 경우만 수집
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
        """data/raw/ 폴더에 CSV 저장"""
        if df is None or df.empty:
            return
        path = os.path.join(DATA_RAW_DIR, f"{filename}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  💾 저장: {path} ({len(df)}건)")

    def _save_url_list(self):
        """URL 목록 저장"""
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

    def _build_company_list(self, extra_companies=None, include_target=True):
        """크롤링 대상 기업 목록 구성

        Args:
            extra_companies: 추가 기업. 다음 형태를 지원:
                - dict: TARGET_COMPANIES와 동일 형식
                    {"기업명": {"company_id": "123", "category": "...", "비고": "..."}}
                - list[str]: 기업명 리스트 (company_id는 자동 검색)
                    ["기업A", "기업B"]
                - list[dict]: 상세 정보 포함 리스트
                    [{"name": "기업A", "company_id": "123", "category": "추가기업"}]
            include_target: True면 TARGET_COMPANIES 포함, False면 추가 기업만

        Returns:
            dict: {기업명: {company_id, category, 비고}} 형식
        """
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
                    companies[item] = {
                        "company_id": None,
                        "category": "추가_의료기업",
                        "비고": "추가 크롤링 대상",
                    }
                elif isinstance(item, dict):
                    name = item.get("name", item.get("기업명", ""))
                    if not name:
                        continue
                    companies[name] = {
                        "company_id": item.get("company_id"),
                        "category": item.get("category", "추가_의료기업"),
                        "비고": item.get("비고", "추가 크롤링 대상"),
                    }

        return companies

    def _crawl_companies(self, companies: dict, file_suffix: str = "의료AI"):
        """기업 목록을 순회하며 크롤링 실행 (내부 공통 로직)

        Args:
            companies: {기업명: {company_id, category, 비고}} 형식
            file_suffix: 저장 파일명 접미사

        Returns:
            tuple: (all_company_data, all_reviews, all_salary, all_interviews)
        """
        all_company_data = []
        all_reviews = []
        all_salary = []
        all_interviews = []

        items = list(companies.items())
        for idx, (name, info) in enumerate(tqdm(items, desc="기업 크롤링"), 1):
            print(f"\n[{idx}/{len(items)}] {name} ({info.get('category', '')})")

            cid = info.get("company_id")
            if not cid:
                print(f"  → 잡플래닛에서 검색 중...")
                cid = self._search_company(name)
                if cid is None:
                    print(f"  ⚠️ 기업을 찾을 수 없음 - 건너뜀")
                    continue
                print(f"  → 검색 결과 ID: {cid}")

            # 기업 정보
            print("  📋 기업 정보 수집 중...")
            company_info = self.crawl_company_info(cid)
            company_info["기업명"] = name
            company_info["분야"] = info.get("category", "")
            all_company_data.append(company_info)

            # 리뷰
            print("  💬 리뷰 수집 중...")
            df_review = self.crawl_company_reviews(cid)
            if not df_review.empty:
                df_review["기업명"] = name
                df_review["분야"] = info.get("category", "")
                all_reviews.append(df_review)

            # 연봉
            print("  💰 연봉 정보 수집 중...")
            df_salary = self.crawl_company_salary(cid)
            if not df_salary.empty:
                df_salary["기업명"] = name
                all_salary.append(df_salary)

            # 면접 후기
            print("  🎤 면접 후기 수집 중...")
            df_interview = self.crawl_interview_reviews(cid)
            if not df_interview.empty:
                df_interview["기업명"] = name
                df_interview["분야"] = info.get("category", "")
                all_interviews.append(df_interview)

            print(f"  ✅ 완료")
            random_delay(3, 6)

        return all_company_data, all_reviews, all_salary, all_interviews

    def _save_results(self, all_company_data, all_reviews, all_salary, all_interviews,
                      file_suffix="의료AI"):
        """크롤링 결과 저장"""
        if all_company_data:
            self.save_data(pd.DataFrame(all_company_data), f"잡플래닛_기업정보_{file_suffix}")
        if all_reviews:
            self.save_data(pd.concat(all_reviews, ignore_index=True), f"잡플래닛_리뷰_{file_suffix}")
        if all_salary:
            self.save_data(pd.concat(all_salary, ignore_index=True), f"잡플래닛_연봉_{file_suffix}")
        if all_interviews:
            self.save_data(pd.concat(all_interviews, ignore_index=True), f"잡플래닛_면접후기_{file_suffix}")

        self._save_url_list()

        print(f"\n🎉 잡플래닛 크롤링 완료!")
        print(f"  기업정보: {len(all_company_data)}건")
        print(f"  리뷰: {sum(len(df) for df in all_reviews)}건")
        print(f"  면접후기: {sum(len(df) for df in all_interviews)}건")

    def run_all(self, extra_companies=None):
        """TARGET_COMPANIES + 추가 기업을 순회하며 크롤링 실행

        Args:
            extra_companies: 추가 기업 (선택). 다음 형태를 지원:
                - dict: {"기업명": {"company_id": "123", "category": "...", "비고": "..."}}
                - list[str]: ["기업A", "기업B"] (company_id 자동 검색)
                - list[dict]: [{"name": "기업A", "company_id": "123"}]

        사용 예시:
            # 기본 12개 기업만
            crawler.run_all()

            # 기본 12개 + 추가 기업 (이름만, 자동 검색)
            crawler.run_all(extra_companies=["삼성서울병원", "서울아산병원"])

            # 기본 12개 + 추가 기업 (company_id 직접 지정)
            crawler.run_all(extra_companies={
                "삼성서울병원": {"company_id": "12345", "category": "대형병원", "비고": "의료AI 도입"},
            })
        """
        companies = self._build_company_list(extra_companies, include_target=True)

        print("=" * 60)
        print("🏢 잡플래닛 크롤링 시작")
        print(f"📅 수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏢 대상 기업: {len(companies)}개 (기본 {len(TARGET_COMPANIES)}개"
              f" + 추가 {len(companies) - len(TARGET_COMPANIES)}개)")
        print("=" * 60)

        if not self.login():
            print("  ⚠️ 로그인 실패 - 로그인 없이 크롤링을 시도합니다.")
            print("  💡 일부 데이터가 제한될 수 있습니다.")

        results = self._crawl_companies(companies)
        self._save_results(*results)

    def run_custom(self, companies, file_suffix="의료AI_추가"):
        """지정한 기업만 크롤링 (TARGET_COMPANIES 제외)

        Args:
            companies: 크롤링할 기업. 다음 형태를 지원:
                - dict: {"기업명": {"company_id": "123", "category": "...", "비고": "..."}}
                - list[str]: ["기업A", "기업B"] (company_id 자동 검색)
                - list[dict]: [{"name": "기업A", "company_id": "123"}]
            file_suffix: 저장 파일명 접미사

        사용 예시:
            # 이름만으로 크롤링 (잡플래닛에서 자동 검색)
            crawler.run_custom(["삼성서울병원", "서울아산병원", "세브란스병원"])

            # company_id 직접 지정
            crawler.run_custom({
                "삼성서울병원": {"company_id": "12345", "category": "대형병원", "비고": ""},
                "에이치디정션": {"company_id": "67890", "category": "스타트업_의료AI", "비고": ""},
            })
        """
        company_list = self._build_company_list(companies, include_target=False)

        if not company_list:
            print("⚠️ 크롤링할 기업이 없습니다.")
            return

        print("=" * 60)
        print("🏢 잡플래닛 추가 기업 크롤링 시작")
        print(f"📅 수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏢 대상 기업: {len(company_list)}개")
        for name in company_list:
            cid = company_list[name].get("company_id") or "자동검색"
            print(f"   - {name} (ID: {cid})")
        print("=" * 60)

        if not self.login():
            print("  ⚠️ 로그인 실패 - 로그인 없이 크롤링을 시도합니다.")

        results = self._crawl_companies(company_list, file_suffix)
        self._save_results(*results, file_suffix=file_suffix)

    def run_single(self, company_name, company_id=None, category="추가_의료기업"):
        """단일 기업 크롤링

        Args:
            company_name: 기업명
            company_id: 잡플래닛 company_id (없으면 자동 검색)
            category: 기업 카테고리

        사용 예시:
            crawler.run_single("삼성서울병원")
            crawler.run_single("에이치디정션", company_id="67890")
        """
        companies = {
            company_name: {
                "company_id": company_id,
                "category": category,
                "비고": "단일 기업 크롤링",
            }
        }
        self.run_custom(companies, file_suffix=f"의료AI_{company_name}")

    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            print("🔒 브라우저 종료")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="잡플래닛 의료 AI 기업 크롤러")
    parser.add_argument(
        "--mode", choices=["all", "custom", "single"], default="all",
        help="실행 모드: all(기본+추가), custom(추가만), single(단일 기업)",
    )
    parser.add_argument(
        "--extra", nargs="+",
        help="추가 기업명 리스트 (예: --extra 삼성서울병원 서울아산병원)",
    )
    parser.add_argument(
        "--company", type=str,
        help="단일 기업명 (--mode single 시 사용)",
    )
    parser.add_argument(
        "--company-id", type=str,
        help="단일 기업의 잡플래닛 company_id (선택, 없으면 자동 검색)",
    )
    parser.add_argument(
        "--suffix", type=str, default="의료AI_추가",
        help="저장 파일명 접미사 (--mode custom 시 사용)",
    )
    parser.add_argument("--headless", action="store_true", help="브라우저 숨김 모드")

    args = parser.parse_args()

    crawler = JobPlanetCrawler(headless=args.headless)
    try:
        if args.mode == "all":
            crawler.run_all(extra_companies=args.extra)
        elif args.mode == "custom":
            if not args.extra:
                print("⚠️ --extra 옵션으로 기업명을 지정해주세요.")
                print("예: python jobplanet_crawler.py --mode custom --extra 삼성서울병원 서울아산병원")
            else:
                crawler.run_custom(args.extra, file_suffix=args.suffix)
        elif args.mode == "single":
            if not args.company:
                print("⚠️ --company 옵션으로 기업명을 지정해주세요.")
                print("예: python jobplanet_crawler.py --mode single --company 삼성서울병원")
            else:
                crawler.run_single(args.company, company_id=args.company_id)
    finally:
        crawler.close()
