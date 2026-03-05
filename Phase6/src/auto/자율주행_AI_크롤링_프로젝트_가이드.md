# 🚗 자율주행 AI 분야 — 크롤링 미니 프로젝트 Claude Code 가이드

> **목적**: 이 문서는 Claude Code를 활용하여 자율주행 AI 분야의 취업 동향 분석을 위한
> Python 크롤링·분석·시각화 파일을 자동 생성하기 위한 **상세 명세서**입니다.

---

## 📁 프로젝트 디렉토리 구조

```
autonomous_driving_analysis/
│
├── config/
│   └── settings.py              # API 키, 공통 설정값 관리
│
├── crawlers/
│   ├── __init__.py
│   ├── jobplanet_crawler.py     # 잡플래닛 크롤링 (기업 리뷰, 연봉, 면접후기)
│   ├── naver_api_crawler.py     # Naver OpenAPI 크롤링 (블로그/뉴스)
│   ├── saramin_crawler.py       # 사람인 채용공고 크롤링
│   └── wanted_crawler.py        # 원티드 기술스택 크롤링
│
├── processors/
│   ├── __init__.py
│   ├── data_cleaner.py          # 데이터 전처리 및 정제
│   ├── text_analyzer.py         # 텍스트 분석 (키워드 추출, 빈도 분석)
│   └── salary_analyzer.py       # 연봉 데이터 분석
│
├── visualizations/
│   ├── __init__.py
│   ├── wordcloud_viz.py         # 워드클라우드 시각화
│   ├── chart_viz.py             # 기본 차트 시각화 (바, 파이, 박스플롯 등)
│   ├── advanced_viz.py          # 고급 시각화 (히트맵, 레이더, 산키 등)
│   ├── interactive_viz.py       # 인터랙티브 시각화 (Plotly)
│   └── dashboard.py             # 종합 대시보드 생성
│
├── data/
│   ├── raw/                     # 크롤링 원본 데이터 (csv, json)
│   └── processed/               # 전처리 완료 데이터
│
├── outputs/
│   ├── charts/                  # 시각화 이미지 저장
│   └── reports/                 # 분석 리포트 저장
│
├── url_list/
│   └── crawling_urls.csv        # 크롤링 URL 목록 (최소 100개)
│
├── main.py                      # 전체 파이프라인 실행
├── requirements.txt             # 필요 패키지 목록
└── README.md                    # 프로젝트 설명
```

---

## 📦 requirements.txt

```
# 크롤링
requests>=2.31.0
beautifulsoup4>=4.12.0
selenium>=4.15.0
webdriver-manager>=4.0.0
fake-useragent>=1.4.0

# 데이터 처리
pandas>=2.1.0
numpy>=1.24.0

# 텍스트 분석
konlpy>=0.6.0
wordcloud>=1.9.0

# 시각화 - 기본
matplotlib>=3.8.0
seaborn>=0.13.0

# 시각화 - 고급/인터랙티브
plotly>=5.18.0
kaleido>=0.2.1

# 유틸리티
tqdm>=4.66.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
```

---

## 🔧 파일별 상세 명세

---

### 1. `config/settings.py`

**역할**: 프로젝트 전체에서 사용하는 설정값과 API 키를 중앙 관리

```python
"""
구현 요구사항:
- Naver OpenAPI 클라이언트 ID / Secret 변수 (.env 파일에서 로드)
- 크롤링 대상 기업 리스트 (딕셔너리 형태: 기업명 → 잡플래닛 URL, 사람인 검색 키워드)
- 크롤링 키워드 리스트
- 크롤링 딜레이 설정 (예: 2~5초 랜덤)
- 저장 경로 상수
- User-Agent 설정
"""
```

**포함할 데이터**:

