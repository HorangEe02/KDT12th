# 심슨 핑퐁 게임 - 메인 파일
# 심슨 이미지와 doh.mp3를 사용한 핑퐁 게임

from tkinter import *
import table
import ball
import bat
import pygame
import os

# 전역 변수 초기화
x_velocity = 10
y_velocity = 0
score_left = 0
score_right = 0
first_serve = True

# 이미지 및 사운드 경로
SIMSON_DIR = "/Users/yeong/Downloads/simson"
BALL_IMAGE = os.path.join(SIMSON_DIR, "d_g.png")
BACKGROUND_IMAGE = os.path.join(SIMSON_DIR, "b_simson.gif")
SOUND_FILE = os.path.join(SIMSON_DIR, "doh.mp3")
GAMEOVER_IMAGE = os.path.join(SIMSON_DIR, "gameover.png")

# Pygame mixer 초기화 (사운드용)
try:
    pygame.mixer.init()
    sound_effect = pygame.mixer.Sound(SOUND_FILE)
    sound_enabled = True
except:
    sound_enabled = False
    print("사운드 파일을 로드할 수 없습니다.")

# tkinter 윈도우 생성
window = Tk()
window.title("심슨 핑퐁 게임 🎮")
window.resizable(False, False)

# 게임 테이블 생성
my_table = table.Table(window, background_image=BACKGROUND_IMAGE,
                       net_colour="yellow", width=800, height=600,
                       vertical_net=True)

# 공 생성 (d_g.png 사용)
my_ball = ball.Ball(table=my_table, image_path=BALL_IMAGE,
                    width=60, height=60, x_speed=x_velocity, y_speed=y_velocity,
                    x_start=370, y_start=270)

# 배트 생성 (왼쪽: 파랑, 오른쪽: 빨강)
bat_L = bat.Bat(table=my_table, width=20, height=120,
                x_posn=30, y_posn=240, colour="dodgerblue",
                y_speed=35)
bat_R = bat.Bat(table=my_table, width=20, height=120,
                x_posn=750, y_posn=240, colour="tomato",
                y_speed=35)

# 게임 상태
game_over = False

#### 함수 정의
def play_sound():
    """충돌 사운드 재생"""
    if sound_enabled:
        try:
            sound_effect.play()
        except:
            pass

def game_flow():
    """게임 메인 루프"""
    global first_serve, score_left, score_right, game_over

    if game_over:
        return

    # 배트와 공 충돌 감지
    collision_L = bat_L.detect_collision(my_ball)
    collision_R = bat_R.detect_collision(my_ball)

    # 충돌 시 사운드 재생
    if collision_L or collision_R:
        play_sound()

    # 왼쪽 벽에서 공이 부딪치는지 감지 (오른쪽 플레이어 득점)
    if my_ball.x_posn <= 3:
        score_right = score_right + 1
        play_sound()

        # 10점 먼저 득점 시 게임 종료
        if score_right >= 10:
            show_game_over("RIGHT")
            return

        # 점수 업데이트 및 공 재시작
        my_table.draw_score(score_left, score_right)
        my_ball.start_position()
        bat_L.start_position()
        bat_R.start_position()
        # 1초 후 공 재시작
        window.after(1000, lambda: my_ball.start_ball(x_speed=x_velocity, y_speed=0))

    # 오른쪽 벽에서 공이 부딪치는지 감지 (왼쪽 플레이어 득점)
    if my_ball.x_posn + my_ball.width >= my_table.width - 3:
        score_left = score_left + 1
        play_sound()

        # 10점 먼저 득점 시 게임 종료
        if score_left >= 10:
            show_game_over("LEFT")
            return

        # 점수 업데이트 및 공 재시작
        my_table.draw_score(score_left, score_right)
        my_ball.start_position()
        bat_L.start_position()
        bat_R.start_position()
        # 1초 후 공 재시작
        window.after(1000, lambda: my_ball.start_ball(x_speed=x_velocity, y_speed=0))

    my_ball.move_next()
    window.after(30, game_flow)

def show_game_over(winner):
    """게임 오버 화면 표시"""
    global game_over
    game_over = True

    # 게임 오버 텍스트
    my_table.canvas.create_rectangle(150, 200, 650, 400, fill="black", outline="yellow", width=5)

    winner_text = "LEFT PLAYER WINS!" if winner == "LEFT" else "RIGHT PLAYER WINS!"
    my_table.canvas.create_text(400, 270, text="GAME OVER!",
                                font=("monaco", 48, "bold"), fill="red")
    my_table.canvas.create_text(400, 330, text=winner_text,
                                font=("monaco", 32, "bold"), fill="yellow")
    my_table.canvas.create_text(400, 370, text="Press SPACE to restart",
                                font=("monaco", 20), fill="white")

def restart_game(event=None):
    """게임 재시작"""
    global score_left, score_right, first_serve, game_over

    # 게임 상태 초기화
    game_over = False
    score_left = 0
    score_right = 0
    first_serve = True

    # 캔버스 초기화 및 재생성
    my_table.canvas.delete("all")

    # 배경 다시 그리기
    try:
        my_table.canvas.create_image(0, 0, anchor=NW, image=my_table.bg_photo)
    except:
        my_table.canvas.config(bg="skyblue")

    # 네트 다시 그리기
    my_table.canvas.create_line(my_table.width/2, 0, my_table.width/2, my_table.height,
                                width=3, fill="yellow", dash=(15, 23))

    # 득점판 재생성
    font = ("monaco", 72, "bold")
    my_table.scoreboard = my_table.canvas.create_text(my_table.width/2, 80,
                                                      font=font, fill="yellow", text="0  0")

    # 게임 객체 재생성
    my_ball.start_ball(x_speed=x_velocity, y_speed=0)
    my_ball.circle = my_table.draw_image(my_ball)

    bat_L.start_position()
    bat_L.rectangle = my_table.draw_rectangle(bat_L)

    bat_R.start_position()
    bat_R.rectangle = my_table.draw_rectangle(bat_R)

    my_table.draw_score(score_left, score_right)

    # 게임 루프 재시작
    game_flow()

# 게임 종료 함수
def quit_game(event=None):
    """ESC 키로 게임 종료"""
    window.quit()
    window.destroy()

# 키보드 컨트롤 바인딩
# 왼쪽 플레이어: W(위), S(아래)
window.bind("w", bat_L.move_up)
window.bind("s", bat_L.move_down)

# 오른쪽 플레이어: 방향키 위/아래
window.bind("<Up>", bat_R.move_up)
window.bind("<Down>", bat_R.move_down)

# 스페이스바: 게임 시작/재시작
window.bind("<space>", restart_game)

# ESC 키: 게임 종료
window.bind("<Escape>", quit_game)

# 게임 설명 표시
info_text = "왼쪽: W/S | 오른쪽: ↑/↓ | 시작: SPACE | 종료: ESC"
my_table.canvas.create_text(400, 30, text=info_text,
                            font=("monaco", 14), fill="white")

# 게임 시작 메시지
my_table.canvas.create_text(400, 300, text="Press SPACE to Start!",
                            font=("monaco", 36, "bold"), fill="yellow",
                            tags="start_msg")

# 스페이스바 눌렀을 때 시작 메시지 제거
def start_game(event=None):
    global first_serve
    my_table.canvas.delete("start_msg")
    first_serve = False
    my_ball.start_ball(x_speed=x_velocity, y_speed=0)
    game_flow()
    window.unbind("<space>")
    window.bind("<space>", restart_game)

window.bind("<space>", start_game)

# tkinter 메인 루프 시작
window.mainloop()
