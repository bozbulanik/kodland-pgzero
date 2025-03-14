import pgzrun
import math
import random

WIDTH = 600
HEIGHT = 800

class GameStage:
    MENU = 0
    PLAY = 1
    GAME_OVER = 2

class GameState:
    stage = GameStage.MENU
    player_bullets = []
    enemy_bullets = []
    asteroids = []
    enemies = []
    explosions = []
    pickups = []
    score = 0
    player = None

class Button:
    def __init__(self, text, center, action):
        self.text = text
        self.rect = Rect(center[0] - 100, center[1] - 25, 200, 50)
        self.action = action

    def draw(self):
        screen.draw.filled_rect(self.rect, "blue")
        screen.draw.text(self.text, center=self.rect.center, fontsize=30, color="white")

    def on_click(self, pos):
        if self.rect.collidepoint(pos):
            if not game.muted:
                sounds.menu_select.play()
            self.action()

class HealthBar:
    def __init__(self, owner, position, bar_type="health"):
        self.owner = owner 
        self.position = position
        self.bar_type = bar_type
        self.width = 200
        self.height = 20
        self.border = 2

        self.colors = {
            "health": {
                "bg": (60, 60, 60),
                "fill": (220, 50, 50),
                "border": (180, 180, 180),
                "slider": (255, 80, 80)
            },
            "shield": {
                "bg": (60, 60, 60),
                "fill": (50, 120, 220),
                "border": (180, 180, 180),
                "slider": (80, 150, 255)
            }
        }
    
    def draw(self):
        if self.bar_type == "health":
            current_value = self.owner.health
            max_value = self.owner.max_health
        else:
            current_value = self.owner.shield
            max_value = self.owner.max_shield

        percentage = max(0, min(1, current_value / max_value))
        fill_width = int((self.width - 2 * self.border) * percentage)

        colors = self.colors[self.bar_type]

        x = self.position[0] - self.width // 2
        y = self.position[1] - self.height // 2


        screen.draw.filled_rect(Rect(x, y, self.width, self.height), colors["bg"])
        screen.draw.filled_rect(Rect(x + self.border, y + self.border, fill_width, self.height - 2 * self.border), colors["fill"])
        
        text = f"{'Can' if self.bar_type == 'health' else 'Kalkan'}: {int(current_value)}/{max_value}"

        screen.draw.text(text, center=(x + self.width // 2, y + self.height // 2), fontsize=24, color="white")

class Bullet(Actor):
    def __init__(self, sprite_name="bullet_small", bullet_speed = 10, **kwargs):
        super(Bullet, self).__init__(sprite_name, **kwargs)
        self.speed = bullet_speed

    def move(self, dx, dy):
        self.x += dx * self.speed
        self.y += dy * self.speed

class Explosion(Actor):
    def __init__(self, sprite_name="explosion00", **kwargs):
        super(Explosion, self).__init__(sprite_name, **kwargs)
        self.frame = 0
        self.animation_speed = 0.1
        self.life = 15

    def animate_sprite(self):
        self.frame += self.animation_speed
        if self.frame >= 9:
            self.frame = 0
        self.image = f'explosion0{int(self.frame)}'

class HealthPickup(Actor):
    def __init__(self, **kwargs):
        super(HealthPickup, self).__init__("health_pickup", **kwargs)
        self.speed = 2
        self.heal_amount = 20
        
    def move(self):
        self.y += self.speed
        
    def apply(self, player):
        player.heal(self.heal_amount)
        if not game.muted:
            sounds.pickup.play()

class ShieldPickup(Actor):
    def __init__(self, **kwargs):
        super(ShieldPickup, self).__init__("shield_pickup", **kwargs)
        self.speed = 2
        self.shield_amount = 15
        
    def move(self):
        self.y += self.speed
        
    def apply(self, player):
        player.recharge_shield(self.shield_amount)
        if not game.muted:
            sounds.pickup.play()

class Asteroid(Actor):
    def __init__(self, sprite_name="meteorbrown_big1", **kwargs):
        super(Asteroid, self).__init__(sprite_name, **kwargs)
        self.speed = 3
        self.health = 15
    
    def move(self):
        self.y += self.speed

class Player(Actor):
    def __init__(self, **kwargs):
        super(Player, self).__init__("player_idle1", **kwargs)
        self.frame = 1
        self.animation_speed = 0.1

        self.speed = 5
        self.max_health = 150
        self.health = 150
        self.shield = 100
        self.max_shield = 100
        self.health_bar = HealthBar(self, (125, 40), "health")
        self.shield_bar = HealthBar(self, (125, 70), "shield")

    def update(self):
        self.frame += self.animation_speed
        if self.frame >= 7:
            self.frame = 1
        self.image = f'player_idle{int(self.frame)}'

    def move(self, dx, dy):
        if dx != 0 and dy != 0:
            length = math.sqrt(dx**2 + dy**2)
            dx /= length
            dy /= length

        self.x += dx * self.speed
        self.y += dy * self.speed

        self.x = max((self.width // 2), min(WIDTH - (self.width // 2), self.x))
        self.y = max((self.height // 2), min(HEIGHT - (self.height // 2), self.y))

    def take_damage(self, amount):
        if self.shield > 0:
            if self.shield >= amount:
                self.shield -= amount
                amount = 0
            else:
                amount -= self.shield
                self.shield = 0
        
        if amount > 0:
            self.health -= amount
            
        if self.health <= 0:
            self.health = 0
            self.die()
            
    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)
        
    def recharge_shield(self, amount):
        self.shield = min(self.shield + amount, self.max_shield)

    def die(self):
        game.can_player_move = False
        explosion = Explosion(pos=(self.pos))
        explosion.fps = 5
        game.game_state.explosions.append(explosion)


        clock.unschedule(game.shoot)
        clock.unschedule(game.create_enemies)
        clock.unschedule(game.create_health_pickup)
        clock.unschedule(game.create_asteroids)

        clock.schedule_unique(self.transition_to_game_over, 1.0)
    
    def transition_to_game_over(self):
        if not game.muted:
            sounds.lose.play()
        game.game_state.stage = GameStage.GAME_OVER

class EnemyShip(Actor):
    def __init__(self, **kwargs):
        super(EnemyShip, self).__init__("enemy_idle1", **kwargs)
        self.frame = 1
        self.animation_speed = 0.1
        self.speed = 3
        self.bullet_timer = 0
        self.horizontal_timer = 0
        self.horizontal_direction = random.choice([-1, 1])


    def update(self):
        self.frame += self.animation_speed
        if self.frame >= 7:
            self.frame = 1
        self.image = f'enemy_idle{int(self.frame)}'

    def move(self):
        self.horizontal_timer += 1
        if self.horizontal_timer > random.randint(20, 50):
            self.horizontal_direction = random.choice([-1, 1])
            self.horizontal_timer = 0
        
        self.x += self.horizontal_direction * (game.difficulty_level - 1)
        self.y += 1 * self.speed

        self.x = max((self.width // 2), min(WIDTH - (self.width // 2), self.x))

    def shoot(self):
        if not len(game.game_state.enemy_bullets) > 30:
            if self.bullet_timer >= random.randint(100, 300):
                enemy_bullet = Bullet(sprite_name = "enemy_bullet_small", bullet_speed=20 + game.difficulty_level, pos=(self.x, self.y + self.height))
                game.game_state.enemy_bullets.append(enemy_bullet)
                if not game.muted:
                    sounds.sfx_laser1.set_volume(0.1)
                    sounds.sfx_laser1.play(1)
                self.bullet_timer = 0
            self.bullet_timer += 1

    def die(self):
        game.game_state.enemies.remove(self)

class Game:
    def __init__(self):
        self.game_state = GameState()
        self.game_state.player = Player(pos=(WIDTH // 2, HEIGHT - 100))
        self.difficulty_level = 1
        self.muted = False
        self.mute_button = Button(
            "Ses: Açık", (WIDTH // 2, HEIGHT//2 + 100), self.mute_sound
        )
        music.play("soundtrack.wav")

        self.start_button = Button(
            "Başla", (WIDTH // 2, HEIGHT // 2), self.setup_new_game
        )
        self.restart_button = Button(
            "Yeniden", (WIDTH // 2, HEIGHT // 2), self.setup_new_game
        )
        self.exit_button = Button(
            "Çıkış", (WIDTH//2, HEIGHT//2 + 200), self.exit
        )
        clock.schedule_interval(self.shoot, 0.2)
        clock.schedule_interval(self.create_enemies, 0.2)
        clock.schedule_interval(self.create_health_pickup, 0.2)
        clock.schedule_interval(self.create_asteroids, 0.2)
        self.can_player_move = True

        self.background = Actor("background_tiled2", (WIDTH // 2, HEIGHT//2))
        self.background2 = Actor("background_tiled2", (WIDTH // 2, -HEIGHT//2))
        self.scroll_speed = 1

        

    def mute_sound(self):
        self.muted = not self.muted
        self.mute_button.text = "Ses: Açık" if not self.muted else "Ses: Kapalı"
        if self.muted:
            music.stop()
        else:
            music.play("soundtrack.wav")

    def exit(self):
        sys.exit()

    def update_difficulty(self):
        new_level = 1 + int(self.game_state.score / 1000)
        if new_level > self.difficulty_level:
            self.difficulty_level = new_level

    def setup_new_game(self):
        self.game_state = GameState()
        self.game_state.player_bullets = []
        self.game_state.enemy_bullets = []
        self.game_state.asteroids = []
        self.game_state.enemies = []
        self.game_state.explosions = []
        self.game_state.pickups = []
        self.game_state.score = 0
        self.game_state.player = Player(pos=(WIDTH // 2, HEIGHT - 100))
        self.game_state.stage = GameStage.PLAY
        clock.schedule_interval(self.shoot, 0.2)
        clock.schedule_interval(self.create_enemies, 0.2)
        clock.schedule_interval(self.create_health_pickup, 0.2)
        clock.schedule_interval(self.create_asteroids, 0.2)
        self.difficulty_level = 1
        self.can_player_move = True

    def create_enemies(self):
        if self.game_state.stage != GameStage.PLAY:
            return
        if random.random() > (0.9 - 0.05 * self.difficulty_level):
            for _ in range(random.randint(1, 3 + self.difficulty_level // 2)):
                x_pos = random.randint(104, WIDTH - 104)
                new_enemy = EnemyShip(pos=(x_pos, -100))
                new_enemy.speed = 3 + 0.5 * self.difficulty_level
                self.game_state.enemies.append(new_enemy)

    def create_health_pickup(self):
        if random.random() > 0.95:
            if random.random() > 0.5:
                x_pos = random.randint(50, WIDTH - 50)
                pickup = HealthPickup(pos=(x_pos, -50))
                self.game_state.pickups.append(pickup)
            else:
                x_pos = random.randint(50, WIDTH - 50)
                pickup = ShieldPickup(pos=(x_pos, -50))
                self.game_state.pickups.append(pickup)

    def create_asteroids(self):
        if random.random() > (0.8 - 0.03 * self.difficulty_level):
            x_pos = random.randint(50, WIDTH - 50)
            asteroid_names = ["meteorbrown_big1","meteorbrown_big2","meteorbrown_big3","meteorbrown_big4", "meteorbrown_big5"]
            asteroid = Asteroid(sprite_name=random.choice(asteroid_names), pos=(x_pos, -50))
            asteroid.speed = 1 + 0.3 * self.difficulty_level
            self.game_state.asteroids.append(asteroid)

    def shoot(self):
        if self.game_state.stage != GameStage.PLAY:
            return
        if not len(self.game_state.player_bullets) > 15:
            bullet = Bullet(sprite_name = "bullet_small", bullet_speed=15 + self.difficulty_level,
                pos=(self.game_state.player.x, self.game_state.player.y - self.game_state.player.height)
            )
            if not self.muted:
                sounds.sfx_laser1.set_volume(0.1)
                sounds.sfx_laser1.play(1)
            self.game_state.player_bullets.append(bullet)

    def on_key_down(self, key):
        if self.game_state.stage == GameStage.MENU:
            if key == keys.SPACE:
                self.game_state.stage = GameStage.PLAY
                self.setup_new_game()
        
        if self.game_state.stage == GameStage.PLAY:
            if key == keys.ESCAPE:
                self.game_state.stage = GameStage.MENU

    def update(self, dt):
        if self.game_state.stage == GameStage.PLAY:
            self.background.y += self.scroll_speed
            self.background2.y += self.scroll_speed

            if self.background.y == HEIGHT * 1.5:
                self.background.y = -HEIGHT // 2
            if self.background2.y == HEIGHT * 1.5:
                self.background2.y = -HEIGHT // 2
            
            self.update_difficulty()
            self.handle_collisions()

            for enemy in self.game_state.enemies:
                enemy.move()
                enemy.shoot()
                enemy.update()

            for asteroid in self.game_state.asteroids:
                asteroid.move()

            for explosion in self.game_state.explosions:
                explosion.animate_sprite()
                explosion.life -= 1
                if explosion.life == 0:
                    self.game_state.explosions.remove(explosion)

            for bullet_element in self.game_state.enemy_bullets:
                bullet_element.move(0, 1)

            for bullet_element in self.game_state.player_bullets:
                bullet_element.move(0, -1)
            
            
            for pickup in self.game_state.pickups:
                pickup.move()
                if pickup.colliderect(self.game_state.player):
                    pickup.apply(self.game_state.player)
                    self.game_state.pickups.remove(pickup)

            self.game_state.player_bullets = [b for b in self.game_state.player_bullets if b.y > 0]
            self.game_state.enemy_bullets = [b for b in self.game_state.enemy_bullets if b.y < HEIGHT]
            self.game_state.enemies = [b for b in self.game_state.enemies if b.y < HEIGHT]
            self.game_state.pickups = [p for p in self.game_state.pickups if p.y < HEIGHT]
            self.game_state.asteroids = [p for p in self.game_state.asteroids if p.y < HEIGHT]

            self.game_state.player.update()

            if self.can_player_move:
                if keyboard.UP or keyboard.w:
                    self.game_state.player.move(0, -1)
                
                if keyboard.DOWN or keyboard.s:
                    self.game_state.player.move(0, 1)
                
                if keyboard.LEFT or keyboard.a:
                    self.game_state.player.move(-1, 0)
                
                if keyboard.RIGHT or keyboard.d:
                    self.game_state.player.move(1, 0)

    def handle_collisions(self):
        for bullet in self.game_state.player_bullets:
            for enemy in self.game_state.enemies:
                if bullet.colliderect(enemy):
                    explosion = Explosion(pos=(enemy.pos))
                    if not self.muted:
                        sounds.explosion_spaceship.play()
                    self.game_state.explosions.append(explosion)
                    self.game_state.player_bullets.remove(bullet)
                    self.game_state.enemies.remove(enemy)
                    self.game_state.score += 10
                    break
        
        for bullet in self.game_state.player_bullets:
            for asteroid in self.game_state.asteroids:
                if bullet.colliderect(asteroid):
                    explosion = Explosion(pos=(asteroid.pos))
                    if not self.muted:
                        sounds.explosion_spaceship.play()
                    self.game_state.explosions.append(explosion)
                    self.game_state.player_bullets.remove(bullet)
                    self.game_state.asteroids.remove(asteroid)
                    self.game_state.score += 5
                    break

        for bullet in self.game_state.enemy_bullets:
            player = self.game_state.player
            if bullet.colliderect(player):
                if not self.muted:
                    sounds.player_hit.play()
                self.game_state.enemy_bullets.remove(bullet)
                self.game_state.player.take_damage(10)
        
        for asteroid in self.game_state.asteroids:
            player = self.game_state.player
            if asteroid.colliderect(player):
                explosion = Explosion(pos=(player.pos))
                if not self.muted:
                    sounds.explosion_spaceship.play()
                self.game_state.explosions.append(explosion)
                self.game_state.asteroids.remove(asteroid)
                self.game_state.player.take_damage(50)

    def draw(self):
        screen.clear()
        self.background.draw()
        self.background2.draw()

        if self.game_state.stage == GameStage.MENU:
            screen.draw.text(
                "Kodland Uzay Macerası", center=(WIDTH // 2, 100), fontsize=50, color="white"
            )
            self.start_button.draw()
            self.mute_button.draw()
            self.exit_button.draw()

        elif self.game_state.stage == GameStage.PLAY:
            self.game_state.player.draw()

            for enemy in self.game_state.enemies:
                enemy.draw()

            for asteroid in self.game_state.asteroids:
                asteroid.draw()

            for bullet in self.game_state.player_bullets:
                bullet.draw()
            
            for bullet in self.game_state.enemy_bullets:
                bullet.draw()

            for explosion in self.game_state.explosions:
                explosion.draw()
            
            for pickup in self.game_state.pickups:
                pickup.draw()

            self.game_state.player.health_bar.draw()
            self.game_state.player.shield_bar.draw()

            screen.draw.text(str(self.game_state.score), center=(WIDTH // 2, 50), fontsize=50, color="white")

        elif self.game_state.stage == GameStage.GAME_OVER:
            screen.draw.text(
                "KAYBETTİN", center=(WIDTH // 2, 100), fontsize=50, color="red"
            )
            screen.draw.text(
                f"Skorun: {self.game_state.score}", center=(WIDTH // 2, 200), fontsize=36, color="white"
            )
            self.restart_button.draw()

game = Game()


def draw():
    game.draw()

def on_key_down(key):
    game.on_key_down(key)

def update(dt):
    game.update(dt)

def on_mouse_down(pos):
    if game.game_state.stage == GameStage.MENU:
        game.start_button.on_click(pos)
        game.mute_button.on_click(pos)
        game.exit_button.on_click(pos)

    elif game.game_state.stage == GameStage.GAME_OVER:
        game.restart_button.on_click(pos)

pgzrun.go()
