# 헬창지피티 (HelChangGPT) v1.1

## AI가 설계하는 나만의 피트니스 라이프 코치

> K-Digital Training 빅데이터 분석가 교육과정 | 자연어처리 미니프로젝트

사용자가 자연어로 신체 정보와 운동 목표를 입력하면, **4단계 NLP 파이프라인**(프로필 분석 → 식단 생성 → 운동 루틴 → 동기부여 피드백)을 통해 개인 맞춤형 건강 관리를 제공하는 AI 피트니스 코칭 웹 서비스입니다.

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| Frontend | React 18 + Tailwind CSS (Neon Kinetic 디자인), CSS 변수 기반 다크/라이트 테마 |
| Backend | Python FastAPI (50+ 엔드포인트) |
| LLM | Ollama (EXAONE 3.5, Qwen 3.5, Gemma 4) |
| NLP | KcBERT, KeyBERT, BM25, sentence-transformers |
| i18n | 경량 딕셔너리 기반 다국어 (한/영/일) |
| 배포 | ngrok HTTPS 터널링 |
| 데이터 | 식품안전나라 API (1,146건), 운동 DB (24종), JSON 파일 기반 사용자 데이터 |

---

## 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Ollama 모델 다운로드
ollama pull exaone3.5:7.8b
ollama pull gemma4:e4b

# 3. 서버 실행
uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload &
cd frontend && npx vite --host 0.0.0.0 &

