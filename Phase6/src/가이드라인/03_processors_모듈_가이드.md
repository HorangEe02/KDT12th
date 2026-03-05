# 03. processors 모듈 가이드

> 수집된 원본 데이터를 정제하고 분석하는 3개의 모듈로 구성된다.
> `salary_analyzer.py`는 완전 범용이고, 나머지 2개는 도메인 용어 부분만 수정하면 된다.

---

## 파일 구조

```
processors/
├── __init__.py            ← 3개 클래스 import
├── data_cleaner.py        ← 데이터 전처리 (HTML 제거, 정규화, 중복 제거)
├── text_analyzer.py       ← 텍스트 분석 (형태소, 빈도, 도메인 분석)
└── salary_analyzer.py     ← 연봉 분석 (완전 범용 - 수정 불필요)
```

---

## 1. data_cleaner.py

### 개요

| 항목 | 내용 |
|------|------|
| 역할 | 원본 데이터(data/raw/) → 정제 데이터(data/processed/) 변환 |
| 분야 전환 난이도 | ★★☆ (도메인 용어 매핑만 변경) |

### 클래스 구조

```python
class DataCleaner:
    def __init__(self)
        self.medical_term_map = { ... }   # ★ 도메인 용어 매핑 → 변경 필요

    # 공통 전처리 (수정 불필요)
    def clean_html_tags(text) → str            # HTML 태그 제거
    def normalize_salary(salary_text) → int    # 연봉 텍스트 → 정수
    def normalize_career(career_text) → str    # 경력 정규화
    def normalize_company_size(info) → str     # 기업 규모 분류
    def normalize_date(date_str) → str         # 날짜 형식 통일
    def deduplicate(df, subset) → DataFrame    # 중복 제거

    # 도메인 특화 (★ 변경 필요)
    def normalize_medical_terms(text) → str    # 의료 용어 정규화

    # 전체 실행
    def process_all_raw_data() → None          # data/raw/ 전체 처리
```

### 수정 불필요 메서드 (범용)

| 메서드 | 기능 | 범용 이유 |
|--------|------|----------|
| `clean_html_tags()` | `<b>`, `&amp;` 등 제거 | 모든 웹 크롤링에 공통 |
| `normalize_salary()` | "4,000만원" → 4000 | 모든 채용공고에 공통 |
| `normalize_career()` | "3~5년" → 표준 형식 | 모든 채용공고에 공통 |
| `normalize_company_size()` | 직원수 → 5단계 분류 | 모든 기업에 공통 |
| `normalize_date()` | 다양한 형식 → YYYY-MM-DD | 범용 날짜 처리 |
| `deduplicate()` | 컬럼 기반 중복 제거 | 데이터 공통 |
| `process_all_raw_data()` | data/raw/ 전체 순회 | 파이프라인 공통 |

### 분야 전환 시 수정 포인트

```python
# [수정 필요] 도메인 용어 정규화 매핑
# 현재: 의료 용어
self.medical_term_map = {
    "X-ray": ["엑스레이", "x-ray", "xray", "엑스선"],
    "CT": ["씨티", "컴퓨터단층촬영", "ct"],
    "MRI": ["엠알아이", "자기공명영상", "mri"],
    "AI": ["인공지능", "에이아이"],
    "EMR": ["전자의무기록", "emr"],
}

# ▼ 변경 예시 (핀테크):
self.domain_term_map = {
    "API": ["에이피아이", "api", "응용프로그램인터페이스"],
    "P2P": ["피투피", "p2p대출", "개인간대출"],
    "KYC": ["본인확인", "신원확인", "kyc"],
    "AML": ["자금세탁방지", "aml"],
    "DeFi": ["디파이", "defi", "탈중앙금융"],
}

# [수정 필요] 메서드명도 변경 권장
# normalize_medical_terms() → normalize_domain_terms()
```

---

## 2. text_analyzer.py

### 개요

| 항목 | 내용 |
|------|------|
| 역할 | 텍스트 분석 - 형태소 추출, 단어 빈도, 기술스택/자격증/도메인 빈도 |
| NLP 엔진 | KoNLPy (Okt) → 설치 안 되면 정규식 폴백 |
| 분야 전환 난이도 | ★★☆ (도메인 분석 변수명만 변경) |

### 클래스 구조

```python
class TextAnalyzer:
    def __init__(self)
        self.okt = Okt()                     # KoNLPy (optional)
        self.stopwords = { ... }              # 불용어 (★ 분야별 추가 가능)
        self.tech_patterns = { ... }          # settings.TECH_STACK_KEYWORDS → 자동
        self.cert_patterns = { ... }          # settings.CERTIFICATE_KEYWORDS → 자동

    # 형태소 분석 (수정 불필요)
    def extract_nouns(text) → list[str]

    # 빈도 분석 (수정 불필요)
    def get_word_frequency(texts, top_n=50) → DataFrame

    # 키워드 사전 기반 분석 (settings 자동 참조 → 수정 불필요)
    def get_tech_stack_frequency(job_data) → DataFrame
    def get_certificate_frequency(job_data) → DataFrame

    # 도메인 분석 (★ 변수명 변경 필요)
    def get_medical_domain_frequency(job_data) → DataFrame

    # 트렌드/요건 분석 (수정 불필요)
    def get_keyword_trend(blog_data) → DataFrame
    def extract_job_requirements(text) → dict
```

