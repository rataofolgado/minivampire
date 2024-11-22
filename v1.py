import pygame
import random
import math
from pygame.math import Vector2

# Inicialização do Pygame
pygame.init()

# Configurações da tela

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mini Vampire Survivors")

# Configurações do mapa
MAP_WIDTH = 2400
MAP_HEIGHT = 1800

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 100, 0)  # Cor do chão

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return Vector2(entity.pos.x - self.camera.x, entity.pos.y - self.camera.y)

    def update(self, target):
        # Centraliza a câmera no jogador
        x = -target.pos.x + int(SCREEN_WIDTH / 2)
        y = -target.pos.y + int(SCREEN_HEIGHT / 2)

        # Limita a câmera aos limites do mapa
        x = min(0, x)  # Limite esquerdo
        y = min(0, y)  # Limite superior
        x = max(-(MAP_WIDTH - SCREEN_WIDTH), x)  # Limite direito
        y = max(-(MAP_HEIGHT - SCREEN_HEIGHT), y)  # Limite inferior

        self.camera.x = -x
        self.camera.y = -y

class Projectile:
    def __init__(self, player, angle_offset):
        self.player = player
        self.angle_offset = angle_offset
        self.orbit_radius = 50
        self.angle = 0
        self.rotation_speed = 3
        self.size = 5
        self.damage = 10
        self.is_active = True
        self.pos = Vector2(0, 0)

    def update(self):
        self.angle += self.rotation_speed
        if self.angle >= 360:
            self.angle = 0

        total_angle = math.radians(self.angle + self.angle_offset)
        offset_x = math.cos(total_angle) * self.orbit_radius
        offset_y = math.sin(total_angle) * self.orbit_radius
        
        self.pos.x = self.player.pos.x + offset_x
        self.pos.y = self.player.pos.y + offset_y

    def draw(self, screen, camera):
        screen_pos = camera.apply(self)
        pygame.draw.circle(screen, WHITE, (int(screen_pos.x), int(screen_pos.y)), self.size)

class Player:
    def __init__(self, x, y):
        self.pos = Vector2(x, y)
        self.speed = 5
        self.size = 20
        self.health = 100
        self.experience = 0
        self.level = 1
        self.projectiles = []
        self.initialize_projectiles()

    def initialize_projectiles(self):
        self.projectiles.clear()
        num_projectiles = min(8, self.level + 2)
        angle_between = 360 / num_projectiles
        
        for i in range(num_projectiles):
            self.projectiles.append(Projectile(self, i * angle_between))

    def move(self, keys):
        if keys[pygame.K_w]:
            self.pos.y -= self.speed
        if keys[pygame.K_s]:
            self.pos.y += self.speed
        if keys[pygame.K_a]:
            self.pos.x -= self.speed
        if keys[pygame.K_d]:
            self.pos.x += self.speed

        # Limita o jogador aos limites do mapa
        self.pos.x = max(self.size, min(self.pos.x, MAP_WIDTH - self.size))
        self.pos.y = max(self.size, min(self.pos.y, MAP_HEIGHT - self.size))

    def update(self):
        for projectile in self.projectiles:
            projectile.update()

    def draw(self, screen, camera):
        screen_pos = camera.apply(self)
        pygame.draw.circle(screen, BLUE, (int(screen_pos.x), int(screen_pos.y)), self.size)
        
        for projectile in self.projectiles:
            projectile.draw(screen, camera)
            
        # HUD (não afetado pela câmera)
        pygame.draw.rect(screen, RED, (10, 10, self.health * 2, 20))
        font = pygame.font.Font(None, 36)
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        xp_text = font.render(f"XP: {self.experience}", True, WHITE)
        screen.blit(level_text, (10, 40))
        screen.blit(xp_text, (10, 70))

class Enemy:
    def __init__(self, x, y):
        self.pos = Vector2(x, y)
        self.speed = 2
        self.size = 15
        self.health = 30
        self.is_active = True

    def move_towards_player(self, player_pos):
        direction = player_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed

    def draw(self, screen, camera):
        screen_pos = camera.apply(self)
        pygame.draw.circle(screen, RED, (int(screen_pos.x), int(screen_pos.y)), self.size)

