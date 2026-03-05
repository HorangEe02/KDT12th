# 🏥 의료 AI 분야 — 크롤링 미니 프로젝트 Claude Code 가이드

> **목적**: 이 문서는 Claude Code를 활용하여 의료 AI 분야의 취업 동향 분석을 위한
> Python 크롤링·분석·시각화 파일을 자동 생성하기 위한 **상세 명세서**입니다.

---

## 📁 프로젝트 디렉토리 구조

```
medical_ai_analysis/
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
    "뷰노": {"jobplanet_id": "...", "category": "스타트업_의료영상"},
    "루닛": {"jobplanet_id": "...", "category": "스타트업_의료영상"},
    "딥노이드": {"jobplanet_id": "...", "category": "스타트업_의료영상"},
    "제이엘케이": {"jobplanet_id": "...", "category": "스타트업_의료AI"},
    "셀바스AI": {"jobplanet_id": "...", "category": "중소기업_AI"},
    "라인웍스": {"jobplanet_id": "...", "category": "스타트업_디지털헬스"},
    "메디컬에이아이": {"jobplanet_id": "...", "category": "스타트업_의료AI"},
    "닥터나우": {"jobplanet_id": "...", "category": "스타트업_원격의료"},
    "에이치투오호스피탈리티": {"jobplanet_id": "...", "category": "스타트업_헬스케어"},
    "인피니트헬스케어": {"jobplanet_id": "...", "category": "중소기업_PACS"},
    "카카오헬스케어": {"jobplanet_id": "...", "category": "대기업_헬스케어"},
    "네이버클라우드(의료)": {"jobplanet_id": "...", "category": "대기업_클라우드"},
}

# Naver OpenAPI 검색 키워드
NAVER_KEYWORDS = [
    "의료 AI 취업 준비",
    "의료 AI 개발자 채용",
    "헬스케어 AI 취업",
    "의료영상 AI 개발자",
    "디지털헬스 취업",
    "의료 데이터 분석가",
    "의료 AI 신입 채용",
    "의료 AI 자격증",
    "의료 AI 포트폴리오",
    "의료 AI 인턴",
    "DICOM 개발자",
    "의료 AI 스타트업 채용",
    "헬스케어 데이터 사이언티스트",
    "의료 AI 석사 취업",
    "의료 AI 교육과정",
    "바이오헬스 AI 취업",
    "의료 AI 논문 취업",
    "FDA SaMD 인허가",
]

# 사람인 검색 키워드
SARAMIN_KEYWORDS = [
    "의료 AI",
    "의료 인공지능",
    "헬스케어 AI",
    "의료영상 분석",
    "디지털헬스",
    "헬스케어 Python",
    "의료 데이터",
    "바이오 AI",
    "의료 딥러닝",
    "의료 머신러닝",
    "PACS 개발",
    "EMR 개발",
]
```

---

### 2. `crawlers/jobplanet_crawler.py`

**역할**: 잡플래닛에서 의료 AI 관련 기업의 리뷰, 연봉, 면접 후기 크롤링

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

**역할**: Naver OpenAPI를 활용하여 의료 AI 관련 블로그·뉴스 데이터 수집

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

**역할**: 사람인에서 의료 AI 관련 채용 공고 상세 정보 크롤링

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
        - 매칭 대상 키워드 (의료 AI 특화):
            Python, R, PyTorch, TensorFlow, Keras,
            OpenCV, scikit-learn, pandas, NumPy, SciPy,
            딥러닝, 머신러닝, 컴퓨터비전, 자연어처리, NLP,
            의료영상, DICOM, PACS, HL7, FHIR,
            CT, MRI, X-ray, 병리, 내시경,
            Docker, Kubernetes, AWS, GCP, Azure,
            SQL, MongoDB, PostgreSQL,
            Git, Linux, MLOps, Kubeflow, MLflow,
            통계분석, 생존분석, 임상시험, FDA, MFDS,
            논문, SCI, 특허,
            Java, C++, JavaScript, React, FastAPI, Django
        - list[str] 반환

    def extract_certificates(self, text: str) -> list:
        - 자격요건/우대사항에서 자격증 키워드 추출
        - 매칭 대상 (의료 AI 특화):
            정보처리기사, 빅데이터분석기사, ADsP, ADP,
            SQLD, SQLP, 의공기사, 방사선사, 임상병리사,
            AWS 자격증, GCP 자격증, 데이터분석준전문가 등

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

