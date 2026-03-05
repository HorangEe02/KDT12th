# 🍩 SIMPSONS DOOM 🍩

> Doom 스타일의 레이캐스팅 기법을 활용한 심슨 테마 게임

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green)
![HTML5](https://img.shields.io/badge/HTML5-Canvas-orange?logo=html5)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-yellow?logo=javascript)

---

## 📋 목차

1. [게임 소개](#게임-소개)
2. [파일 구성](#파일-구성)
3. [실행 방법](#실행-방법)
4. [조작법](#조작법)
5. [게임 규칙](#게임-규칙)
6. [기술 구현](#기술-구현)
7. [맵 구조](#맵-구조)

---

## 🎮 게임 소개

**SIMPSONS DOOM**은 1993년 출시된 클래식 FPS 게임 **DOOM**의 레이캐스팅 렌더링 기법을 재현한 미니 게임입니다. 플레이어는 호머 심슨이 되어 맵 곳곳에 숨겨진 도넛을 모두 수집해야 하며, 동시에 플랜더스의 추격을 피해야 합니다.

### 주요 특징

- **레이캐스팅 3D 렌더링**: 2D 맵 데이터를 기반으로 유사 3D 시점 구현
- **두 가지 플랫폼 지원**: Python(Pygame) 버전과 웹(HTML5 Canvas) 버전 제공
- **심슨 테마**: 호머, 도넛, 플랜더스 등 심슨 캐릭터 활용
- **미니맵**: 실시간 위치 및 아이템 표시

---

## 📁 파일 구성

```
doom(packman_homer)/
├── new.py                      # Python 버전 게임 코드
├── simpsons_doom_complete.html # 웹 버전 게임 코드 (단일 파일)
├── d_g.png                     # 도넛 이미지
├── flanders.png                # 플랜더스 이미지
├── gameover.png                # 게임오버 이미지
├── s_g.png                     # 호머 이미지
└── SIMPSONS_DOOM_README.md     # 본 문서
```

### 버전별 비교

| 구분 | Python 버전 (`new.py`) | 웹 버전 (`.html`) |
|------|------------------------|-------------------|
| **플랫폼** | Python 3.x + Pygame | 웹 브라우저 |
| **해상도** | 1024 × 768 | 700 × 450 |
| **이미지** | 외부 PNG 파일 | Base64 내장 |
| **배포** | Python 환경 필요 | 브라우저만 있으면 실행 |
| **터치 지원** | ❌ | ✅ (모바일 대응) |
| **한글 키보드** | ❌ | ✅ (ㅈ/ㄴ/ㅁ/ㅇ) |

---

## 🚀 실행 방법

### Python 버전

**1. 필수 라이브러리 설치**
```bash
pip install pygame
```

**2. 게임 실행**
```bash
cd doom(packman_homer)
python new.py
```

> ⚠️ 이미지 파일(`d_g.png`, `flanders.png`, `gameover.png`, `s_g.png`)이 `new.py`와 같은 폴더에 있어야 합니다.

### 웹 버전

`simpsons_doom_complete.html` 파일을 웹 브라우저에서 열면 바로 실행됩니다.

```bash
# macOS
open simpsons_doom_complete.html

# Windows
start simpsons_doom_complete.html

# Linux
xdg-open simpsons_doom_complete.html
```

---

## 🎹 조작법

### 키보드

| 동작 | Python 버전 | 웹 버전 |
|------|-------------|---------|
| 전진 | `W` | `W` / `↑` / `ㅈ` |
| 후진 | `S` | `S` / `↓` / `ㄴ` |
| 좌측 이동 (스트레이프) | `A` | `A` / `ㅁ` |
| 우측 이동 (스트레이프) | `D` | `D` / `ㅇ` |
| 좌회전 | `←` | `←` |
| 우회전 | `→` | `→` |
| 게임 종료 | `ESC` | - |
| 재시작 (게임오버 시) | `R` | 버튼 클릭 |

### 터치 컨트롤 (웹 버전 전용)

모바일 기기에서는 화면 하단의 가상 버튼으로 조작할 수 있습니다.

---

## 📜 게임 규칙

### 목표
맵에 있는 **도넛 6개**를 모두 수집하면 승리!

### 체력 시스템
- **시작 체력**: 100
- **플랜더스 접촉**: 체력 -1 (지속 데미지)
- **도넛 수집**: 체력 +10 (최대 100)
- **체력 0**: 게임 오버

### 승리/패배 조건
- ✅ **승리**: 도넛 6개 모두 수집
- ❌ **패배**: 체력이 0이 됨

---

## 🔧 기술 구현

### 1. 레이캐스팅 (Raycasting)

레이캐스팅은 2D 맵에서 플레이어 시점의 광선을 발사하여 벽과의 거리를 계산하고, 이를 기반으로 3D처럼 보이는 화면을 렌더링하는 기법입니다.

```python
# 핵심 알고리즘 (Python)
FOV = math.pi / 3  # 시야각 60도
NUM_RAYS = 512     # 화면 너비의 절반만큼 광선 발사

for ray in range(NUM_RAYS):
    # 각 광선의 각도 계산
    ray_angle = player.angle - HALF_FOV + ray * DELTA_ANGLE
    
    # 광선 진행 (벽에 닿을 때까지)
    for depth in range(MAX_DEPTH * 100):
        target_x = player.x + depth * math.cos(ray_angle) * 0.01
        target_y = player.y + depth * math.sin(ray_angle) * 0.01
        
        if MAP[int(target_y)][int(target_x)] == 1:  # 벽 충돌
            break
    
    # 벽 높이 계산 (거리에 반비례)
    wall_height = SCREEN_HEIGHT / depth
```

### 2. 어안 효과 보정 (Fisheye Correction)

레이캐스팅에서 발생하는 어안 렌즈 효과를 보정합니다.

```javascript
// JavaScript
const correctedDepth = depth * Math.cos(player.angle - rayAngle);
const wallHeight = SCREEN_HEIGHT / correctedDepth;
```

### 3. 스프라이트 렌더링

도넛과 플랜더스는 빌보드 방식으로 항상 플레이어를 향하도록 렌더링됩니다.

```python
# 스프라이트와 플레이어 간의 각도/거리 계산
dx = sprite.x - player.x
dy = sprite.y - player.y
distance = math.sqrt(dx * dx + dy * dy)
angle = math.atan2(dy, dx) - player.angle

# 화면상 위치 및 크기 계산
screen_x = (angle / FOV + 0.5) * SCREEN_WIDTH
sprite_height = SCREEN_HEIGHT / distance * scale
```

### 4. 적 AI (플랜더스)

플랜더스는 단순한 추적 AI로 플레이어를 향해 직선으로 이동합니다.

```python
def update_flanders(self):
    dx = player.x - flanders.x
    dy = player.y - flanders.y
    distance = math.sqrt(dx * dx + dy * dy)
    
    # 정규화 후 이동
    dx /= distance
    dy /= distance
    flanders.x += dx * speed
    flanders.y += dy * speed
```

---

## 🗺️ 맵 구조

게임 맵은 16×16 2D 배열로 정의됩니다.

### 타일 타입
| 값 | 의미 |
|----|------|
| `0` | 빈 공간 (이동 가능) |
| `1` | 벽 (이동 불가) |
| `2` | 도넛 스폰 위치 |
| `3` | 플랜더스 스폰 위치 |

### 맵 시각화

```
■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■
■ P · · · · · · · · · · · · · ■
■ · ■ ■ · · · 🍩· · ■ ■ · · · ■
■ · ■ · · · · · · · · ■ · 😈· ■
■ · · · · ■ ■ · ■ ■ · · · · · ■
■ · · 🍩· ■ · · · ■ · · · · · ■
■ · · · · · · · · · · · ■ ■ · ■
■ · ■ · · · 😈· · · · · ■ · · ■
■ · ■ ■ · · · · · · · · · · 🍩■
■ · · · · · · · ■ ■ ■ · · · · ■
■ · · · ■ ■ · · ■ · · · · ■ · ■
■ · 🍩· ■ · · · · · 😈· · ■ · ■
■ · · · · · · · · · · · · · · ■
■ · · ■ ■ · · 🍩· · ■ ■ · · · ■
■ · · · · · · · · · · · · · · ■
■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■

P = 플레이어 시작 위치
🍩 = 도넛 (6개)
😈 = 플랜더스 (3명)
■ = 벽
```

---

## 📝 참고 사항

- Python 버전은 `os.path`를 사용하여 스크립트 위치 기준으로 이미지를 로드합니다.
- 웹 버전은 이미지가 Base64로 인코딩되어 있어 별도 파일 없이 실행 가능합니다.
- 두 버전 모두 동일한 맵 데이터와 게임 로직을 공유합니다.

---

## 📜 라이선스

이 프로젝트는 학습 목적으로 제작되었습니다.  
심슨 캐릭터 관련 저작권은 20th Century Studios / The Walt Disney Company에 있습니다.

---

*Made with 🍩 and Python/JavaScript*
