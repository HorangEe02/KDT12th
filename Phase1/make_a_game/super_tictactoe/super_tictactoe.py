import tkinter as tk
from tkinter import font, messagebox
import random

class GameBoard:
    """
    Super Tic-Tac-Toe 게임의 로직을 관리하는 클래스.
    - 9개의 작은 틱택토 판으로 구성된 큰 판
    - 강제 이동 규칙 적용
    - 작은 판 승리 및 전체 게임 승리 확인
    """
    def __init__(self):
        self.reset()

    def reset(self):
        """게임을 초기 상태로 리셋합니다."""
        # 9개의 작은 보드 (각각 3x3)
        self.small_boards = [['' for _ in range(9)] for _ in range(9)]
        # 각 작은 보드의 승리 상태 (None, 'X', 'O', 'Draw')
        self.board_winners = [None for _ in range(9)]
        # 다음 플레이어가 두어야 할 보드 번호 (None이면 자유 선택)
        self.next_board = None

    def get_cell_index(self, board_idx, cell_idx):
        """보드와 셀 인덱스를 (행, 열) 좌표로 변환"""
        board_row = board_idx // 3
        board_col = board_idx % 3
        cell_row = cell_idx // 3
        cell_col = cell_idx % 3
        return board_row, board_col, cell_row, cell_col

    def make_move(self, board_idx, cell_idx, player):
        """
        플레이어의 수를 보드에 놓습니다.

        Args:
            board_idx: 작은 보드 번호 (0-8)
            cell_idx: 셀 번호 (0-8)
            player: 'X' 또는 'O'

        Returns:
            성공 여부 (bool)
        """
        # 1. 이미 승부가 난 보드인지 확인
        if self.board_winners[board_idx] is not None:
            return False

        # 2. 이미 채워진 칸인지 확인
        if self.small_boards[board_idx][cell_idx] != '':
            return False

        # 3. 강제 이동 규칙 확인 (next_board가 None이 아니면 해당 보드에만 둘 수 있음)
        if self.next_board is not None and board_idx != self.next_board:
            return False

        # 4. 수를 놓음
        self.small_boards[board_idx][cell_idx] = player

        # 5. 작은 보드 승리 확인
        if self.check_small_board_win(board_idx, player):
            self.board_winners[board_idx] = player
        elif self.is_small_board_full(board_idx):
            self.board_winners[board_idx] = 'Draw'

        # 6. 다음 플레이어가 갈 보드 설정
        # 현재 플레이어가 놓은 셀 위치가 다음 플레이어가 가야 할 보드를 결정
        if self.board_winners[cell_idx] is None:
            # 해당 보드가 아직 진행 중이면 그곳으로 보냄
            self.next_board = cell_idx
        else:
            # 해당 보드가 이미 끝났으면 자유 선택
            self.next_board = None

        return True

    def check_small_board_win(self, board_idx, player):
        """작은 보드에서 특정 플레이어가 승리했는지 확인"""
        board = self.small_boards[board_idx]

        # 가로 확인
        for i in range(0, 9, 3):
            if board[i] == board[i+1] == board[i+2] == player:
                return True

        # 세로 확인
        for i in range(3):
            if board[i] == board[i+3] == board[i+6] == player:
                return True

        # 대각선 확인
        if board[0] == board[4] == board[8] == player:
            return True
        if board[2] == board[4] == board[6] == player:
            return True

        return False

    def is_small_board_full(self, board_idx):
        """작은 보드가 가득 찼는지 확인"""
        return all(cell != '' for cell in self.small_boards[board_idx])

    def check_game_win(self):
        """
        전체 게임의 승리 조건을 확인합니다.
        작은 보드의 승리 상태를 기준으로 큰 보드에서 승리를 확인합니다.

        Returns:
            'X', 'O', 'Draw', 또는 None (게임 진행 중)
        """
        winners = self.board_winners

        # 가로 확인
        for i in range(0, 9, 3):
            if winners[i] == winners[i+1] == winners[i+2] and winners[i] in ['X', 'O']:
                return winners[i]

        # 세로 확인
        for i in range(3):
            if winners[i] == winners[i+3] == winners[i+6] and winners[i] in ['X', 'O']:
                return winners[i]

        # 대각선 확인
        if winners[0] == winners[4] == winners[8] and winners[0] in ['X', 'O']:
            return winners[0]
        if winners[2] == winners[4] == winners[6] and winners[2] in ['X', 'O']:
            return winners[2]

        # 무승부 확인 (모든 보드가 끝났는지)
        if all(w is not None for w in winners):
            return 'Draw'

        return None

    def get_valid_boards(self):
        """플레이어가 수를 둘 수 있는 보드 목록 반환"""
        if self.next_board is not None:
            return [self.next_board]
        else:
            # 자유 선택 - 아직 끝나지 않은 모든 보드
            return [i for i in range(9) if self.board_winners[i] is None]

    def get_valid_cells(self, board_idx):
        """특정 보드에서 수를 둘 수 있는 셀 목록 반환"""
        if self.board_winners[board_idx] is not None:
            return []
        return [i for i in range(9) if self.small_boards[board_idx][i] == '']


