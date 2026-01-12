"""
🍩 SIMPSONS DOOM 🍩
A Doom-style raycasting game with Simpsons characters!

Controls:
- W/S: Move forward/backward
- A/D: Strafe left/right
- LEFT/RIGHT arrows: Rotate camera
- SPACE: Collect donuts / Interact
- ESC: Quit

Objective: Collect all donuts while avoiding Flanders!
"""

import pygame
import math
import sys
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Screen settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
HALF_HEIGHT = SCREEN_HEIGHT // 2
FPS = 60

# Raycasting settings
FOV = math.pi / 3  # 60 degrees
HALF_FOV = FOV / 2
NUM_RAYS = SCREEN_WIDTH // 2
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 20
SCALE = SCREEN_WIDTH // NUM_RAYS

# Player settings
PLAYER_SPEED = 0.05
PLAYER_ROT_SPEED = 0.03
PLAYER_SIZE = 0.3

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 213, 0)  # Simpsons yellow
PINK = (255, 105, 180)  # Donut pink
SKY_BLUE = (135, 206, 235)
FLOOR_BROWN = (139, 90, 43)

# Map (1 = wall, 0 = empty, 2 = donut spawn, 3 = flanders spawn)
GAME_MAP = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 0, 0, 0, 2, 0, 0, 1, 1, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 3, 0, 1],
    [1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 2, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 2, 0, 1, 0, 0, 0, 0, 0, 3, 0, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 2, 0, 0, 1, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_WIDTH = len(GAME_MAP[0])
MAP_HEIGHT = len(GAME_MAP)


@dataclass
class Sprite:
    """Game sprite (donuts, enemies)"""
    x: float
    y: float
    sprite_type: str  # 'donut' or 'flanders'
    image: pygame.Surface
    active: bool = True
    scale: float = 0.6
    
    # For Flanders AI
    speed: float = 0.02
    direction: float = 0.0


class Player:
    def __init__(self, x: float, y: float, angle: float):
        self.x = x
        self.y = y
        self.angle = angle
        self.health = 100
        self.donuts_collected = 0
        
    def move(self, dx: float, dy: float, game_map: List[List[int]]):
        """Move player with collision detection"""
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check collision with walls
        if game_map[int(new_y)][int(new_x + PLAYER_SIZE * (1 if dx > 0 else -1))] == 0:
            self.x = new_x
        if game_map[int(new_y + PLAYER_SIZE * (1 if dy > 0 else -1))][int(new_x)] == 0:
            self.y = new_y


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🍩 SIMPSONS DOOM - Collect the Donuts!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        
        # Load assets
        self.load_assets()
        
        # Initialize game state
        self.reset_game()
        
        # Game state
        self.running = True
        self.game_over = False
        self.victory = False
        
    def load_assets(self):
        """Load game images"""
        try:
            # Load and scale images
            self.donut_img = pygame.image.load("/Users/yeong/00_work_out/make_a_game/h_doom/d_g.png").convert_alpha()
            self.flanders_img = pygame.image.load("/Users/yeong/00_work_out/make_a_game/h_doom/flanders.png").convert_alpha()
            self.gameover_img = pygame.image.load("/Users/yeong/00_work_out/make_a_game/h_doom/gameover.png").convert_alpha()
            self.homer_img = pygame.image.load("/Users/yeong/00_work_out/make_a_game/h_doom/s_g.png").convert_alpha()
            
            # Scale HUD homer
            self.homer_hud = pygame.transform.scale(self.homer_img, (150, 200))
            
            # Create wall texture (Simpsons-style)
            self.wall_texture = self.create_wall_texture()
            
            print("✅ Assets loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading assets: {e}")
            sys.exit(1)
    
    def create_wall_texture(self) -> pygame.Surface:
        """Create a Simpsons-style wall texture"""
        texture = pygame.Surface((64, 64))
        texture.fill((180, 140, 100))  # Base color
        
        # Add brick pattern
        for y in range(0, 64, 16):
            offset = 16 if (y // 16) % 2 else 0
            for x in range(-16 + offset, 64, 32):
                pygame.draw.rect(texture, (160, 120, 80), (x, y, 30, 14))
                pygame.draw.rect(texture, (140, 100, 60), (x, y, 30, 14), 1)
        
        return texture
    
    def reset_game(self):
        """Reset game state"""
        # Find player start position (first empty space)
        self.player = Player(1.5, 1.5, 0)
        
        # Create sprites from map
        self.sprites: List[Sprite] = []
        self.total_donuts = 0
        
        for y, row in enumerate(GAME_MAP):
            for x, cell in enumerate(row):
                if cell == 2:  # Donut
                    sprite = Sprite(
                        x=x + 0.5,
                        y=y + 0.5,
                        sprite_type='donut',
                        image=self.donut_img,
                        scale=0.4
                    )
                    self.sprites.append(sprite)
                    self.total_donuts += 1
                elif cell == 3:  # Flanders
                    sprite = Sprite(
                        x=x + 0.5,
                        y=y + 0.5,
                        sprite_type='flanders',
                        image=self.flanders_img,
                        scale=0.7,
                        direction=random.random() * math.pi * 2
                    )
                    self.sprites.append(sprite)
        
        self.player.health = 100
        self.player.donuts_collected = 0
        self.game_over = False
        self.victory = False
    
    def cast_rays(self) -> List[Tuple[float, float, bool]]:
        """Cast rays and return wall distances"""
        rays = []
        
        ray_angle = self.player.angle - HALF_FOV
        
        for ray in range(NUM_RAYS):
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)
            
            # Ray marching
            depth = 0
            hit_vertical = False
            
            for depth in range(1, MAX_DEPTH * 100):
                target_x = self.player.x + depth * cos_a * 0.01
                target_y = self.player.y + depth * sin_a * 0.01
                
                map_x = int(target_x)
                map_y = int(target_y)
                
                if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
                    if GAME_MAP[map_y][map_x] == 1:
                        # Determine if vertical or horizontal wall hit
                        hit_vertical = abs(target_x - map_x - 0.5) > abs(target_y - map_y - 0.5)
                        break
                else:
                    break
            
            # Fix fisheye effect
            depth = depth * 0.01 * math.cos(self.player.angle - ray_angle)
            rays.append((depth, ray_angle, hit_vertical))
            
            ray_angle += DELTA_ANGLE
        
        return rays
    
    def render_3d(self, rays: List[Tuple[float, float, bool]]):
        """Render 3D view using raycasting"""
        # Draw sky
        pygame.draw.rect(self.screen, SKY_BLUE, (0, 0, SCREEN_WIDTH, HALF_HEIGHT))
        
        # Draw floor
        pygame.draw.rect(self.screen, FLOOR_BROWN, (0, HALF_HEIGHT, SCREEN_WIDTH, HALF_HEIGHT))
        
        # Draw walls
        for i, (depth, angle, hit_vertical) in enumerate(rays):
            if depth > 0:
                # Calculate wall height
                wall_height = min(int(SCREEN_HEIGHT / (depth + 0.0001)), SCREEN_HEIGHT * 2)
                
                # Shade based on distance and wall orientation
                shade = max(50, 255 - int(depth * 25))
                if hit_vertical:
                    shade = int(shade * 0.7)  # Darker for vertical walls
                
                color = (min(255, shade + 30), min(255, shade), min(255, shade - 30))
                
                # Draw wall slice
                x = i * SCALE
                y = HALF_HEIGHT - wall_height // 2
                
                pygame.draw.rect(self.screen, color, (x, y, SCALE + 1, wall_height))
    
    def get_sprite_data(self, sprite: Sprite) -> Optional[Tuple[float, float, float, pygame.Surface]]:
        """Calculate sprite screen position and scale"""
        dx = sprite.x - self.player.x
        dy = sprite.y - self.player.y
        
        distance = math.sqrt(dx * dx + dy * dy)
        if distance < 0.1:
            distance = 0.1
        
        # Angle to sprite
        theta = math.atan2(dy, dx)
        
        # Relative angle
        delta = theta - self.player.angle
        
        # Normalize angle
        while delta > math.pi:
            delta -= 2 * math.pi
        while delta < -math.pi:
            delta += 2 * math.pi
        
        # Check if sprite is in FOV
        if abs(delta) > HALF_FOV + 0.3:
            return None
        
        # Screen X position
        screen_x = (delta / FOV + 0.5) * SCREEN_WIDTH
        
        # Scale based on distance
        scale = min(1.5, sprite.scale / (distance + 0.001))
        
        return (screen_x, distance, scale, sprite.image)
    
    def render_sprites(self, rays: List[Tuple[float, float, bool]]):
        """Render all sprites with depth sorting"""
        sprite_data = []
        
        for sprite in self.sprites:
            if not sprite.active:
                continue
            
            data = self.get_sprite_data(sprite)
            if data:
                sprite_data.append((sprite, *data))
        
        # Sort by distance (far to near)
        sprite_data.sort(key=lambda x: x[2], reverse=True)
        
        for sprite, screen_x, distance, scale, image in sprite_data:
            # Calculate sprite size
            sprite_height = int(SCREEN_HEIGHT * scale * 0.8)
            sprite_width = int(sprite_height * image.get_width() / image.get_height())
            
            if sprite_width > 0 and sprite_height > 0:
                # Scale sprite image
                scaled_img = pygame.transform.scale(image, (sprite_width, sprite_height))
                
                # Apply distance shading
                darkness = max(0, min(200, int(distance * 20)))
                if darkness > 0:
                    dark_surface = pygame.Surface(scaled_img.get_size())
                    dark_surface.fill((darkness, darkness, darkness))
                    scaled_img.blit(dark_surface, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
                
                # Position
                x = int(screen_x - sprite_width // 2)
                y = int(HALF_HEIGHT - sprite_height // 2)
                
                # Draw with depth check (simplified)
                self.screen.blit(scaled_img, (x, y))
    
    def render_hud(self):
        """Render HUD elements"""
        # Homer in corner
        self.screen.blit(self.homer_hud, (10, SCREEN_HEIGHT - 210))
        
        # Health bar
        pygame.draw.rect(self.screen, (100, 100, 100), (170, SCREEN_HEIGHT - 60, 200, 30))
        health_width = int(196 * self.player.health / 100)
        health_color = (0, 255, 0) if self.player.health > 50 else (255, 255, 0) if self.player.health > 25 else (255, 0, 0)
        pygame.draw.rect(self.screen, health_color, (172, SCREEN_HEIGHT - 58, health_width, 26))
        pygame.draw.rect(self.screen, WHITE, (170, SCREEN_HEIGHT - 60, 200, 30), 2)
        
        # Health text
        health_text = self.small_font.render(f"Health: {self.player.health}", True, WHITE)
        self.screen.blit(health_text, (175, SCREEN_HEIGHT - 55))
        
        # Donut counter
        donut_text = self.font.render(f"🍩 {self.player.donuts_collected}/{self.total_donuts}", True, PINK)
        self.screen.blit(donut_text, (SCREEN_WIDTH - 150, 20))
        
        # Mini-map
        self.render_minimap()
    
    def render_minimap(self):
        """Render a mini-map in the corner"""
        map_size = 150
        cell_size = map_size // max(MAP_WIDTH, MAP_HEIGHT)
        offset_x = SCREEN_WIDTH - map_size - 10
        offset_y = SCREEN_HEIGHT - map_size - 70
        
        # Background
        pygame.draw.rect(self.screen, (0, 0, 0, 128), (offset_x - 5, offset_y - 5, map_size + 10, map_size + 10))
        
        for y, row in enumerate(GAME_MAP):
            for x, cell in enumerate(row):
                color = (100, 100, 100) if cell == 1 else (50, 50, 50)
                pygame.draw.rect(self.screen, color, 
                               (offset_x + x * cell_size, offset_y + y * cell_size, 
                                cell_size - 1, cell_size - 1))
        
        # Draw player
        player_x = offset_x + int(self.player.x * cell_size)
        player_y = offset_y + int(self.player.y * cell_size)
        pygame.draw.circle(self.screen, YELLOW, (player_x, player_y), 3)
        
        # Draw player direction
        dir_x = player_x + int(math.cos(self.player.angle) * 8)
        dir_y = player_y + int(math.sin(self.player.angle) * 8)
        pygame.draw.line(self.screen, YELLOW, (player_x, player_y), (dir_x, dir_y), 2)
        
        # Draw sprites on minimap
        for sprite in self.sprites:
            if sprite.active:
                sx = offset_x + int(sprite.x * cell_size)
                sy = offset_y + int(sprite.y * cell_size)
                color = PINK if sprite.sprite_type == 'donut' else (0, 255, 0)
                pygame.draw.circle(self.screen, color, (sx, sy), 2)
    
    def render_game_over(self):
        """Render game over screen"""
        # Darken screen
        dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        dark.fill((0, 0, 0))
        dark.set_alpha(180)
        self.screen.blit(dark, (0, 0))
        
        # Game over image
        go_img = pygame.transform.scale(self.gameover_img, (300, 400))
        self.screen.blit(go_img, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 250))
        
        # Text
        if self.victory:
            text = self.font.render("WOOHOO! ALL DONUTS COLLECTED!", True, PINK)
        else:
            text = self.font.render("D'OH! FLANDERS GOT YOU!", True, (255, 0, 0))
        
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 180))
        self.screen.blit(text, text_rect)
        
        # Restart prompt
        restart = self.small_font.render("Press R to restart or ESC to quit", True, WHITE)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 230))
        self.screen.blit(restart, restart_rect)
    
    def update_flanders(self):
        """Update Flanders AI - they chase the player!"""
        for sprite in self.sprites:
            if sprite.sprite_type == 'flanders' and sprite.active:
                # Calculate direction to player
                dx = self.player.x - sprite.x
                dy = self.player.y - sprite.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance > 0.5:  # Chase player
                    # Normalize and move
                    dx /= distance
                    dy /= distance
                    
                    new_x = sprite.x + dx * sprite.speed
                    new_y = sprite.y + dy * sprite.speed
                    
                    # Simple collision check
                    if GAME_MAP[int(new_y)][int(new_x)] != 1:
                        sprite.x = new_x
                        sprite.y = new_y
                
                # Check collision with player
                if distance < 0.5:
                    self.player.health -= 1
                    if self.player.health <= 0:
                        self.game_over = True
    
    def check_donut_collection(self):
        """Check if player collected a donut"""
        for sprite in self.sprites:
            if sprite.sprite_type == 'donut' and sprite.active:
                dx = self.player.x - sprite.x
                dy = self.player.y - sprite.y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance < 0.5:
                    sprite.active = False
                    self.player.donuts_collected += 1
                    self.player.health = min(100, self.player.health + 10)
                    
                    # Check victory
                    if self.player.donuts_collected >= self.total_donuts:
                        self.victory = True
                        self.game_over = True
    
    def handle_input(self):
        """Handle player input"""
        keys = pygame.key.get_pressed()
        
        # Calculate movement vectors
        cos_a = math.cos(self.player.angle)
        sin_a = math.sin(self.player.angle)
        
        dx, dy = 0, 0
        
        # Forward/backward
        if keys[pygame.K_w]:
            dx += cos_a * PLAYER_SPEED
            dy += sin_a * PLAYER_SPEED
        if keys[pygame.K_s]:
            dx -= cos_a * PLAYER_SPEED
            dy -= sin_a * PLAYER_SPEED
        
        # Strafe
        if keys[pygame.K_a]:
            dx += sin_a * PLAYER_SPEED
            dy -= cos_a * PLAYER_SPEED
        if keys[pygame.K_d]:
            dx -= sin_a * PLAYER_SPEED
            dy += cos_a * PLAYER_SPEED
        
        # Rotation
        if keys[pygame.K_LEFT]:
            self.player.angle -= PLAYER_ROT_SPEED
        if keys[pygame.K_RIGHT]:
            self.player.angle += PLAYER_ROT_SPEED
        
        # Apply movement
        self.player.move(dx, dy, GAME_MAP)
    
    def run(self):
        """Main game loop"""
        print("\n" + "="*50)
        print("🍩 SIMPSONS DOOM 🍩")
        print("="*50)
        print("Collect all donuts while avoiding Flanders!")
        print("\nControls:")
        print("  W/S - Move forward/backward")
        print("  A/D - Strafe left/right")
        print("  ←/→ - Rotate")
        print("  ESC - Quit")
        print("="*50 + "\n")
        
        while self.running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset_game()
            
            if not self.game_over:
                # Update
                self.handle_input()
                self.update_flanders()
                self.check_donut_collection()
                
                # Render
                rays = self.cast_rays()
                self.render_3d(rays)
                self.render_sprites(rays)
                self.render_hud()
            else:
                # Still render the scene
                rays = self.cast_rays()
                self.render_3d(rays)
                self.render_sprites(rays)
                self.render_hud()
                self.render_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