```python
# 크롤링 대상 기업 리스트
TARGET_COMPANIES = {
    "현대모비스": {"jobplanet_id": "...", "category": "대기업_부품"},
    "네이버랩스": {"jobplanet_id": "...", "category": "IT_대기업"},
    "오토노머스에이투지": {"jobplanet_id": "...", "category": "스타트업"},
    "라이드플럭스": {"jobplanet_id": "...", "category": "스타트업"},
    "HL만도": {"jobplanet_id": "...", "category": "대기업_부품"},
    "현대오토에버": {"jobplanet_id": "...", "category": "대기업_IT"},
    "42dot": {"jobplanet_id": "...", "category": "스타트업"},
    "소네트": {"jobplanet_id": "...", "category": "스타트업"},
    "서울로보틱스": {"jobplanet_id": "...", "category": "스타트업"},
    "모라이": {"jobplanet_id": "...", "category": "스타트업"},
}

# Naver OpenAPI 검색 키워드
NAVER_KEYWORDS = [
    "자율주행 취업 준비",
    "자율주행 개발자 채용",
    "ADAS 엔지니어 취업",
    "자율주행 신입 채용",
    "ROS 개발자 취업",
    "자율주행 자격증",
    "자율주행 포트폴리오",
    "자율주행 인턴",
    "LiDAR 개발자",
    "컴퓨터비전 자율주행",
    "자율주행 경진대회",
    "SLAM 취업",
    "자율주행 교육과정",
    "자율주행 석사 취업",
    "자율주행 스타트업 채용",
]

# 사람인 검색 키워드
SARAMIN_KEYWORDS = [
    "자율주행",
    "자율주행 AI",
    "ADAS",
    "자율주행 Python",
    "자율주행 엔지니어",
    "자율주행 인지",
    "자율주행 판단",
    "자율주행 제어",
    "ROS 개발",
    "LiDAR",
    "자율주행 시뮬레이션",
]
```

---

### 2. `crawlers/jobplanet_crawler.py`

**역할**: 잡플래닛에서 자율주행 관련 기업의 리뷰, 연봉, 면접 후기 크롤링

```python
"""
구현 요구사항:

[클래스 구조]
class JobPlanetCrawler:
    def __init__(self, driver_path=None):
        - Selenium WebDriver 초기화 (Chrome headless)
        - 로그인 처리 (필요 시)

    def crawl_company_reviews(self, company_id: str) -> pd.DataFrame:
        - 기업 리뷰 페이지 크롤링
        - 수집 필드:
            - 리뷰 제목, 리뷰 내용 (장점/단점)
            - 총점, 승진기회, 워라밸, 급여, 사내문화, 경영진 점수
            - 작성일, 재직 상태(현직/전직), 직무
        - 페이지네이션 처리 (최소 3페이지)
        - DataFrame 반환

    def crawl_company_salary(self, company_id: str) -> pd.DataFrame:
        - 연봉 정보 크롤링
        - 수집 필드:
            - 직무, 연차, 연봉(만원), 성과급 여부
        - DataFrame 반환

    def crawl_interview_reviews(self, company_id: str) -> pd.DataFrame:
        - 면접 후기 크롤링
        - 수집 필드:
            - 면접 경험(긍정/보통/부정)
            - 면접 난이도
            - 면접 질문 내용
            - 합격 여부
            - 지원 경로
        - DataFrame 반환

    def crawl_company_info(self, company_id: str) -> dict:
        - 기업 기본 정보 크롤링
        - 수집 필드:
            - 기업명, 업종, 사원수, 설립연도
            - 평균 연봉, 총 평점
        - dict 반환

    def save_data(self, df: pd.DataFrame, filename: str):
        - data/raw/ 폴더에 CSV 저장
        - 크롤링한 URL을 url_list/crawling_urls.csv에 추가

    def run_all(self):
        - settings.py의 TARGET_COMPANIES 전체를 순회하며 크롤링 실행
        - tqdm으로 진행률 표시
        - 각 기업 사이 랜덤 딜레이 적용

[예외 처리]
- 페이지 로드 실패 시 재시도 (최대 3회)
- 로그인 세션 만료 시 재로그인
- 크롤링 차단 시 딜레이 증가 후 재시도
- 모든 예외는 로그 파일에 기록

[robots.txt 및 윤리적 크롤링]
- 요청 간 2~5초 랜덤 딜레이
- User-Agent 설정
- 과도한 요청 자제
"""
```

---

### 3. `crawlers/naver_api_crawler.py`

**역할**: Naver OpenAPI를 활용하여 블로그·뉴스 데이터 수집

