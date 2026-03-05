# 02. crawlers 모듈 가이드

> 4개의 크롤러가 각각 다른 데이터 소스에서 데이터를 수집한다.
> `settings.py`의 키워드와 기업 목록을 참조하므로, 대부분 **파일명 접미사 변경**만으로 재사용 가능하다.

---

## 파일 구조

```
crawlers/
├── __init__.py              ← 4개 크롤러 import
├── naver_api_crawler.py     ← 네이버 OpenAPI (블로그 + 뉴스)
├── saramin_crawler.py       ← 사람인 (requests + BeautifulSoup)
├── wanted_crawler.py        ← 원티드 API v4 (REST API)
└── jobplanet_crawler.py     ← 잡플래닛 (Selenium + 로그인)
```

---

## 인증 정보 (현재 프로젝트에서 사용 중)

### 네이버 OpenAPI

```
Client ID     : F7QE6pmxq_MDivA5jrqq
Client Secret : 9OfednhamT
```

- 발급 위치: https://developers.naver.com → 애플리케이션 등록
- 하루 25,000건 호출 제한 → 동일 키 재사용 가능

### 잡플래닛 로그인

```
ID (이메일) : catlife0202@kmu.kr
Password    : hellcat9021@
```

- 잡플래닛은 로그인 없이 리뷰/면접후기 열람 불가
- Selenium으로 자동 로그인 후 크롤링 수행

---

## 1. naver_api_crawler.py

### 개요

| 항목 | 내용 |
|------|------|
| 수집 대상 | 네이버 블로그, 네이버 뉴스 |
| 수집 방식 | 네이버 OpenAPI (urllib) |
| 인증 | Client ID + Client Secret |
| 수집량 | 키워드당 최대 30건 |
| 분야 전환 난이도 | ★☆☆ (파일명 접미사만 변경) |

### 클래스 구조

```python
class NaverAPICrawler:
    def __init__(self, client_id=None, client_secret=None)

    # 단일 키워드 검색
    def search_blog(query, display=100, start=1, sort="sim") → DataFrame
    def search_news(query, display=100, start=1, sort="date") → DataFrame

    # 전체 키워드 일괄 검색 (중복 제거 포함)
    def search_all_keywords(keywords, search_type="blog", max_per_keyword=30) → DataFrame

    # 저장
    def save_data(df, filename) → None    # CSV + JSON 저장

    # 전체 실행
    def run_all() → (df_blog, df_news)
```

### 수집 필드

| 필드 | 블로그 | 뉴스 | 설명 |
|------|--------|------|------|
| title | O | O | 제목 (HTML 태그 제거됨) |
| description | O | O | 본문 요약 |
| link | O | O | 원문 URL |
| bloggername | O | - | 블로거 이름 |
| bloggerlink | O | - | 블로그 주소 |
| originallink | - | O | 뉴스 원문 URL |
| pubDate | O | O | 게시일 (YYYY-MM-DD 정규화) |
| 검색키워드 | O | O | 수집 시 사용한 키워드 |

### 분야 전환 시 수정 포인트

```python
# run_all() 메서드 내부의 파일명만 변경
def run_all(self):
    df_blog = self.search_all_keywords(NAVER_BLOG_KEYWORDS, "blog")
    self.save_data(df_blog, "naver_blog_의료AI")     # ← "naver_blog_{분야명}" 으로 변경

    df_news = self.search_all_keywords(NAVER_NEWS_KEYWORDS, "news")
    self.save_data(df_news, "naver_news_의료AI")     # ← "naver_news_{분야명}" 으로 변경
```

> 키워드는 settings.py의 `NAVER_BLOG_KEYWORDS`, `NAVER_NEWS_KEYWORDS`를 자동 참조하므로 크롤러 코드 자체는 수정 불필요.

---

## 2. saramin_crawler.py

### 개요

| 항목 | 내용 |
|------|------|
| 수집 대상 | 사람인 채용공고 |
| 수집 방식 | requests + BeautifulSoup (HTML 파싱) |
| 인증 | 불필요 (공개 웹페이지) |
| 수집량 | 키워드 × 5페이지 |
| 분야 전환 난이도 | ★☆☆ (파일명 접미사만 변경) |

### 클래스 구조