class Game:
    def __init__(self):
        self.player = Player(MAP_WIDTH//2, MAP_HEIGHT//2)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.enemies = []
        self.spawn_timer = 0
        self.spawn_delay = 60
        self.game_over = False
        self.clock = pygame.time.Clock()
        self.wave = 1
        self.enemies_killed = 0
        
        # Gera elementos do mapa
        self.generate_map_elements()

    def generate_map_elements(self):
        self.trees = []
        self.rocks = []
        
        # Gera árvores aleatórias
        for _ in range(100):
            x = random.randint(0, MAP_WIDTH)
            y = random.randint(0, MAP_HEIGHT)
            self.trees.append(Vector2(x, y))
            
        # Gera rochas aleatórias
        for _ in range(50):
            x = random.randint(0, MAP_WIDTH)
            y = random.randint(0, MAP_HEIGHT)
            self.rocks.append(Vector2(x, y))

    def spawn_enemy(self):
        # Spawn inimigos em uma distância específica do jogador
        spawn_distance = 400
        angle = random.uniform(0, 2 * math.pi)
        
        x = self.player.pos.x + math.cos(angle) * spawn_distance
        y = self.player.pos.y + math.sin(angle) * spawn_distance
        
        # Mantém os inimigos dentro dos limites do mapa
        x = max(0, min(x, MAP_WIDTH))
        y = max(0, min(y, MAP_HEIGHT))
        
        self.enemies.append(Enemy(x, y))

    def check_collisions(self):
        for projectile in self.player.projectiles:
            for enemy in self.enemies[:]:
                if (Vector2(projectile.pos) - Vector2(enemy.pos)).length() < enemy.size + projectile.size:
                    enemy.health -= projectile.damage
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.player.experience += 10
                        self.enemies_killed += 1
                        
                        if self.player.experience >= self.player.level * 100:
                            self.player.level += 1
                            self.player.health = min(100, self.player.health + 20)
                            self.player.initialize_projectiles()

        for enemy in self.enemies:
            if (Vector2(self.player.pos) - Vector2(enemy.pos)).length() < self.player.size + enemy.size:
                self.player.health -= 1
                if self.player.health <= 0:
                    self.game_over = True

    def draw_map(self, screen, camera):
        # Desenha o fundo
        screen.fill(GREEN)
        
        # Desenha elementos do mapa
        for tree in self.trees:
            screen_pos = camera.apply(type('Obj', (), {'pos': tree})())
            if 0 <= screen_pos.x <= SCREEN_WIDTH and 0 <= screen_pos.y <= SCREEN_HEIGHT:
                pygame.draw.circle(screen, (0, 150, 0), (int(screen_pos.x), int(screen_pos.y)), 10)
        
        for rock in self.rocks:
            screen_pos = camera.apply(type('Obj', (), {'pos': rock})())
            if 0 <= screen_pos.x <= SCREEN_WIDTH and 0 <= screen_pos.y <= SCREEN_HEIGHT:
                pygame.draw.circle(screen, (100, 100, 100), (int(screen_pos.x), int(screen_pos.y)), 8)

        # Desenha grade do mapa (opcional, para referência)
        grid_size = 200
        for x in range(0, MAP_WIDTH, grid_size):
            start_pos = camera.apply(type('Obj', (), {'pos': Vector2(x, 0)})())
            end_pos = camera.apply(type('Obj', (), {'pos': Vector2(x, MAP_HEIGHT)})())
            pygame.draw.line(screen, (50, 50, 50), (int(start_pos.x), int(start_pos.y)), 
                           (int(end_pos.x), int(end_pos.y)))
        
        for y in range(0, MAP_HEIGHT, grid_size):
            start_pos = camera.apply(type('Obj', (), {'pos': Vector2(0, y)})())
            end_pos = camera.apply(type('Obj', (), {'pos': Vector2(MAP_WIDTH, y)})())
            pygame.draw.line(screen, (50, 50, 50), (int(start_pos.x), int(start_pos.y)), 
                           (int(end_pos.x), int(end_pos.y)))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and self.game_over:
                    if event.key == pygame.K_r:
                        self.__init__()

            if not self.game_over:
                keys = pygame.key.get_pressed()
                self.player.move(keys)
                self.player.update()
                self.camera.update(self.player)
                
                self.spawn_timer += 1
                if self.spawn_timer >= self.spawn_delay:
                    self.spawn_enemy()
                    self.spawn_timer = 0
                    self.spawn_delay = max(20, self.spawn_delay - 1)

                for enemy in self.enemies:
                    enemy.move_towards_player(self.player.pos)

                self.check_collisions()

                if self.enemies_killed >= self.wave * 10:
                    self.wave += 1
                    self.spawn_delay = max(15, self.spawn_delay - 5)

            # Renderização
            self.draw_map(screen, self.camera)
            
            for enemy in self.enemies:
                enemy.draw(screen, self.camera)
            
            self.player.draw(screen, self.camera)

            if not self.game_over:
                font = pygame.font.Font(None, 36)
                wave_text = font.render(f"Wave: {self.wave}", True, WHITE)
                screen.blit(wave_text, (SCREEN_WIDTH - 120, 10))

                # Adiciona minimapa
                minimap_size = 150
                minimap_surface = pygame.Surface((minimap_size, minimap_size))
                minimap_surface.fill((0, 50, 0))
                
                # Desenha jogador no minimapa
                player_mini_x = (self.player.pos.x / MAP_WIDTH) * minimap_size
                player_mini_y = (self.player.pos.y / MAP_HEIGHT) * minimap_size
                pygame.draw.circle(minimap_surface, BLUE, (int(player_mini_x), int(player_mini_y)), 3)
                
                # Desenha inimigos no minimapa
                for enemy in self.enemies:
                    enemy_mini_x = (enemy.pos.x / MAP_WIDTH) * minimap_size
                    enemy_mini_y = (enemy.pos.y / MAP_HEIGHT) * minimap_size
                    pygame.draw.circle(minimap_surface, RED, (int(enemy_mini_x), int(enemy_mini_y)), 2)
                
                screen.blit(minimap_surface, (SCREEN_WIDTH - minimap_size - 10, SCREEN_HEIGHT - minimap_size - 10))

            if self.game_over:
                font = pygame.font.Font(None, 74)
                text = font.render('Game Over - Press R to Restart', True, WHITE)
                screen.blit(text, (SCREEN_WIDTH//2 - 300, SCREEN_HEIGHT//2))

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