```python
"""
구현 요구사항:

[클래스 구조]
class NaverAPICrawler:
    def __init__(self, client_id: str, client_secret: str):
        - API 인증 정보 설정
        - 요청 헤더 구성

    def search_blog(self, query: str, display: int = 100, start: int = 1, sort: str = "sim") -> pd.DataFrame:
        - Naver 블로그 검색 API 호출
        - URL: https://openapi.naver.com/v1/search/blog.json
        - 수집 필드:
            - 제목, 블로거명, 블로그 링크, 본문 요약, 작성일
        - display 파라미터로 최대 100개씩 수집
        - start 파라미터로 페이지네이션 (1, 101, 201, ...)
        - DataFrame 반환

    def search_news(self, query: str, display: int = 100, start: int = 1, sort: str = "date") -> pd.DataFrame:
        - Naver 뉴스 검색 API 호출
        - URL: https://openapi.naver.com/v1/search/news.json
        - 수집 필드:
            - 제목, 원문 링크, 본문 요약, 언론사, 발행일
        - DataFrame 반환

    def search_all_keywords(self, keywords: list, search_type: str = "blog") -> pd.DataFrame:
        - 키워드 리스트 전체를 순회하며 검색
        - 키워드별 결과를 하나의 DataFrame으로 병합
        - '검색키워드' 컬럼 추가
        - 중복 URL 제거

    def save_data(self, df: pd.DataFrame, filename: str):
        - data/raw/ 폴더에 CSV/JSON 저장
        - 크롤링한 API 요청 URL을 url_list/crawling_urls.csv에 추가

    def run_all(self):
        - settings.py의 NAVER_KEYWORDS 전체에 대해
        - 블로그 검색 + 뉴스 검색 실행
        - 각 키워드당 최소 100개 결과 확보 시도

[주의사항]
- API 일일 호출 제한: 25,000회
- 호출 간 0.1초 딜레이 권장
- HTML 태그 제거 처리 (제목, 본문에 <b> 등 포함됨)
- 날짜 형식 통일: YYYY-MM-DD
"""
```

---

### 4. `crawlers/saramin_crawler.py`

**역할**: 사람인에서 자율주행 관련 채용 공고 상세 정보 크롤링

```python
"""
구현 요구사항:

[클래스 구조]
class SaraminCrawler:
    def __init__(self):
        - requests Session 초기화
        - User-Agent 설정
        - (선택) Selenium WebDriver 초기화

    def search_jobs(self, keyword: str, pages: int = 5) -> list:
        - 키워드로 채용 공고 검색
        - 검색 결과 목록에서 각 공고의 URL 추출
        - list[str] (URL 목록) 반환

    def parse_job_detail(self, url: str) -> dict:
        - 개별 채용 공고 상세 페이지 파싱
        - 수집 필드:
            - 공고 제목, 회사명, 회사 규모(대기업/중소기업/스타트업)
            - 경력 조건 (신입/경력/무관)
            - 학력 조건
            - 근무 지역
            - 연봉 정보 (기재 시)
            - 마감일
            - 직무 분야
            - [핵심] 자격 요건 텍스트 전문
            - [핵심] 우대 사항 텍스트 전문
            - [핵심] 기술스택 / 필요 기술 목록
            - 복리후생 목록
        - dict 반환

    def extract_tech_stack(self, text: str) -> list:
        - 자격요건/우대사항 텍스트에서 기술스택 키워드 추출
        - 매칭 대상 키워드:
            Python, C++, C, Java, ROS, ROS2, PyTorch, TensorFlow,
            OpenCV, SLAM, LiDAR, RADAR, 카메라, 센서퓨전,
            AUTOSAR, MATLAB, Simulink, Linux, Docker, Git,
            딥러닝, 머신러닝, 컴퓨터비전, 영상처리, 포인트클라우드,
            CUDA, CAN, V2X, HD맵, 시뮬레이션, CARLA,
            SQL, AWS, GCP, Kubernetes
        - list[str] 반환

    def extract_certificates(self, text: str) -> list:
        - 자격요건/우대사항에서 자격증 키워드 추출
        - 매칭 대상:
            정보처리기사, 빅데이터분석기사, ADsP, SQLD,
            전자기사, 임베디드기사, 운전면허 등

    def crawl_all(self, keywords: list) -> pd.DataFrame:
        - 키워드 리스트 전체를 순회
        - 공고 목록 → 상세 파싱 파이프라인 실행
        - 전체 결과를 DataFrame으로 반환

    def save_data(self, df: pd.DataFrame, filename: str):
        - data/raw/ 폴더에 CSV 저장
        - URL 목록을 url_list/crawling_urls.csv에 추가

[예외 처리]
- 공고 마감/삭제 시 스킵
- 요청 실패 시 3회 재시도
- 2~4초 랜덤 딜레이
"""
```

---

### 5. `crawlers/wanted_crawler.py`

**역할**: 원티드에서 자율주행 관련 포지션 및 기술스택 태그 크롤링