```python
class SaraminCrawler:
    def __init__(self)

    # 검색 → URL 목록 수집
    def search_jobs(keyword, pages=5) → list[str]

    # 개별 공고 상세 파싱
    def parse_job_detail(url) → dict

    # 텍스트에서 기술스택/자격증 추출
    def extract_tech_stack(text) → list[str]    # settings.TECH_STACK_KEYWORDS 사용
    def extract_certificates(text) → list[str]  # settings.CERTIFICATE_KEYWORDS 사용

    # 전체 크롤링
    def crawl_all(keywords=None) → DataFrame
    def save_data(df, filename) → None
    def run_all() → DataFrame
```

### 수집 필드

| 필드 | 설명 |
|------|------|
| 제목 | 채용공고 제목 |
| 회사명 | 기업명 |
| 지역 | 근무지 |
| 경력 | 경력 요건 |
| 학력 | 학력 요건 |
| 기술스택 | 추출된 기술 키워드 리스트 |
| 자격증 | 추출된 자격증 리스트 |
| URL | 공고 URL |
| 검색키워드 | 수집 시 사용한 키워드 |

### 분야 전환 시 수정 포인트

```python
# run_all() 내부의 파일명만 변경
self.save_data(df, "사람인_채용_의료AI")  # ← "사람인_채용_{분야명}" 으로 변경
```

> 기술스택/자격증 추출은 settings.py의 키워드 사전을 참조하므로 크롤러 코드 자체는 수정 불필요.

---

## 3. wanted_crawler.py

### 개요

| 항목 | 내용 |
|------|------|
| 수집 대상 | 원티드 채용 포지션 |
| 수집 방식 | 원티드 API v4 (requests, Selenium 아님) |
| 인증 | 불필요 (공개 API) |
| 수집량 | 카테고리 전체 포지션 |
| 분야 전환 난이도 | ★★☆ (카테고리 ID + 서브카테고리 맵 변경) |

### 클래스 구조

```python
class WantedCrawler:
    BASE_URL = "https://www.wanted.co.kr"
    CATEGORY_ID = 515              # ★ 의료/제약/바이오 → 변경 필요
    SUBCATEGORY_MAP = { ... }      # ★ 하위 카테고리 매핑 → 변경 필요

    def __init__(self, headless=True)

    # 2단계 수집: 목록 → 상세
    def fetch_job_listings(limit=20) → list[dict]
    def fetch_job_detail(job_id) → dict
    def parse_job_data(listing, detail) → dict

    # 전체 크롤링
    def crawl_all() → DataFrame
    def save_data(df, filename) → None
    def run_all() → DataFrame
    def close() → None
```

### 수집 필드

| 필드 | 설명 |
|------|------|
| position_id | 포지션 고유 ID |
| 회사명 | 기업명 |
| 포지션명 | 채용 포지션 제목 |
| 기술태그 | skill_tags (원티드 자체 태깅) |
| 카테고리 | 하위 카테고리 (SUBCATEGORY_MAP으로 매핑) |
| 경력요건 | 최소~최대 경력 |
| 지역 | 근무지 |
| 연봉범위 | 최소~최대 연봉 |
| 자격요건 | 자격요건 텍스트 |
| 우대사항 | 우대사항 텍스트 |

### 분야 전환 시 수정 포인트

```python
class WantedCrawler:
    # [필수 변경] 카테고리 ID
    # 현재: 515 (의료/제약/바이오)
    CATEGORY_ID = 515

    # 원티드 카테고리 ID 참고:
    #   507: 금융
    #   510: 교육
    #   518: 게임
    #   660: 모빌리티
    #   506: IT/웹/통신
    # 확인 방법: 원티드 웹에서 카테고리 선택 → 개발자도구 Network 탭 확인

    # [필수 변경] 하위 카테고리 매핑
    SUBCATEGORY_MAP = {
        10069: "의약품",
        10070: "의료기기",
        10071: "임상시험/CRO",
        10072: "바이오",
        10073: "동물약품",
        10074: "건강기능식품",
        10075: "화장품/뷰티",
        10076: "보건의료",
        # ... 등 → 분야에 맞게 재정의
    }
```

**카테고리 ID 확인 방법**:
1. 원티드 웹사이트 접속
2. 원하는 카테고리 클릭
3. 브라우저 개발자 도구(F12) → Network 탭
4. API 요청에서 `tag_type_ids` 파라미터 값 확인

