# 심슨 핑퐁 게임 - Ball 클래스
# d_g.png 이미지를 사용한 공 클래스

import table
import random
from PIL import Image, ImageTk

class Ball:
    #### 생성자
    def __init__(self, table, image_path, width=50, height=50,
                 x_speed=8, y_speed=0, x_start=0, y_start=0):
        self.width = width
        self.height = height
        self.x_posn = x_start
        self.y_posn = y_start

        self.x_start = x_start
        self.y_start = y_start
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.table = table

        # 이미지 로드
        try:
            img = Image.open(image_path)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.circle = self.table.draw_image(self)
        except:
            # 이미지 로드 실패시 기본 원 사용
            self.photo = None
            self.circle = self.table.canvas.create_oval(
                x_start, y_start, x_start + width, y_start + height,
                fill="yellow", outline="orange", width=3)

    #### 메서드
    def start_position(self):
        self.x_posn = self.x_start
        self.y_posn = self.y_start

    def start_ball(self, x_speed, y_speed):
        # 랜덤하게 방향 결정
        self.x_speed = -x_speed if random.randint(0, 1) else x_speed
        self.y_speed = -y_speed if random.randint(0, 1) else y_speed
        self.start_position()

    def move_next(self):
        self.x_posn = self.x_posn + self.x_speed
        self.y_posn = self.y_posn + self.y_speed

        # 공이 위쪽 벽에 부딪쳤을 때
        if self.y_posn <= 3:
            self.y_posn = 3
            self.y_speed = -self.y_speed

        # 공이 아래쪽 벽에 부딪쳤을 때
        if self.y_posn >= (self.table.height - self.height - 3):
            self.y_posn = (self.table.height - self.height - 3)
            self.y_speed = -self.y_speed

        # 공의 위치 업데이트
        if self.photo:
            self.table.move_item(self.circle, self.x_posn, self.y_posn)
        else:
            x1 = self.x_posn
            x2 = self.x_posn + self.width
            y1 = self.y_posn
            y2 = self.y_posn + self.height
            self.table.move_item(self.circle, x1, y1, x2, y2)

    def stop_ball(self):
        self.x_speed = 0
        self.y_speed = 0