```python
"""
구현 요구사항:

[클래스 구조]
class WantedCrawler:
    def __init__(self):
        - Selenium WebDriver 초기화 (동적 페이지 대응)

    def search_positions(self, keyword: str) -> list:
        - 원티드 검색 페이지에서 포지션 목록 수집
        - 무한 스크롤 대응 (scroll down + wait)
        - 각 포지션 카드의 URL 추출
        - list[str] 반환

    def parse_position_detail(self, url: str) -> dict:
        - 포지션 상세 페이지 파싱
        - 수집 필드:
            - 포지션명, 회사명
            - 기술스택 태그 목록 (원티드 고유 태그)
            - 주요 업무, 자격 요건, 우대 사항, 혜택 및 복지
            - 경력 조건, 연봉 정보
        - dict 반환

    def crawl_all(self) -> pd.DataFrame:
        - 자율주행 관련 키워드로 전체 포지션 크롤링
        - DataFrame 반환

    def save_data(self, df: pd.DataFrame, filename: str):
        - data/raw/ 저장 + URL 목록 추가
"""
```

---

### 6. `processors/data_cleaner.py`

**역할**: 수집된 원본 데이터의 전처리 및 정제

```python
"""
구현 요구사항:

[클래스 구조]
class DataCleaner:
    def __init__(self):
        pass

    def clean_html_tags(self, text: str) -> str:
        - HTML 태그 제거 (<b>, <br>, &amp; 등)
        - 특수문자 정리

    def normalize_salary(self, salary_text: str) -> int:
        - 연봉 텍스트를 정수(만원 단위)로 변환
        - "3,500만원" → 3500
        - "3,500 ~ 4,500만원" → 평균값 4000
        - "회사 내규에 따름" → None

    def normalize_career(self, career_text: str) -> str:
        - 경력 조건 통일
        - "신입" / "경력 1~3년" / "경력 3~5년" / "경력 5년 이상" / "무관"

    def normalize_company_size(self, info: dict) -> str:
        - 사원수 기반 기업 규모 분류
        - "스타트업" (50명 미만) / "중소기업" / "중견기업" / "대기업"

    def normalize_date(self, date_str: str) -> str:
        - 다양한 날짜 포맷을 YYYY-MM-DD로 통일

    def deduplicate(self, df: pd.DataFrame, subset: list) -> pd.DataFrame:
        - 중복 데이터 제거

    def process_all_raw_data(self):
        - data/raw/ 폴더의 모든 CSV를 읽어 전처리
        - 결과를 data/processed/ 폴더에 저장
"""
```

---

### 7. `processors/text_analyzer.py`

**역할**: 텍스트 데이터에서 키워드 추출 및 빈도 분석

```python
"""
구현 요구사항:

[클래스 구조]
class TextAnalyzer:
    def __init__(self):
        - KoNLPy Okt/Komoran 형태소 분석기 초기화
        - 불용어 리스트 정의

    def extract_nouns(self, text: str) -> list:
        - 텍스트에서 명사 추출
        - 불용어 제거
        - 1글자 명사 제거 (선택적)

    def get_word_frequency(self, texts: list, top_n: int = 50) -> pd.DataFrame:
        - 텍스트 리스트에서 전체 단어 빈도 계산
        - 상위 N개 반환
        - 컬럼: [단어, 빈도, 비율(%)]

    def get_tech_stack_frequency(self, job_data: pd.DataFrame) -> pd.DataFrame:
        - 채용 공고 데이터에서 기술스택 빈도 분석
        - 미리 정의된 기술스택 사전과 매칭
        - 컬럼: [기술스택, 빈도, 비율(%)]

    def get_certificate_frequency(self, job_data: pd.DataFrame) -> pd.DataFrame:
        - 채용 공고 데이터에서 자격증 빈도 분석

    def get_keyword_trend(self, blog_data: pd.DataFrame) -> pd.DataFrame:
        - 블로그/뉴스 데이터에서 시기별 키워드 트렌드 분석
        - 월별 키워드 언급 빈도

    def extract_job_requirements(self, text: str) -> dict:
        - 채용 공고 텍스트에서 구조화된 정보 추출
        - { "학력": ..., "경력": ..., "기술": [...], "자격증": [...] }
"""
```

---

### 8. `processors/salary_analyzer.py`

**역할**: 연봉 데이터 전문 분석

```python
"""
구현 요구사항:

[클래스 구조]
class SalaryAnalyzer:
    def __init__(self, salary_data: pd.DataFrame):
        - 연봉 데이터 로드

    def get_salary_stats(self) -> dict:
        - 기본 통계: 평균, 중앙값, 최소, 최대, 표준편차, 사분위수

    def get_salary_by_company(self) -> pd.DataFrame:
        - 기업별 평균 연봉 비교

    def get_salary_by_career(self) -> pd.DataFrame:
        - 경력별 연봉 분포

    def get_salary_by_company_size(self) -> pd.DataFrame:
        - 기업 규모별(대기업/스타트업) 연봉 비교

    def get_salary_by_tech_stack(self) -> pd.DataFrame:
        - 요구 기술스택별 연봉 차이 분석
        - 예: ROS 요구 vs 미요구 → 연봉 차이
"""
```

