import pygame, sys, random, time, json, os
from pygame.locals import *

pygame.init()

# Configuration & Constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)
GRAY  = (100, 100, 100)

# Asset Cache
ASSETS = {}

def load_assets():
    # Images
    ASSETS["coin"] = pygame.transform.scale(pygame.image.load("assets/coin.png").convert_alpha(), (30, 30))
    ASSETS["big_coin"] = pygame.transform.scale(pygame.image.load("assets/coin.png").convert_alpha(), (50, 50))
    ASSETS["oil"] = pygame.transform.scale(pygame.image.load("assets/oil.png").convert_alpha(), (40, 40))
    ASSETS["nitro"] = pygame.transform.scale(pygame.image.load("assets/nitro.png").convert_alpha(), (55, 55))
    ASSETS["shield"] = pygame.transform.scale(pygame.image.load("assets/shield.png").convert_alpha(), (55, 55))
    ASSETS["enemy"] = pygame.image.load("assets/Enemy.png").convert_alpha()
    ASSETS["repair"] = pygame.transform.scale(pygame.image.load("assets/repair.png").convert_alpha(), (55, 55))
    
    # Load player colors
    ASSETS["player_Blue"] = pygame.image.load("assets/player_blue.png").convert_alpha()
    ASSETS["player_Red"] = pygame.image.load("assets/player_red.png").convert_alpha()
    ASSETS["player_Green"] = pygame.image.load("assets/player_green.png").convert_alpha()
    ASSETS["bg"] = pygame.image.load("assets/AnimatedStreet.png").convert()

# JSON helper functions 
def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

# Scene Base Class
class SceneBase:

    def __init__(self):
        self.next = self

    def ProcessInput(self, events, pressed_keys): pass
    def Update(self): pass
    def Render(self, screen): pass
    def SwitchToScene(self, next_scene): self.next = next_scene
    def Terminate(self): self.SwitchToScene(None)

# Game Sprites
class Player(pygame.sprite.Sprite):

    def __init__(self, image_path):
        super().__init__()
        # Load the specific colored asset provided by the user
        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect()
        self.rect.center = (160, 520)
        self.shielded = False

    def move(self):
        pressed_keys = pygame.key.get_pressed()
        speed = 7
        if self.rect.left > 0 and pressed_keys[K_LEFT]:
            self.rect.move_ip(-speed, 0)
        if self.rect.right < SCREEN_WIDTH and pressed_keys[K_RIGHT]:
            self.rect.move_ip(speed, 0)

