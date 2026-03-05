"""
=============================================================
📌 잡플래닛 크롤링 - 자율주행·의료 AI 기업 분석 (v2)
=============================================================
- Selenium을 활용한 잡플래닛 로그인 후 크롤링
- 수집 대상: 기업 리뷰, 연봉, 평점, 면접 후기
- 대상 기업: 자율주행·ADAS·의료 AI 관련 기업
=============================================================
⚠️ 실행 전 필요사항:
   pip install selenium beautifulsoup4 pandas
   Chrome 브라우저 설치 (selenium 4.6+ 자동 드라이버 지원)
=============================================================
변경사항 (v2):
  - 잡플래닛 URL에서 company_id를 직접 활용하여 안정적 접근
  - 대구·경북 자율주행 부품 기업 5개 추가
    (아진산업, 에스엘, 삼보모터스, 대동, 평화발레오)
  - 검색 기반 → ID 기반 직접 접근으로 크롤링 안정성 향상
  - 리뷰/연봉/면접 페이지 CSS 셀렉터 다중화
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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)

# ============================================================
# 1. 설정
# ============================================================
USER_ID = "catlife0202@kmu.kr"
PASSWD = "hellcat9021@"

LOGIN_URL = "https://www.jobplanet.co.kr/users/sign_in"
BASE_URL = "https://www.jobplanet.co.kr"

SAVE_DIR = "data_jobplanet"
os.makedirs(SAVE_DIR, exist_ok=True)


# ============================================================
# 2. 크롤링 대상 기업 목록
# ============================================================
# ── 잡플래닛 URL 패턴 ──
#   리뷰:   /companies/{id}/reviews/{name}
#   연봉:   /companies/{id}/salaries/{name}
#   면접:   /companies/{id}/interviews/{name}
#   기업정보: /companies/{id}/landing/{name}
#
# company_id가 있으면 → 검색 없이 직접 접근 (안정적)
# company_id가 None이면 → 기업명 검색 후 접근 (기존 방식)
# ──────────────────────────────────────────

# ═══════════════════════════════════════
# 그룹 A: 대구·경북 자율주행 부품 기업
#   (잡플래닛 URL 제공, company_id 확정)
# ═══════════════════════════════════════
DAEGU_AUTO_COMPANIES = [
    {
        "name": "아진산업",
        "company_id": "22086",
        "url_name": "%EC%95%84%EC%A7%84%EC%82%B0%EC%97%85",
        "분야": "자율주행부품",
        "비고": "현대차 1차 협력사, AVM/블랙박스 전장 IT부품",
    },
    {
        "name": "에스엘(SL)",
        "company_id": "20826",
        "url_name": "%EC%97%90%EC%8A%A4%EC%97%98",
        "분야": "자율주행부품",
        "비고": "글로벌 자동차 조명 TOP5, LiDAR/Camera 센서퓨전 ADAS",
    },
    {
        "name": "삼보모터스",
        "company_id": "30332",
        "url_name": "%EC%82%BC%EB%B3%B4%EB%AA%A8%ED%84%B0%EC%8A%A4",
        "분야": "자율주행부품",
        "비고": "자동변속기 부품, 전기차 부품(테슬라 납품), 자율주행 협업",
    },
    {
        "name": "대동",
        "company_id": "40446",
        "url_name": "%EB%8C%80%EB%8F%99",
        "분야": "자율주행부품",
        "비고": "농기계 + 자율주행 농기계/스마트팜",
    },
    {
        "name": "평화발레오",
        "company_id": "50192",
        "url_name": "%ED%8F%89%ED%99%94%EB%B0%9C%EB%A0%88%EC%98%A4",
        "분야": "자율주행부품",
        "비고": "Valeo JV, ADAS 센서·전장, 자율주행 모빌리티 협업",
    },
]

# ═══════════════════════════════════════
# 그룹 B: 자율주행 SW/AI 기업
# ═══════════════════════════════════════
AUTONOMOUS_COMPANIES = [
    {
        "name": "현대모비스",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "ADAS/자율주행 모듈 개발",
    },
    {
        "name": "현대오토에버",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "커넥티드카 SW, 차량 인포테인먼트",
    },
    {
        "name": "네이버랩스",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "자율주행/로보틱스/HD맵",
    },
    {
        "name": "카카오모빌리티",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "모빌리티 플랫폼, 자율주행 서비스",
    },
    {
        "name": "모라이",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "자율주행 시뮬레이션",
    },
    {
        "name": "오토노머스에이투지",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "자율주행 Level4, 대구 자율주행 협업 총괄",
    },
    {
        "name": "포티투닷",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "현대차그룹 자율주행 PBV",
    },
    {
        "name": "만도",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "ADAS/자율주행 제어기",
    },
    {
        "name": "HL클레무브",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "전동 조향·제동, ADAS 액추에이터",
    },
    {
        "name": "서울로보틱스",
        "company_id": None,
        "url_name": None,
        "분야": "자율주행",
        "비고": "LiDAR 인식 소프트웨어",
    },
]

# ═══════════════════════════════════════
# 그룹 C: 의료 AI 기업
# ═══════════════════════════════════════
MEDICAL_AI_COMPANIES = [
    {
        "name": "뷰노",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "의료영상 AI 진단",
    },
    {
        "name": "루닛",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "흉부 X-ray AI",
    },
    {
        "name": "딥노이드",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "의료영상 딥러닝",
    },
    {
        "name": "메디컬에이아이",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "심전도 AI 분석",
    },
    {
        "name": "셀바스AI",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "음성인식/필기인식 AI + 헬스케어",
    },
    {
        "name": "제이엘케이",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "뇌졸중 AI 진단",
    },
    {
        "name": "인피니트헬스케어",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "PACS/의료정보 시스템",
    },
    {
        "name": "카카오헬스케어",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "디지털 헬스케어 플랫폼",
    },
    {
        "name": "라인웍스",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "의료 자연어처리",
    },
    {
        "name": "솔트룩스",
        "company_id": None,
        "url_name": None,
        "분야": "의료AI",
        "비고": "AI 플랫폼(의료/산업 적용)",
    },
]

# 전체 기업 목록 통합
ALL_COMPANIES = DAEGU_AUTO_COMPANIES + AUTONOMOUS_COMPANIES + MEDICAL_AI_COMPANIES


# ============================================================
# 3. Selenium 드라이버 설정
# ============================================================
def create_driver(headless=False):
    """
    Chrome WebDriver 생성

    Parameters:
        headless (bool): True면 화면 없이 실행 (CAPTCHA 시 False로 변경)
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    # navigator.webdriver 속성 제거 (자동화 탐지 우회)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        },
    )
    return driver