---

### 9. `visualizations/wordcloud_viz.py`

**역할**: 워드클라우드 시각화 생성

```python
"""
구현 요구사항:

[생성할 워드클라우드 목록]

1. 채용공고_기술스택_워드클라우드
   - 데이터: 사람인+원티드 채용공고에서 추출한 기술스택
   - 스타일: 자동차 실루엣 마스크(선택) 또는 사각형
   - 색상: 파란계열 컬러맵
   - 폰트: 나눔고딕(한글 지원)

2. 블로그_취준_키워드_워드클라우드
   - 데이터: Naver 블로그 제목+본문에서 추출한 명사
   - 불용어 처리 적용

3. 면접후기_키워드_워드클라우드
   - 데이터: 잡플래닛 면접 후기 텍스트
   - 면접 질문에서 자주 등장하는 키워드

4. 기업리뷰_장점_워드클라우드 / 기업리뷰_단점_워드클라우드
   - 데이터: 잡플래닛 리뷰의 장점/단점 텍스트 분리

[공통 설정]
- 해상도: 300 DPI
- 크기: 1200 x 800px
- 한글 폰트 경로 설정
- 배경: 흰색
- outputs/charts/ 폴더에 PNG 저장
"""
```

---

### 10. `visualizations/chart_viz.py`

**역할**: 기본 정적 차트 시각화 (matplotlib + seaborn)

```python
"""
구현 요구사항:

[생성할 차트 목록]

1. 기술스택 TOP 15 수평 막대그래프 (Horizontal Bar Chart)
   - X축: 빈도수, Y축: 기술스택명
   - 빈도 높은 순으로 정렬
   - 각 막대 끝에 수치 레이블 표시
   - 색상: 그라데이션 적용

2. 경력/신입 비율 도넛차트 (Donut Chart)
   - 신입 / 경력1~3년 / 경력3~5년 / 경력5년+ / 무관
   - 중앙에 전체 공고 수 표시
   - 각 조각에 비율(%) 표시

3. 기업별 연봉 박스플롯 (Box Plot)
   - X축: 기업명, Y축: 연봉(만원)
   - 중앙값, 사분위수, 이상치 표시
   - 대기업/스타트업 색상 구분

4. 기업 평점 항목별 그룹 막대그래프 (Grouped Bar Chart)
   - 항목: 총점, 승진기회, 워라밸, 급여, 사내문화, 경영진
   - 기업별 비교
   - 5점 만점 기준선 표시

5. 자격증/우대사항 빈도 수평 막대그래프
   - 요구/우대되는 자격증 TOP 10
   - 필수 vs 우대 색상 구분

6. 월별 채용공고 수 추이 라인차트 (Line Chart)
   - X축: 월, Y축: 공고 수
   - 전년 동기 대비 가능 시 비교선 추가

7. 기업 규모별 채용 비율 파이차트
   - 대기업 / 중견기업 / 중소기업 / 스타트업

8. 근무 지역별 분포 수평 막대그래프
   - 서울 / 경기 / 판교 / 기타 지역별 공고 수

[공통 설정]
- 폰트: 나눔고딕 (한글 깨짐 방지)
- 스타일: seaborn 'whitegrid'
- 해상도: 300 DPI
- 크기: figsize=(12, 8) 또는 차트에 맞게 조정
- 제목, 축 레이블, 범례 필수 포함
- outputs/charts/ 폴더에 PNG 저장
- 각 차트 생성 함수는 독립적으로 호출 가능
"""
```

---

### 11. `visualizations/advanced_viz.py`

**역할**: 고급 시각화 (히트맵, 레이더차트, 산키 다이어그램, 트리맵 등)

