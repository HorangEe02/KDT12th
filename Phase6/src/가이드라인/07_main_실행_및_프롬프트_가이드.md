# 07. main.py 실행 및 클로드 코드 프롬프트 가이드

> `main.py`는 전체 파이프라인의 **오케스트레이터**로, 5개 Phase를 순차 실행한다.
> 클로드 코드에게 제공할 프롬프트 템플릿도 함께 정리한다.

---

## 1. main.py 구조

### 함수 구성

```python
# Phase별 실행 함수
def run_crawling(source="all")          # Phase 1: 크롤링
def run_processing()                     # Phase 2: 전처리
def run_analysis()                       # Phase 3: 텍스트/연봉 분석
def run_visualization(analysis_results)  # Phase 4: 시각화
def organize_url_list()                  # Phase 5: URL 정리

# 메인 엔트리포인트
def main()                               # argparse CLI
```

### CLI 사용법

```bash
# 전체 파이프라인 실행
python main.py

# 특정 Phase만 실행
python main.py --phase crawl         # 크롤링만
python main.py --phase process       # 전처리만
python main.py --phase analyze       # 분석만
python main.py --phase visualize     # 시각화만

# 크롤링 소스 선택
python main.py --phase crawl --source naver
python main.py --phase crawl --source saramin
python main.py --phase crawl --source wanted
python main.py --phase crawl --source jobplanet

# 크롤링 건너뛰기 (이미 수집된 데이터로 분석만)
python main.py --skip-crawl
```

### CLI 인자

| 인자 | 선택값 | 기본값 | 설명 |
|------|--------|--------|------|
| `--phase` | crawl, process, analyze, visualize, all | all | 실행할 Phase |
| `--source` | naver, saramin, wanted, jobplanet, all | all | 크롤링 소스 |
| `--skip-crawl` | (플래그) | False | 크롤링 건너뛰기 |

---

## 2. 분야 전환 시 수정 포인트

```python
# [수정 1] 파일명 접미사 매칭 패턴
# run_processing() 내부에서 raw 파일을 찾을 때 패턴 매칭
# 기존: "_의료AI" → 변경: "_{분야명}"

# [수정 2] 도메인 분석 함수 호출명
# run_analysis() 내부
# 기존:
domain_freq = analyzer.get_medical_domain_frequency(job_data)
# 변경:
domain_freq = analyzer.get_domain_frequency(job_data)

# [수정 3] 시각화 data_dict 키
# run_visualization() 내부
# 기존: data_dict["medical_domain"] = ...
# 변경: data_dict["domain"] = ... (시각화 모듈과 키 이름 맞춤)

# [수정 4] CLI 도움말 텍스트 (선택)
# argparse의 description, help 문자열 변경
```

---

## 3. 실행 순서 가이드

### 최초 실행 (전체 파이프라인)

```bash
# 1. settings.py 설정 완료 확인
# 2. 필요 라이브러리 설치
pip install requests beautifulsoup4 selenium pandas numpy
pip install matplotlib seaborn plotly wordcloud pillow
pip install konlpy tqdm python-dotenv squarify networkx

# 3. Chrome WebDriver 설치 (잡플래닛용)
# macOS: brew install chromedriver
# 또는 수동 다운로드: https://chromedriver.chromium.org

# 4. 전체 실행
python main.py
```

### 재분석 (기존 데이터 활용)

```bash
# 크롤링 건너뛰고 전처리~시각화만 재실행
python main.py --skip-crawl

# 시각화만 재실행
python main.py --phase visualize
```

---

## 4. 클로드 코드 프롬프트 템플릿

### 프롬프트 1: 전체 프로젝트 생성

```
다음 프로젝트를 참고하여 [{분야명}] 분야의 취업 동향 분석 프로젝트를 만들어줘:

참고 프로젝트:
/path/to/medical_ai_analysis/

가이드라인 문서:
/path/to/outputs/reports/가이드라인/ 디렉토리의 00~07번 가이드 전체

대상 기업 목록 (잡플래닛 company_id 포함):
1. {기업명} (company_id: {ID}) - {카테고리} - {설명}
2. {기업명} (company_id: {ID}) - {카테고리} - {설명}
... (10~15개)

핵심 기술 스택 (50개):
프로그래밍: Python, Java, ...
프레임워크: Spring, React, ...
분야 특화: {기술1}, {기술2}, ...

관련 자격증: {자격증1}, {자격증2}, ...

도메인 키워드 카테고리:
- {카테고리1}: {키워드1}, {키워드2}, ...
- {카테고리2}: {키워드3}, {키워드4}, ...
- {카테고리3}: {키워드5}, {키워드6}, ...

네이버 API:
  Client ID: F7QE6pmxq_MDivA5jrqq
  Client Secret: 9OfednhamT

잡플래닛 계정:
  ID: catlife0202@kmu.kr
  PW: hellcat9021@

원티드 카테고리 ID: {ID}

워드클라우드 마스크: {분야 상징 이미지 경로 또는 "기본 사각형"}
```