**역할**: 원티드에서 의료 AI 관련 포지션 및 기술스택 태그 크롤링

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
        - 의료 AI 관련 키워드로 전체 포지션 크롤링
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
        - HTML 태그 제거 (<b>, <br>, & 등)
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

    def normalize_medical_terms(self, text: str) -> str:
        - 의료 용어 통일 처리 (의료 AI 특화)
        - "엑스레이" / "X-ray" / "X레이" → "X-ray"
        - "씨티" / "CT" / "컴퓨터단층촬영" → "CT"
        - "엠알아이" / "MRI" / "자기공명영상" → "MRI"
        - "PACS" / "팍스" / "의료영상저장전송시스템" → "PACS"

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
        - 의료 도메인 사용자 사전 추가 (선택)
            예: "의료영상", "디지털헬스", "인허가", "임상시험" 등

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

    def get_medical_domain_frequency(self, job_data: pd.DataFrame) -> pd.DataFrame:
        - 의료 도메인 키워드 빈도 분석 (의료 AI 특화)
        - 카테고리별 분류:
            - 영상의학: CT, MRI, X-ray, 초음파
            - 병리: 조직검사, 세포검사, 디지털병리
            - 임상: EMR, 임상시험, 바이오마커
            - 인허가: FDA, MFDS, SaMD, CE마킹
            - 유전체: 유전체, 오믹스, NGS

    def get_keyword_trend(self, blog_data: pd.DataFrame) -> pd.DataFrame:
        - 블로그/뉴스 데이터에서 시기별 키워드 트렌드 분석
        - 월별 키워드 언급 빈도

    def extract_job_requirements(self, text: str) -> dict:
        - 채용 공고 텍스트에서 구조화된 정보 추출
        - { "학력": ..., "경력": ..., "기술": [...], "자격증": [...], "도메인": [...] }
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
        - 기업 규모별(대기업계열/스타트업) 연봉 비교

    def get_salary_by_subdomain(self) -> pd.DataFrame:
        - 의료 AI 세부 도메인별 연봉 비교 (의료 AI 특화)
        - 의료영상 / 디지털헬스 / 신약개발 / 임상데이터 / 유전체

    def get_salary_by_tech_stack(self) -> pd.DataFrame:
        - 요구 기술스택별 연봉 차이 분석
        - 예: PyTorch 요구 vs TensorFlow 요구 → 연봉 차이

    def get_salary_by_funding_stage(self) -> pd.DataFrame:
        - 투자 단계별 연봉 비교 (의료 AI 스타트업 특화)
        - 시드 / 시리즈A / 시리즈B / 시리즈C+ / 상장
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
   - 스타일: 십자가/하트 의료 심볼 마스크(선택) 또는 사각형
   - 색상: 초록·파랑 계열 컬러맵 (의료 이미지 연상)
   - 폰트: 나눔고딕(한글 지원)

2. 블로그_취준_키워드_워드클라우드
   - 데이터: Naver 블로그 제목+본문에서 추출한 명사
   - 불용어 처리 적용

3. 면접후기_키워드_워드클라우드
   - 데이터: 잡플래닛 면접 후기 텍스트
   - 면접 질문에서 자주 등장하는 키워드

4. 기업리뷰_장점_워드클라우드 / 기업리뷰_단점_워드클라우드
   - 데이터: 잡플래닛 리뷰의 장점/단점 텍스트 분리

5. 의료_도메인_키워드_워드클라우드 (의료 AI 특화)
   - 데이터: 채용공고+블로그에서 추출한 의료 도메인 키워드
   - CT, MRI, DICOM, 병리, 임상시험, FDA 등

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
   - 스타트업/대기업계열 색상 구분

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
   - 스타트업 / 중소기업 / 중견기업 / 대기업계열

8. 근무 지역별 분포 수평 막대그래프
   - 서울 / 경기 / 판교 / 대전 / 기타 지역별 공고 수

9. 학력 조건 분포 막대그래프 (의료 AI 특화)
   - 학사 / 석사 / 박사 / 무관
   - 의료 AI 특성상 석·박사 비율 강조

10. 의료 도메인별 채용 분포 파이차트 (의료 AI 특화)
    - 의료영상 / 디지털헬스 / 신약개발 / 임상데이터 / 유전체 / 기타

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
   - X축: 기술스택 (Python, PyTorch, TensorFlow, Docker 등)
   - Y축: 기업명
   - 값: 해당 기업 공고에서 해당 기술 언급 빈도 (또는 요구 여부 0/1)
   - 색상: Greens 또는 Blues 컬러맵
   - annotate=True (셀 안에 수치 표시)

2. 기업별 종합 평가 레이더차트 (Radar/Spider Chart)
   - 축: 연봉, 워라밸, 성장성, 사내문화, 복지, 기술력
   - 기업 3~5개 비교 (뷰노 vs 루닛 vs 딥노이드 등)
   - 반투명 영역으로 겹쳐서 표시