# ============================================================
# 4. 잡플래닛 로그인
# ============================================================
def login_jobplanet(driver):
    """잡플래닛 로그인 (이메일 + 비밀번호)"""
    print("🔐 잡플래닛 로그인 시도...")
    driver.get(LOGIN_URL)
    time.sleep(3)

    try:
        # 이메일 입력
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "input[type='email'], input[name='user[email]'], "
                    "input#user_email, input[placeholder*='이메일']",
                )
            )
        )
        email_input.clear()
        for ch in USER_ID:
            email_input.send_keys(ch)
            time.sleep(0.05)
        time.sleep(0.5)

        # 비밀번호 입력
        pw_input = driver.find_element(
            By.CSS_SELECTOR,
            "input[type='password'], input[name='user[password]'], "
            "input#user_password, input[placeholder*='비밀번호']",
        )
        pw_input.clear()
        for ch in PASSWD:
            pw_input.send_keys(ch)
            time.sleep(0.05)
        time.sleep(0.5)

        # 로그인 버튼 클릭
        login_btn = driver.find_element(
            By.CSS_SELECTOR,
            "button[type='submit'], .btn_sign_in, .login-btn, "
            "button.btn.signin_btn, input[type='submit']",
        )
        login_btn.click()
        time.sleep(4)

        # 로그인 성공 확인
        if "sign_in" not in driver.current_url:
            print("  ✅ 로그인 성공!")
            return True
        else:
            print("  ⚠️ 로그인 실패 - CAPTCHA 확인 필요")
            return False

    except TimeoutException:
        print("  ❌ 로그인 페이지 로딩 실패")
        return False
    except Exception as e:
        print(f"  ❌ 로그인 중 오류: {e}")
        return False