```python
"""
구현 요구사항:

[생성할 고급 차트 목록]

1. 기업×기술스택 히트맵 (Heatmap)
   - X축: 기술스택 (Python, C++, ROS, PyTorch 등)
   - Y축: 기업명
   - 값: 해당 기업 공고에서 해당 기술 언급 빈도 (또는 요구 여부 0/1)
   - 색상: YlOrRd 또는 Blues 컬러맵
   - annotate=True (셀 안에 수치 표시)

2. 기업별 종합 평가 레이더차트 (Radar/Spider Chart)
   - 축: 연봉, 워라밸, 성장성, 사내문화, 복지, 기술력
   - 기업 3~5개 비교 (대기업 vs 스타트업)
   - 반투명 영역으로 겹쳐서 표시

3. 직무 분류 트리맵 (Treemap)
   - 대분류: 인지 / 판단 / 제어 / 인프라 / 데이터
   - 소분류: 세부 직무 (센서처리, 경로계획, 차량제어, MLOps 등)
   - 크기: 채용 공고 수 비례
   - matplotlib의 squarify 패키지 활용

4. 자율주행 기술스택 생태계 네트워크 그래프 (Network Graph)
   - 노드: 기술스택 키워드
   - 엣지: 같은 공고에 동시 등장한 기술 연결
   - 노드 크기: 출현 빈도 비례
   - networkx + matplotlib 또는 plotly 활용

5. 경력-연봉 산점도 + 회귀선 (Scatter Plot with Regression)
   - X축: 요구 경력(년), Y축: 연봉(만원)
   - 기업 규모별 색상 구분
   - 회귀선(trend line) 추가
   - 상관계수 표시

6. 기술스택 카테고리별 스택 막대그래프 (Stacked Bar Chart)
   - 카테고리: 프로그래밍언어 / 프레임워크 / 도구 / 도메인지식
   - 각 카테고리 내 기술별 비율 표시

7. 기업 리뷰 감성 분포 바이올린 플롯 (Violin Plot)
   - X축: 기업명, Y축: 리뷰 평점 (1~5점)
   - 분포의 형태와 중앙값 동시 표현
   - 대기업/스타트업 그룹으로 분리

8. 채용 키워드 시계열 버블차트 (Bubble Chart)
   - X축: 시간(월별), Y축: 키워드
   - 버블 크기: 해당 월 해당 키워드 언급 빈도
   - 트렌드 변화를 한눈에 파악

[공통 설정]
- 한글 폰트 적용
- 300 DPI, PNG 저장
- 색맹 친화적 컬러팔레트 사용 권장
"""
```

---

### 12. `visualizations/interactive_viz.py`

**역할**: Plotly 기반 인터랙티브 시각화 (HTML 저장 가능)

```python
"""
구현 요구사항:

[생성할 인터랙티브 차트 목록]

1. 기업별 연봉 분포 인터랙티브 박스플롯
   - 호버 시 상세 정보 표시 (평균, 중앙값, 사분위수)
   - 기업 클릭으로 필터링 가능

2. 기술스택 빈도 인터랙티브 막대그래프
   - 호버 시 해당 기술을 요구하는 기업 목록 표시
   - 정렬 기준 전환 가능

3. 기업 평점 비교 인터랙티브 레이더차트
   - 드롭다운으로 비교 기업 선택
   - plotly.graph_objects의 Scatterpolar 활용

4. 채용 트렌드 인터랙티브 라인차트
   - 범위 슬라이더로 기간 선택
   - 키워드별 토글 가능

5. 기업-기술스택 산키 다이어그램 (Sankey Diagram)
   - 왼쪽: 기업명
   - 중간: 직무 분류 (인지/판단/제어)
   - 오른쪽: 요구 기술스택
   - 흐름의 두께: 공고 수 비례

6. 기술스택 동시 출현 인터랙티브 히트맵
   - X축, Y축 모두 기술스택
   - 값: 동시 출현 빈도
   - 호버 시 상세 정보

[공통 설정]
- HTML 파일로 저장 (outputs/charts/ 폴더)
- 정적 PNG도 함께 저장 (kaleido 활용)
- 한글 폰트 적용
- 발표용 테마(template="plotly_white") 적용
"""
```

---

### 13. `visualizations/dashboard.py`

**역할**: 분석 결과 종합 대시보드 생성

```python
"""
구현 요구사항:

[클래스 구조]
class AnalysisDashboard:
    def __init__(self, processed_data_path: str):
        - 전처리 완료된 데이터 로드

    def create_summary_dashboard(self):
        - matplotlib subplot 기반 종합 대시보드
        - 구성 (2×3 또는 3×3 그리드):
            - [1] 기술스택 TOP 10 막대그래프
            - [2] 경력/신입 비율 도넛차트
            - [3] 기업별 연봉 박스플롯
            - [4] 기업 평점 레이더차트
            - [5] 채용 트렌드 라인차트
            - [6] 기업 규모별 분포 파이차트
        - 전체 제목: "자율주행 AI 분야 취업 동향 종합 분석"
        - 고해상도 PNG 저장 (A3 크기)

    def create_plotly_dashboard(self):
        - Plotly subplots 기반 인터랙티브 대시보드
        - HTML 파일로 저장
        - 발표 시 브라우저에서 바로 시연 가능

    def generate_summary_stats(self) -> dict:
        - 핵심 통계 요약 (발표 슬라이드용)
        - 총 분석 공고 수
        - 가장 많이 요구되는 기술스택 TOP 5
        - 평균 연봉 및 연봉 범위
        - 신입 채용 비율
        - 가장 평점 높은 기업
"""
```

