# 틱택토 (Tic-Tac-Toe) 게임

## 개요

콘솔 기반의 클래식 틱택토 게임입니다. 1인용(vs AI) 모드와 2인용 모드를 지원하며, 3×3 보드에서 먼저 가로, 세로, 또는 대각선으로 3개를 연속으로 놓는 플레이어가 승리합니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| 싱글 플레이어 모드 | AI와 대전 (플레이어: X, AI: O) |
| 2인용 모드 | 두 명이 번갈아가며 플레이 |
| 승리/무승부 판정 | 가로, 세로, 대각선 승리 조건 및 무승부 확인 |
| AI 전략 | 승리 수 탐색 → 방어 수 탐색 → 랜덤 선택 |

## 게임 보드 구조

```
 X | O | X 
---|---|---
 O | X |   
---|---|---
   | O |   
```

좌표는 `(행 열)` 형식으로 입력하며, 1부터 시작합니다.

## 코드 구조

### 전역 변수

```python
board = [[' ' for _ in range(3)] for _ in range(3)]
```

3×3 2차원 리스트로 게임 보드를 표현합니다.

### 핵심 함수

#### `print_board(board)`
현재 보드 상태를 콘솔에 출력합니다.

#### `check_win(board, player)`
특정 플레이어의 승리 여부를 확인합니다.

**승리 조건 검사:**
- 가로 3줄 (3개)
- 세로 3줄 (3개)
- 대각선 2줄 (2개)

```python
# 가로 확인
if all(board[i][j] == player for j in range(3)): return True
# 세로 확인
if all(board[j][i] == player for j in range(3)): return True
# 대각선 확인
if all(board[i][i] == player for i in range(3)): return True
if all(board[i][2 - i] == player for i in range(3)): return True
```

#### `check_draw(board)`
무승부 여부를 확인합니다. 모든 칸이 채워지면 무승부입니다.

#### `get_empty_cells(board)`
비어있는 모든 칸의 좌표 리스트를 반환합니다.

**반환값:** `[(row, col), ...]`

#### `get_player_move(player)`
플레이어로부터 유효한 입력을 받습니다.

**입력 형식:** `행 열` (예: `1 2`)

**유효성 검사:**
- 좌표 범위: 1~3
- 빈 칸 여부 확인

#### `get_ai_move(board, ai_player)`
AI의 다음 수를 결정합니다.

**AI 전략 (우선순위 순):**
1. **승리 수 탐색**: AI가 즉시 이길 수 있는 수 탐색
2. **방어 수 탐색**: 상대가 이길 수 있는 수 차단
3. **랜덤 선택**: 위 조건에 해당하지 않으면 랜덤 선택

```python
# 1. AI 승리 수 확인
for row, col in empty_cells:
    board[row][col] = ai_player
    if check_win(board, ai_player):
        return row, col
    board[row][col] = ' '

# 2. 플레이어 승리 수 차단
for row, col in empty_cells:
    board[row][col] = player
    if check_win(board, player):
        board[row][col] = ' '
        return row, col
    board[row][col] = ' '

# 3. 랜덤 선택
return random.choice(empty_cells)
```

### 게임 모드 함수

#### `main_1p()`
싱글 플레이어 모드를 실행합니다.

**게임 흐름:**
1. 보드 초기화
2. 플레이어(X)와 AI(O)가 번갈아 가며 진행
3. AI는 1초 딜레이 후 수를 둠
4. 승리/무승부 시 결과 출력 후 종료

#### `main_2p()`
2인용 모드를 실행합니다.

**게임 흐름:**
1. 보드 초기화
2. 플레이어 X, O가 번갈아 가며 진행
3. 승리/무승부 시 결과 출력 후 종료

## 사용 방법

### 실행
```bash
python tictactoe.py
```

### 메뉴 선택
```
--- 틱택토 게임 ---
1. 싱글 플레이어 (vs AI)
2. 2인용
3. 종료
모드를 선택하세요: 
```

### 게임 플레이
```
플레이어 'X', 좌표를 입력하세요 (예: 1 1): 2 2
```

## 의존성

- Python 3.x
- `random` (표준 라이브러리)
- `time` (표준 라이브러리)

## 개선 가능 사항

1. **미니맥스 알고리즘**: 현재 AI는 단순 휴리스틱을 사용하며, 완벽한 플레이를 위해 미니맥스 알고리즘 적용 가능
2. **GUI 추가**: tkinter 등을 활용한 그래픽 인터페이스 구현
3. **난이도 선택**: 쉬움/보통/어려움 모드 추가
4. **전적 기록**: 승/패/무승부 통계 저장

## 파일 정보

| 항목 | 내용 |
|------|------|
| 파일명 | `tictactoe.py` |
| 언어 | Python 3 |
| UI | 콘솔 (CLI) |
| 라인 수 | 약 130줄 |