3. 의료 AI 직무 분류 트리맵 (Treemap) — 의료 AI 특화
   - 대분류: 의료영상 / NLP / 데이터엔지니어링 / MLOps / 프론트엔드·백엔드 / 연구
   - 소분류: 세부 직무 (CT분석, 병리영상, 임상NLP, 데이터파이프라인 등)
   - 크기: 채용 공고 수 비례
   - matplotlib의 squarify 패키지 활용

4. 의료 AI 기술스택 생태계 네트워크 그래프 (Network Graph)
   - 노드: 기술스택 키워드
   - 엣지: 같은 공고에 동시 등장한 기술 연결
   - 노드 크기: 출현 빈도 비례
   - 노드 색상: 카테고리별 구분 (프로그래밍/프레임워크/의료도메인/인프라)
   - networkx + matplotlib 또는 plotly 활용

5. 경력-연봉 산점도 + 회귀선 (Scatter Plot with Regression)
   - X축: 요구 경력(년), Y축: 연봉(만원)
   - 기업별 또는 도메인별 색상 구분
   - 회귀선(trend line) 추가
   - 상관계수 표시

6. 기술스택 카테고리별 스택 막대그래프 (Stacked Bar Chart)
   - 카테고리: 프로그래밍언어 / ML프레임워크 / 의료도메인 / 인프라·DevOps / 데이터베이스
   - 각 카테고리 내 기술별 비율 표시

7. 기업 리뷰 감성 분포 바이올린 플롯 (Violin Plot)
   - X축: 기업명, Y축: 리뷰 평점 (1~5점)
   - 분포의 형태와 중앙값 동시 표현
   - 의료영상 기업 / 디지털헬스 기업 그룹으로 분리

8. 채용 키워드 시계열 버블차트 (Bubble Chart)
   - X축: 시간(월별), Y축: 키워드
   - 버블 크기: 해당 월 해당 키워드 언급 빈도
   - 트렌드 변화를 한눈에 파악

9. 의료 AI 인허가-기술 매핑 히트맵 (의료 AI 특화)
   - X축: 인허가 유형 (FDA 510(k), FDA De Novo, MFDS 3등급, CE마킹)
   - Y축: 기업명
   - 값: 보유 인허가 수 또는 여부
   - 기업의 기술 성숙도를 간접 파악

10. 학력×연봉 그룹 바이올린 플롯 (의료 AI 특화)
    - X축: 학력 (학사/석사/박사)
    - Y축: 연봉(만원)
    - 의료 AI 특성상 학력에 따른 연봉 차이 분석

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

5. 기업-직무-기술스택 산키 다이어그램 (Sankey Diagram)
   - 왼쪽: 기업명
   - 중간: 직무 분류 (의료영상/NLP/데이터엔지니어/MLOps/연구)
   - 오른쪽: 요구 기술스택
   - 흐름의 두께: 공고 수 비례

6. 기술스택 동시 출현 인터랙티브 히트맵
   - X축, Y축 모두 기술스택
   - 값: 동시 출현 빈도
   - 호버 시 상세 정보

7. 의료 AI 기업 포지셔닝 맵 인터랙티브 산점도 (의료 AI 특화)
   - X축: 기업 규모(직원수), Y축: 평균 연봉
   - 버블 크기: 채용 공고 수
   - 색상: 도메인 분류
   - 호버 시 기업 상세 정보