---

### 14. `main.py`

**역할**: 전체 파이프라인 실행 스크립트

```python
"""
구현 요구사항:

[실행 흐름]

def main():
    print("=" * 60)
    print("🚗 자율주행 AI 분야 취업 동향 분석 시작")
    print("=" * 60)

    # Phase 1: 크롤링
    print("\n📥 Phase 1: 데이터 크롤링")
    # 1-1. Naver OpenAPI 크롤링 (블로그 + 뉴스)
    # 1-2. 사람인 채용공고 크롤링
    # 1-3. 원티드 포지션 크롤링
    # 1-4. 잡플래닛 기업 리뷰/연봉/면접후기 크롤링

    # Phase 2: 데이터 전처리
    print("\n🔧 Phase 2: 데이터 전처리")
    # 2-1. HTML 태그 제거, 날짜 통일
    # 2-2. 연봉 데이터 정규화
    # 2-3. 기술스택/자격증 추출
    # 2-4. 중복 제거

    # Phase 3: 분석
    print("\n📊 Phase 3: 데이터 분석")
    # 3-1. 텍스트 분석 (키워드 빈도, 기술스택 빈도)
    # 3-2. 연봉 분석
    # 3-3. 트렌드 분석

    # Phase 4: 시각화
    print("\n🎨 Phase 4: 시각화 생성")
    # 4-1. 워드클라우드 생성
    # 4-2. 기본 차트 생성
    # 4-3. 고급 차트 생성
    # 4-4. 인터랙티브 차트 생성
    # 4-5. 종합 대시보드 생성

    # Phase 5: URL 목록 정리
    print("\n📋 Phase 5: 크롤링 URL 목록 정리")
    # 5-1. url_list/crawling_urls.csv 정리
    # 5-2. URL 100개 이상 확인

    print("\n✅ 전체 분석 완료!")
    print(f"📁 결과 저장 위치: outputs/")
    print(f"📊 차트 저장 위치: outputs/charts/")
    print(f"🔗 URL 목록: url_list/crawling_urls.csv")

[CLI 옵션]
- argparse 활용
- --phase: 특정 단계만 실행 (crawl / process / analyze / visualize / all)
- --source: 특정 소스만 크롤링 (naver / saramin / wanted / jobplanet / all)
- --skip-crawl: 크롤링 스킵하고 기존 데이터로 분석만 실행

예시:
    python main.py --phase all
    python main.py --phase crawl --source naver
    python main.py --phase visualize --skip-crawl
"""
```

---

### 15. `url_list/crawling_urls.csv`

**역할**: 크롤링한 모든 URL을 기록하는 파일 (제출용, 최소 100개)

```
"""
CSV 컬럼 구조:
- 번호 (1, 2, 3, ...)
- URL (실제 크롤링한 URL)
- 소스 (잡플래닛 / Naver블로그 / Naver뉴스 / 사람인 / 원티드)
- 검색키워드 (사용한 검색어)
- 수집일시 (YYYY-MM-DD HH:MM:SS)
- 데이터유형 (기업리뷰 / 채용공고 / 블로그 / 뉴스 / 면접후기)
- 비고

URL 확보 목표 분배:
- Naver OpenAPI 블로그: 30개+ (키워드 15개 × 2개 이상)
- Naver OpenAPI 뉴스: 20개+
- 사람인 채용공고: 25개+
- 잡플래닛 기업 리뷰/연봉/면접: 15개+ (기업 5개 × 3종)
- 원티드 포지션: 10개+
- 합계: 100개 이상
"""
```

---

## 📊 시각화 총 목록 (체크리스트)

### 기본 차트 (chart_viz.py) — 8개
- [ ] 기술스택 TOP 15 수평 막대그래프
- [ ] 경력/신입 비율 도넛차트
- [ ] 기업별 연봉 박스플롯
- [ ] 기업 평점 항목별 그룹 막대그래프
- [ ] 자격증/우대사항 빈도 막대그래프
- [ ] 월별 채용공고 수 추이 라인차트
- [ ] 기업 규모별 채용 비율 파이차트
- [ ] 근무 지역별 분포 막대그래프