# ============================================================
# 5. 기업 검색 (company_id가 없는 기업용)
# ============================================================
def search_company(driver, company_name):
    """
    잡플래닛에서 기업을 검색하고 company_id를 반환
    (company_id가 미리 지정되지 않은 기업에만 사용)
    """
    search_url = f"{BASE_URL}/search?query={urllib.parse.quote(company_name)}"
    driver.get(search_url)
    time.sleep(2)

    try:
        company_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/companies/']")
        for link in company_links:
            href = link.get_attribute("href") or ""
            match = re.search(r"/companies/(\d+)", href)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"    검색 오류: {e}")
        return None


# ============================================================
# 6. 헬퍼 함수
# ============================================================
def get_soup(driver, url, wait=2):
    """URL 이동 후 BeautifulSoup 객체 반환"""
    driver.get(url)
    time.sleep(wait)
    return BeautifulSoup(driver.page_source, "html.parser")


def safe_text(element):
    """element가 None이어도 안전하게 텍스트 반환"""
    return element.get_text(strip=True) if element else ""


def try_selectors(soup_or_tag, selectors):
    """여러 CSS 셀렉터를 순서대로 시도, 첫 매칭 결과 반환"""
    for sel in selectors:
        el = soup_or_tag.select_one(sel)
        if el:
            return el
    return None


# ============================================================
# 7. 기업 기본 정보 크롤링
# ============================================================
def crawl_company_info(driver, company_id):
    """기업 기본 정보 (평점, 추천율, 산업, 사원수 등)"""
    url = f"{BASE_URL}/companies/{company_id}"
    soup = get_soup(driver, url)
    info = {}

    try:
        # 전체 평점
        el = try_selectors(
            soup,
            [
                ".rate_point .num",
                ".company_rating .num",
                ".total_rating",
                "[class*='rating'] .num",
                ".rate_point",
            ],
        )
        if el:
            nums = re.findall(r"[\d.]+", safe_text(el))
            if nums:
                info["전체평점"] = nums[0]

        # 기업명
        el = try_selectors(
            soup,
            [
                "h1.name",
                "h1.company_name",
                ".company-header h1",
                "h1",
            ],
        )
        if el:
            info["기업명_잡플래닛"] = safe_text(el)

        # dt/dd 쌍으로 기업 상세 정보
        for dt in soup.select("dt"):
            dd = dt.find_next_sibling("dd")
            if dd:
                key, val = safe_text(dt), safe_text(dd)
                if key and val:
                    info[key] = val

        # 세부 평점 항목
        for section in soup.select(
            ".rating_item, .score_item, [class*='sub_rating'], "
            ".company_grade_item, .chart_item"
        ):
            label_el = try_selectors(
                section, [".rating_label", ".item_name", "dt", ".name", ".tit"]
            )
            value_el = try_selectors(
                section, [".rating_value", ".item_value", "dd", ".star_score", ".num"]
            )
            if label_el and value_el:
                label, value = safe_text(label_el), safe_text(value_el)
                if label and value:
                    info[f"평점_{label}"] = value

    except Exception as e:
        info["크롤링_오류"] = str(e)

    return info