8. 의료 도메인 선버스트 차트 (Sunburst Chart, 의료 AI 특화)
   - 중심: "의료 AI"
   - 1단계: 도메인 (의료영상/디지털헬스/신약/임상/유전체)
   - 2단계: 세부 기술 (CT분석, 병리, 약물반응예측 등)
   - 3단계: 요구 기술스택
   - 크기: 채용 공고 수 비례

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
        - 구성 (3×3 그리드):
            - [1] 기술스택 TOP 10 막대그래프
            - [2] 경력/신입 비율 도넛차트
            - [3] 기업별 연봉 박스플롯
            - [4] 기업 평점 레이더차트
            - [5] 채용 트렌드 라인차트
            - [6] 기업 규모별 분포 파이차트
            - [7] 의료 도메인별 분포 파이차트
            - [8] 학력 조건 분포 막대그래프
            - [9] 핵심 통계 텍스트 요약 패널
        - 전체 제목: "의료 AI 분야 취업 동향 종합 분석"
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
        - 석·박사 요구 비율
        - 가장 활발한 의료 도메인
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
    print("🏥 의료 AI 분야 취업 동향 분석 시작")
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
    # 2-3. 의료 용어 통일 (의료 AI 특화)
    # 2-4. 기술스택/자격증 추출
    # 2-5. 중복 제거

    # Phase 3: 분석
    print("\n📊 Phase 3: 데이터 분석")
    # 3-1. 텍스트 분석 (키워드 빈도, 기술스택 빈도)
    # 3-2. 의료 도메인 빈도 분석 (의료 AI 특화)
    # 3-3. 연봉 분석
    # 3-4. 트렌드 분석

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
- Naver OpenAPI 블로그: 35개+ (키워드 18개 × 2개 이상)
- Naver OpenAPI 뉴스: 20개+
- 사람인 채용공고: 25개+
- 잡플래닛 기업 리뷰/연봉/면접: 15개+ (기업 5개 × 3종)
- 원티드 포지션: 10개+
- 합계: 105개 이상
"""
```

---

## 📊 시각화 총 목록 (체크리스트)

### 기본 차트 (chart_viz.py) — 10개

- [ ] 기술스택 TOP 15 수평 막대그래프
- [ ] 경력/신입 비율 도넛차트
- [ ] 기업별 연봉 박스플롯
- [ ] 기업 평점 항목별 그룹 막대그래프
- [ ] 자격증/우대사항 빈도 막대그래프
- [ ] 월별 채용공고 수 추이 라인차트
- [ ] 기업 규모별 채용 비율 파이차트
- [ ] 근무 지역별 분포 막대그래프
- [ ] 학력 조건 분포 막대그래프 ★의료AI특화
- [ ] 의료 도메인별 채용 분포 파이차트 ★의료AI특화

### 워드클라우드 (wordcloud_viz.py) — 6개

- [ ] 채용공고 기술스택 워드클라우드
- [ ] 블로그 취준 키워드 워드클라우드
- [ ] 면접후기 키워드 워드클라우드
- [ ] 기업리뷰 장점 워드클라우드
- [ ] 기업리뷰 단점 워드클라우드
- [ ] 의료 도메인 키워드 워드클라우드 ★의료AI특화

### 고급 차트 (advanced_viz.py) — 10개

- [ ] 기업×기술스택 히트맵
- [ ] 기업별 종합 평가 레이더차트
- [ ] 의료 AI 직무 분류 트리맵
- [ ] 기술스택 생태계 네트워크 그래프
- [ ] 경력-연봉 산점도 + 회귀선
- [ ] 기술스택 카테고리별 스택 막대그래프
- [ ] 기업 리뷰 감성 분포 바이올린 플롯
- [ ] 채용 키워드 시계열 버블차트
- [ ] 의료 AI 인허가-기술 매핑 히트맵 ★의료AI특화
- [ ] 학력×연봉 그룹 바이올린 플롯 ★의료AI특화

### 인터랙티브 차트 (interactive_viz.py) — 8개

- [ ] 기업별 연봉 분포 인터랙티브 박스플롯
- [ ] 기술스택 빈도 인터랙티브 막대그래프
- [ ] 기업 평점 비교 인터랙티브 레이더차트
- [ ] 채용 트렌드 인터랙티브 라인차트
- [ ] 기업-직무-기술스택 산키 다이어그램
- [ ] 기술스택 동시 출현 인터랙티브 히트맵
- [ ] 의료 AI 기업 포지셔닝 맵 인터랙티브 산점도 ★의료AI특화
- [ ] 의료 도메인 선버스트 차트 ★의료AI특화

### 대시보드 (dashboard.py) — 2개

- [ ] 종합 대시보드 (matplotlib, PNG)
- [ ] 인터랙티브 대시보드 (Plotly, HTML)

**총 시각화 수: 36개** (자율주행 29개 대비 +7개, 의료 AI 특화 시각화 포함)

---

## 🆚 자율주행 파트 대비 의료 AI 파트 차별점 요약

| 구분                | 자율주행 파트                        | 의료 AI 파트                            |
| ------------------- | ------------------------------------ | --------------------------------------- |
| **기술스택 키워드** | ROS, C++, SLAM, LiDAR, AUTOSAR       | PyTorch, TensorFlow, DICOM, PACS, HL7   |
| **자격증**          | 정보처리기사, 전자기사, 임베디드기사 | 정보처리기사, 의공기사, 방사선사, ADsP  |
| **도메인 분류**     | 인지/판단/제어/인프라                | 의료영상/NLP/임상데이터/유전체/신약     |
| **기업 특성**       | 대기업+스타트업 혼재                 | 스타트업 중심 (투자 단계별 분석)        |
| **특화 분석**       | 직무별(인지/판단/제어) 분류          | 인허가(FDA/MFDS) 매핑, 학력별 연봉      |
| **특화 시각화**     | —                                    | 선버스트 차트, 인허가 히트맵, 학력×연봉 |
| **전처리 특화**     | —                                    | 의료 용어 정규화 (X-ray, CT, MRI 등)    |
| **총 시각화 수**    | 29개                                 | 36개                                    |

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
7. **의료 데이터 민감성**: 환자 개인정보가 포함된 데이터는 절대 수집하지 않음 (채용공고·기업리뷰만 대상)

---

_Yeong — 의료 AI 파트 | Claude Code 프로젝트 가이드 v1.0_