### 프롬프트 2: settings.py만 생성

```
/path/to/medical_ai_analysis/config/settings.py를 참고하여
[{분야명}] 분야에 맞는 settings.py를 만들어줘.

01_config_모듈_가이드.md의 체크리스트를 따라 모든 항목을 변경해줘.

대상 기업 (잡플래닛 company_id 포함):
- {기업명}: {company_id}, {카테고리}
... (10~15개)

블로그 검색 키워드 (20개): {분야} 취업 준비 관점
뉴스 검색 키워드 (15개): {분야} 산업 트렌드 관점
사람인 키워드 (12개): {분야} 채용공고 검색
원티드 키워드 (5개): {분야} 카테고리
기술스택 키워드 (50개): {주요 기술 나열}
자격증 키워드 (12개): {자격증 나열}
도메인 키워드 카테고리: {카테고리 구조}

API 인증:
  네이버 Client ID: F7QE6pmxq_MDivA5jrqq
  네이버 Client Secret: 9OfednhamT
  잡플래닛 ID: catlife0202@kmu.kr
  잡플래닛 PW: hellcat9021@
```

### 프롬프트 3: 기존 프로젝트 분야 전환

```
/path/to/medical_ai_analysis/ 프로젝트의 모든 Python 파일을
[{분야명}] 분야에 맞게 수정해줘.

가이드라인 폴더의 00~07번 문서를 순서대로 참고하여
각 모듈의 체크리스트 항목을 모두 수정해줘.

변경할 내용:
- 분야명: {분야명}
- 대상 기업: {기업 목록 + company_id}
- 기술 스택: {기술 목록}
- 자격증: {자격증 목록}
- 도메인 키워드: {카테고리별 키워드}
- 원티드 카테고리 ID: {ID}
- 마스크 이미지: {경로}

네이버/잡플래닛 인증 정보는 기존 것 재사용:
  네이버 Client ID: F7QE6pmxq_MDivA5jrqq
  네이버 Client Secret: 9OfednhamT
  잡플래닛 ID: catlife0202@kmu.kr
  잡플래닛 PW: hellcat9021@
```

### 프롬프트 4: 특정 모듈만 수정

```
/path/to/medical_ai_analysis/의 [{모듈 폴더}] 모듈을
[{분야명}] 분야에 맞게 수정해줘.

가이드라인 참고: /path/to/outputs/reports/가이드라인/{해당 번호}_가이드.md
변경 사항: {구체적인 변경 사항}
```

### 프롬프트 5: 보고서 작성 요청

```
/path/to/{분야명}_analysis/ 프로젝트의 모든 파일을 확인한 후
결과 보고서를 작성해줘. md 파일로 만들어줘.

포함 내용:
- 각 크롤링 한 결과에 대한 이유 설명
- 각 기업을 선택해서 가져오게 된 이유와 과정
- 시각화 한 결과에 대해서 각 시각화를 사용한 이유와 결과 해석
```

---

## 5. 실행 시 주의사항

### 잡플래닛 크롤링

- **Chrome WebDriver**가 설치되어 있어야 함
- `headless=False` 시 실제 브라우저 창이 열림 (모니터링 가능)
- 기업 간 **3~6초 랜덤 딜레이** 자동 적용
- 로그인 실패 시 크롤링이 중단되므로 계정 상태 확인 필요

### 네이버 API

- 하루 **25,000건** 호출 제한
- 키워드 22+15=37개 × 30건 = 약 1,110건 → 충분히 여유
- API 호출 간 **0.1초** 딜레이 적용

### 원티드 API

- 공개 API이므로 인증 불필요
- 요청 빈도 제한이 있으므로 딜레이 준수
- API 구조 변경 시 파싱 로직 수정 필요

### 사람인

- 웹 스크래핑 방식이므로 HTML 구조 변경 시 파싱 로직 수정 필요
- 요청 간 **2~5초** 랜덤 딜레이 적용
- User-Agent 헤더로 정상 브라우저로 인식

---

## 6. 수정 체크리스트

- [ ] main.py: 파일명 매칭 패턴 변경 (`_의료AI` → `_{분야명}`)
- [ ] main.py: `get_medical_domain_frequency()` → `get_domain_frequency()` 호출명 변경
- [ ] main.py: data_dict 키 변경 (`"medical_domain"` → `"domain"`)
- [ ] main.py: CLI 도움말 텍스트 변경 (선택)