# 4. 접속
# http://localhost:5173
```

또는 원클릭 스크립트:
```bash
bash start_public.sh   # 백엔드 + 프론트 + ngrok 한 번에
bash stop_public.sh    # 전체 종료
```

---

## 프로젝트 폴더 구조

```
helchanggpt/
├── api/                      # FastAPI 백엔드 서버
├── src/                      # 핵심 NLP/LLM 비즈니스 로직
│   ├── profile/              #   Stage 1: 프로필 분석
│   ├── diet/                 #   Stage 2: 식단 생성
│   ├── workout/              #   Stage 3: 운동 루틴
│   ├── feedback/             #   Stage 4: 감성 분석 & 피드백
│   └── utils/                #   공통 유틸리티
├── frontend/                 # React 프론트엔드
│   └── src/
│       ├── pages/            #   페이지 컴포넌트 (8개)
│       ├── components/       #   공통 컴포넌트 (4개)
│       ├── context/          #   전역 상태 (Auth, Settings)
│       └── i18n/             #   다국어 번역 딕셔너리
├── data/                     # 데이터 저장소
├── scripts/                  # 데이터 수집 & 실험 스크립트
├── docs/                     # 보고서 & 기능 설명서
├── notebooks/                # Jupyter 노트북 (실험용)
├── requirements.txt          # Python 의존성
├── start_public.sh           # 원클릭 서버 시작 스크립트
└── stop_public.sh            # 서버 종료 스크립트
```

---

## 폴더별 상세 설명

### `api/` — FastAPI 백엔드 서버

| 파일 | 설명 |
|------|------|
| `main.py` | FastAPI 메인 앱 (50+ 엔드포인트). 인증, 프로필, 인바디, 식단, 운동, 피드백, 일기, 어드민 API 전체 포함 |

주요 API 그룹:
- **인증** — 회원가입, 로그인, 탈퇴
- **프로필** — 저장, BMI/BMR/TDEE 계산, NLP 분석, AI 채팅
- **인바디** — 다중 포맷 업로드(이미지/CSV/PDF/Word/Excel), 건강 분석
- **식단** — AI 식단 생성, 3일치 생성, 일정 변동 대응, 저장/조회/삭제
- **운동** — AI 루틴 생성, 운동 검색(BM25/임베딩/필터), 저장/조회/삭제
- **피드백** — 감성 분석 + 5종 모드별 AI 피드백
- **일기** — 저장, 이력 조회, 성장 통계
- **어드민** — 사용자 관리, 시스템 통계, 역할/비밀번호/활성화 관리

---

### `src/` — 핵심 NLP/LLM 비즈니스 로직

4단계(기·승·전·결) 파이프라인의 핵심 모듈입니다.

#### `src/profile/` — Stage 1: 프로필 분석 (기-起)

사용자의 신체 정보를 분석하여 구조화된 건강 프로필을 생성합니다.

| 파일 | 설명 |
|------|------|
| `profile_ner.py` | 정규식 기반 NER — 나이/성별/키/체중/운동빈도 추출 (정확도 100%) |
| `goal_classifier.py` | 운동 목표 5클래스 분류 (규칙+LLM, F1=0.849) |
| `goal_classifier_bert.py` | KcBERT 파인튜닝 비교 실험용 |
| `body_calculator.py` | Mifflin-St Jeor BMR, KSSO BMI 6단계, TDEE 계산 |
| `inbody_parser.py` | 인바디 다중 포맷 파싱 (이미지 비전/CSV/PDF/Word/Excel) |
| `inbody_analyzer.py` | 체형 분석(C/I/D), 내장지방, 근감소증(SMI), ECW 비율 |
| `health_analyzer.py` | 대사증후군 스크리닝, 프로필 신뢰도 점수 |
| `profile_builder.py` | 전체 분석 통합 → 구조화된 프로필 생성 |
| `report_generator.py` | PDF/Word/Excel/CSV/JSON 리포트 내보내기 |
| `user_history.py` | 사용자별 인바디 측정 이력 관리 (JSON) |
| `keyword_extractor.py` | KeyBERT 키워드 추출 |
| `evaluation.py` | NER 정확도, 목표 F1, BMR 비교 평가 |

#### `src/diet/` — Stage 2: 식단 생성 (승-承)

프로필 기반 맞춤형 식단을 생성하고 일정 변동에 대응합니다.

| 파일 | 설명 |
|------|------|
| `macro_calculator.py` | 목표별 탄단지 비율 계산 + 제약사항(당뇨/고혈압 등) 보정 |
| `nutrition_db.py` | 식품 영양성분 DB (API 1,146건 + 기본 30종) |
| `diet_prompts.py` | LLM 프롬프트 4종 (Zero-shot/Few-shot/CoT/Scheduled) |
| `diet_generator.py` | LLM 식단 생성 + 프롬프트 비교 실험 실행기 |
| `diet_analyzer.py` | 칼로리 정확도, 매크로 검증, 제약사항 위반 체크, KeyBERT 키워드 |
| `diet_adjuster.py` | 6가지 일정 변동 시나리오 감지 + 식단 재조정 |
| `meal_scheduler.py` | 시간대별 끼니 배정 (운동 전후 간식 포함) |
| `eating_out_db.py` | 외식/회식 메뉴 칼로리 추정 DB (21종) |

#### `src/workout/` — Stage 3: 운동 루틴 (전-轉)

개인 맞춤 운동 계획을 생성하고 안전한 운동을 추천합니다.

| 파일 | 설명 |
|------|------|
| `workout_prompts.py` | 면책 문구, 분할 추천 규칙, 유산소/근력 비율 기준 |
| `workout_generator.py` | LLM 7일 운동 루틴 생성 + 데모 루틴 + 제약사항 반영 |
| `exercise_search.py` | BM25 + 임베딩 + 필터 하이브리드 검색 + 제약 안전 필터링 |
| `workout_analyzer.py` | 근육군 균형 점수, 유산소 비율, 볼륨 평가 |

#### `src/feedback/` — Stage 4: 감성 분석 & 피드백 (결-結)

운동 일지의 감성을 분석하고 5종 모드로 동기부여 피드백을 생성합니다.

| 파일 | 설명 |
|------|------|
| `sentiment_analyzer.py` | 키워드 기반 감성 분석 (긍정/부정/중립, 정확도 70%) + LLM 병행 |
| `feedback_modes.py` | 5종 피드백 모드 정의 (코치/친구/교관/매미킴/해병문학) |
| `feedback_generator.py` | 규칙 기반 + LLM 기반 피드백 생성 (모드별 톤/스타일 적용) |
| `weekly_summarizer.py` | 주간 요약 + 하이라이트 추출 |

#### `src/utils/` — 공통 유틸리티

| 파일 | 설명 |
|------|------|
| `llm_client.py` | Ollama/OpenAI 통합 클라이언트, 11개 모델 레지스트리, 기본 모델 할당 |

---

### `frontend/` — React 프론트엔드

Neon Kinetic 디자인 시스템을 적용한 React 18 + Tailwind CSS SPA입니다.

#### `frontend/src/pages/` — 페이지 컴포넌트 (8개)

| 파일 | 설명 |
|------|------|
| `LoginPage.jsx` | 로그인/회원가입 (다국어 지원) |
| `OnboardingPage.jsx` | 내 몸 알기 — 4탭: 직접 입력, 인바디 업로드, AI 채팅, 프로필 보기 |
| `DietPage.jsx` | 오늘 뭐 먹지 — 3탭: AI 대화(+사이드 미리보기), 식단 보기, 저장 이력 |
| `WorkoutPage.jsx` | 오늘 뭐 하지 — 3탭: AI 트레이너, 상세 루틴 보기, 저장 이력 |
| `DiaryPage.jsx` | 운동 일기 — 3탭: 오늘의 일기(5종 피드백 모드), 성장 기록, 목표 달성률 |
| `SettingsPage.jsx` | 설정 — 언어(한/영/일), 테마(다크/라이트), AI 모델, 데이터 관리 |
| `AdminPage.jsx` | 시스템 관리 — 관리자 전용 대시보드, 시스템 통계 |
| `MemberManagePage.jsx` | 회원 관리 — 사용자 목록, 역할 변경, 비밀번호 초기화, 활성화 관리 |

#### `frontend/src/components/` — 공통 컴포넌트 (4개)

| 파일 | 설명 |
|------|------|
| `ModelSelector.jsx` | AI 모델 선택기 (6개 모델, 컴팩트/풀 모드) |
| `InBodyUploader.jsx` | 인바디 파일 업로드 (이미지/CSV/PDF/Word/Excel) |
| `NaturalLanguageInput.jsx` | 자연어 입력 + NER 분석 결과 표시 |
| `ProfilePreview.jsx` | 프로필 미리보기 카드 |

#### `frontend/src/context/` — 전역 상태 관리

| 파일 | 설명 |
|------|------|
| `AuthContext.jsx` | 인증 상태 (로그인/로그아웃/역할), localStorage 기반 |
| `SettingsContext.jsx` | 설정 상태 (테마/언어/모델) + `t()` 번역 함수 |

#### `frontend/src/i18n/` — 다국어 번역

| 파일 | 설명 |
|------|------|
| `translations.js` | 한국어/영어/일본어 번역 딕셔너리 (~50키 × 3언어, 핵심 UI) |

#### 프론트엔드 설정 파일

| 파일 | 설명 |
|------|------|
| `vite.config.js` | Vite 설정 — 프록시(→8002), 호스트 바인딩, ngrok 허용 |
| `tailwind.config.js` | Tailwind 설정 — CSS 변수 기반 색상, Neon Kinetic 토큰 |
| `postcss.config.js` | PostCSS 설정 (Tailwind + Autoprefixer) |
| `index.html` | 엔트리 HTML |

---

### `data/` — 데이터 저장소

수집 데이터, 학습 데이터, 사용자 데이터를 저장합니다.

| 폴더/파일 | 설명 |
|----------|------|
| `nutrition/` | 식품 영양성분 DB — `foods.json` (1,146건, 식품안전나라 API), `foods.csv`, `summary.json` |
| `exercises/` | 운동 DB — `exercise_db.json` (24종, 11개 근육군), `exercise_met.json` (30종 MET 참조) |
| `experiments/` | 실험 결과 — `experiment_results.json` (NER/분류/감성/BMR/검색 평가) |
| `user_samples/` | 학습/평가 데이터 — 목표분류 train/val/test (100+건), KNHANES 통계, Fitness100 참조 |
| `diary_samples/` | 일기 샘플 — `diary_samples.json` (데모/평가용 일지) |
| `users/` | 사용자 인증 데이터 — `{user_id}.json` (닉네임, 비밀번호 해시, 역할, 가입일) |
| `user_profiles/` | 사용자별 데이터 디렉토리 (아래 참조) |

#### `data/user_profiles/{user_id}/` — 사용자별 데이터

| 파일 | 설명 |
|------|------|
| `profile.json` | 최신 프로필 (NLP 분석 결과 포함) |
| `history.json` | 인바디 측정 이력 |
| `diet_history.json` | 저장된 식단 계획 이력 |
| `workout_history.json` | 저장된 운동 루틴 이력 |
| `diary_history.json` | 운동 일기 이력 |
| `activity_log.json` | 사용자 활동 로그 |

---

### `scripts/` — 데이터 수집 & 실험 스크립트

| 파일 | 설명 |
|------|------|
| `config.py` | 환경 설정 (API 키, 경로) |
| `fetch_nutrition_api.py` | 식품안전나라 COOKRCP01 API 식품 데이터 수집 |
| `fetch_food_data_go_kr.py` | 식품안전나라 I2790 API 수집 |
| `fetch_fitness100_api.py` | 국민체력100 API 기준 데이터 수집 |
| `build_exercise_db.py` | 운동 DB + MET 테이블 구축 |
| `process_knhanes.py` | 국민건강영양조사(KNHANES) 통계 가공 |
| `prepare_training_data.py` | 목표분류/감성분석 학습 데이터 생성 |
| `run_experiments.py` | 4단계 전체 평가 실험 실행기 (NER/분류/감성/BMR/검색) |
| `run_all.py` | 전체 스크립트 순차 실행 |

---

### `docs/` — 보고서 & 기능 설명서

| 파일 | 설명 |
|------|------|
| `final_report.md` | 최종 보고서 — 주제/모델/프롬프트/파라미터/결과/개선/한계점 (10개 필수 섹션) |
| `experiment_report.md` | 실험 결과 분석 — 4단계별 정량 평가 + v1.1 업데이트 내역 |
| `feature_01_my_body.md` | 기능 설명서: 내 몸 알기 (Stage 1) |
| `feature_02_diet.md` | 기능 설명서: 오늘 뭐 먹지? (Stage 2) |
| `feature_03_workout.md` | 기능 설명서: 오늘 뭐 하지? (Stage 3) |
| `feature_04_diary.md` | 기능 설명서: 운동 일기 (Stage 4) |

---

### `notebooks/` — Jupyter 노트북

실험 및 데이터 분석용 Jupyter 노트북을 저장하는 폴더입니다. (현재 비어 있음 — 필요 시 실험 분석 노트북 추가)

---

## 주요 실험 결과

| 단계 | NLP 기법 | 정확도/점수 |
|------|---------|-----------|
| Stage 1 NER | 정규식 기반 | **100%** (21/21 필드) |
| Stage 1 분류 | 키워드 매칭 | **85%**, F1=0.849 |
| Stage 2 식단 | LLM Few-shot | JSON 준수율 매우 높음 |
| Stage 3 검색 | BM25+필터 하이브리드 | 자연어+정확 매칭 최적 |
| Stage 4 감성 | 키워드 기반 | **70%** (LLM 병행 시 85%+) |

---

*최종 수정: 2026-04-10 | 헬창지피티 v1.1*
