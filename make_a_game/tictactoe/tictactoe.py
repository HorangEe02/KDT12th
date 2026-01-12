import random
import time

# 게임 보드 초기화
board = [[' ' for _ in range(3)] for _ in range(3)]

def print_board(board):
    """게임 보드를 출력합니다."""
    print()
    for i in range(3):
        print(f" {board[i][0]} | {board[i][1]} | {board[i][2]} ")
        if i < 2:
            print("---|---|---")
    print()

def check_win(board, player):
    """승리 조건을 확인합니다."""
    # 가로, 세로, 대각선 확인
    for i in range(3):
        if all(board[i][j] == player for j in range(3)): return True
        if all(board[j][i] == player for j in range(3)): return True
    if all(board[i][i] == player for i in range(3)): return True
    if all(board[i][2 - i] == player for i in range(3)): return True
    return False

def check_draw(board):
    """무승부 조건을 확인합니다."""
    for row in board:
        if ' ' in row:
            return False
    return True

def get_empty_cells(board):
    """보드에서 비어있는 모든 칸의 리스트를 반환합니다."""
    cells = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == ' ':
                cells.append((i, j))
    return cells

def get_player_move(player):
    """플레이어로부터 입력을 받습니다."""
    while True:
        try:
            move = input(f"플레이어 '{player}', 좌표를 입력하세요 (예: 1 1): ")
            row, col = map(int, move.split())
            row -= 1
            col -= 1
            if 0 <= row < 3 and 0 <= col < 3 and board[row][col] == ' ':
                return row, col
            else:
                print("잘못된 입력이거나 이미 채워진 칸입니다. 다시 시도하세요.")
        except (ValueError, IndexError):
            print("잘못된 형식입니다. '행 열' 형식으로 숫자를 입력하세요 (예: 1 2).")

def get_ai_move(board, ai_player):
    """AI의 다음 수를 결정합니다."""
    player = 'X' if ai_player == 'O' else 'O'
    empty_cells = get_empty_cells(board)

    # 1. AI가 이길 수 있는 수가 있는지 확인
    for row, col in empty_cells:
        board[row][col] = ai_player
        if check_win(board, ai_player):
            return row, col
        board[row][col] = ' '

    # 2. 플레이어가 이길 수 있는 수를 막기
    for row, col in empty_cells:
        board[row][col] = player
        if check_win(board, player):
            board[row][col] = ' '
            return row, col
        board[row][col] = ' '

    # 3. 그 외에는 랜덤하게 선택
    return random.choice(empty_cells)

def main_1p():
    """싱글 플레이어 게임을 진행합니다."""
    global board
    board = [[' ' for _ in range(3)] for _ in range(3)]
    human_player = 'X'
    ai_player = 'O'

    print("\n싱글 플레이어 모드입니다. 당신이 'X', AI가 'O'입니다.")
    
    current_player = human_player
    while True:
        print_board(board)
        if current_player == human_player:
            row, col = get_player_move(human_player)
            board[row][col] = human_player
        else:
            print("AI의 차례입니다...")
            time.sleep(1)
            row, col = get_ai_move(board, ai_player)
            board[row][col] = ai_player
            print(f"AI가 ({row + 1}, {col + 1})에 수를 두었습니다.")

        if check_win(board, current_player):
            print_board(board)
            winner = "당신" if current_player == human_player else "AI"
            print(f"{winner}의 승리입니다!")
            break
        
        if check_draw(board):
            print_board(board)
            print("무승부입니다!")
            break

        current_player = ai_player if current_player == human_player else human_player


def main_2p():
    """2인용 게임을 진행합니다."""
    global board
    board = [[' ' for _ in range(3)] for _ in range(3)]
    current_player = 'X'
    
    print("\n2인용 모드입니다.")

    while True:
        print_board(board)
        row, col = get_player_move(current_player)
        board[row][col] = current_player

        if check_win(board, current_player):
            print_board(board)
            print(f"플레이어 '{current_player}'가 승리했습니다!")
            break
        
        if check_draw(board):
            print_board(board)
            print("무승부입니다!")
            break

        current_player = 'O' if current_player == 'X' else 'X'

if __name__ == '__main__':
    while True:
        print("\n--- 틱택토 게임 ---")
        print("1. 싱글 플레이어 (vs AI)")
        print("2. 2인용")
        print("3. 종료")
        choice = input("모드를 선택하세요: ")

        if choice == '1':
            main_1p()
        elif choice == '2':
            main_2p()
        elif choice == '3':
            print("게임을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 다시 입력해주세요.")