# ============================================================
# 8. 리뷰 크롤링
# ============================================================
def crawl_reviews(driver, company_id, url_name=None, max_pages=3):
    """
    기업 리뷰 크롤링 (최대 max_pages 페이지)
    수집: 직종, 재직상태, 별점, 한줄평, 장점, 단점, 경영진에 바라는 점
    """
    reviews = []

    for page in range(1, max_pages + 1):
        if url_name:
            url = f"{BASE_URL}/companies/{company_id}/reviews/{url_name}?page={page}"
        else:
            url = f"{BASE_URL}/companies/{company_id}/reviews?page={page}"

        soup = get_soup(driver, url, wait=2.5)

        # 리뷰 컨테이너
        review_items = soup.select(
            "section.content_wrap, "
            "article[class*='ReviewCard'], "
            "div[class*='review_item'], "
            "div[class*='content_body'], "
            "li[class*='review-card']"
        )

        if not review_items:
            break

        for item in review_items:
            review = {}

            # 직종 / 재직상태
            el = try_selectors(
                item,
                [
                    ".content_top_ty2 span",
                    ".reviewer_info",
                    "[class*='status']",
                    ".user_info span",
                    ".content_top span",
                ],
            )
            if el:
                review["직종_재직상태"] = safe_text(el)

            # 한줄평
            el = try_selectors(
                item,
                [
                    ".content_top_ty2 h2",
                    ".summary_title",
                    "h2.title",
                    ".review_summary",
                    "[class*='title']",
                ],
            )
            if el:
                review["한줄평"] = safe_text(el)

            # 별점
            el = try_selectors(
                item,
                [
                    ".star_score",
                    ".rating",
                    "[class*='star'] .num",
                    ".rate_point .num",
                ],
            )
            if el:
                nums = re.findall(r"[\d.]+", safe_text(el))
                if nums:
                    review["별점"] = nums[0]

            # 장점
            el = try_selectors(item, [".pro", "[class*='pros']", ".merit", "div.pro"])
            if el:
                txt = re.sub(r"^장점\s*", "", safe_text(el))
                if txt:
                    review["장점"] = txt[:500]

            # 단점
            el = try_selectors(item, [".con", "[class*='cons']", ".demerit", "div.con"])
            if el:
                txt = re.sub(r"^단점\s*", "", safe_text(el))
                if txt:
                    review["단점"] = txt[:500]

            # 경영진에 바라는 점
            el = try_selectors(
                item,
                [".wish", "[class*='wish']", ".comment", ".etc_comment", "div.wish"],
            )
            if el:
                txt = re.sub(r"^경영진에게?\s*(바라는\s*점)?\s*", "", safe_text(el))
                if txt:
                    review["경영진에_바라는점"] = txt[:500]

            # 등록일
            el = try_selectors(
                item,
                [
                    ".content_top_ty2 .txt1",
                    ".review_date",
                    "[class*='date']",
                    "time",
                ],
            )
            if el:
                review["등록일"] = safe_text(el)

            if review:
                reviews.append(review)

        print(f"      리뷰 p{page}: {len(review_items)}건")

    return reviews


# ============================================================
# 9. 연봉 정보 크롤링
# ============================================================
def crawl_salary(driver, company_id, url_name=None):
    """기업 연봉 정보 크롤링"""
    if url_name:
        url = f"{BASE_URL}/companies/{company_id}/salaries/{url_name}"
    else:
        url = f"{BASE_URL}/companies/{company_id}/salaries"

    soup = get_soup(driver, url, wait=2.5)
    salary_info = {}

    try:
        el = try_selectors(
            soup,
            [
                ".avg_salary",
                ".salary_avg",
                "[class*='average']",
                ".total_salary .num",
                ".salary_info .num",
            ],
        )
        if el:
            salary_info["평균연봉"] = safe_text(el)

        rows = soup.select(
            ".salary_item, .salary_row, tr[class*='salary'], "
            ".chart_row, [class*='SalaryItem']"
        )
        details = []
        for row in rows:
            cols = row.select("td, .cell, span, div")
            texts = [safe_text(c) for c in cols if safe_text(c)]
            if len(texts) >= 2:
                details.append({"구분": texts[0], "연봉": texts[-1]})
        if details:
            salary_info["상세"] = details

    except Exception as e:
        salary_info["크롤링_오류"] = str(e)

    return salary_info


# ============================================================
# 10. 면접 후기 크롤링
# ============================================================
def crawl_interviews(driver, company_id, url_name=None, max_pages=2):
    """면접 후기 크롤링"""
    interviews = []

    for page in range(1, max_pages + 1):
        if url_name:
            url = f"{BASE_URL}/companies/{company_id}/interviews/{url_name}?page={page}"
        else:
            url = f"{BASE_URL}/companies/{company_id}/interviews?page={page}"

        soup = get_soup(driver, url, wait=2.5)

        items = soup.select(
            "section.content_wrap, "
            "article[class*='InterviewCard'], "
            "div[class*='interview_item'], "
            "li[class*='interview-card']"
        )

        if not items:
            break

        for item in items:
            interview = {}

            el = try_selectors(
                item,
                [".content_top_ty2 span", "[class*='position']", ".user_info span"],
            )
            if el:
                interview["지원직무"] = safe_text(el)

            el = try_selectors(item, [".difficulty", "[class*='difficulty']", ".level"])
            if el:
                interview["면접난이도"] = safe_text(el)

            el = try_selectors(item, [".result", "[class*='result']", ".pass_fail"])
            if el:
                interview["면접결과"] = safe_text(el)

            el = try_selectors(
                item,
                [
                    ".content_body_ty2",
                    ".interview_content",
                    "[class*='content'] p",
                ],
            )
            if el:
                interview["면접경험"] = safe_text(el)[:500]

            questions = item.select(
                ".question_item, [class*='question'] li, .etc_question li"
            )
            if questions:
                interview["면접질문"] = " | ".join([safe_text(q) for q in questions])[
                    :500
                ]

            if interview:
                interviews.append(interview)

        print(f"      면접후기 p{page}: {len(items)}건")

    return interviews