### 수정 불필요 메서드

| 메서드 | 기능 | 범용 이유 |
|--------|------|----------|
| `extract_nouns()` | 한국어 명사 추출 | KoNLPy/정규식 범용 |
| `get_word_frequency()` | 상위 N개 단어 빈도 | 데이터 공통 |
| `get_tech_stack_frequency()` | 기술스택 빈도 | settings.py 자동 참조 |
| `get_certificate_frequency()` | 자격증 빈도 | settings.py 자동 참조 |
| `get_keyword_trend()` | 월별 키워드 트렌드 | 시계열 공통 |
| `extract_job_requirements()` | 구조화 요건 추출 | 채용공고 공통 |

### 분야 전환 시 수정 포인트

```python
# [수정 필요 1] 메서드명 변경
# 기존:
def get_medical_domain_frequency(self, job_data):
    # settings.MEDICAL_DOMAIN_KEYWORDS 참조
    ...

# 변경:
def get_domain_frequency(self, job_data):
    # settings.DOMAIN_KEYWORDS 참조 (settings.py 변수명도 함께 변경)
    ...

# [수정 필요 2] 불용어 추가 (선택)
self.stopwords = {
    # 기존 공통 불용어 유지
    "있는", "하는", "있다", "합니다", "입니다", "등", "및",
    # 분야별 빈번하지만 분석에 불필요한 단어 추가
    # 예: 핀테크 → "금융", "서비스" 등 너무 일반적인 단어
}
```

### 출력 데이터 형식

**tech_stack_frequency.csv**:
```
기술스택,빈도,비율(%)
Python,35,5.69
R,69,11.22
...
```

**certificate_frequency.csv**:
```
자격증,빈도,비율(%)
ADP,10,35.71
방사선사,8,28.57
...
```

**medical_domain_frequency.csv** (→ domain_frequency.csv로 변경):
```
카테고리,키워드,빈도
영상의학,CT,52
인허가,FDA,46
...
```

---

## 3. salary_analyzer.py

### 개요

| 항목 | 내용 |
|------|------|
| 역할 | 연봉 데이터 통계 분석 |
| 분야 전환 난이도 | **수정 불필요** (완전 범용) |

### 클래스 구조

```python
class SalaryAnalyzer:
    def __init__(self, salary_data: DataFrame = None)

    # 기본 통계
    def get_salary_stats() → dict               # 평균, 중앙값, 사분위수 등

    # 다차원 분석
    def get_salary_by_company() → DataFrame      # 기업별 평균 연봉
    def get_salary_by_career() → DataFrame       # 경력별 평균 연봉
    def get_salary_by_company_size() → DataFrame  # 기업 규모별 평균 연봉
    def get_salary_by_subdomain() → DataFrame    # 하위 도메인별 평균 연봉
    def get_salary_by_tech_stack() → DataFrame   # 기술스택별 평균 연봉
    def get_salary_by_funding_stage() → DataFrame # 투자 단계별 평균 연봉
```

### 범용성

이 모듈은 DataFrame의 연봉 컬럼을 자동 감지(`_find_column()`)하여 분석한다. 컬럼명이 "연봉", "salary", "급여" 등 다양한 이름이어도 자동 매칭된다. **어떤 분야에서도 수정 없이 그대로 사용 가능.**

---

## 전처리 파이프라인 흐름

```
data/raw/                          data/processed/
├── naver_blog_의료AI.csv    ──→   ├── naver_blog_의료AI_processed.csv
├── naver_news_의료AI.csv    ──→   ├── naver_news_의료AI_processed.csv
├── 원티드_포지션_의료AI.csv  ──→   ├── 원티드_포지션_의료AI_processed.csv
├── 잡플래닛_기업정보.csv     ──→   ├── 잡플래닛_기업정보_processed.csv
├── 잡플래닛_리뷰.csv         ──→   ├── 잡플래닛_리뷰_processed.csv
└── 잡플래닛_면접후기.csv     ──→   ├── 잡플래닛_면접후기_processed.csv
                                   │
                                   │  [TextAnalyzer 분석 결과]
                                   ├── tech_stack_frequency.csv
                                   ├── certificate_frequency.csv
                                   ├── medical_domain_frequency.csv
                                   └── word_frequency.csv
```

---

## 수정 체크리스트

- [ ] data_cleaner.py: `medical_term_map` → `domain_term_map` 내용 교체
- [ ] data_cleaner.py: `normalize_medical_terms()` → `normalize_domain_terms()` 메서드명 변경
- [ ] text_analyzer.py: `get_medical_domain_frequency()` → `get_domain_frequency()` 변경
- [ ] text_analyzer.py: `MEDICAL_DOMAIN_KEYWORDS` 참조 → `DOMAIN_KEYWORDS` 변경
- [ ] text_analyzer.py: (선택) 분야별 불용어 추가
- [ ] salary_analyzer.py: **수정 불필요**
