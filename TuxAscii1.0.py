import pygame
import random
import math
import sys
import time
from enum import Enum

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TuxAscii")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

# Game states
class GameState(Enum):
    TITLE = 0
    GAMEPLAY = 1
    LORE = 2
    CONTROLS = 3
    GAME_OVER = 4

# Fonts
title_font = pygame.font.SysFont('courier', 48, bold=True)
menu_font = pygame.font.SysFont('courier', 24)
game_font = pygame.font.SysFont('courier', 16)
big_font = pygame.font.SysFont('courier', 36)

# Game clock
clock = pygame.time.Clock()
FPS = 60

# Player class
class Player:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.width = 30
        self.height = 30
        self.speed = 5
        self.bullets = []
        self.shoot_delay = 200  # milliseconds
        self.last_shot = pygame.time.get_ticks()
        self.score = 0
        self.lives = 3
        self.bombs = 3
        self.power_level = 1
        self.power_type = "normal"  # normal, double, speed, bomb
        self.power_timer = 0
        self.invincible = False
        self.invincible_timer = 0
        
    def move(self, keys):
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < WIDTH - self.width:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < HEIGHT - self.height:
            self.y += self.speed
            
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            if self.power_type == "double":
                self.bullets.append(Bullet(self.x + 5, self.y, -1))
                self.bullets.append(Bullet(self.x + self.width - 5, self.y, -1))
            elif self.power_type == "triple":
                self.bullets.append(Bullet(self.x + self.width // 2, self.y, -1))
                self.bullets.append(Bullet(self.x + 5, self.y, -1, angle=-15))
                self.bullets.append(Bullet(self.x + self.width - 5, self.y, -1, angle=15))
            else:  # normal
                self.bullets.append(Bullet(self.x + self.width // 2, self.y, -1))
    
    def use_bomb(self):
        if self.bombs > 0:
            self.bombs -= 1
            return True
        return False
    
    def apply_powerup(self, powerup_type):
        self.power_type = powerup_type
        self.power_timer = pygame.time.get_ticks()
        
        if powerup_type == "speed":
            self.speed = 8
        elif powerup_type == "bomb":
            self.bombs += 1
        elif powerup_type in ["double", "triple"]:
            self.shoot_delay = 150
    
    def update_powerups(self):
        now = pygame.time.get_ticks()
        if self.power_type != "normal" and now - self.power_timer > 10000:  # 10 seconds
            self.power_type = "normal"
            self.speed = 5
            self.shoot_delay = 200
        
        if self.invincible and now - self.invincible_timer > 3000:  # 3 seconds
            self.invincible = False
    
    def draw(self, surface):
        # Draw updated player ASCII art
        player_ascii = [
            " /\\ ",
            "/><\\",
            "\\__/"
        ]
        
        for i, line in enumerate(player_ascii):
            text = game_font.render(line, True, WHITE if not self.invincible or pygame.time.get_ticks() % 400 < 200 else YELLOW)
            surface.blit(text, (self.x, self.y + i * 15))

# Bullet class
class Bullet:
    def __init__(self, x, y, direction, angle=0, speed=10, char="*", color=WHITE):
        self.x = x
        self.y = y
        self.direction = direction  # 1 for enemy bullets (down), -1 for player bullets (up)
        self.angle = angle  # Degrees, 0 is straight
        self.speed = speed
        self.char = char
        self.color = color
        self.width = 5
        self.height = 5
        
    def update(self):
        # Calculate movement based on angle
        rad_angle = math.radians(self.angle)
        self.x += math.sin(rad_angle) * self.speed
        self.y += self.direction * math.cos(rad_angle) * self.speed
        
    def draw(self, surface):
        text = game_font.render(self.char, True, self.color)
        surface.blit(text, (self.x, self.y))
        
    def is_offscreen(self):
        return self.y < 0 or self.y > HEIGHT or self.x < 0 or self.x > WIDTH

# Enemy class
class Enemy:
    def __init__(self, x, y, enemy_type="normal"):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.speed = random.randint(1, 3)
        self.bullets = []
        self.shoot_delay = random.randint(1000, 3000)
        self.last_shot = pygame.time.get_ticks()
        self.health = 3 if enemy_type == "normal" else 10
        self.enemy_type = enemy_type
        self.movement_pattern = random.choice(["straight", "zigzag", "circular"])
        self.angle = 0
        
    def update(self):
        # Different movement patterns
        if self.movement_pattern == "straight":
            self.y += self.speed
        elif self.movement_pattern == "zigzag":
            self.x += math.sin(pygame.time.get_ticks() * 0.002) * 2
            self.y += self.speed
        elif self.movement_pattern == "circular":
            self.angle += 0.05
            self.x += math.sin(self.angle) * 2
            self.y += self.speed
            
        # Shoot bullets
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            self.shoot()
            
    def shoot(self):
        if self.enemy_type == "boss":
            # Boss shoots multiple bullets in patterns
            pattern = random.choice(["circle", "spread", "aimed"])
            
            if pattern == "circle":
                for angle in range(0, 360, 30):
                    self.bullets.append(Bullet(self.x + self.width // 2, self.y + self.height, 1, angle=angle, char="+", color=RED))
            elif pattern == "spread":
                for angle in range(-45, 46, 15):
                    self.bullets.append(Bullet(self.x + self.width // 2, self.y + self.height, 1, angle=angle, char="*", color=MAGENTA))
            else:  # aimed
                for i in range(-2, 3):
                    self.bullets.append(Bullet(self.x + self.width // 2, self.y + self.height, 1, angle=i*10, speed=5, char="o", color=CYAN))
        else:
            # Normal enemies shoot simple bullets
            self.bullets.append(Bullet(self.x + self.width // 2, self.y + self.height, 1, char="v", color=YELLOW))
    
    def draw(self, surface):
        if self.enemy_type == "boss":
            boss = [
                " /^\\/^\\ ",
                "<|00  |>",
                " \\VV__/ "
            ]
            for i, line in enumerate(boss):
                text = game_font.render(line, True, RED)
                surface.blit(text, (self.x - 10, self.y + i * 15))
        else:
            enemy = [
                "/\\_/\\",
                "o o ",
                ">-<"
            ]
            for i, line in enumerate(enemy):
                text = game_font.render(line, True, YELLOW)
                surface.blit(text, (self.x, self.y + i * 15))
    
    def is_offscreen(self):
        return self.y > HEIGHT + 50

# Powerup class
class Powerup:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.speed = 2
        self.powerup_type = random.choice(["double", "triple", "speed", "bomb"])
        self.colors = {
            "double": YELLOW,
            "triple": CYAN,
            "speed": GREEN,
            "bomb": RED
        }
        
    def update(self):
        self.y += self.speed
        
    def draw(self, surface):
        symbols = {
            "double": "D",
            "triple": "T",
            "speed": "S",
            "bomb": "B"
        }
        
        # Draw powerup
        pygame.draw.circle(surface, self.colors[self.powerup_type], (self.x + self.width // 2, self.y + self.height // 2), 10)
        text = game_font.render(symbols[self.powerup_type], True, BLACK)
        text_rect = text.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        surface.blit(text, text_rect)
    
    def is_offscreen(self):
        return self.y > HEIGHT

# Star class for background
class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.randint(1, 3)
        self.char = random.choice(['*', '.', '+', '·'])
        
    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)
            
    def draw(self, surface):
        text = game_font.render(self.char, True, WHITE)
        surface.blit(text, (self.x, self.y))

# Game class
class Game:
    def __init__(self):
        self.state = GameState.TITLE
        self.player = Player()
        self.enemies = []
        self.powerups = []
        self.stars = [Star() for _ in range(100)]
        self.enemy_spawn_timer = 0
        self.boss_timer = 0
        self.background_offset = 0
        
    def reset_game(self):
        self.player.reset()
        self.enemies = []
        self.powerups = []
        self.enemy_spawn_timer = pygame.time.get_ticks()
        self.boss_timer = pygame.time.get_ticks()
        
    def update(self):
        # Update background stars
        for star in self.stars:
            star.update()
            
        if self.state == GameState.GAMEPLAY:
            # Update player
            keys = pygame.key.get_pressed()
            self.player.move(keys)
            self.player.update_powerups()
            
            if keys[pygame.K_SPACE]:
                self.player.shoot()
                
            if keys[pygame.K_b]:
                if self.player.use_bomb():
                    # Clear all enemies and bullets
                    for enemy in self.enemies:
                        self.player.score += 100
                    self.enemies = []
                    for enemy in self.enemies:
                        enemy.bullets = []
            
            # Spawn enemies
            now = pygame.time.get_ticks()
            if now - self.enemy_spawn_timer > 1500:  # Spawn enemy every 1.5 seconds
                self.enemy_spawn_timer = now
                self.enemies.append(Enemy(random.randint(50, WIDTH - 50), -30))
                
            # Spawn boss
            if now - self.boss_timer > 30000:  # Boss every 30 seconds
                self.boss_timer = now
                self.enemies.append(Enemy(WIDTH // 2 - 50, -50, enemy_type="boss"))
                
            # Update bullets
            for bullet in self.player.bullets[:]:
                bullet.update()
                if bullet.is_offscreen():
                    self.player.bullets.remove(bullet)
            
            # Update enemies
            for enemy in self.enemies[:]:
                enemy.update()
                
                # Enemy bullet updates
                for bullet in enemy.bullets[:]:
                    bullet.update()
                    if bullet.is_offscreen():
                        enemy.bullets.remove(bullet)
                    elif not self.player.invincible and self.check_collision(bullet.x, bullet.y, bullet.width, bullet.height,
                                  self.player.x, self.player.y, self.player.width, self.player.height):
                        enemy.bullets.remove(bullet)
                        self.player.lives -= 1
                        self.player.invincible = True
                        self.player.invincible_timer = pygame.time.get_ticks()
                        if self.player.lives <= 0:
                            self.state = GameState.GAME_OVER
                
                # Check if enemy is hit by player's bullet
                for bullet in self.player.bullets[:]:
                    if self.check_collision(bullet.x, bullet.y, bullet.width, bullet.height,
                                  enemy.x, enemy.y, enemy.width, enemy.height):
                        self.player.bullets.remove(bullet)
                        enemy.health -= 1
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                            self.player.score += 500 if enemy.enemy_type == "boss" else 100
                            
                            # Chance to spawn powerup
                            if random.random() < 0.3 or enemy.enemy_type == "boss":
                                self.powerups.append(Powerup(enemy.x, enemy.y))
                            break
                
                if enemy.is_offscreen():
                    self.enemies.remove(enemy)
            
            # Update powerups
            for powerup in self.powerups[:]:
                powerup.update()
                if powerup.is_offscreen():
                    self.powerups.remove(powerup)
                elif self.check_collision(powerup.x, powerup.y, powerup.width, powerup.height,
                              self.player.x, self.player.y, self.player.width, self.player.height):
                    self.player.apply_powerup(powerup.powerup_type)
                    self.powerups.remove(powerup)
    
    def check_collision(self, x1, y1, w1, h1, x2, y2, w2, h2):
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)
    
    def draw_title_screen(self):
        # Draw stars
        for star in self.stars:
            star.draw(screen)
        
        # Draw title
        title_text = title_font.render("TuxAscii", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        # Draw by line
        by_text = menu_font.render("By ElysiumSoft 2025", True, WHITE)
        by_rect = by_text.get_rect(center=(WIDTH // 2, HEIGHT // 4 + 50))
        screen.blit(by_text, by_rect)
        
        # Draw menu options
        options = [
            "S [Start Game]",
            "A [Lore]",
            "D [Controls]"
        ]
        
        for i, option in enumerate(options):
            option_text = menu_font.render(option, True, WHITE)
            option_rect = option_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + i * 40))
            screen.blit(option_text, option_rect)
    
    def draw_lore_screen(self):
        # Draw stars
        for star in self.stars:
            star.draw(screen)
        
        # Draw title
        title_text = big_font.render("Lore", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_text, title_rect)
        
        # Draw lore text
        lore_text = [
            "In the year 2099, the cosmic emperor Propriebus has",
            "declared war on all open-source lifeforms. His armies",
            "of locked-down drones sweep through the galaxy,",
            "assimilating all in their path.",
            "",
            "Only one hero remains to defend the freedom of code:",
            "Tux, the last penguin warrior, armed with the power",
            "of ASCII and an unbreakable spirit of openness.",
            "",
            "Pilot Tux through waves of enemies and reclaim the",
            "digital universe one character at a time!"
        ]
        
        for i, line in enumerate(lore_text):
            line_text = menu_font.render(line, True, WHITE)
            line_rect = line_text.get_rect(center=(WIDTH // 2, 150 + i * 30))
            screen.blit(line_text, line_rect)
        
        # Draw back instruction
        back_text = menu_font.render("Press Q to return to title screen", True, WHITE)
        back_rect = back_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        screen.blit(back_text, back_rect)
    
    def draw_controls_screen(self):
        # Draw stars
        for star in self.stars:
            star.draw(screen)
        
        # Draw title
        title_text = big_font.render("Controls", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_text, title_rect)
        
        # Draw controls text
        controls_text = [
            "Arrow Keys - Move Tux",
            "Space - Shoot",
            "B - Use Bomb (clears all enemies)",
            "Q - Quit to title screen",
            "",
            "Power-ups:",
            "D - Double shot",
            "T - Triple shot",
            "S - Speed boost",
            "B - Extra bomb"
        ]
        
        for i, line in enumerate(controls_text):
            line_text = menu_font.render(line, True, WHITE)
            line_rect = line_text.get_rect(center=(WIDTH // 2, 150 + i * 30))
            screen.blit(line_text, line_rect)
        
        # Draw back instruction
        back_text = menu_font.render("Press Q to return to title screen", True, WHITE)
        back_rect = back_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        screen.blit(back_text, back_rect)
    
    def draw_game_over_screen(self):
        # Draw stars
        for star in self.stars:
            star.draw(screen)
        
        # Draw game over text
        game_over_text = big_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(game_over_text, game_over_rect)
        
        # Draw score
        score_text = menu_font.render(f"Final Score: {self.player.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(score_text, score_rect)
        
        # Draw restart instructions
        restart_text = menu_font.render("Press R to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(restart_text, restart_rect)
        
        # Draw quit instructions
        quit_text = menu_font.render("Press Q to return to title screen", True, WHITE)
        quit_rect = quit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
        screen.blit(quit_text, quit_rect)
    
    def draw_gameplay(self):
        # Draw stars
        for star in self.stars:
            star.draw(screen)
        
        # Draw player
        self.player.draw(screen)
        
        # Draw player bullets
        for bullet in self.player.bullets:
            bullet.draw(screen)
        
        # Draw enemies and their bullets
        for enemy in self.enemies:
            enemy.draw(screen)
            for bullet in enemy.bullets:
                bullet.draw(screen)
        
        # Draw powerups
        for powerup in self.powerups:
            powerup.draw(screen)
        
        # Draw HUD
        score_text = game_font.render(f"Score: {self.player.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        lives_text = game_font.render(f"Lives: {self.player.lives}", True, WHITE)
        screen.blit(lives_text, (10, 30))
        
        bombs_text = game_font.render(f"Bombs: {self.player.bombs}", True, WHITE)
        screen.blit(bombs_text, (10, 50))
        
        power_text = game_font.render(f"Power: {self.player.power_type.capitalize()}", True, self.get_power_color())
        screen.blit(power_text, (10, 70))
    
    def get_power_color(self):
        if self.player.power_type == "double":
            return YELLOW
        elif self.player.power_type == "triple":
            return CYAN
        elif self.player.power_type == "speed":
            return GREEN
        elif self.player.power_type == "bomb":
            return RED
        else:
            return WHITE
    
    def draw(self):
        screen.fill(BLACK)
        
        if self.state == GameState.TITLE:
            self.draw_title_screen()
        elif self.state == GameState.LORE:
            self.draw_lore_screen()
        elif self.state == GameState.CONTROLS:
            self.draw_controls_screen()
        elif self.state == GameState.GAMEPLAY:
            self.draw_gameplay()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over_screen()
        
        pygame.display.flip()

# Main game loop
def main():
    game = Game()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if game.state == GameState.TITLE:
                    if event.key == pygame.K_s:
                        game.state = GameState.GAMEPLAY
                        game.reset_game()
                    elif event.key == pygame.K_a:
                        game.state = GameState.LORE
                    elif event.key == pygame.K_d:
                        game.state = GameState.CONTROLS
                elif game.state == GameState.LORE or game.state == GameState.CONTROLS:
                    if event.key == pygame.K_q:
                        game.state = GameState.TITLE
                elif game.state == GameState.GAMEPLAY:
                    if event.key == pygame.K_q:
                        game.state = GameState.TITLE
                elif game.state == GameState.GAME_OVER:
                    if event.key == pygame.K_r:
                        game.state = GameState.GAMEPLAY
                        game.reset_game()
                    elif event.key == pygame.K_q:
                        game.state = GameState.TITLE
        
        game.update()
        game.draw()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
