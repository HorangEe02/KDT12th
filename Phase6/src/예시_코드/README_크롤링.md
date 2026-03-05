# 🚀 자율주행·의료 AI 취업 동향 크롤링 프로젝트

## Yeong 파트: 자율주행·의료 AI 분야 인재 수요 및 요구 역량 분석

---

## 📁 파일 구조

```
Yeong_크롤링/
├── crawl_naver_api.py        # Naver OpenAPI 크롤링 (블로그 + 뉴스)
├── crawl_jobplanet.py        # 잡플래닛 크롤링 (기업 리뷰/연봉/면접)
├── analyze_visualize.py      # 데이터 분석 및 시각화
├── README.md                 # 이 파일
│
├── data_naver/               # (자동 생성) Naver 수집 데이터
│   ├── naver_blog_자율주행_의료AI.csv
│   ├── naver_blog_자율주행_의료AI.json
│   ├── naver_news_자율주행_의료AI.csv
│   ├── naver_news_자율주행_의료AI.json
│   └── 크롤링_URL_목록_네이버.csv
│
├── data_jobplanet/           # (자동 생성) 잡플래닛 수집 데이터
│   ├── 잡플래닛_기업정보_자율주행_의료AI.csv
│   ├── 잡플래닛_리뷰_자율주행_의료AI.csv
│   ├── 잡플래닛_면접후기_자율주행_의료AI.csv
│   ├── 잡플래닛_전체데이터_자율주행_의료AI.json
│   └── 크롤링_URL_목록_잡플래닛.csv
│
└── data_analysis/            # (자동 생성) 분석 결과 차트
    ├── blog_keyword_freq.png
    ├── news_keyword_freq.png
    ├── tech_stack.png
    ├── cert_freq.png
    ├── field_comparison.png
    ├── wordcloud.png
    ├── company_ratings.png
    └── news_trend.png
```

---

## ⚙️ 실행 환경 설정

### 필수 패키지 설치

```bash
pip install requests beautifulsoup4 pandas matplotlib seaborn wordcloud selenium
```

### Chrome WebDriver (잡플래닛 크롤링용)

- **selenium 4.6 이상**: 자동 다운로드 지원 (별도 설치 불필요)
- **그 이하 버전**: [ChromeDriver](https://chromedriver.chromium.org/) 수동 설치

---

## 🚀 실행 순서

### 1단계: Naver OpenAPI 크롤링

```bash
python crawl_naver_api.py
```

- 블로그 20개 키워드 × 최대 30건 = 최대 600건
- 뉴스 15개 키워드 × 최대 30건 = 최대 450건
- 중복 제거 후 100개 이상 URL 확보 목표
- 예상 소요 시간: 약 3~5분

### 2단계: 잡플래닛 크롤링

```bash
python crawl_jobplanet.py
```

- 자율주행 기업 15개 + 의료AI 기업 15개 = 총 30개 기업
- 각 기업별: 기업정보 + 리뷰(3페이지) + 연봉 + 면접후기(2페이지)
- 예상 소요 시간: 약 20~30분
- ⚠️ CAPTCHA가 나올 경우 `--headless` 옵션 주석 해제 후 수동 로그인

### 3단계: 분석 및 시각화

```bash
python analyze_visualize.py
```

- 1, 2단계 데이터를 종합 분석
- 7개 시각화 차트 자동 생성
- 예상 소요 시간: 약 1분

---

## 📊 시각화 목록

| # | 차트 | 파일명 | 설명 |
|---|------|--------|------|
| 1 | 블로그 키워드별 수집 건수 | `blog_keyword_freq.png` | 어떤 키워드가 블로그에서 많이 다뤄지는지 |
| 2 | 뉴스 키워드별 수집 건수 | `news_keyword_freq.png` | 어떤 키워드가 뉴스에서 많이 보도되는지 |
| 3 | 요구 기술스택 TOP 20 | `tech_stack.png` | Python, PyTorch, ROS 등 기술 빈도 |
| 4 | 자격증 언급 빈도 | `cert_freq.png` | 정보처리기사, ADsP 등 자격증 빈도 |
| 5 | 자율주행 vs 의료AI 비교 | `field_comparison.png` | 두 분야 관심도 비교 |
| 6 | 취업 키워드 워드클라우드 | `wordcloud.png` | 전체 텍스트 키워드 시각화 |
| 7 | 기업 평점 비교 | `company_ratings.png` | 잡플래닛 기업 평점 비교 |
| 8 | 뉴스 트렌드 | `news_trend.png` | 월별 뉴스 발행 추이 |

---

## 🔑 API 키 정보

| 서비스 | 항목 | 값 |
|--------|------|-----|
| Naver OpenAPI | Client ID | `F7QE6pmxq_MDivA5jrqq` |
| Naver OpenAPI | Client Secret | `9OfednhamT` |
| 잡플래닛 | 이메일 | `catlife0202@kmu.kr` |
| 잡플래닛 | 비밀번호 | `hellcat9021@` |

> ⚠️ 실제 제출 시에는 API 키와 비밀번호를 마스킹하거나 환경변수로 관리하는 것을 권장합니다.

---

## 📋 크롤링 URL 요구사항

프로젝트 요구사항에 따라 1인당 최소 100개 이상의 크롤링 URL을 확보해야 합니다.

- **Naver OpenAPI**: 블로그 + 뉴스 = 약 200~500개 URL
- **잡플래닛**: 30개 기업 × 4종(기업/리뷰/연봉/면접) = 약 120개 URL
- **합계**: 최소 300개 이상 URL 확보 예상

URL 목록은 아래 파일에 자동 저장됩니다:
- `data_naver/크롤링_URL_목록_네이버.csv`
- `data_jobplanet/크롤링_URL_목록_잡플래닛.csv`

---

## ⚠️ 주의사항

1. **잡플래닛 크롤링 시 차단 방지**: 요청 간격을 3초로 설정했으나, 빈번한 실행 시 IP 차단될 수 있음
2. **Naver API 일일 한도**: 일 25,000건 (블로그/뉴스 각각)
3. **CAPTCHA**: 잡플래닛 로그인 시 CAPTCHA가 나올 경우 headless 모드를 해제하고 수동으로 진행
4. **데이터 정제**: 잡플래닛의 HTML 구조가 변경되면 CSS 셀렉터 수정이 필요할 수 있음
