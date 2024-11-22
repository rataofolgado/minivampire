import pygame
import random
import math
from pygame.math import Vector2

# Inicialização do Pygame
pygame.init()

# Configurações da tela
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mini Vampire Survivors")

# Configurações do mapa
MAP_WIDTH = 3400
MAP_HEIGHT = 2800

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 100, 0)
YELLOW = (255, 255, 0)

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
        self.initialize_projectiles()  # Chama o método para inicializar os projéteis
        self.gold = 0
        self.dash_cooldown = 0
        self.dash_duration = 0
        self.has_dash = False
        self.bombs = 0
        self.potions = 0
        self.dash_speed = 15

    def update(self):
        # Adicione aqui as atualizações que deseja no jogador (ex: cooldowns, status)
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.dash_duration > 0:
            self.dash_duration -= 1

    def initialize_projectiles(self):
        # Crie projéteis ao redor do jogador em diferentes ângulos
        angles = [0, 120, 240]  # Ângulos para os projéteis
        self.projectiles = [Projectile(self, angle) for angle in angles]
        

    def use_dash(self, keys):
        if not self.has_dash or self.dash_cooldown > 0:
            return

        if keys[pygame.K_SPACE]:
            self.dash_duration = 10
            self.dash_cooldown = 120  # 2 segundos de cooldown

    def use_potion(self):
        if self.potions > 0 and self.health < 100:
            self.health = min(100, self.health + 30)
            self.potions -= 1

    def use_bomb(self):
        if self.bombs > 0:
            self.bombs -= 1
            return True
        return False

    def move(self, keys):
        # Atualiza cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.dash_duration > 0:
            self.dash_duration -= 1
            current_speed = self.dash_speed
        else:
            current_speed = self.speed

        # Movimento normal ou dash
        direction = Vector2(0, 0)
        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_d]:
            direction.x += 1

        if direction.length() > 0:
            direction = direction.normalize()
            self.pos += direction * current_speed

        # Limita o jogador aos limites do mapa
        self.pos.x = max(self.size, min(self.pos.x, MAP_WIDTH - self.size))
        self.pos.y = max(self.size, min(self.pos.y, MAP_HEIGHT - self.size))

        # Usa dash se disponível
        self.use_dash(keys)

    def draw(self, screen, camera):
        screen_pos = camera.apply(self)
        # Desenha o jogador com uma cor diferente durante o dash
        color = (0, 255, 255) if self.dash_duration > 0 else BLUE
        pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), self.size)
        
        for projectile in self.projectiles:
            projectile.draw(screen, camera)
            
        # HUD atualizado
        pygame.draw.rect(screen, RED, (10, 10, self.health * 2, 20))
        font = pygame.font.Font(None, 36)
        level_text = font.render(f"Level: {self.level}", True, WHITE)
        xp_text = font.render(f"XP: {self.experience}", True, WHITE)
        gold_text = font.render(f"Gold: {self.gold}", True, YELLOW)
        items_text = font.render(f"Potions: {self.potions} Bombs: {self.bombs}", True, WHITE)
        
        screen.blit(level_text, (10, 40))
        screen.blit(xp_text, (10, 70))
        screen.blit(gold_text, (10, 100))
        screen.blit(items_text, (10, 130))

        # Indicador de cooldown do dash
        if self.has_dash:
            cooldown_width = (120 - self.dash_cooldown) * 100 // 120
            pygame.draw.rect(screen, (100, 100, 100), (10, 160, 100, 10))
            pygame.draw.rect(screen, (0, 255, 255), (10, 160, cooldown_width, 10))

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

class Shop:
    def __init__(self):
        self.items = {
            'dash': {'price': 100, 'description': 'Dash Ability'},
            'potion': {'price': 50, 'description': 'Health Potion'},
            'bomb': {'price': 75, 'description': 'Area Damage Bomb'}
        }
        self.is_open = False
        self.font = pygame.font.Font(None, 36)

    def toggle(self):
        self.is_open = not self.is_open

    def draw(self, screen, player):
        if not self.is_open:
            return

        # Desenha o fundo da loja
        shop_surface = pygame.Surface((400, 300))
        shop_surface.fill((50, 50, 50))
        
        # Títulos e items
        title = self.font.render("SHOP", True, WHITE)
        shop_surface.blit(title, (170, 10))
        
        y = 60
        for item, details in self.items.items():
            if item == 'dash' and player.has_dash:
                text = self.font.render(f"{details['description']}: SOLD OUT", True, (100, 100, 100))
            else:
                text = self.font.render(f"{details['description']}: {details['price']} gold", True, WHITE)
            shop_surface.blit(text, (20, y))
            y += 50

        instructions = self.font.render("Press 1-3 to buy, P to close", True, WHITE)
        shop_surface.blit(instructions, (20, 250))

        # Posiciona a loja no centro da tela
        screen.blit(shop_surface, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 150))

    def buy_item(self, player, item_key):
        if not self.is_open:
            return False

        item = self.items.get(item_key)
        if not item:
            return False

        if player.gold < item['price']:
            return False

        if item_key == 'dash' and player.has_dash:
            return False

        player.gold -= item['price']

        if item_key == 'dash':
            player.has_dash = True
        elif item_key == 'potion':
            player.potions += 1
        elif item_key == 'bomb':
            player.bombs += 1

        return True