### 워드클라우드 (wordcloud_viz.py) — 5개
- [ ] 채용공고 기술스택 워드클라우드
- [ ] 블로그 취준 키워드 워드클라우드
- [ ] 면접후기 키워드 워드클라우드
- [ ] 기업리뷰 장점 워드클라우드
- [ ] 기업리뷰 단점 워드클라우드

### 고급 차트 (advanced_viz.py) — 8개
- [ ] 기업×기술스택 히트맵
- [ ] 기업별 종합 평가 레이더차트
- [ ] 직무 분류 트리맵
- [ ] 기술스택 생태계 네트워크 그래프
- [ ] 경력-연봉 산점도 + 회귀선
- [ ] 기술스택 카테고리별 스택 막대그래프
- [ ] 기업 리뷰 감성 분포 바이올린 플롯
- [ ] 채용 키워드 시계열 버블차트

### 인터랙티브 차트 (interactive_viz.py) — 6개
- [ ] 기업별 연봉 분포 인터랙티브 박스플롯
- [ ] 기술스택 빈도 인터랙티브 막대그래프
- [ ] 기업 평점 비교 인터랙티브 레이더차트
- [ ] 채용 트렌드 인터랙티브 라인차트
- [ ] 기업-기술스택 산키 다이어그램
- [ ] 기술스택 동시 출현 인터랙티브 히트맵

### 대시보드 (dashboard.py) — 2개
- [ ] 종합 대시보드 (matplotlib, PNG)
- [ ] 인터랙티브 대시보드 (Plotly, HTML)

**총 시각화 수: 29개**

---

## 🚀 Claude Code 사용 가이드

### 실행 순서

```bash
# 1단계: 프로젝트 구조 생성
claude "이 MD 파일을 읽고 프로젝트 디렉토리 구조를 생성해줘"

# 2단계: config 파일 생성
claude "settings.py를 명세에 맞게 생성해줘"

# 3단계: 크롤러 생성 (하나씩 진행)
claude "naver_api_crawler.py를 명세에 맞게 생성해줘"
claude "saramin_crawler.py를 명세에 맞게 생성해줘"
claude "wanted_crawler.py를 명세에 맞게 생성해줘"
claude "jobplanet_crawler.py를 명세에 맞게 생성해줘"

# 4단계: 프로세서 생성
claude "data_cleaner.py를 명세에 맞게 생성해줘"
claude "text_analyzer.py를 명세에 맞게 생성해줘"
claude "salary_analyzer.py를 명세에 맞게 생성해줘"

# 5단계: 시각화 생성
claude "wordcloud_viz.py를 명세에 맞게 생성해줘"
claude "chart_viz.py를 명세에 맞게 생성해줘"
claude "advanced_viz.py를 명세에 맞게 생성해줘"
claude "interactive_viz.py를 명세에 맞게 생성해줘"
claude "dashboard.py를 명세에 맞게 생성해줘"

# 6단계: 메인 파이프라인 생성
claude "main.py를 명세에 맞게 생성해줘"

# 7단계: 테스트 및 실행
claude "main.py를 실행하고 에러를 수정해줘"
```

### 주요 프롬프트 예시

```
"이 프로젝트 가이드 MD 파일의 [파일명] 섹션을 참고하여
해당 Python 파일을 완전한 실행 가능한 코드로 작성해줘.
명세에 정의된 모든 클래스와 메서드를 구현하고,
예외 처리와 로깅도 포함해줘."
```

---

## ⚠️ 프로젝트 주의사항

1. **크롤링 윤리**: robots.txt 준수, 적절한 딜레이 적용, 과도한 요청 자제
2. **API 키 관리**: `.env` 파일에 저장, `.gitignore`에 추가, 절대 코드에 하드코딩 금지
3. **URL 100개**: 각 크롤러에서 수집한 URL을 반드시 `crawling_urls.csv`에 기록
4. **한글 폰트**: 시각화 시 한글 깨짐 방지를 위해 나눔고딕 폰트 설정 필수
5. **데이터 저장**: 모든 크롤링 데이터는 CSV/JSON으로 반드시 파일 저장
6. **재현성**: 시드 고정, 경로 설정 등을 통해 코드 재실행 시 동일 결과 보장

---

*Yeong — 자율주행 AI 파트 | Claude Code 프로젝트 가이드 v1.0*
