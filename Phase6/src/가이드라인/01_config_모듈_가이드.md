# 01. config 모듈 가이드

> `config/settings.py`는 프로젝트 전체의 **중앙 설정 파일**이다.
> 이 파일만 제대로 수정하면 나머지 모듈이 자동으로 새 분야에 맞춰 동작한다.

---

## 파일 구조

```
config/
├── __init__.py          ← 빈 파일 (패키지 인식용)
└── settings.py          ★ 전체 설정 중앙 관리
```

---

## 현재 프로젝트에서 사용 중인 인증 정보

### 네이버 OpenAPI

| 항목 | 값 |
|------|---|
| Client ID | `F7QE6pmxq_MDivA5jrqq` |
| Client Secret | `9OfednhamT` |
| 발급 위치 | [네이버 개발자센터](https://developers.naver.com) |
| 용도 | 블로그/뉴스 검색 API |

> **새 프로젝트 시**: 네이버 개발자센터에서 새 애플리케이션을 등록하여 별도 키를 발급받는 것을 권장한다.
> 하나의 키로 하루 25,000건 호출 가능하므로, 동일 키를 재사용해도 무방하다.

### 잡플래닛 로그인 정보

| 항목 | 값 |
|------|---|
| ID (이메일) | `catlife0202@kmu.kr` |
| Password | `hellcat9021@` |
| 용도 | 잡플래닛 기업리뷰/면접후기 크롤링 (로그인 필수) |

> **새 프로젝트 시**: 잡플래닛은 로그인 없이는 리뷰/면접후기 열람이 불가하다.
> 동일 계정을 사용하거나, 새 계정을 생성하여 사용한다.

---

## settings.py 전체 구성

```python
# ============================================================
# 1. API/인증 정보
# ============================================================
NAVER_CLIENT_ID = "F7QE6pmxq_MDivA5jrqq"
NAVER_CLIENT_SECRET = "9OfednhamT"
JOBPLANET_USER_ID = "catlife0202@kmu.kr"
JOBPLANET_PASSWORD = "hellcat9021@"

# ============================================================
# 2. 대상 기업 리스트
# ============================================================
TARGET_COMPANIES = { ... }          # 12개 기업 (잡플래닛 company_id 포함)

# ============================================================
# 3. 검색 키워드
# ============================================================
NAVER_BLOG_KEYWORDS = [ ... ]       # 22개 블로그 키워드
NAVER_NEWS_KEYWORDS = [ ... ]       # 15개 뉴스 키워드
SARAMIN_KEYWORDS = [ ... ]          # 12개 사람인 키워드
WANTED_KEYWORDS = [ ... ]           # 5개 원티드 키워드
KEYWORD_COLOR_MAP = { ... }         # 키워드별 시각화 색상

# ============================================================
# 4. 기술스택 / 자격증 / 도메인 키워드 사전
# ============================================================
TECH_STACK_KEYWORDS = [ ... ]       # 55개 기술 키워드
CERTIFICATE_KEYWORDS = [ ... ]      # 12개 자격증
MEDICAL_DOMAIN_KEYWORDS = { ... }   # 5개 카테고리, 27개 키워드

# ============================================================
# 5. 크롤링 설정
# ============================================================
CRAWL_DELAY_MIN / MAX              # 크롤링 딜레이 (초)
API_CALL_DELAY                     # API 호출 간격
USER_AGENT                         # 브라우저 User-Agent

# ============================================================
# 6. 경로 설정
# ============================================================
BASE_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR,
OUTPUTS_CHARTS_DIR, OUTPUTS_REPORTS_DIR, URL_LIST_DIR

# ============================================================
# 7. 시각화 설정
# ============================================================
KOREAN_FONT_CANDIDATES = [ ... ]    # 한글 폰트 경로 목록
WORDCLOUD_MASK_PATH                 # 워드클라우드 마스크 이미지 경로
```

---

## 분야 전환 시 수정 항목 (9개)

### [필수 수정 1] API 인증 정보

```python
# 동일 키 재사용 가능 (하루 25,000건 제한)
# 새로 발급하려면: https://developers.naver.com → 애플리케이션 등록
NAVER_CLIENT_ID = "F7QE6pmxq_MDivA5jrqq"     # 기존 키 재사용 또는 새 발급
NAVER_CLIENT_SECRET = "9OfednhamT"

# 잡플래닛 - 동일 계정 재사용 가능
JOBPLANET_USER_ID = "catlife0202@kmu.kr"
JOBPLANET_PASSWORD = "hellcat9021@"
```

### [필수 수정 2] 대상 기업 리스트

```python
# 현재 의료 AI 프로젝트의 12개 기업:
TARGET_COMPANIES = {
    "뷰노":           {"company_id": "329047", "category": "스타트업_의료영상",   "비고": "의료영상 AI 진단"},
    "루닛":           {"company_id": "325870", "category": "스타트업_의료영상",   "비고": "흉부 X-ray AI"},
    "딥노이드":        {"company_id": "62240",  "category": "스타트업_의료영상",   "비고": "의료영상 딥러닝"},
    "제이엘케이":      {"company_id": "327410", "category": "스타트업_의료AI",     "비고": "뇌졸중 AI 진단"},
    "셀바스AI":       {"company_id": "79634",  "category": "중소기업_AI",         "비고": "음성인식/필기인식 AI + 헬스케어"},
    "라인웍스":        {"company_id": "390283", "category": "스타트업_디지털헬스",  "비고": "의료 자연어처리"},
    "메디컬에이아이":   {"company_id": "389808", "category": "스타트업_의료AI",     "비고": "심전도 AI 분석"},
    "닥터나우":        {"company_id": "377124", "category": "스타트업_원격의료",    "비고": "원격 진료 플랫폼"},
    "인피니트헬스케어": {"company_id": "57691",  "category": "중소기업_PACS",       "비고": "PACS/의료정보 시스템"},
    "카카오헬스케어":   {"company_id": "405810", "category": "대기업_헬스케어",     "비고": "디지털 헬스케어 플랫폼"},
    "네이버클라우드(의료)": {"company_id": "42216", "category": "대기업_클라우드",  "비고": "클라우드 기반 의료 AI"},
    "솔트룩스":        {"company_id": "71198",  "category": "중소기업_AI",         "비고": "AI 플랫폼(의료/산업 적용)"},
}

# ▼ 다른 분야로 변경 시: 기업명, company_id, category, 비고를 모두 교체
# company_id 찾는 법:
#   1. 잡플래닛 접속 → 기업 검색
#   2. 기업 페이지 URL 확인: https://www.jobplanet.co.kr/companies/329047/reviews/뷰노
#   3. URL의 숫자 = company_id (329047)
```

### [필수 수정 3] 블로그 검색 키워드

```python
# 현재: 의료 AI 취업 준비 관점의 22개 키워드
NAVER_BLOG_KEYWORDS = [
    "의료 AI 취업 준비",        # 취업 준비 일반
    "의료 AI 개발자 취업",
    "헬스케어 AI 취업",
    "의료영상 AI 개발자",       # 직무 특화
    "디지털헬스 취업",
    "의료 데이터 분석가",
    "의료 AI 신입 채용",        # 경력 단계
    "의료 AI 자격증",           # 역량 개발
    "의료 AI 포트폴리오",
    "의료 AI 인턴",
    "의료AI Python 개발",       # 기술 키워드
    "헬스케어 데이터 자격증",
    "의료 AI 석사 취업",
    "의료 AI 교육과정",
    "의료 영상 AI 취업",
    "DICOM 개발자",
    "바이오헬스 AI 취업",
    "의료 AI 논문 취업",
    "FDA SaMD 인허가",          # 도메인 특화
    "의료 AI 스타트업 취업",
    "임상시험 SAS 통계",
    "의료 SPSS 데이터분석",
]

# ▼ 변경 시: "의료 AI"를 "{분야명}"으로 교체하고 분야 특화 키워드 추가
```

### [필수 수정 4] 뉴스 검색 키워드

```python
# 현재: 산업 트렌드/채용 현황 관점의 15개 키워드
NAVER_NEWS_KEYWORDS = [
    "의료 AI 채용",             # 채용 현황
    "헬스케어 AI 인력",
    "의료 AI 스타트업 채용",
    "디지털 헬스케어 채용",
    "의료 AI 산업 전망",         # 산업 전망
    "헬스케어 데이터 채용",
    "의료AI 연봉",              # 보상
    "의료 AI 인력 수요",         # 인력 수급
    "의료 AI 개발자 부족",
    "의료 AI 기술 인재",
    "의료 데이터 사이언티스트",
    "의료 AI 투자",             # 투자/규제
    "헬스케어 AI 시장",
    "의료 AI 규제",
    "의료 AI 인허가",
]
```

### [필수 수정 5] 사람인/원티드 키워드

```python
SARAMIN_KEYWORDS = [
    "의료 AI", "의료 인공지능", "헬스케어 AI", "의료영상 분석",
    "디지털헬스", "헬스케어 Python", "의료 데이터", "바이오 AI",
    "의료 딥러닝", "의료 머신러닝", "PACS 개발", "EMR 개발",
]

WANTED_KEYWORDS = [
    "의료 AI", "헬스케어", "의료영상", "디지털헬스", "바이오 AI",
]
```

### [필수 수정 6] 키워드 색상 맵

```python
# 블로그 키워드 → 파란 계열, 뉴스 키워드 → 주황/빨강 계열
# 키워드 변경 시 동일한 색상 할당 규칙으로 재작성
KEYWORD_COLOR_MAP = {
    "의료 AI 취업 준비": "#1f77b4",
    # ... 전체 키워드에 색상 지정
}
```

### [필수 수정 7] 기술스택 키워드 사전

```python
# 현재: 의료 AI 특화 55개 기술
TECH_STACK_KEYWORDS = [
    # 프로그래밍 언어
    "Python", "R", "Java", "C++", "JavaScript",
    # AI/ML 프레임워크
    "PyTorch", "TensorFlow", "Keras", "OpenCV", "scikit-learn",
    # 의료 특화 (← 이 부분을 분야에 맞게 교체)
    "의료영상", "DICOM", "PACS", "HL7", "FHIR",
    "CT", "MRI", "X-ray", "병리", "내시경",
    # 통계/분석 도구
    "SAS", "SPSS", "통계분석", "임상시험", "FDA", "MFDS",
    # 인프라
    "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "SQL", "MongoDB", "PostgreSQL",
    "Git", "Linux", "MLOps", "MLflow",
    # 연구
    "논문", "SCI", "특허",
    # 웹 프레임워크
    "React", "FastAPI", "Django",
]
```

### [필수 수정 8] 자격증 키워드 사전

```python
# 현재: 의료 AI 관련 12개 자격증
CERTIFICATE_KEYWORDS = [
    "정보처리기사", "빅데이터분석기사", "ADsP", "ADP",
    "SQLD", "SQLP", "의공기사", "방사선사", "임상병리사",
    "AWS 자격증", "GCP 자격증", "데이터분석준전문가",
]
# ▼ 분야 특화 자격증으로 교체 (공통 IT 자격증은 유지)
```

### [필수 수정 9] 도메인 키워드

```python
# 현재: 의료 AI 5개 도메인 카테고리
MEDICAL_DOMAIN_KEYWORDS = {
    "영상의학": ["CT", "MRI", "X-ray", "초음파", "의료영상", "방사선"],
    "병리":    ["조직검사", "세포검사", "디지털병리", "병리", "슬라이드"],
    "임상":    ["EMR", "임상시험", "바이오마커", "임상데이터", "전자의무기록"],
    "인허가":  ["FDA", "MFDS", "SaMD", "CE마킹", "인허가", "510(k)"],
    "유전체":  ["유전체", "오믹스", "NGS", "게노믹스", "바이오인포매틱스"],
}

# ▼ 변경 시: 변수명도 DOMAIN_KEYWORDS 또는 {분야}_DOMAIN_KEYWORDS로 변경
# ▼ 참조하는 파일(text_analyzer.py, main.py)의 변수명도 함께 변경 필요
```

---

## 수정 불필요 항목 (그대로 재사용)

| 항목 | 값 | 이유 |
|------|---|------|
| `CRAWL_DELAY_MIN/MAX` | 2~5초 | 모든 분야에서 동일한 크롤링 예절 |
| `API_CALL_DELAY` | 0.1초 | API 호출 간격 표준 |
| `USER_AGENT` | Chrome UA | 모든 웹사이트에 공통 |
| `BASE_DIR` 등 경로 | 상대 경로 | 프로젝트 위치 자동 계산 |
| `KOREAN_FONT_CANDIDATES` | OS별 폰트 경로 | 한국어 프로젝트 공통 |
| `random_delay()` | 유틸 함수 | 범용 |

---

## 수정 체크리스트

- [ ] NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 확인 또는 새 발급
- [ ] JOBPLANET_USER_ID / JOBPLANET_PASSWORD 확인 또는 새 계정
- [ ] TARGET_COMPANIES 전면 교체 (10~15개 기업 + company_id)
- [ ] NAVER_BLOG_KEYWORDS 교체 (15~25개)
- [ ] NAVER_NEWS_KEYWORDS 교체 (10~15개)
- [ ] SARAMIN_KEYWORDS 교체 (8~12개)
- [ ] WANTED_KEYWORDS 교체 (3~5개)
- [ ] KEYWORD_COLOR_MAP 교체
- [ ] TECH_STACK_KEYWORDS 교체 (40~60개)
- [ ] CERTIFICATE_KEYWORDS 교체 (8~15개)
- [ ] MEDICAL_DOMAIN_KEYWORDS 변수명 + 내용 교체
- [ ] WORDCLOUD_MASK_PATH 마스크 이미지 경로 변경 (선택)
