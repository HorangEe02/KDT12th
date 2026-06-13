# Phase 1 - KDT12 Python 미니 프로젝트 모음

> **기간**: 2026년 1월
> **과정**: KDT12 Python
> **구성**: 게임 개발 (6개) + 의료 통계 시스템 (3개)

---

## 목차

1. [폴더 구조](#폴더-구조)
2. [게임 프로젝트 (make_a_game)](#게임-프로젝트-make_a_game)
   - [Simpsons DOOM](#1-h_doom---simpsons-doom)
   - [심슨 탁구](#2-pingpong_game---심슨-탁구)
   - [슈퍼 틱택토](#3-super_tictactoe---슈퍼-틱택토)
   - [틱택토](#4-tictactoe---틱택토)
   - [호머 배구](#5-volleyball---호머-배구)
   - [슈퍼 심슨 (폐기)](#6-super_homer폐기---슈퍼-심슨)
3. [의료 통계 프로젝트 (medical_stats)](#의료-통계-프로젝트-medical_stats)
   - [건강 상태 체크 시스템](#1-health_project---건강-상태-체크-시스템)
   - [통합 의료 시스템](#2-medical_system---통합-의료-시스템)
   - [환자 정보 관리 시스템](#3-patient_project---환자-정보-관리-시스템-crud)
4. [프로젝트 간 관계](#프로젝트-간-관계)
5. [기술 스택 요약](#기술-스택-요약)

---

## 폴더 구조

```
phase1/
├── make_a_game/                    # 게임 프로젝트
│   ├── h_doom/                     #   Simpsons DOOM (레이캐스팅 FPS)
│   ├── pingpong_game/              #   심슨 탁구 (2인용)
│   ├── super_tictactoe/            #   슈퍼 틱택토 (9x9 보드)
│   ├── tictactoe/                  #   틱택토 (콘솔)
│   ├── volleyball/                 #   호머 배구
│   └── super_homer(폐기)/          #   슈퍼 심슨 (개발 중단)
│
├── medical_stats/                  # 의료 통계 프로젝트
│   ├── health_project/             #   건강 상태 체크 시스템
│   ├── medical_system/             #   통합 의료 시스템 (건강체크 + 환자관리)
│   └── patient_project/            #   환자 정보 관리 시스템 (CRUD)
│
└── Phase1_Overview.md              # 본 문서
```

---

## 게임 프로젝트 (make_a_game)

### 1. `h_doom/` - Simpsons DOOM

DOOM(1993) 스타일의 레이캐스팅 기법을 활용한 심슨 테마 FPS 게임.
호머 심슨이 되어 맵에 숨겨진 도넛 6개를 수집하고, 플랜더스의 추격을 피해야 한다.

**핵심 기술**
- 레이캐스팅 3D 렌더링 (2D 맵 기반 유사 3D 시점)
- 어안 효과 보정 (Fisheye Correction)
- 빌보드 스프라이트 렌더링
- 적 AI (플랜더스 직선 추적)

**플랫폼**
| 구분 | Python 버전 | 웹 버전 |
|------|------------|---------|
| 환경 | Python 3 + Pygame | 웹 브라우저 (HTML5 Canvas) |
| 해상도 | 1024 x 768 | 700 x 450 |
| 이미지 | 외부 PNG 파일 | Base64 내장 |
| 모바일 | 미지원 | 터치 컨트롤 지원 |

**파일 구성**
| 파일 | 설명 |
|------|------|
| `simson_doom.py` | Python 메인 게임 코드 |
| `(beta_2)simson_doom_v2.py` | Python 베타 버전 |
| `simpsons_doom_complete.html` | 웹 버전 (단일 파일) |
| `d_g.png`, `s_g.png` | 도넛, 호머 이미지 |
| `flanders.png`, `gameover.png` | 플랜더스, 게임오버 이미지 |
| `original/` | 원본 팩맨 코드 |
| `test/` | JSX 베타, Python 데모 |

**게임 규칙**
- 시작 체력 100, 플랜더스 접촉 시 -1, 도넛 수집 시 +10
- 도넛 6개 모두 수집하면 승리, 체력 0이 되면 패배
- 맵: 16x16 2D 배열 (0=빈 공간, 1=벽, 2=도넛, 3=플랜더스)

---

### 2. `pingpong_game/` - 심슨 탁구

Tkinter 기반 2인 대전 심슨 테마 탁구 게임. 10점 선취 시 승리.

**핵심 기술**
- 스위트 스팟 시스템: 배트 중심/가장자리에 따라 반사각 변화
- 4방향 충돌 감지 (N/S/E/W)
- Pygame mixer를 이용한 "D'oh!" 효과음

**파일 구성**
| 파일 | 설명 |
|------|------|
| `main.py` | 게임 루프, 키 바인딩, 이벤트 처리 |
| `table.py` | 캔버스(테이블) 클래스 |
| `ball.py` | 공 클래스 (물리 이동, 벽 반사) |
| `bat.py` | 패들 클래스 (충돌 감지, 스위트 스팟) |
| `simson/` | 이미지 4개 + `doh.mp3` 사운드 |

**조작법**
| 키 | 동작 |
|----|------|
| W / S | 왼쪽 배트 상하 이동 |
| 방향키 위/아래 | 오른쪽 배트 상하 이동 |
| Space | 게임 시작/재시작 |
| ESC | 게임 종료 |

**의존성**: tkinter, PIL/Pillow, pygame

---

### 3. `super_tictactoe/` - 슈퍼 틱택토

9개의 작은 3x3 보드로 구성된 Ultimate Tic-Tac-Toe.
**강제 이동 규칙**이 적용되어 전략적 깊이가 더해진 고급 틱택토.

**게임 규칙**
- 작은 보드에서 승리하면 해당 보드를 차지
- 큰 보드에서 가로/세로/대각선 3개를 먼저 차지하면 승리
- 내가 놓은 셀의 위치가 상대의 다음 보드를 결정 (강제 이동)

**파일 구성**
| 파일 | 설명 |
|------|------|
| `super_tictactoe.py` | 게임 코드 (~450줄, 클래스 2개) |
| `super_tictactoe.md` | 코드 분석 문서 |

**클래스 구조**
- `GameBoard`: 게임 로직 (보드 상태, 승리 판정, 유효 이동 관리)
- `SuperTicTacToe`: GUI 및 상호작용 (UI 생성, 이벤트 처리, AI)

**AI 전략** (우선순위)
1. 전체 게임 즉시 승리 수 탐색
2. 상대 승리 차단 (방어)
3. 위치 선호: 중앙(4) > 모서리(0,2,6,8) > 변(1,3,5,7)

**의존성**: tkinter, random (표준 라이브러리만 사용)

---

### 4. `tictactoe/` - 틱택토

콘솔(CLI) 기반 클래식 3x3 틱택토 게임.

**파일 구성**
| 파일 | 설명 |
|------|------|
| `tictactoe.py` | 게임 코드 (~130줄) |
| `tictactoe.md` | 코드 분석 문서 |

**모드**
- 싱글 플레이어 (vs AI): 플레이어 X, AI O
- 2인용: 번갈아가며 플레이

**AI 전략** (우선순위)
1. AI 승리 수 탐색
2. 플레이어 승리 수 차단
3. 랜덤 선택

**입력**: `행 열` 형식 (예: `1 2`), 좌표 1~3

**의존성**: random, time (표준 라이브러리만 사용)

---

### 5. `volleyball/` - 호머 배구

Pygame 기반 심슨 테마 배구 게임. 11점 선취 시 승리.

**물리 시뮬레이션**
| 상수 | 값 | 설명 |
|------|----|------|
| GRAVITY | 0.8 | 중력 가속도 |
| JUMP_STRENGTH | -15 | 점프 힘 |
| MOVE_SPEED | 7 | 이동 속도 |
| BALL_BOUNCE | 0.85 | 공 바운스 계수 |

**파일 구성**
| 파일 | 설명 |
|------|------|
| `homer_volleyball.py` | 게임 코드 |
| `simson/` | 이미지 4개 + `doh.mp3` 사운드 |

**의존성**: pygame

---

### 6. `super_homer(폐기)/` - 슈퍼 심슨

슈퍼 마리오 스타일 심슨 횡스크롤 게임. **개발 중단됨.**

**파일 구성**
| 파일 | 설명 |
|------|------|
| `super_simpson.py` | 게임 코드 (미완성) |

**특징**
- 호머, 플랜더스, 스미더스 캐릭터를 Pygame 도형으로 직접 그려서 구현
- 외부 이미지 파일 없이 코드로 캐릭터 렌더링

**의존성**: pygame

---

## 의료 통계 프로젝트 (medical_stats)

### 1. `health_project/` - 건강 상태 체크 시스템

건강 정보를 입력하면 BMI, 혈압, 심혈관 질환 위험도를 분석하고 맞춤형 건강 조언을 제공하는 시스템.

**주요 기능**
| 기능 | 설명 |
|------|------|
| BMI 분석 | WHO 아시아-태평양 기준 (저체중~고도비만 5단계) |
| 혈압 분석 | 대한고혈압학회 기준 (저혈압~2기 고혈압 6단계) |
| 심혈관 위험도 | 나이, BMI, 혈압, 콜레스테롤, 혈당, 생활습관 종합 평가 |
| 건강 기록 | CSV 파일로 기록 저장 및 조회 |
| Kaggle 통계 | 70,000건 데이터 기반 평균값 비교 |

**프로젝트 구조**
```
health_project/
├── data/
│   ├── sample_data.csv         # Kaggle 형식 샘플 데이터 (50건)
│   └── user_records.csv        # 사용자 기록 저장 파일
├── src/
│   ├── main.py                 # 메인 GUI 프로그램
│   ├── health_checker.py       # 건강 분석 클래스
│   └── data_manager.py         # 데이터 관리 클래스
├── docs/
│   └── 설계문서.md
├── 건강체크시스템_README.md
└── 건강체크시스템_설계문서.md
```

**데이터 출처**: Kaggle - Cardiovascular Disease Dataset (70,000건)

**의존성**: tkinter (Python 기본 포함)

---

### 2. `medical_system/` - 통합 의료 시스템

건강 체크 시스템과 환자 관리 시스템을 **하나로 통합 연동**한 확장 버전.

**시스템 구조**
```
medical_system/
├── data/
│   ├── cardiovascular_sample.csv   # 심혈관 샘플 데이터
│   ├── health_records.csv          # 건강 기록
│   └── patients.csv                # 환자 데이터
├── src/
│   ├── main.py                     # 통합 메인 진입점
│   ├── health_app/                 # 건강 체크 모듈
│   │   ├── data_manager.py
│   │   ├── health_checker.py
│   │   └── health_gui.py
│   ├── patient_app/                # 환자 관리 모듈
│   │   ├── patient.py
│   │   ├── patient_manager.py
│   │   └── patient_gui.py
│   └── integration/                # 연동 모듈
│       └── integration_manager.py
├── docs/
│   ├── 설계문서.md
│   └── 연동설계서.md
├── 건강체크시스템_README.md
├── 건강체크시스템_설계문서.md
└── 연동설계서.md
```

**연동 방식**
- 공통 필드 (이름, 나이, 성별)로 환자 매칭
- `patient_id`를 건강 기록에 추가하여 명확한 연결
- 건강 위험도 → 진단명 자동 매핑 (비만 → Obesity, 고혈압 → Hypertension 등)

**의존성**: tkinter (Python 기본 포함)

---

### 3. `patient_project/` - 환자 정보 관리 시스템 (CRUD)

병원/의료기관에서 환자 정보를 효율적으로 관리하기 위한 CRUD 시스템.

**CRUD 기능**
| 기능 | 설명 |
|------|------|
| Create | 새 환자 등록 (자동 ID 생성, 입력값 유효성 검사) |
| Read | 전체 목록/검색/상세 정보 조회 |
| Update | 모든 필드 수정 가능, 실시간 파일 저장 |
| Delete | 삭제 전 확인 다이얼로그, 안전한 삭제 처리 |

**추가 기능**
- 퇴원 처리 (입원 → 퇴원 상태 변경, 오늘 날짜 자동 기록)
- 통계 대시보드 (성별 분포, 진단명별 환자 수, 비용 분석)
- 상태바 (총 환자 수, 입원 중, 오늘 입원)

**프로젝트 구조**
```
patient_project/
├── data/
│   ├── patients.csv                # 환자 데이터
│   └── healthcare_dataset.csv.zip  # Kaggle 원본 데이터
├── src/
│   ├── main.py                     # 메인 GUI 프로그램
│   ├── patient.py                  # Patient 클래스 (모델)
│   └── patient_manager.py          # PatientManager 클래스 (CRUD)
├── docs/
│   └── 설계문서.md
├── 환자관리시스템_README.md
└── 환자관리시스템_설계문서.md
```

**단축키**
| 단축키 | 기능 |
|--------|------|
| `Ctrl+N` | 새 환자 등록 |
| `Ctrl+F` | 검색창 포커스 |
| `Ctrl+E` | 선택 환자 수정 |
| `Delete` | 선택 환자 삭제 |
| `F5` | 테이블 새로고침 |
| `Double-Click` | 상세 정보 보기 |

**데이터 출처**: Kaggle - Healthcare Dataset (합성 데이터)

**의존성**: tkinter (Python 기본 포함)

---

## 프로젝트 간 관계

```
make_a_game/
  h_doom ·········· 독립 프로젝트 (레이캐스팅 FPS)
  pingpong_game ··· 독립 프로젝트 (2인 탁구)
  super_tictactoe · tictactoe의 확장판 (3x3 → 9x9)
  tictactoe ······· 기본 틱택토
  volleyball ······ 독립 프로젝트 (배구)
  super_homer ····· 독립 프로젝트 (폐기)

medical_stats/
  health_project ──────┐
    (건강 체크 단독)      │  통합
                         ▼
  medical_system ◄──── 두 시스템을 하나로 연동
    (건강 체크 + 환자관리)  ▲
                         │  통합
  patient_project ─────┘
    (환자 관리 단독)
```

- `health_project`와 `patient_project`는 각각 독립적으로 실행 가능한 프로젝트
- `medical_system`은 두 프로젝트를 통합하고 연동 모듈을 추가한 확장 버전

---

## 기술 스택 요약

### 사용 라이브러리별 프로젝트

| 기술 | 사용 프로젝트 |
|------|-------------|
| **Pygame** | h_doom, pingpong_game, volleyball, super_homer |
| **Tkinter** | pingpong_game, super_tictactoe, health_project, medical_system, patient_project |
| **HTML5 Canvas / JavaScript** | h_doom (웹 버전) |
| **PIL / Pillow** | pingpong_game |
| **CSV 파일 I/O** | health_project, medical_system, patient_project |
| **표준 라이브러리만** | tictactoe |

### KDT12 학습 내용 활용

| Day | 학습 주제 | 활용 내용 |
|-----|----------|-----------|
| Day 02 | 조건문 / 반복문 | BMI 판정, 혈압 분류, 게임 승리 조건, AI 전략 |
| Day 03 | 자료구조 | 딕셔너리로 데이터 관리, 게임 맵 배열 |
| Day 04 | 함수 | 분석 함수, 충돌 감지, CRUD 함수 |
| Day 05 | 모듈 | 프로젝트별 모듈 분리 (health_checker, patient_manager 등) |
| Day 06 | 클래스 | OOP 설계 (Ball, Bat, GameBoard, Patient 등) |
| Day 07 | tkinter | GUI 인터페이스 (버튼, Treeview, Canvas 등) |
| Day 08 | 파일 I/O | CSV 저장/불러오기, 데이터 영속성 |

---

## 실행 환경

- **Python**: 3.x
- **OS**: macOS / Windows / Linux
- **필수 패키지** (게임 프로젝트): `pip install pygame pillow`
- **필수 패키지** (의료 프로젝트): 추가 설치 없음 (표준 라이브러리만 사용)
