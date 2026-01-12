import pygame
import sys

# 초기화
pygame.init()

# 화면 설정
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("슈퍼 심슨 (Homer Mario)")

# 색상 정의
WHITE = (255, 255, 255)
SKY_BLUE = (135, 206, 235)
YELLOW = (255, 217, 15)  # 심슨 피부색
BLUE = (0, 80, 150)      # 바지 색
BROWN = (139, 69, 19)
GREEN = (34, 139, 34)
BLACK = (0, 0, 0)
WHITE_EYE = (255, 255, 255)
BEARD = (209, 178, 120)  # 호머 수염 색
PINK = (255, 182, 193)   # 도넛 색

# 적 캐릭터 색상
NED_GREEN = (46, 139, 87) # 플랜더스 스웨터
NED_MUSTACHE = (101, 67, 33) # 플랜더스 콧수염
SMITHERS_PURPLE = (128, 0, 128) # 스미더스 나비넥타이
GRAY = (169, 169, 169) # 스미더스 머리색

# 게임 상수
GRAVITY = 0.8
JUMP_STRENGTH = -16
PLAYER_SPEED = 5
ENEMY_SPEED = 2

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 60), pygame.SRCALPHA)
        self.draw_homer()
        self.rect = self.image.get_rect()
        self.reset_position()
        self.vel_y = 0
        self.is_jumping = False

    def reset_position(self):
        self.rect.x = 100
        self.rect.y = SCREEN_HEIGHT - 150
        self.vel_y = 0

    def draw_homer(self):
        # 몸통 (흰색 셔츠)
        pygame.draw.rect(self.image, WHITE, (5, 25, 30, 20))
        # 바지 (파란색)
        pygame.draw.rect(self.image, BLUE, (5, 45, 30, 15))
        # 머리 (노란색)
        pygame.draw.ellipse(self.image, YELLOW, (10, 0, 20, 28))
        # 입주변 (수염/입)
        pygame.draw.ellipse(self.image, BEARD, (10, 18, 20, 12))
        # 눈
        pygame.draw.circle(self.image, WHITE_EYE, (15, 10), 4)
        pygame.draw.circle(self.image, WHITE_EYE, (25, 10), 4)
        pygame.draw.circle(self.image, BLACK, (15, 10), 1)
        pygame.draw.circle(self.image, BLACK, (25, 10), 1)

    def update(self, platforms):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # 플랫폼 충돌 체크
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.is_jumping = False
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED

        if self.rect.left < 0:
            self.rect.left = 0

    def jump(self):
        if not self.is_jumping:
            self.vel_y = JUMP_STRENGTH
            self.is_jumping = True

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="ned"):
        super().__init__()
        self.image = pygame.Surface((40, 60), pygame.SRCALPHA)
        self.type = enemy_type
        if enemy_type == "ned":
            self.draw_ned()
        else:
            self.draw_smithers()
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 1
        self.move_range = 100
        self.start_x = x

    def draw_ned(self):
        # 네드 플랜더스 그리기
        pygame.draw.rect(self.image, NED_GREEN, (5, 25, 30, 20)) # 스웨터
        pygame.draw.rect(self.image, GRAY, (5, 45, 30, 15)) # 회색 바지
        pygame.draw.ellipse(self.image, YELLOW, (10, 0, 20, 28)) # 머리
        pygame.draw.rect(self.image, NED_MUSTACHE, (12, 18, 16, 4)) # 콧수염
        pygame.draw.circle(self.image, BLACK, (15, 10), 5, 1) # 안경 왼쪽
        pygame.draw.circle(self.image, BLACK, (25, 10), 5, 1) # 안경 오른쪽

    def draw_smithers(self):
        # 스미더스 그리기
        pygame.draw.rect(self.image, WHITE, (5, 25, 30, 20)) # 셔츠
        pygame.draw.rect(self.image, SMITHERS_PURPLE, (15, 27, 10, 5)) # 나비넥타이
        pygame.draw.rect(self.image, BLUE, (5, 45, 30, 15)) # 바지
        pygame.draw.ellipse(self.image, YELLOW, (10, 5, 20, 25)) # 머리
        pygame.draw.ellipse(self.image, GRAY, (10, 0, 20, 10)) # 머리카락
        pygame.draw.circle(self.image, BLACK, (15, 12), 4, 1) # 안경

    def update(self):
        self.rect.x += self.direction * ENEMY_SPEED
        # 좌우 이동 범위 제한
        if abs(self.rect.x - self.start_x) > self.move_range:
            self.direction *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, is_ground=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        if is_ground:
            self.image.fill(GREEN)
        else:
            self.image.fill(BROWN)
            pygame.draw.rect(self.image, BLACK, (0, 0, width, height), 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Donut(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PINK, (15, 15), 12)
        pygame.draw.circle(self.image, SKY_BLUE, (15, 15), 4)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

def main():
    clock = pygame.time.Clock()
    player = Player()
    
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    donuts = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    all_sprites.add(player)

    # 지면
    ground = Platform(0, SCREEN_HEIGHT - 40, 5000, 40, True)
    platforms.add(ground)
    all_sprites.add(ground)

    # 발판 및 적 배치
    level_data = [
        {"plat": (300, 450, 200, 40), "enemy": "ned"},
        {"plat": (600, 350, 250, 40), "enemy": "smithers"},
        {"plat": (1000, 400, 200, 40), "enemy": "ned"},
        {"plat": (1300, 250, 200, 40), "enemy": "smithers"}
    ]

    for data in level_data:
        p_x, p_y, p_w, p_h = data["plat"]
        p = Platform(p_x, p_y, p_w, p_h)
        platforms.add(p)
        all_sprites.add(p)
        
        # 적 생성
        e = Enemy(p_x + 50, p_y - 60, data["enemy"])
        enemies.add(e)
        all_sprites.add(e)

        # 도넛 생성
        d = Donut(p_x + p_w//2 - 15, p_y - 40)
        donuts.add(d)
        all_sprites.add(d)

    score = 0
    font = pygame.font.SysFont("malgungothic", 30)
    camera_x = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_UP]:
                    player.jump()

        # 업데이트
        player.update(platforms)
        enemies.update()

        # 도넛 획득
        donut_hits = pygame.sprite.spritecollide(player, donuts, True)
        for hit in donut_hits:
            score += 10

        # 적과의 충돌 처리
        enemy_hits = pygame.sprite.spritecollide(player, enemies, False)
        for enemy in enemy_hits:
            # 머리 위에서 밟았을 때 (내려오는 중이고 발이 적 머리 근처일 때)
            if player.vel_y > 0 and player.rect.bottom < enemy.rect.centery + 10:
                enemy.kill()
                player.vel_y = JUMP_STRENGTH / 1.5 # 반동 점프
                score += 50
            else:
                # 옆이나 아래서 부딪히면 사망
                player.reset_position()
                camera_x = 0
                score = max(0, score - 20)

        # 카메라 이동
        if player.rect.right > SCREEN_WIDTH / 2 + camera_x:
            camera_x = player.rect.right - SCREEN_WIDTH / 2

        # 그리기
        screen.fill(SKY_BLUE)

        for sprite in all_sprites:
            screen.blit(sprite.image, (sprite.rect.x - camera_x, sprite.rect.y))

        # UI 표시
        score_text = font.render(f"도넛 점수: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        instr_text = font.render("밟아서 처치하세요!", True, WHITE)
        screen.blit(instr_text, (SCREEN_WIDTH - 250, 10))

        # 낙사 체크
        if player.rect.top > SCREEN_HEIGHT:
            player.reset_position()
            camera_x = 0

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()