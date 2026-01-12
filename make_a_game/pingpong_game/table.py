# 심슨 핑퐁 게임 - Table 클래스
# 게임 테이블(캔버스)을 정의합니다

from tkinter import *
from PIL import Image, ImageTk

class Table:
    #### 생성자
    def __init__(self, window, background_image=None, net_colour="yellow",
                 width=800, height=600, vertical_net=True, horizontal_net=False):
        self.width = width
        self.height = height
        self.window = window

        # tkinter 캔버스 생성
        self.canvas = Canvas(window, height=self.height, width=self.width)
        self.canvas.pack()

        # 배경 이미지 설정
        if background_image:
            try:
                bg_img = Image.open(background_image)
                bg_img = bg_img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(bg_img)
                self.canvas.create_image(0, 0, anchor=NW, image=self.bg_photo)
            except:
                self.canvas.config(bg="skyblue")
        else:
            self.canvas.config(bg="skyblue")

        # 네트(중앙선) 추가
        if vertical_net:
            self.canvas.create_line(self.width/2, 0, self.width/2, self.height,
                                   width=3, fill=net_colour, dash=(15, 23))
        if horizontal_net:
            self.canvas.create_line(0, self.height/2, self.width, self.height/2,
                                   width=3, fill=net_colour, dash=(15, 23))

        # 득점판 추가
        font = ("monaco", 72, "bold")
        self.scoreboard = self.canvas.create_text(self.width/2, 80, font=font,
                                                  fill="yellow", text="0  0")

    #### 메서드
    # Canvas에 직사각형을 추가
    def draw_rectangle(self, rectangle):
        x1 = rectangle.x_posn
        x2 = rectangle.x_posn + rectangle.width
        y1 = rectangle.y_posn
        y2 = rectangle.y_posn + rectangle.height
        c = rectangle.colour
        return self.canvas.create_rectangle(x1, y1, x2, y2, fill=c, outline="black", width=2)

    # Canvas에 이미지를 추가
    def draw_image(self, image_obj):
        return self.canvas.create_image(image_obj.x_posn, image_obj.y_posn,
                                       anchor=NW, image=image_obj.photo)

    # canvas의 아이템 이동
    def move_item(self, item, x1, y1, x2=None, y2=None):
        if x2 is None:  # 이미지의 경우
            self.canvas.coords(item, x1, y1)
        else:  # 직사각형의 경우
            self.canvas.coords(item, x1, y1, x2, y2)

    def remove_item(self, item):
        self.canvas.delete(item)

    def change_item_colour(self, item, c):
        self.canvas.itemconfigure(item, fill=c)

    # 득점판 업데이트
    def draw_score(self, left, right):
        scores = str(left) + "  " + str(right)
        self.canvas.itemconfigure(self.scoreboard, text=scores)
