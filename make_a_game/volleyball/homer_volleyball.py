# python3 /Users/yeong/00_work_out/make_a_game/volleyball/homer_volleyball.py
import pygame
import math
import os
import sys

# 게임 초기화
pygame.init()

# 게임 상수
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 220, 0)
PINK = (255, 182, 193)
BLUE = (100, 149, 237)
GREEN = (34, 139, 34)
BROWN = (139, 69, 19)
RED = (220, 20, 60)

# 게임 설정
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 7
BALL_BOUNCE = 0.85
WINNING_SCORE = 11

class Player:
    def __init__(self, x, y, player_num):
        self.x = x
        self.y = y
        self.player_num = player_num
        self.width = 60
        self.height = 80
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True if player_num == 1 else False

        # 이미지 로드 시도
        self.image = None
        image_path = "/Users/yeong/00_work_out/make_a_game/volleyball/simson/s_g.png"
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
            except:
                self.image = None

    def update(self, keys, is_ai=False, ball=None):
        # 플레이어 조작 (is_ai가 False일 때)
        if not is_ai:
            if self.player_num == 1:  # Player 1: WASD 키 (대소문자 및 한글 입력 모드 모두 지원)
                # 좌우 이동 - A(왼쪽), D(오른쪽)
                # pygame.K_a와 pygame.K_d는 물리적 키를 감지하므로
                # 대문자(A,D), 소문자(a,d), 한글(ㅁ,ㅇ) 모두 자동 인식
                if keys[pygame.K_a]:
                    self.vel_x = -MOVE_SPEED
                    self.facing_right = False
                elif keys[pygame.K_d]:
                    self.vel_x = MOVE_SPEED
                    self.facing_right = True
                else:
                    self.vel_x = 0

                # 점프 - W키 (대문자W, 소문자w, 한글ㅈ 모두 인식)
                if keys[pygame.K_w] and self.on_ground:
                    self.vel_y = JUMP_STRENGTH
                    self.on_ground = False

                # S키는 피카츄 배구에서 사용하지 않지만 입력은 인식
                # (필요시 빠른 낙하 등의 기능 추가 가능)

            elif self.player_num == 2:  # Player 2: 방향키
                # 좌우 이동
                if keys[pygame.K_LEFT]:
                    self.vel_x = -MOVE_SPEED
                    self.facing_right = False
                elif keys[pygame.K_RIGHT]:
                    self.vel_x = MOVE_SPEED
                    self.facing_right = True
                else:
                    self.vel_x = 0

                # 점프
                if keys[pygame.K_UP] and self.on_ground:
                    self.vel_y = JUMP_STRENGTH
                    self.on_ground = False

        # AI 조작 (is_ai가 True일 때)
        elif is_ai and ball:
            self.ai_control(ball)

        # 중력 적용
        if not self.on_ground:
            self.vel_y += GRAVITY

        # 위치 업데이트
        self.x += self.vel_x
        self.y += self.vel_y

        # 화면 경계 체크
        if self.x < 0:
            self.x = 0
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width

        # 바닥 체크
        ground_level = SCREEN_HEIGHT - 100
        if self.y >= ground_level - self.height:
            self.y = ground_level - self.height
            self.vel_y = 0
            self.on_ground = True

        # 네트 충돌 (왼쪽 플레이어는 중앙 왼쪽까지만, 오른쪽 플레이어는 중앙 오른쪽부터)
        net_x = SCREEN_WIDTH // 2 - 5
        if self.player_num == 1 and self.x + self.width > net_x:
            self.x = net_x - self.width
        elif self.player_num == 2 and self.x < net_x + 10:
            self.x = net_x + 10

    def ai_control(self, ball):
        """간단한 AI 로직"""
        # 공이 자기 쪽 코트에 있을 때만 반응
        target_x = ball.x

        # 공을 향해 이동
        if self.x + self.width // 2 < target_x - 20:
            self.vel_x = MOVE_SPEED
            self.facing_right = True
        elif self.x + self.width // 2 > target_x + 20:
            self.vel_x = -MOVE_SPEED
            self.facing_right = False
        else:
            self.vel_x = 0

        # 공이 가까이 있고 아래로 떨어지고 있으면 점프
        distance = math.sqrt((self.x - ball.x)**2 + (self.y - ball.y)**2)
        if distance < 150 and ball.vel_y > 0 and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def draw(self, screen):
        if self.image:
            # 이미지가 있으면 이미지 사용
            if not self.facing_right and self.player_num == 1:
                screen.blit(pygame.transform.flip(self.image, True, False), (int(self.x), int(self.y)))
            elif self.facing_right and self.player_num == 2:
                screen.blit(pygame.transform.flip(self.image, True, False), (int(self.x), int(self.y)))
            else:
                screen.blit(self.image, (int(self.x), int(self.y)))
        else:
            # 이미지가 없으면 호머 심슨 모양으로 그리기
            # 몸통
            color = YELLOW if self.player_num == 1 else (255, 200, 100)
            pygame.draw.circle(screen, color, (int(self.x + self.width // 2), int(self.y + 20)), 18)
            pygame.draw.rect(screen, color, (int(self.x + self.width // 2 - 15), int(self.y + 30), 30, 35))

            # 눈
            eye_offset = 5 if self.facing_right else -5
            pygame.draw.circle(screen, WHITE, (int(self.x + self.width // 2 + eye_offset), int(self.y + 18)), 4)
            pygame.draw.circle(screen, BLACK, (int(self.x + self.width // 2 + eye_offset), int(self.y + 18)), 2)

            # 다리
            pygame.draw.rect(screen, BLUE, (int(self.x + self.width // 2 - 12), int(self.y + 65), 10, 15))
            pygame.draw.rect(screen, BLUE, (int(self.x + self.width // 2 + 2), int(self.y + 65), 10, 15))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 25
        self.vel_x = 5
        self.vel_y = 0
        self.last_hit_player = None

        # 도넛 이미지 로드 시도
        self.image = None
        image_path = "/Users/yeong/00_work_out/make_a_game/volleyball/simson/d_g.png"
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path)
                self.image = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
            except:
                self.image = None

        # 충돌 사운드 로드
        self.hit_sound = None
        sound_path = "/Users/yeong/00_work_out/make_a_game/volleyball/simson/doh.mp3"
        if os.path.exists(sound_path):
            try:
                self.hit_sound = pygame.mixer.Sound(sound_path)
                self.hit_sound.set_volume(0.5)  # 볼륨 50%
            except:
                self.hit_sound = None

    def update(self):
        # 중력 적용
        self.vel_y += GRAVITY * 0.5

        # 위치 업데이트
        self.x += self.vel_x
        self.y += self.vel_y

        # 좌우 벽 충돌
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vel_x *= -BALL_BOUNCE
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vel_x *= -BALL_BOUNCE

        # 바닥 충돌
        ground_level = SCREEN_HEIGHT - 100
        if self.y + self.radius > ground_level:
            return True  # 점수 발생

        # 네트 충돌
        net_x = SCREEN_WIDTH // 2
        net_height = 120
        if abs(self.x - net_x) < self.radius + 5 and self.y + self.radius > SCREEN_HEIGHT - 100 - net_height:
            if self.x < net_x:
                self.x = net_x - self.radius - 5
            else:
                self.x = net_x + self.radius + 5
            self.vel_x *= -BALL_BOUNCE

        return False

    def check_collision(self, player):
        """플레이어와의 충돌 체크 및 처리"""
        player_rect = player.get_rect()

        # 원과 사각형의 충돌 감지
        closest_x = max(player_rect.left, min(self.x, player_rect.right))
        closest_y = max(player_rect.top, min(self.y, player_rect.bottom))

        distance = math.sqrt((self.x - closest_x)**2 + (self.y - closest_y)**2)

        if distance < self.radius:
            # 충돌 발생
            self.last_hit_player = player.player_num

            # 충돌 사운드 재생
            if self.hit_sound:
                self.hit_sound.play()

            # 플레이어 중심으로부터의 각도 계산
            angle = math.atan2(self.y - player.y - player.height // 2,
                             self.x - player.x - player.width // 2)

            # 속도 계산
            speed = math.sqrt(self.vel_x**2 + self.vel_y**2)
            speed = max(speed, 10)  # 최소 속도 보장

            self.vel_x = math.cos(angle) * speed
            self.vel_y = math.sin(angle) * speed - 3  # 약간 위로

            # 위치 조정 (겹침 방지)
            overlap = self.radius - distance
            self.x += math.cos(angle) * overlap
            self.y += math.sin(angle) * overlap

    def reset(self, winner_player=None):
        """공 리셋"""
        self.x = SCREEN_WIDTH // 2
        self.y = 200
        if winner_player == 1:
            self.vel_x = 5
        elif winner_player == 2:
            self.vel_x = -5
        else:
            self.vel_x = 5 if self.last_hit_player == 2 else -5
        self.vel_y = 0

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (int(self.x - self.radius), int(self.y - self.radius)))
        else:
            # 도넛 그리기
            pygame.draw.circle(screen, PINK, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 228, 196), (int(self.x), int(self.y)), self.radius - 5)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius // 3)
            # 스프링클 (장식)
            for i in range(8):
                angle = i * math.pi / 4
                sx = int(self.x + math.cos(angle) * (self.radius - 8))
                sy = int(self.y + math.sin(angle) * (self.radius - 8))
                color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)][i % 4]
                pygame.draw.circle(screen, color, (sx, sy), 2)


class Game:
    def __init__(self, screen, mode):
        self.screen = screen
        self.mode = mode  # 'single' or 'two_player'
        self.player1 = Player(100, SCREEN_HEIGHT - 200, 1)
        self.player2 = Player(SCREEN_WIDTH - 160, SCREEN_HEIGHT - 200, 2)
        self.ball = Ball(SCREEN_WIDTH // 2, 200)
        self.score1 = 0
        self.score2 = 0
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
        self.game_over = False
        self.winner = None

        # 배경 이미지 로드
        self.background = None
        bg_path = "/Users/yeong/Downloads/simson/simpson.gif"
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except:
                self.background = None

        # 게임 오버 이미지 로드
        self.gameover_image = None
        gameover_path = "/Users/yeong/00_work_out/make_a_game/volleyball/simson/gameover.png"
        if os.path.exists(gameover_path):
            try:
                self.gameover_image = pygame.image.load(gameover_path)
                # 화면 중앙에 표시할 적당한 크기로 조정
                self.gameover_image = pygame.transform.scale(self.gameover_image, (400, 300))
            except:
                self.gameover_image = None

    def draw_court(self):
        """코트 그리기"""
        # 배경
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((135, 206, 235))  # 하늘색
            # 바닥
            ground_level = SCREEN_HEIGHT - 100
            pygame.draw.rect(self.screen, GREEN, (0, ground_level, SCREEN_WIDTH, 100))

        # 네트
        net_x = SCREEN_WIDTH // 2
        net_height = 120
        ground_level = SCREEN_HEIGHT - 100
        pygame.draw.rect(self.screen, WHITE, (net_x - 5, ground_level - net_height, 10, net_height))
        # 네트 꼭대기
        pygame.draw.circle(self.screen, RED, (net_x, ground_level - net_height), 8)

        # 중앙선
        pygame.draw.line(self.screen, WHITE, (net_x, ground_level), (net_x, SCREEN_HEIGHT), 2)

    def draw_score(self):
        """점수 표시"""
        score_text1 = self.font.render(str(self.score1), True, BLACK)
        score_text2 = self.font.render(str(self.score2), True, BLACK)

        self.screen.blit(score_text1, (SCREEN_WIDTH // 4 - 20, 30))
        self.screen.blit(score_text2, (3 * SCREEN_WIDTH // 4 - 20, 30))

        # 플레이어 이름
        p1_text = self.small_font.render("Player 1", True, BLACK)
        p2_text = self.small_font.render("Player 2" if self.mode == 'two_player' else "AI", True, BLACK)

        self.screen.blit(p1_text, (SCREEN_WIDTH // 4 - 50, 80))
        self.screen.blit(p2_text, (3 * SCREEN_WIDTH // 4 - 50, 80))

    def check_score(self):
        """점수 확인"""
        ground_level = SCREEN_HEIGHT - 100

        if self.ball.y + self.ball.radius > ground_level:
            # 공이 바닥에 닿음
            net_x = SCREEN_WIDTH // 2

            if self.ball.x < net_x:
                # 왼쪽에 떨어짐 - 플레이어 2 득점
                self.score2 += 1
                self.ball.reset(winner_player=2)
            else:
                # 오른쪽에 떨어짐 - 플레이어 1 득점
                self.score1 += 1
                self.ball.reset(winner_player=1)

            # 게임 종료 확인
            if self.score1 >= WINNING_SCORE:
                self.game_over = True
                self.winner = 1
            elif self.score2 >= WINNING_SCORE:
                self.game_over = True
                self.winner = 2

            return True
        return False

    def draw_game_over(self):
        """게임 오버 화면"""
        # 반투명 검은 오버레이
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 게임 오버 이미지 표시
        if self.gameover_image:
            image_rect = self.gameover_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
            self.screen.blit(self.gameover_image, image_rect)

        # 승자 텍스트
        winner_text = f"{'Player ' + str(self.winner) if self.winner == 1 else ('AI' if self.mode == 'single' else 'Player 2')} Wins!"
        text = self.font.render(winner_text, True, YELLOW)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(text, text_rect)

        # 재시작 안내
        restart_text = self.small_font.render("Press SPACE to return to menu", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 160))
        self.screen.blit(restart_text, restart_rect)

    def run(self):
        """게임 실행"""
        running = True

        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'menu'
                    if self.game_over and event.key == pygame.K_SPACE:
                        return 'menu'

            if not self.game_over:
                # 키 입력 처리
                keys = pygame.key.get_pressed()

                # 플레이어 업데이트
                if self.mode == 'single':
                    # 싱글 모드: Player 1은 사람, Player 2는 AI
                    self.player1.update(keys, is_ai=False, ball=None)
                    self.player2.update(keys, is_ai=True, ball=self.ball)
                else:
                    # 2인 모드: 둘 다 사람
                    self.player1.update(keys, is_ai=False, ball=None)
                    self.player2.update(keys, is_ai=False, ball=None)

                # 공 업데이트
                self.ball.update()

                # 충돌 체크
                self.ball.check_collision(self.player1)
                self.ball.check_collision(self.player2)

                # 점수 체크
                self.check_score()

            # 그리기
            self.draw_court()
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            self.ball.draw(self.screen)
            self.draw_score()

            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()

        return 'quit'


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 48)
        self.clock = pygame.time.Clock()

        # 배경 이미지 로드
        self.background = None
        bg_path = "/Users/yeong/Downloads/simson/simson_fo.gif"
        if os.path.exists(bg_path):
            try:
                self.background = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except:
                self.background = None

        # 버튼 설정
        button_width = 300
        button_height = 80
        center_x = SCREEN_WIDTH // 2 - button_width // 2

        self.single_button = pygame.Rect(center_x, 200, button_width, button_height)
        self.two_player_button = pygame.Rect(center_x, 320, button_width, button_height)
        self.quit_button = pygame.Rect(center_x, 440, button_width, button_height)

    def draw_button(self, rect, text, color, hover_color, mouse_pos):
        """버튼 그리기"""
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, hover_color, rect, border_radius=10)
        else:
            pygame.draw.rect(self.screen, color, rect, border_radius=10)

        pygame.draw.rect(self.screen, BLACK, rect, 3, border_radius=10)

        text_surface = self.small_font.render(text, True, BLACK)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

    def run(self):
        """메뉴 실행"""
        running = True

        while running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.single_button.collidepoint(mouse_pos):
                        return 'single'
                    elif self.two_player_button.collidepoint(mouse_pos):
                        return 'two_player'
                    elif self.quit_button.collidepoint(mouse_pos):
                        return 'quit'

            # 배경
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill((135, 206, 250))

            # 제목
            title = self.font.render("HOMER VOLLEYBALL", True, YELLOW)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))

            # 제목에 그림자 효과
            shadow = self.font.render("HOMER VOLLEYBALL", True, BLACK)
            self.screen.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
            self.screen.blit(title, title_rect)

            # 버튼
            self.draw_button(self.single_button, "Single Player", (100, 200, 100), (150, 255, 150), mouse_pos)
            self.draw_button(self.two_player_button, "Two Players", (100, 150, 250), (150, 200, 255), mouse_pos)
            self.draw_button(self.quit_button, "Quit", (250, 100, 100), (255, 150, 150), mouse_pos)

            # 조작법 안내
            controls_font = pygame.font.Font(None, 24)
            controls = [
                "Player 1: W (Jump), A (Left), D (Right)",
                "Player 2: ↑ (Jump), ← (Left), → (Right)"
            ]

            for i, text in enumerate(controls):
                control_text = controls_font.render(text, True, BLACK)
                self.screen.blit(control_text, (SCREEN_WIDTH // 2 - 200, 540 + i * 25))

            pygame.display.flip()

        return 'quit'


def main():
    """메인 함수"""
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Homer Simpson Volleyball")

    # 아이콘 설정 (선택사항)
    try:
        if os.path.exists("icon.png"):
            icon = pygame.image.load("icon.png")
            pygame.display.set_icon(icon)
    except:
        pass

    menu = Menu(screen)

    while True:
        choice = menu.run()

        if choice == 'quit':
            break
        elif choice in ['single', 'two_player']:
            game = Game(screen, choice)
            result = game.run()

            if result == 'quit':
                break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
