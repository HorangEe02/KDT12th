# 심슨 핑퐁 게임 - Bat 클래스
# 배트(패들) 클래스 정의

import table
from PIL import Image, ImageTk

class Bat:
    #### 생성자
    def __init__(self, table, width=20, height=120, x_posn=50, y_posn=50,
                 colour="blue", image_path=None, x_speed=25, y_speed=25):
        self.width = width
        self.height = height
        self.x_posn = x_posn
        self.y_posn = y_posn
        self.colour = colour

        self.x_start = x_posn
        self.y_start = y_posn
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.table = table

        # 이미지 사용 시
        if image_path:
            try:
                img = Image.open(image_path)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.rectangle = self.table.canvas.create_image(
                    x_posn, y_posn, anchor='nw', image=self.photo)
                self.is_image = True
            except:
                self.photo = None
                self.rectangle = self.table.draw_rectangle(self)
                self.is_image = False
        else:
            self.photo = None
            self.rectangle = self.table.draw_rectangle(self)
            self.is_image = False

    #### 메서드
    def detect_collision(self, ball, sides_sweet_spot=True, topnbottom_sweet_spot=False):
        collision_direction = ""
        collision = False
        feel = 6

        # 배트 변수
        top = self.y_posn
        bottom = self.y_posn + self.height
        left = self.x_posn
        right = self.x_posn + self.width
        v_centre = top + (self.height / 2)
        h_centre = left + (self.width / 2)

        # 공 변수
        top_b = ball.y_posn
        bottom_b = ball.y_posn + ball.height
        left_b = ball.x_posn
        right_b = ball.x_posn + ball.width
        r = (right_b - left_b) / 2
        v_centre_b = top_b + r
        h_centre_b = left_b + r

        # 충돌 감지
        if ((bottom_b > top) and (top_b < bottom) and
            (right_b > left) and (left_b < right)):
            collision = True

        if collision:
            # 오른쪽에서 충돌
            if ((top_b > top - r) and (bottom_b < bottom + r) and
                (right_b > right) and (left_b <= right)):
                collision_direction = "E"
                ball.x_speed = abs(ball.x_speed)

            # 아래쪽에서 충돌
            elif ((left_b > left - r) and (right_b < right + r) and
                  (bottom_b > bottom) and (top_b <= bottom)):
                collision_direction = "S"
                ball.y_speed = abs(ball.y_speed)

            # 위쪽에서 충돌
            elif ((left_b > left - r) and (right_b < right + r) and
                  (top_b < top) and (bottom_b >= top)):
                collision_direction = "N"
                ball.y_speed = -abs(ball.y_speed)

            # 왼쪽에서 충돌
            elif ((top_b > top - r) and (bottom_b < bottom + r) and
                  (left_b < left) and (right_b >= left)):
                collision_direction = "W"
                ball.x_speed = -abs(ball.x_speed)

            else:
                collision_direction = "miss"

            # 스위트 스팟 효과 (측면)
            if ((sides_sweet_spot == True) and
                (collision_direction == "W" or collision_direction == "E")):
                adjustment = (-(v_centre - v_centre_b)) / (self.height / 2)
                ball.y_speed = feel * adjustment

            # 스위트 스팟 효과 (상하)
            if ((topnbottom_sweet_spot == True) and
                (collision_direction == "N" or collision_direction == "S")):
                adjustment = (-(h_centre - h_centre_b)) / (self.width / 2)
                ball.x_speed = feel * adjustment

            return (collision, collision_direction)

    def move_up(self, master=None):
        self.y_posn = self.y_posn - self.y_speed
        if self.y_posn <= 0:
            self.y_posn = 0
        self._update_position()

    def move_down(self, master=None):
        self.y_posn = self.y_posn + self.y_speed
        far_bottom = self.table.height - self.height
        if self.y_posn >= far_bottom:
            self.y_posn = far_bottom
        self._update_position()

    def _update_position(self):
        if self.is_image:
            self.table.move_item(self.rectangle, self.x_posn, self.y_posn)
        else:
            x1 = self.x_posn
            x2 = self.x_posn + self.width
            y1 = self.y_posn
            y2 = self.y_posn + self.height
            self.table.move_item(self.rectangle, x1, y1, x2, y2)

    def start_position(self):
        self.x_posn = self.x_start
        self.y_posn = self.y_start
        self._update_position()
