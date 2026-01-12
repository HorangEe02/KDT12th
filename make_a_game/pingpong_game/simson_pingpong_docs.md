# 심슨 핑퐁 게임 코드 분석 📄

이 문서는 Python과 Tkinter를 사용하여 제작된 심슨 테마 핑퐁 게임의 소스 코드를 분석하고 설명합니다.

---

## 프로젝트 구조

```
simson_pingpong/
├── main.py      # 게임 메인 로직 및 실행 파일
├── table.py     # 게임 테이블(캔버스) 클래스
├── ball.py      # 공 클래스
└── bat.py       # 배트(패들) 클래스
```

---

## 1. table.py - 게임 테이블 클래스

게임이 진행되는 캔버스(테이블)를 정의하는 클래스입니다.

### 클래스 구조

```python
class Table:
    def __init__(self, window, background_image=None, net_colour="yellow",
                 width=800, height=600, vertical_net=True, horizontal_net=False)
```

### 주요 속성

| 속성 | 타입 | 설명 |
|------|------|------|
| `width` | int | 테이블 너비 (기본값: 800) |
| `height` | int | 테이블 높이 (기본값: 600) |
| `canvas` | Canvas | Tkinter 캔버스 객체 |
| `bg_photo` | ImageTk | 배경 이미지 |
| `scoreboard` | int | 득점판 캔버스 아이템 ID |

### 주요 메서드

| 메서드 | 설명 |
|--------|------|
| `draw_rectangle(rectangle)` | 캔버스에 직사각형(배트) 추가 |
| `draw_image(image_obj)` | 캔버스에 이미지(공) 추가 |
| `move_item(item, x1, y1, x2, y2)` | 아이템 위치 이동 |
| `remove_item(item)` | 아이템 삭제 |
| `change_item_colour(item, c)` | 아이템 색상 변경 |
| `draw_score(left, right)` | 득점판 업데이트 |

### 특징

- PIL(Pillow) 라이브러리를 사용하여 배경 이미지 로드 및 리사이즈
- 이미지 로드 실패 시 기본 하늘색 배경으로 폴백
- 중앙에 점선 네트 표시 (수직/수평 선택 가능)
- Monaco 폰트로 득점판 표시

---

## 2. ball.py - 공 클래스

게임에서 움직이는 공을 정의하는 클래스입니다.

### 클래스 구조

```python
class Ball:
    def __init__(self, table, image_path, width=50, height=50,
                 x_speed=8, y_speed=0, x_start=0, y_start=0)
```

### 주요 속성

| 속성 | 타입 | 설명 |
|------|------|------|
| `width`, `height` | int | 공의 크기 |
| `x_posn`, `y_posn` | int | 현재 위치 |
| `x_speed`, `y_speed` | int | 이동 속도 |
| `photo` | ImageTk | 공 이미지 |
| `circle` | int | 캔버스 아이템 ID |

### 주요 메서드

| 메서드 | 설명 |
|--------|------|
| `start_position()` | 공을 시작 위치로 리셋 |
| `start_ball(x_speed, y_speed)` | 랜덤 방향으로 공 시작 |
| `move_next()` | 다음 프레임으로 공 이동 |
| `stop_ball()` | 공 정지 |

### 물리 로직

```python
def move_next(self):
    # 위치 업데이트
    self.x_posn = self.x_posn + self.x_speed
    self.y_posn = self.y_posn + self.y_speed

    # 상단 벽 충돌 → y 방향 반전
    if self.y_posn <= 3:
        self.y_speed = -self.y_speed

    # 하단 벽 충돌 → y 방향 반전
    if self.y_posn >= (self.table.height - self.height - 3):
        self.y_speed = -self.y_speed
```

---

## 3. bat.py - 배트(패들) 클래스

플레이어가 조작하는 패들을 정의하는 클래스입니다.

### 클래스 구조

```python
class Bat:
    def __init__(self, table, width=20, height=120, x_posn=50, y_posn=50,
                 colour="blue", image_path=None, x_speed=25, y_speed=25)
```

### 주요 속성

| 속성 | 타입 | 설명 |
|------|------|------|
| `width`, `height` | int | 배트 크기 |
| `x_posn`, `y_posn` | int | 현재 위치 |
| `colour` | str | 배트 색상 |
| `y_speed` | int | 상하 이동 속도 |
| `is_image` | bool | 이미지 사용 여부 |

### 충돌 감지 알고리즘

`detect_collision()` 메서드는 공과 배트의 충돌을 감지하고 방향을 반환합니다.

```
충돌 방향:
    N (North) - 위쪽에서 충돌
    S (South) - 아래쪽에서 충돌
    E (East)  - 오른쪽에서 충돌
    W (West)  - 왼쪽에서 충돌
```

### 스위트 스팟 시스템

배트의 중심에서 멀어질수록 공의 반사 각도가 달라지는 물리 시뮬레이션:

```python
# 배트 중심에서 공 중심까지의 거리에 따라 y 속도 조절
adjustment = (-(v_centre - v_centre_b)) / (self.height / 2)
ball.y_speed = feel * adjustment  # feel = 6
```

### 이동 메서드

| 메서드 | 설명 |
|--------|------|
| `move_up()` | 배트를 위로 이동 (경계 체크 포함) |
| `move_down()` | 배트를 아래로 이동 (경계 체크 포함) |
| `start_position()` | 시작 위치로 리셋 |

---

## 4. main.py - 메인 게임 파일

게임의 진입점이자 전체 게임 로직을 관리합니다.

### 게임 설정

```python
# 전역 변수
x_velocity = 10      # 공의 x 속도
y_velocity = 0       # 공의 초기 y 속도
score_left = 0       # 왼쪽 플레이어 점수
score_right = 0      # 오른쪽 플레이어 점수

# 리소스 경로
SIMSON_DIR = "/Users/yeong/Downloads/simson"
BALL_IMAGE = "d_g.png"           # 공 이미지 (도넛?)
BACKGROUND_IMAGE = "b_simson.gif" # 배경 이미지
SOUND_FILE = "doh.mp3"           # 호머의 "D'oh!" 효과음
```

### 게임 객체 생성

```python
# 테이블 생성 (800x600)
my_table = table.Table(window, background_image=BACKGROUND_IMAGE, ...)

# 공 생성 (60x60 크기)
my_ball = ball.Ball(table=my_table, image_path=BALL_IMAGE, width=60, height=60, ...)

# 배트 생성 (왼쪽: 파랑, 오른쪽: 빨강)
bat_L = bat.Bat(table=my_table, colour="dodgerblue", ...)
bat_R = bat.Bat(table=my_table, colour="tomato", ...)
```

### 게임 루프 (game_flow)

```
┌─────────────────────────────────────────┐
│              game_flow()                 │
├─────────────────────────────────────────┤
│  1. 게임 오버 체크                        │
│  2. 배트-공 충돌 감지                     │
│  3. 충돌 시 사운드 재생                   │
│  4. 벽 충돌 체크 → 득점 처리              │
│  5. 10점 도달 시 게임 종료                │
│  6. 공 이동 (move_next)                  │
│  7. 30ms 후 자기 자신 재호출              │
└─────────────────────────────────────────┘
```

### 키보드 컨트롤

| 키 | 동작 |
|----|------|
| `W` | 왼쪽 배트 위로 |
| `S` | 왼쪽 배트 아래로 |
| `↑` | 오른쪽 배트 위로 |
| `↓` | 오른쪽 배트 아래로 |
| `Space` | 게임 시작/재시작 |
| `ESC` | 게임 종료 |

### 사운드 시스템

Pygame mixer를 사용하여 효과음 재생:

```python
pygame.mixer.init()
sound_effect = pygame.mixer.Sound(SOUND_FILE)  # "D'oh!" 사운드

def play_sound():
    if sound_enabled:
        sound_effect.play()
```

---

## 의존성

```
tkinter     # GUI 프레임워크 (Python 내장)
PIL/Pillow  # 이미지 처리
pygame      # 사운드 재생
```

설치 명령:
```bash
pip install pillow pygame
```

---

## 실행 방법

```bash
python main.py
```

### 필요한 리소스 파일

- `d_g.png` - 공 이미지 (도넛 모양 추정)
- `b_simson.gif` - 배경 이미지
- `doh.mp3` - 충돌 효과음

---

## 게임 규칙

1. 10점을 먼저 획득한 플레이어가 승리
2. 공이 상대방 벽에 닿으면 1점 획득
3. 배트 중앙에 맞추면 공이 직선으로, 가장자리에 맞추면 각도가 생김

---

## 클래스 다이어그램

```
┌─────────────┐      ┌─────────────┐
│    Table    │◄─────│    Ball     │
│             │      │             │
│ - canvas    │      │ - table     │
│ - scoreboard│      │ - x_posn    │
│             │      │ - y_posn    │
│ + draw_*()  │      │ + move_next │
└─────────────┘      └─────────────┘
       ▲
       │
       │
┌─────────────┐      ┌─────────────┐
│    Bat      │      │   main.py   │
│             │      │             │
│ - table     │◄─────│ 게임 루프    │
│ - x_posn    │      │ 키 바인딩    │
│ - y_posn    │      │ 이벤트 처리  │
│ + move_*()  │      │             │
└─────────────┘      └─────────────┘
```

---

## 개선 가능 사항

1. **AI 상대** - 싱글플레이어 모드를 위한 컴퓨터 상대 추가
2. **난이도 조절** - 공 속도, 배트 크기 조절 옵션
3. **파워업** - 게임 중 등장하는 특수 아이템
4. **네트워크 멀티플레이어** - 소켓 통신을 이용한 온라인 대전
5. **설정 저장** - JSON 파일로 게임 설정 저장/불러오기