# ============================================================
# 11. 전체 크롤링 실행
# ============================================================
def crawl_all_companies(driver, companies):
    """전체 기업 목록 크롤링"""
    all_company_data = []
    all_reviews = []
    all_interviews = []
    all_urls = []

    print("=" * 60)
    print("🏢 잡플래닛 기업 크롤링 시작")
    print(f"   대상 기업 수: {len(companies)}개")
    print("=" * 60)

    for idx, company in enumerate(companies, 1):
        name = company["name"]
        cid = company.get("company_id")
        url_name = company.get("url_name")
        field = company["분야"]
        note = company.get("비고", "")

        print(f"\n[{idx}/{len(companies)}] {name} ({field})")

        # ── company_id 확보 ──
        if cid:
            print(f"  → ID 직접 사용: {cid}")
        else:
            print(f"  → 검색 중...")
            cid = search_company(driver, name)
            if cid is None:
                print(f"  ⚠️ 기업을 찾을 수 없음 - 건너뜀")
                continue
            print(f"  → 검색 결과 ID: {cid}")

        # ── URL 생성 ──
        base_company_url = f"{BASE_URL}/companies/{cid}"
        review_url = (
            f"{base_company_url}/reviews/{url_name}"
            if url_name
            else f"{base_company_url}/reviews"
        )
        salary_url = (
            f"{base_company_url}/salaries/{url_name}"
            if url_name
            else f"{base_company_url}/salaries"
        )
        interview_url = (
            f"{base_company_url}/interviews/{url_name}"
            if url_name
            else f"{base_company_url}/interviews"
        )

        all_urls.append(
            {"기업명": name, "분야": field, "URL": base_company_url, "유형": "기업정보"}
        )
        all_urls.append(
            {"기업명": name, "분야": field, "URL": review_url, "유형": "리뷰"}
        )
        all_urls.append(
            {"기업명": name, "분야": field, "URL": salary_url, "유형": "연봉"}
        )
        all_urls.append(
            {"기업명": name, "분야": field, "URL": interview_url, "유형": "면접후기"}
        )

        # ── 기업 기본 정보 ──
        print("  📋 기업 정보 수집 중...")
        info = crawl_company_info(driver, cid)
        info["기업명"] = name
        info["분야"] = field
        info["기업ID"] = cid
        info["기업URL"] = base_company_url
        info["비고"] = note

        # ── 리뷰 ──
        print("  💬 리뷰 수집 중...")
        reviews = crawl_reviews(driver, cid, url_name, max_pages=3)
        for r in reviews:
            r["기업명"] = name
            r["분야"] = field
        all_reviews.extend(reviews)

        # ── 연봉 ──
        print("  💰 연봉 정보 수집 중...")
        salary = crawl_salary(driver, cid, url_name)
        info["연봉정보"] = json.dumps(salary, ensure_ascii=False)

        # ── 면접 후기 ──
        print("  🎤 면접 후기 수집 중...")
        interviews = crawl_interviews(driver, cid, url_name, max_pages=2)
        for iv in interviews:
            iv["기업명"] = name
            iv["분야"] = field
        all_interviews.extend(interviews)

        all_company_data.append(info)

        print(f"  ✅ 완료 - 리뷰: {len(reviews)}건, 면접: {len(interviews)}건")
        time.sleep(3)

    return all_company_data, all_reviews, all_interviews, all_urls