class SuperTicTacToe:
    """
    Super Tic-Tac-Toe GUI 및 게임 상호작용 관리 클래스
    """
    def __init__(self, root):
        self.root = root
        self.root.title("슈퍼 틱택토 (Ultimate Tic-Tac-Toe)")
        self.root.resizable(False, False)

        self.board = GameBoard()
        self.buttons = [[None for _ in range(9)] for _ in range(9)]  # 9개 보드, 각 9개 셀
        self.board_frames = [None for _ in range(9)]  # 9개의 작은 보드 프레임
        self.board_labels = [None for _ in range(9)]  # 승리 표시 라벨

        self.game_mode = None  # 1: vs AI, 2: vs Player
        self.current_player = 'X'
        self.game_over = False

        self.player_colors = {'X': '#4A90E2', 'O': '#E2794A'}
        self.default_color = '#F0F0F0'
        self.highlight_color = '#FFFACD'  # 다음 차례 보드 강조 색
        self.won_board_color = {'X': '#B3D9FF', 'O': '#FFD4B3'}  # 승리한 보드 배경색

        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack()

        self.create_menu()

    def create_menu(self):
        """게임 모드 선택 메뉴 생성"""
        self.clear_frame()
        menu_frame = tk.Frame(self.main_frame)
        menu_frame.pack()

        title_font = font.Font(family="Helvetica", size=24, weight="bold")
        button_font = font.Font(family="Helvetica", size=14)

        tk.Label(menu_frame, text="슈퍼 틱택토", font=title_font, pady=20).pack()
        tk.Label(menu_frame, text="(Ultimate Tic-Tac-Toe)", font=("Helvetica", 12), pady=5).pack()

        tk.Button(menu_frame, text="1인용 (vs AI)", font=button_font, width=20,
                 command=lambda: self.start_game(1)).pack(pady=10)
        tk.Button(menu_frame, text="2인용", font=button_font, width=20,
                 command=lambda: self.start_game(2)).pack(pady=10)

    def start_game(self, mode):
        """게임 시작"""
        self.game_mode = mode
        self.reset_game_state()
        self.create_board_ui()

    def create_board_ui(self):
        """게임 보드 UI 생성 - 3x3 격자의 작은 보드들"""
        self.clear_frame()

        # 상태 표시
        self.status_label = tk.Label(self.main_frame,
                                    text=f"플레이어 {self.current_player}의 차례",
                                    font=("Helvetica", 16), pady=10)
        self.status_label.pack()

        # 규칙 설명
        self.rule_label = tk.Label(self.main_frame,
                                   text="어디든 자유롭게 선택하세요!",
                                   font=("Helvetica", 12), fg='green')
        self.rule_label.pack()

        # 메인 보드 프레임
        board_container = tk.Frame(self.main_frame, bg='black')
        board_container.pack(pady=10)

        cell_font = font.Font(family="Helvetica", size=20, weight="bold")
        win_font = font.Font(family="Helvetica", size=60, weight="bold")

        # 3x3 격자로 9개의 작은 보드 배치
        for board_idx in range(9):
            board_row = board_idx // 3
            board_col = board_idx % 3

            # 각 작은 보드를 위한 프레임
            board_frame = tk.Frame(board_container, bd=3, relief=tk.RAISED, bg='white')
            board_frame.grid(row=board_row, column=board_col, padx=3, pady=3)
            self.board_frames[board_idx] = board_frame

            # 승리 표시를 위한 라벨 (처음엔 숨김)
            win_label = tk.Label(board_frame, text='', font=win_font,
                               width=6, height=3, bg='white')
            win_label.grid(row=0, column=0, rowspan=3, columnspan=3)
            win_label.grid_remove()  # 처음엔 숨김
            self.board_labels[board_idx] = win_label

            # 각 작은 보드 안에 3x3 버튼 생성
            for cell_idx in range(9):
                cell_row = cell_idx // 3
                cell_col = cell_idx % 3

                button = tk.Button(board_frame, text='', font=cell_font,
                                 width=3, height=1,
                                 bg=self.default_color,
                                 command=lambda b=board_idx, c=cell_idx: self.on_cell_click(b, c))
                button.grid(row=cell_row, column=cell_col, padx=1, pady=1)
                self.buttons[board_idx][cell_idx] = button

        # 컨트롤 버튼
        control_frame = tk.Frame(self.main_frame, pady=15)
        control_frame.pack()
        tk.Button(control_frame, text="새 게임", font=("Helvetica", 12),
                 command=self.create_menu).pack()

        self.update_board_ui()

    def on_cell_click(self, board_idx, cell_idx):
        """셀 클릭 이벤트 처리"""
        if self.game_over:
            return

        # 플레이어의 수 처리
        if self.board.make_move(board_idx, cell_idx, self.current_player):
            self.update_board_ui()

            # 게임 승리 확인
            winner = self.board.check_game_win()
            if winner:
                self.handle_game_end(winner)
                return

            # 턴 변경
            self.current_player = 'O' if self.current_player == 'X' else 'X'
            self.update_status()

            # AI 턴
            if self.game_mode == 1 and not self.game_over and self.current_player == 'O':
                self.root.after(500, self.ai_move)

    def ai_move(self):
        """AI의 수 결정 및 실행"""
        if self.game_over:
            return

        valid_boards = self.board.get_valid_boards()

        # 전략 1: 즉시 이길 수 있는 수 찾기
        for board_idx in valid_boards:
            valid_cells = self.board.get_valid_cells(board_idx)
            for cell_idx in valid_cells:
                # 시뮬레이션
                self.board.small_boards[board_idx][cell_idx] = 'O'
                if self.board.check_small_board_win(board_idx, 'O'):
                    # 이 보드를 이기면 전체 게임도 이기는지 확인
                    temp_winner = self.board.board_winners[board_idx]
                    self.board.board_winners[board_idx] = 'O'
                    if self.board.check_game_win() == 'O':
                        self.board.board_winners[board_idx] = temp_winner
                        self.board.small_boards[board_idx][cell_idx] = ''
                        self.execute_ai_move(board_idx, cell_idx)
                        return
                    self.board.board_winners[board_idx] = temp_winner
                self.board.small_boards[board_idx][cell_idx] = ''

        # 전략 2: 상대방이 이기는 것 막기
        for board_idx in valid_boards:
            valid_cells = self.board.get_valid_cells(board_idx)
            for cell_idx in valid_cells:
                self.board.small_boards[board_idx][cell_idx] = 'X'
                if self.board.check_small_board_win(board_idx, 'X'):
                    temp_winner = self.board.board_winners[board_idx]
                    self.board.board_winners[board_idx] = 'X'
                    if self.board.check_game_win() == 'X':
                        self.board.board_winners[board_idx] = temp_winner
                        self.board.small_boards[board_idx][cell_idx] = ''
                        self.execute_ai_move(board_idx, cell_idx)
                        return
                    self.board.board_winners[board_idx] = temp_winner
                self.board.small_boards[board_idx][cell_idx] = ''

        # 전략 3: 중앙 선호, 그 다음 모서리, 마지막으로 변
        preference_order = [4, 0, 2, 6, 8, 1, 3, 5, 7]

        for board_idx in valid_boards:
            valid_cells = self.board.get_valid_cells(board_idx)
            for cell_idx in preference_order:
                if cell_idx in valid_cells:
                    self.execute_ai_move(board_idx, cell_idx)
                    return

    def execute_ai_move(self, board_idx, cell_idx):
        """AI의 수를 실행"""
        self.board.make_move(board_idx, cell_idx, 'O')
        self.update_board_ui()

        winner = self.board.check_game_win()
        if winner:
            self.handle_game_end(winner)
            return

        self.current_player = 'X'
        self.update_status()

    def update_status(self):
        """상태 라벨 업데이트"""
        self.status_label.config(text=f"플레이어 {self.current_player}의 차례")

        # 규칙 라벨 업데이트
        valid_boards = self.board.get_valid_boards()
        if len(valid_boards) == 1:
            board_row = valid_boards[0] // 3 + 1
            board_col = valid_boards[0] % 3 + 1
            self.rule_label.config(
                text=f"강제 이동: {board_row}행 {board_col}열 보드에만 둘 수 있습니다",
                fg='red'
            )
        else:
            self.rule_label.config(
                text="자유 선택: 원하는 보드에 둘 수 있습니다!",
                fg='green'
            )

    def update_board_ui(self):
        """보드 UI 업데이트"""
        valid_boards = self.board.get_valid_boards()

        for board_idx in range(9):
            # 승리한 보드 표시
            if self.board.board_winners[board_idx] in ['X', 'O']:
                winner = self.board.board_winners[board_idx]
                self.board_labels[board_idx].config(
                    text=winner,
                    fg=self.player_colors[winner],
                    bg=self.won_board_color[winner]
                )
                self.board_labels[board_idx].grid()
                # 버튼들 비활성화
                for cell_idx in range(9):
                    self.buttons[board_idx][cell_idx].config(state=tk.DISABLED)

            elif self.board.board_winners[board_idx] == 'Draw':
                self.board_labels[board_idx].config(
                    text='무',
                    fg='gray',
                    bg='lightgray'
                )
                self.board_labels[board_idx].grid()
                for cell_idx in range(9):
                    self.buttons[board_idx][cell_idx].config(state=tk.DISABLED)

            else:
                # 진행 중인 보드
                # 보드 강조 (다음 차례 보드)
                if board_idx in valid_boards:
                    self.board_frames[board_idx].config(bg='gold', bd=5)
                else:
                    self.board_frames[board_idx].config(bg='white', bd=3)

                # 각 셀 업데이트
                for cell_idx in range(9):
                    player = self.board.small_boards[board_idx][cell_idx]
                    button = self.buttons[board_idx][cell_idx]

                    if player:
                        button.config(
                            text=player,
                            fg=self.player_colors[player],
                            bg='white',
                            state=tk.DISABLED
                        )
                    else:
                        button.config(
                            text='',
                            fg='black',
                            bg=self.default_color,
                            state=tk.NORMAL
                        )

    def handle_game_end(self, winner):
        """게임 종료 처리"""
        self.game_over = True

        if winner == 'Draw':
            self.status_label.config(text="무승부!")
            messagebox.showinfo("게임 종료", "무승부입니다!")
        else:
            self.status_label.config(text=f"플레이어 {winner} 승리!")
            messagebox.showinfo("게임 종료", f"플레이어 {winner}가 승리했습니다!")

        self.rule_label.config(text="게임이 종료되었습니다")

    def reset_game_state(self):
        """게임 상태 초기화"""
        self.board.reset()
        self.current_player = 'X'
        self.game_over = False

    def clear_frame(self):
        """메인 프레임의 모든 위젯 제거"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    game = SuperTicTacToe(root)
    root.mainloop()