---

## 4. jobplanet_crawler.py

### 개요

| 항목 | 내용 |
|------|------|
| 수집 대상 | 잡플래닛 기업정보, 리뷰, 면접후기 |
| 수집 방식 | Selenium + Chrome WebDriver (로그인 필수) |
| 인증 | **잡플래닛 계정 필수** |
| 수집량 | 기업당 리뷰 3페이지, 면접후기 2페이지 |
| 분야 전환 난이도 | ★☆☆ (settings의 기업 목록 자동 참조) |

### 로그인 정보

```
ID       : catlife0202@kmu.kr
Password : hellcat9021@
```

### 클래스 구조

```python
class JobPlanetCrawler:
    BASE_URL = "https://www.jobplanet.co.kr"
    LOGIN_URL = "https://www.jobplanet.co.kr/users/sign_in"

    def __init__(self, driver_path=None, headless=False)

    # 로그인
    def login() → bool

    # 기업별 크롤링
    def crawl_company_info(company_id) → dict           # 기업 개요, 평점
    def crawl_company_reviews(company_id, max_pages=3) → DataFrame  # 장단점 리뷰
    def crawl_company_salary(company_id) → DataFrame    # 연봉 정보
    def crawl_interview_reviews(company_id, max_pages=2) → DataFrame  # 면접 후기

    # 저장 및 실행
    def save_data(df, filename) → None
    def run_all() → None     # TARGET_COMPANIES 전체 순회
    def close() → None       # 브라우저 종료
```

### 수집 필드

**기업정보** (crawl_company_info):

| 필드 | 설명 |
|------|------|
| 기업명 | 회사명 |
| 평점 | 총 평점 (5점 만점) |
| 업종 | 업종 분류 |
| 규모 | 직원 수 |
| 설립연도 | 설립 연도 |
| 위치 | 본사 소재지 |

**기업리뷰** (crawl_company_reviews):

| 필드 | 설명 |
|------|------|
| 장점 | 리뷰 장점 텍스트 |
| 단점 | 리뷰 단점 텍스트 |
| 경영진평가 | 경영진에 대한 의견 |
| 재직상태 | 현직자/전직자 |
| 직종 | 직무 분류 |
| 평점 | 개별 리뷰 평점 |

**면접후기** (crawl_interview_reviews):

| 필드 | 설명 |
|------|------|
| 면접질문 | 실제 면접 질문 내용 |
| 난이도 | 면접 난이도 |
| 면접결과 | 합격/불합격/대기 |
| 경로 | 지원 경로 (직접지원, 헤드헌팅 등) |
| 직종 | 지원 직종 |

### 분야 전환 시 수정 포인트

```python
# run_all() 메서드가 settings.TARGET_COMPANIES를 자동 순회하므로
# settings.py의 기업 목록만 바꾸면 자동 적용!

# 파일명 접미사만 변경:
self.save_data(df, "잡플래닛_기업정보_의료AI")  # ← "잡플래닛_기업정보_{분야명}"
self.save_data(df, "잡플래닛_리뷰_의료AI")      # ← "잡플래닛_리뷰_{분야명}"
self.save_data(df, "잡플래닛_면접후기_의료AI")   # ← "잡플래닛_면접후기_{분야명}"
```

> 잡플래닛의 HTML 구조는 분야와 무관하게 동일하므로, CSS 선택자나 파싱 로직은 수정 불필요.

---

## 크롤러 전체 수정 체크리스트

- [ ] naver_api_crawler.py: 저장 파일명 접미사 변경 (`_의료AI` → `_{분야명}`)
- [ ] saramin_crawler.py: 저장 파일명 접미사 변경
- [ ] wanted_crawler.py: `CATEGORY_ID` 변경
- [ ] wanted_crawler.py: `SUBCATEGORY_MAP` 재정의
- [ ] wanted_crawler.py: 저장 파일명 접미사 변경
- [ ] jobplanet_crawler.py: 저장 파일명 접미사 변경

---

## 공통 기능: URL 수집 추적

모든 크롤러는 `self.collected_urls` 리스트에 수집한 URL을 기록하고, `_save_url_list()` 메서드로 `url_list/crawling_urls.csv`에 저장한다. 이 기능은 분야와 무관하게 동일하게 작동한다.