# ============================================================
# 12. 데이터 저장
# ============================================================
def save_all_data(company_data, reviews, interviews, urls):
    """수집 데이터 전체 저장"""
    print()
    print("=" * 60)
    print("💾 데이터 저장")
    print("=" * 60)

    if company_data:
        df = pd.DataFrame(company_data)
        path = os.path.join(SAVE_DIR, "잡플래닛_기업정보_자율주행_의료AI.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  기업 정보: {path} ({len(df)}건)")

    if reviews:
        df = pd.DataFrame(reviews)
        path = os.path.join(SAVE_DIR, "잡플래닛_리뷰_자율주행_의료AI.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  리뷰:     {path} ({len(df)}건)")

    if interviews:
        df = pd.DataFrame(interviews)
        path = os.path.join(SAVE_DIR, "잡플래닛_면접후기_자율주행_의료AI.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  면접후기: {path} ({len(df)}건)")

    if urls:
        df = pd.DataFrame(urls)
        path = os.path.join(SAVE_DIR, "크롤링_URL_목록_잡플래닛.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"  URL 목록: {path} ({len(df)}건)")

    backup = {
        "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "기업정보": company_data,
        "리뷰": reviews,
        "면접후기": interviews,
    }
    json_path = os.path.join(SAVE_DIR, "잡플래닛_전체데이터_자율주행_의료AI.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(backup, f, ensure_ascii=False, indent=2)
    print(f"  JSON:     {json_path}")


# ============================================================
# 13. 메인 실행
# ============================================================
def main():
    print("🚀 잡플래닛 크롤링 시작 (v2)")
    print(f"📅 수집 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 저장 경로: {os.path.abspath(SAVE_DIR)}")
    print()

    # 기업 목록 요약
    field_counts = {}
    for c in ALL_COMPANIES:
        field_counts[c["분야"]] = field_counts.get(c["분야"], 0) + 1
    print("📊 기업 목록:")
    for f, cnt in field_counts.items():
        print(f"   {f}: {cnt}개")
    id_count = sum(1 for c in ALL_COMPANIES if c.get("company_id"))
    print(f"   ID 확정: {id_count}개 / 검색 필요: {len(ALL_COMPANIES) - id_count}개")
    print(
        f"   총 URL 생성 예상: {len(ALL_COMPANIES) * 4}개 (기업당 4개: 기업정보/리뷰/연봉/면접)"
    )
    print()

    driver = None
    try:
        # ── 드라이버 생성 ──
        # CAPTCHA가 뜨면 headless=False 상태에서 수동 처리
        driver = create_driver(headless=False)

        # ── 로그인 ──
        if not login_jobplanet(driver):
            print()
            print("   💡 CAPTCHA가 뜨면 브라우저에서 수동으로 완료해주세요.")
            input("   ▶ CAPTCHA 완료 후 Enter 키를 누르세요... ")
            if "sign_in" in driver.current_url:
                print("   ❌ 여전히 로그인되지 않았습니다. 종료합니다.")
                return

        # ── 크롤링 실행 ──
        company_data, reviews, interviews, urls = crawl_all_companies(
            driver, ALL_COMPANIES
        )

        # ── 저장 ──
        save_all_data(company_data, reviews, interviews, urls)

        # ── 결과 요약 ──
        print()
        print("=" * 60)
        print("📊 수집 결과 요약")
        print("=" * 60)
        print(f"  기업 정보: {len(company_data)}건")
        print(f"  리뷰:     {len(reviews)}건")
        print(f"  면접후기: {len(interviews)}건")
        print(f"  총 URL:   {len(urls)}건")

        field_stats = {}
        for c in company_data:
            f = c.get("분야", "기타")
            field_stats[f] = field_stats.get(f, 0) + 1
        print("\n  📋 분야별 수집 기업 수:")
        for f, cnt in field_stats.items():
            print(f"     {f}: {cnt}개")

        if len(urls) >= 100:
            print(f"\n  ✅ URL {len(urls)}개 확보 → 100개 요구사항 충족!")
        else:
            print(
                f"\n  ⚠️ URL {len(urls)}개 → Naver API 데이터와 합산하여 100개 충족 가능"
            )

        print("\n🎉 잡플래닛 크롤링 완료!")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if driver:
            driver.quit()
            print("🔒 브라우저 종료")


if __name__ == "__main__":
    main()