class Enemy(pygame.sprite.Sprite):

    def __init__(self, speed):
        super().__init__()
        self.image = ASSETS["enemy"]
        self.rect = self.image.get_rect()
        self.reset()
        self.speed = speed

    def move(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.top > SCREEN_HEIGHT:
            self.reset()
            return True # Passed safely
        return False

    def reset(self):
        self.rect.center = (random.randint(40, SCREEN_WIDTH-40), -100)

class Collectible(pygame.sprite.Sprite):

    def __init__(self, surface, value=1, type="coin"):
        super().__init__()
        self.type = type
        self.value = value
        self.image = surface
        self.rect = self.image.get_rect()
        self.reset()

    def move(self, speed):
        self.rect.move_ip(0, speed)
        if self.rect.top > SCREEN_HEIGHT:
            if self.type == "coin":
                self.reset()
            else:
                self.kill()

    def reset(self):
        self.rect.center = (random.randint(40, SCREEN_WIDTH - 40), random.randint(-500, -50))

# Scenes 

class MenuScene(SceneBase):

    def __init__(self):
        super().__init__()
        self.font = pygame.font.SysFont("Verdana", 40)
        self.small_font = pygame.font.SysFont("Verdana", 20)

    def Render(self, screen):
        screen.fill(WHITE)
        title = self.font.render("RACER ARCADE", True, BLACK)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        opts = ["[P] Play", "[L] Leaderboard", "[S] Settings", "[Q] Quit"]
        for i, opt in enumerate(opts):
            txt = self.small_font.render(opt, True, BLUE)
            screen.blit(txt, (SCREEN_WIDTH//2 - 70, 250 + i*40))

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_p: self.SwitchToScene(EntryScene())
                if event.key == K_l: self.SwitchToScene(LeaderboardScene())
                if event.key == K_s: self.SwitchToScene(SettingsScene())
                if event.key == K_q: self.Terminate()

class EntryScene(SceneBase):

    def __init__(self):
        super().__init__()
        self.name = ""
        self.font = pygame.font.SysFont("Verdana", 20)

    def Render(self, screen):
        screen.fill(WHITE)
        txt = self.font.render(f"Enter Name: {self.name}", True, BLACK)
        screen.blit(txt, (50, SCREEN_HEIGHT//2))
        instr = self.font.render("Press ENTER to Start", True, GRAY)
        screen.blit(instr, (50, SCREEN_HEIGHT//2 + 40))

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_RETURN and self.name:
                    self.SwitchToScene(GameScene(self.name))
                elif event.key == K_BACKSPACE:
                    self.name = self.name[:-1]
                else:
                    if len(self.name) < 10 and event.unicode.isalnum():
                        self.name += event.unicode

class SettingsScene(SceneBase):

    def __init__(self):
        super().__init__()
        self.settings = load_json("settings.json", {"sound": True, "color": "Blue", "diff": 1})
        self.font = pygame.font.SysFont("Verdana", 20)

    def Render(self, screen):
        screen.fill(WHITE)
        lines = [
            f"[M] Sound: {'ON' if self.settings['sound'] else 'OFF'}",
            f"[C] Car Color: {self.settings['color']}",
            f"[D] Difficulty: {['Easy', 'Med', 'Hard'][self.settings['diff']-1]}",
            "[B] Back to Menu"
        ]
        for i, line in enumerate(lines):
            txt = self.font.render(line, True, BLACK)
            screen.blit(txt, (50, 100 + i*50))

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_m: self.settings['sound'] = not self.settings['sound']
                if event.key == K_c:
                    colors = {"Blue": "Red", "Red": "Green", "Green": "Blue"}
                    self.settings['color'] = colors[self.settings['color']]
                if event.key == K_d:
                    self.settings['diff'] = (self.settings['diff'] % 3) + 1
                if event.key == K_b:
                    save_json("settings.json", self.settings)
                    self.SwitchToScene(MenuScene())

class GameScene(SceneBase):

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.settings = load_json("settings.json", {"sound": True, "color": "Blue", "diff": 1})
        self.level = 0
        # Assets
        self.bg = ASSETS["bg"]
        self.ui_font = pygame.font.SysFont("Verdana", 18)
        self.coin_sound = pygame.mixer.Sound("assets/coin_pickup.wav")
        self.crash_sound = pygame.mixer.Sound("assets/crash.wav")
        self.oil_slowdown_timer = 0

        # Player Setup
        color_files = {
            "Blue": "assets/player_blue.png",
            "Red": "assets/player_red.png",
            "Green": "assets/player_green.png"
        }
        
        # Get the path based on settings, default to blue if not found
        img_path = color_files.get(self.settings['color'], "assets/player_blue.png")
        
        # Initialize player with the specific asset
        self.player = Player(img_path)
        
        # Groups
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.hazards = pygame.sprite.Group()
        
        # Initial State
        self.speed = 4 + self.settings['diff'] * 2
        self.score = 0
        self.coins_collected = 0
        self.distance = 0
        self.finish_line = 5000
        self.boost_timer = 0
        self.repair_timer = 0 
        
        # Spawn Initial Enemy and prepare second
        self.enemy = Enemy(self.speed)
        self.enemy2 = Enemy(self.speed)
        self.enemies.add(Enemy(self.speed))

        # Add 2 coins with random weights
        for _ in range(2):
            if random.random() < 0.4: # 40% chance for a big coin
                self.coins.add(Collectible(ASSETS["big_coin"], 3, "coin"))
            else:
                self.coins.add(Collectible(ASSETS["coin"], 1, "coin"))
    def fix_spawn(self, obj):
        for _ in range(10): 
            collision = False
        
            for e in self.enemies:
                if obj.rect.colliderect(e.rect):
                    collision = True
                    break
        
            if not collision:
                return  
        
            obj.reset() 

    def Update(self):
        if self.boost_timer > 0:
            self.boost_timer -= 1
            current_speed = self.speed * 2
        else:
            current_speed = self.speed

        
        if self.oil_slowdown_timer > 0:
            self.oil_slowdown_timer -= 1
            current_speed *= 0.5
        self.distance += current_speed / 10  

        new_level = int(self.distance // 300)

        if new_level > self.level:
            self.level = new_level
            self.speed += 0.5 
            
        # set speed for enemies
        for e in self.enemies:
                e.speed = current_speed * 1

        self.player.move()

        for e in self.enemies:
            if e.move(): self.score += 10 # Score for dodging
        
        for c in self.coins: c.move(current_speed)
        for p in self.powerups: p.move(current_speed)
        for h in self.hazards: h.move(current_speed)

        # Spawning Logic
        additional_hazard_chance = min(self.distance / 100000, 0.01)
        if random.random() < 0.001 + additional_hazard_chance: # Random Hazards
            oil = Collectible(ASSETS["oil"], 0, "oil")
            self.fix_spawn(oil)
            self.hazards.add(oil)
        # random power-ups if there is no active power-up or power-up on screen
        if len(self.powerups) == 0 and self.boost_timer <= 0 and not self.player.shielded and self.repair_timer <= 0:
            if random.random() < 0.05: 
                ptype = random.choice(["nitro", "shield", "repair"])
                p = Collectible(ASSETS[ptype], 0, ptype)
                self.fix_spawn(p)
                self.powerups.add(p)
        
        # if finished 40% of distance add logic for another car
        if self.distance > self.finish_line * 0.4:
            if len(self.enemies) < 2: # spawn it if has not
                self.enemies.add(self.enemy2)
            if abs(self.enemy.rect.top - self.enemy2.rect.top) < 100:
                self.enemy2.rect.top = self.enemy.rect.top + 200

        # Collisions
        if pygame.sprite.spritecollideany(self.player, self.enemies):
            if self.player.shielded:
                self.player.shielded = False
                for e in self.enemies: e.reset()
            else:
                self.handle_game_over()

        # Coin Pickup
        coin_hit = pygame.sprite.spritecollideany(self.player, self.coins)
        if coin_hit:
            if self.settings['sound']: self.coin_sound.play()
            self.coins_collected += coin_hit.value * 10
            self.speed += 0.05

            # Decide if the next coin should be big or small
            if random.random() < 0.4:
                coin_hit.image = ASSETS["big_coin"]
                coin_hit.value = 3
            else:
                coin_hit.image = ASSETS["coin"]
                coin_hit.value = 1

            coin_hit.reset()
            self.fix_spawn(coin_hit)

        # Powerup Pickup
        pu_hit = pygame.sprite.spritecollideany(self.player, self.powerups)
        if pu_hit:
            if pu_hit.type == "nitro": self.boost_timer = 180 
            if pu_hit.type == "shield": self.player.shielded = True
            if pu_hit.type == "repair": 
                self.repair_timer = 300 # 5 seconds at 60 FPS
            pu_hit.kill()

        # Oil Hazard
        hazard_hit = pygame.sprite.spritecollideany(self.player, self.hazards)
        if hazard_hit:
            self.oil_slowdown_timer = 120  # 2 seconds at 50 FPS
            hazard_hit.kill()

        # Countdown the repair timer
        if self.repair_timer > 0:
            self.repair_timer -= 1
            # While active, continuously clear enemies and hazards
            for e in self.enemies: e.reset()
            self.hazards.empty()

    def handle_game_over(self, win=False):
        if self.settings['sound']: self.crash_sound.play()
        final_score = int(self.score + self.distance/10 + win * 200 * self.settings["diff"])
        
        # Save Score
        lb = load_json("leaderboard.json", [])
        lb.append({"name": self.username, "score": final_score, "dist": int(self.distance)})
        lb = sorted(lb, key=lambda x: x['score'], reverse=True)[:10]
        save_json("leaderboard.json", lb)
        
        self.SwitchToScene(GameOverScene(final_score, int(self.distance), self.coins_collected, win))

    def Render(self, screen):
        screen.blit(self.bg, (0,0))
        screen.blit(self.player.image, self.player.rect)
        for g in [self.enemies, self.coins, self.powerups, self.hazards]:
            g.draw(screen)
        
        # UI
        screen.blit(self.ui_font.render(f"Score: {self.score}", True, BLACK), (10, 10))
        screen.blit(self.ui_font.render(f"Coins: {self.coins_collected}", True, BLACK), (10, 30))
        screen.blit(self.ui_font.render(f"Dist: {int(self.distance)}/{int(self.finish_line)}m", True, BLACK), (10, 50))
        
        if self.player.shielded:
            screen.blit(self.ui_font.render("SHIELD ACTIVE", True, BLUE), (250, 10))
        if self.boost_timer > 0:
            screen.blit(self.ui_font.render("NITRO!", True, RED), (250, 30))
        if self.repair_timer > 0:
            color = (0, 200, 0) if pygame.time.get_ticks() % 500 < 250 else WHITE
            screen.blit(self.ui_font.render("ROAD CLEAR!", True, color), (250, 50))

class GameOverScene(SceneBase):

    def __init__(self, score, dist, coins, win=False):
        super().__init__()
        self.stats = [f"Score: {score}", f"Distance: {dist}m", f"Coins: {coins}"]
        self.win = win
        self.font = pygame.font.SysFont("Verdana", 30)

    def Render(self, screen):
        if self.win:
            msg = self.font.render("YOU WIN", True, WHITE)
            screen.fill(GREEN)
        else:
            msg = self.font.render("GAME OVER", True, WHITE)
            screen.fill(RED)

        screen.blit(msg, (SCREEN_WIDTH//2 - msg.get_width()//2, 100))
        
        for i, stat in enumerate(self.stats):
            txt = pygame.font.SysFont("Verdana", 20).render(stat, True, WHITE)
            screen.blit(txt, (SCREEN_WIDTH//2 - 50, 200 + i*30))
            
        retry = pygame.font.SysFont("Verdana", 20).render("[R] Retry  [M] Menu", True, BLACK)
        screen.blit(retry, (SCREEN_WIDTH//2 - retry.get_width()//2, 400))

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_r: self.SwitchToScene(EntryScene())
                if event.key == K_m: self.SwitchToScene(MenuScene())

class LeaderboardScene(SceneBase):

    def __init__(self):
        super().__init__()
        self.data = load_json("leaderboard.json", [])
        self.font = pygame.font.SysFont("Verdana", 20)

    def Render(self, screen):
        screen.fill(WHITE)
        title = pygame.font.SysFont("Verdana", 30).render("Top 10 Scores", True, BLACK)
        screen.blit(title, (50, 30))
        
        for i, entry in enumerate(self.data):
            line = f"{i+1}. {entry['name']} - {entry['score']} pts"
            txt = self.font.render(line, True, BLACK)
            screen.blit(txt, (50, 80 + i*35))
            
        back = self.font.render("[B] Back", True, BLUE)
        screen.blit(back, (50, 500))

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == KEYDOWN and event.key == K_b:
                self.SwitchToScene(MenuScene())

# main loop 
def run_game(width, height, fps, starting_scene):

    
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    load_assets()
    active_scene = starting_scene
    
    while active_scene is not None:
        pressed_keys = pygame.key.get_pressed()
        filtered_events = []
        for event in pygame.event.get():
            if event.type == QUIT:
                active_scene.Terminate()
            else:
                filtered_events.append(event)
        
        active_scene.ProcessInput(filtered_events, pressed_keys)
        active_scene.Update()
        active_scene.Render(screen)
        active_scene = active_scene.next
        
        pygame.display.flip()
        clock.tick(fps)

if __name__ == "__main__":
    run_game(SCREEN_WIDTH, SCREEN_HEIGHT, FPS, MenuScene())