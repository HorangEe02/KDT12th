# 04. data 디렉토리 가이드

> 크롤링 원본 데이터(`raw/`)와 전처리 완료 데이터(`processed/`)를 저장하는 디렉토리이다.
> 분야 전환 시 파일명 패턴만 이해하면 된다.

---

## 디렉토리 구조

```
data/
├── raw/                    ← 크롤러가 저장하는 원본 데이터
│   ├── naver_blog_의료AI.csv
│   ├── naver_blog_의료AI.json
│   ├── naver_news_의료AI.csv
│   ├── naver_news_의료AI.json
│   ├── 원티드_포지션_의료AI.csv
│   ├── 잡플래닛_기업정보_의료AI.csv
│   ├── 잡플래닛_리뷰_의료AI.csv
│   └── 잡플래닛_면접후기_의료AI.csv
│
└── processed/              ← DataCleaner가 전처리한 데이터
    ├── naver_blog_의료AI_processed.csv        (532건)
    ├── naver_news_의료AI_processed.csv        (451건)
    ├── 원티드_포지션_의료AI_processed.csv      (75건)
    ├── 잡플래닛_기업정보_의료AI_processed.csv   (13건)
    ├── 잡플래닛_리뷰_의료AI_processed.csv      (156건)
    ├── 잡플래닛_면접후기_의료AI_processed.csv   (304건)
    │
    │  [TextAnalyzer 분석 결과]
    ├── tech_stack_frequency.csv               (38종)
    ├── certificate_frequency.csv              (7종)
    ├── medical_domain_frequency.csv           (21종)
    └── word_frequency.csv                     (51종)
```

---

## 파일명 규칙

### raw/ (원본)

```
{소스명}_{데이터유형}_{분야명}.csv
{소스명}_{데이터유형}_{분야명}.json    (네이버만 JSON도 생성)
```

| 소스명 | 데이터유형 | 파일명 예시 |
|--------|----------|-----------|
| naver_blog | 블로그 | `naver_blog_의료AI.csv` |
| naver_news | 뉴스 | `naver_news_의료AI.csv` |
| 원티드_포지션 | 채용공고 | `원티드_포지션_의료AI.csv` |
| 잡플래닛_기업정보 | 기업정보 | `잡플래닛_기업정보_의료AI.csv` |
| 잡플래닛_리뷰 | 기업리뷰 | `잡플래닛_리뷰_의료AI.csv` |
| 잡플래닛_면접후기 | 면접후기 | `잡플래닛_면접후기_의료AI.csv` |

### processed/ (전처리 완료)

```
{원본 파일명}_processed.csv          ← 전처리 완료 데이터
{분석유형}_frequency.csv             ← 빈도 분석 결과
```

---

## 분야 전환 시 변경 사항

### 파일명 접미사만 변경

```
기존: naver_blog_의료AI.csv
변경: naver_blog_{분야명}.csv       (예: naver_blog_핀테크.csv)
```

이 변경은 **크롤러의 `save_data()` 호출 시 파일명**에서 자동으로 결정된다. 크롤러의 파일명만 바꾸면 data/ 디렉토리의 파일명도 자동으로 변경된다.

### 빈도 분석 파일명

```
tech_stack_frequency.csv         ← 변경 불필요 (분야 무관)
certificate_frequency.csv        ← 변경 불필요
medical_domain_frequency.csv     ← domain_frequency.csv로 변경 권장
word_frequency.csv               ← 변경 불필요
```

---

## 각 파일의 컬럼 구조

### naver_blog_*_processed.csv

| 컬럼 | 타입 | 설명 |
|------|------|------|
| title | str | 블로그 제목 (HTML 태그 제거됨) |
| description | str | 본문 요약 |
| bloggername | str | 블로거 이름 |
| bloggerlink | str | 블로그 주소 |
| link | str | 원문 URL |
| pubDate | str | 게시일 (YYYY-MM-DD) |
| 검색키워드 | str | 수집 키워드 |

### naver_news_*_processed.csv

| 컬럼 | 타입 | 설명 |
|------|------|------|
| title | str | 뉴스 제목 |
| description | str | 본문 요약 |
| originallink | str | 뉴스 원문 URL |
| link | str | 네이버 뉴스 URL |
| pubDate | str | 게시일 (YYYY-MM-DD) |
| 검색키워드 | str | 수집 키워드 |

### 원티드_포지션_*_processed.csv

| 컬럼 | 타입 | 설명 |
|------|------|------|
| position_id | int | 포지션 고유 ID |
| 회사명 | str | 기업명 |
| 포지션명 | str | 채용 포지션 제목 |
| 기술태그 | str | 기술 태그 (쉼표 구분) |
| 카테고리 | str | 하위 카테고리 |
| 경력요건 | str | 최소~최대 경력 |
| 지역 | str | 근무지 |
| 자격요건 | str | 자격요건 전문 |
| 우대사항 | str | 우대사항 전문 |

### 잡플래닛_기업정보_*_processed.csv

| 컬럼 | 타입 | 설명 |
|------|------|------|
| 기업명 | str | 회사명 |
| 평점 | float | 총 평점 (5점 만점) |
| 업종 | str | 업종 분류 |
| 규모 | str | 직원 수 범위 |
| 설립연도 | str | 설립 연도 |
| 위치 | str | 본사 소재지 |
| category | str | 기업 카테고리 (settings에서 지정) |

### 잡플래닛_리뷰_*_processed.csv

| 컬럼 | 타입 | 설명 |
|------|------|------|
| 기업명 | str | 회사명 |
| 장점 | str | 리뷰 장점 텍스트 |
| 단점 | str | 리뷰 단점 텍스트 |
| 경영진평가 | str | 경영진에 대한 의견 |
| 재직상태 | str | 현직자 / 전직자 |
| 직종 | str | 직무 분류 |
| 평점 | float | 개별 리뷰 평점 |

### 잡플래닛_면접후기_*_processed.csv

| 컬럼 | 타입 | 설명 |
|------|------|------|
| 기업명 | str | 회사명 |
| 면접질문 | str | 실제 면접 질문 |
| 난이도 | str | 면접 난이도 |
| 면접결과 | str | 합격/불합격/대기 |
| 경로 | str | 지원 경로 |
| 직종 | str | 지원 직종 |

### tech_stack_frequency.csv

```
기술스택,빈도,비율(%)
```

### certificate_frequency.csv

```
자격증,빈도,비율(%)
```

### medical_domain_frequency.csv

```
카테고리,키워드,빈도
```

### word_frequency.csv

```
단어,빈도,비율(%)
```

---

## 데이터 흐름 요약

```
[Phase 1: 크롤링]
  crawlers/ → data/raw/*.csv

[Phase 2: 전처리]
  data/raw/*.csv → processors/data_cleaner → data/processed/*_processed.csv

[Phase 3: 분석]
  data/processed/*_processed.csv → processors/text_analyzer → data/processed/*_frequency.csv

[Phase 4: 시각화]
  data/processed/*.csv → visualizations/ → outputs/charts/*.png
```

---

## 수정 체크리스트

- [ ] 크롤러에서 저장 파일명의 `_의료AI` 접미사를 `_{분야명}`으로 변경
- [ ] (선택) `medical_domain_frequency.csv` → `domain_frequency.csv`로 변경
- [ ] 디렉토리 자체는 자동 생성되므로 수동 생성 불필요 (settings.py에서 `os.makedirs` 자동 실행)