class Game:
    def __init__(self):
        self.player = Player(MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.enemies = []
        self.spawn_timer = 0
        self.spawn_delay = 60
        self.game_over = False
        self.clock = pygame.time.Clock()
        self.wave = 1
        self.enemies_killed = 0
        self.shop = Shop()  # Nova instância da loja
        self.explosions = []  # Lista para controlar explosões das bombas
        self.generate_map_elements()

    # Função para gerar inimigos
    def spawn_enemy(self):
        # Para gerar um inimigo em uma posição aleatória no mapa
        x = random.randint(0, MAP_WIDTH)
        y = random.randint(0, MAP_HEIGHT)
        enemy = Enemy(x, y)  # Supondo que você tenha uma classe Enemy já definida
        self.enemies.append(enemy)


    def draw_map(self, screen, camera):
        # Aqui você pode desenhar o fundo do mapa ou qualquer coisa do cenário
        screen.fill(GREEN) 

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


    def handle_bomb_explosion(self, pos):
        explosion_radius = 100
        # Marca inimigos para remoção se estiverem no raio da explosão
        enemies_to_remove = []
        for enemy in self.enemies:
            if (Vector2(enemy.pos) - Vector2(pos)).length() < explosion_radius:
                enemies_to_remove.append(enemy)
                self.player.experience += 10
                self.player.gold += random.randint(5, 15)
                self.enemies_killed += 1

        # Remove os inimigos atingidos
        for enemy in enemies_to_remove:
            if enemy in self.enemies:
                self.enemies.remove(enemy)

        # Adiciona explosão visual
        self.explosions.append({'pos': pos, 'radius': explosion_radius, 'duration': 30})

    def run(self):
        running = True
        while running:
            for projectile in self.player.projectiles:
                projectile.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.game_over and event.key == pygame.K_r:
                        self.__init__()
                    elif event.key == pygame.K_p:  # Tecla P para abrir/fechar a loja
                        self.shop.toggle()
                    elif event.key == pygame.K_h and self.player.potions > 0:  # Tecla H para usar poção
                        self.player.use_potion()
                    elif event.key == pygame.K_b and self.player.bombs > 0:  # Tecla B para usar bomba
                        if self.player.use_bomb():
                            self.handle_bomb_explosion(self.player.pos)
                    
                    # Comprar itens (quando a loja está aberta)
                    if self.shop.is_open:
                        if event.key == pygame.K_1:
                            self.shop.buy_item(self.player, 'dash')
                        elif event.key == pygame.K_2:
                            self.shop.buy_item(self.player, 'potion')
                        elif event.key == pygame.K_3:
                            self.shop.buy_item(self.player, 'bomb')

            if not self.game_over and not self.shop.is_open:
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

                # Atualiza explosões
                self.explosions = [exp for exp in self.explosions if exp['duration'] > 0]
                for explosion in self.explosions:
                    explosion['duration'] -= 1

                if self.enemies_killed >= self.wave * 10:
                    self.wave += 1
                    self.spawn_delay = max(15, self.spawn_delay - 5)

            # Renderização
            self.draw_map(screen, self.camera)
            
            # Desenha explosões
            for explosion in self.explosions:
                screen_pos = self.camera.apply(type('Obj', (), {'pos': explosion['pos']})())
                alpha = int(255 * (explosion['duration'] / 30))
                explosion_surface = pygame.Surface((explosion['radius']*2, explosion['radius']*2), pygame.SRCALPHA)
                pygame.draw.circle(explosion_surface, (255, 165, 0, alpha), 
                                (explosion['radius'], explosion['radius']), explosion['radius'])
                screen.blit(explosion_surface, 
                          (int(screen_pos.x - explosion['radius']), 
                           int(screen_pos.y - explosion['radius'])))

            for enemy in self.enemies:
                enemy.draw(screen, self.camera)
            
            self.player.draw(screen, self.camera)

            # Interface da loja
            self.shop.draw(screen, self.player)

            if not self.game_over:
                font = pygame.font.Font(None, 36)
                wave_text = font.render(f"Wave: {self.wave}", True, WHITE)
                screen.blit(wave_text, (SCREEN_WIDTH - 120, 10))

                controls_text = font.render("P: Shop | H: Use Potion | B: Use Bomb | SPACE: Dash", True, WHITE)
                screen.blit(controls_text, (SCREEN_WIDTH//2 - 250, 10))

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

    def check_collisions(self):
    # Verifica colisões entre os projéteis e os inimigos
        for projectile in self.player.projectiles:
            for enemy in self.enemies[:]:
                if (Vector2(projectile.pos) - Vector2(enemy.pos)).length() < enemy.size + projectile.size:
                    enemy.health -= projectile.damage
                if enemy.health <= 0:
                    self.enemies.remove(enemy)
                    self.player.experience += 10
                    self.player.gold += random.randint(5, 15)  # Ouro dropado
                    self.enemies_killed += 1
                
                # Verifica se o jogador ganha experiência para subir de nível
                if self.player.experience >= self.player.level * 100:
                    self.player.level += 1
                    self.player.health = min(100, self.player.health + 20)
                    self.player.initialize_projectiles()

        for enemy in self.enemies:
            if (Vector2(self.player.pos) - Vector2(enemy.pos)).length() < self.player.size + enemy.size:
                self.player.health -= 1
                if self.player.health <= 0:
                    self.game_over = True

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
