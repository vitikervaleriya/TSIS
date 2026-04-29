import pygame
import random
import json
import db  # Our helper module

pygame.init()

# Constants
WIDTH, HEIGHT = 600, 600
CELL = 30
FPS = 10
POWERUP_FIELD_TIME = 8000  # 8 seconds on field
EFFECT_DURATION = 5000    # 5 seconds effect duration

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_POISON = (139, 0, 0)
COLOR_GOLD = (255, 215, 0)

def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except:
        return {"snake_color": [0, 255, 0], "grid_on": True, "sound_on": True}

def save_settings(settings):
    with open("settings.json", "wb") as f:
        f.write(json.dumps(settings).encode("utf-8"))

class SceneBase:
    def __init__(self): self.next = self
    def ProcessInput(self, events, pressed_keys): pass
    def Update(self): pass
    def Render(self, screen): pass
    def SwitchToScene(self, next_scene): self.next = next_scene
    def Terminate(self): self.next = None

class MenuScene(SceneBase):
    def __init__(self):
        super().__init__()
        self.username = ""
        self.font = pygame.font.SysFont("Verdana", 20)

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(self.username) > 0:
                    self.SwitchToScene(GameScene(self.username))
                elif event.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.SwitchToScene(LeaderboardScene())
                elif event.key == pygame.K_F1:
                    self.SwitchToScene(SettingsScene())
                else:
                    if len(self.username) < 10 and event.unicode.isalnum():
                        self.username += event.unicode

    def Render(self, screen):
        screen.fill(COLOR_BLACK)
        txt = self.font.render(f"Enter Name: {self.username}", True, COLOR_WHITE)
        screen.blit(txt, (150, 150))
        hint1 = self.font.render("Press ENTER to Play", True, (150, 150, 150))
        screen.blit(hint1, (150, 300))
        hint2 = self.font.render("ESCAPE for Leaderboard", True, (150, 150, 150))
        screen.blit(hint2, (150, 350))
        hint3 = self.font.render("F1 for settings", True, (150, 150, 150))
        screen.blit(hint3, (150, 400))

class GameScene(SceneBase):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.snake = [pygame.Rect(300, 300, CELL, CELL)]
        self.dir = (CELL, 0)
        self.score = 0
        self.level = 1
        self.obstacles = []
        self.font = pygame.font.SysFont("Verdana", 20)
        self.food = self.spawn_item("normal")
        self.poison = self.spawn_item("poison")
        self.powerup = None
        self.speed = FPS
        self.actual_speed = FPS
        self.settings = load_settings()
        self.personal_best = db.get_personal_best(username) 
        
        # Power-up state tracking
        self.active_powerup_type = None
        self.powerup_expire_time = 0  
        self.effect_end_time = 0     
        self.shield_active = False    

        pygame.mixer.init()
        try:
            self.snd_food = pygame.mixer.Sound("assets/food_eaten.wav")
            self.snd_powerup = pygame.mixer.Sound("assets/powerup_eaten.wav")
            self.snd_gameover = pygame.mixer.Sound("assets/gameover.wav")
        except pygame.error as e:
            print(f"Could not load sounds: {e}")
            self.snd_food = self.snd_powerup = self.snd_gameover = None

    def spawn_powerup(self):
        # Only one power-up active on the field at a time
        if self.powerup is not None: return 
        
        types = ["speed", "slow", "shield"]
        self.powerup = self.spawn_item(random.choice(types))
        self.powerup_expire_time = pygame.time.get_ticks() + 8000 # 8 second life

    def spawn_item(self, type):
        while True:
            pos = pygame.Rect(random.randint(0, (WIDTH//CELL)-1)*CELL, 
                              random.randint(0, (HEIGHT//CELL)-1)*CELL, CELL, CELL)
            if pos.collidelist(self.snake) == -1 and pos.collidelist(self.obstacles) == -1:
                weight = 1
                if type == "normal":
                    weight = random.choices([1, 3], weights=[80, 20])[0]
                return {"pos": pos, "type": type, "weight": weight, "spawn_time": pygame.time.get_ticks()}

    def update_level(self):
        if self.score >= self.level * 5:
            self.level += 1
            self.speed += 2
            if self.level >= 3:
                for _ in range(3):
                    while True:
                        obs = pygame.Rect(random.randint(0, (WIDTH//CELL)-1)*CELL, 
                                         random.randint(0, (HEIGHT//CELL)-1)*CELL, CELL, CELL)
                        
                        # Check collision with snake, other obstacles, and existing items
                        collision_items = [self.food["pos"], self.poison["pos"]]
                        if self.powerup: collision_items.append(self.powerup["pos"])
                        
                        if (obs.collidelist(self.snake) == -1 and 
                            obs.collidelist(self.obstacles) == -1 and
                            obs.collidelist(collision_items) == -1):
                            self.obstacles.append(obs)
                            break

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.dir != (0, CELL): self.dir = (0, -CELL)
                if event.key == pygame.K_DOWN and self.dir != (0, -CELL): self.dir = (0, CELL)
                if event.key == pygame.K_LEFT and self.dir != (CELL, 0): self.dir = (-CELL, 0)
                if event.key == pygame.K_RIGHT and self.dir != (-CELL, 0): self.dir = (CELL, 0)

    def Update(self):
        now = pygame.time.get_ticks()

        if self.powerup is None and not self.shield_active and random.random() < 0.05: # ~1% chance per frame
            self.spawn_powerup()
        
        # check if power-up disappeared
        if self.powerup and now > self.powerup_expire_time:
            self.powerup = None

        # Applying speed/slow effects
        self.actual_speed = self.speed
        if now < self.effect_end_time:
            if self.active_powerup_type == "speed":
                self.actual_speed += 5 # Increases snake speed
            elif self.active_powerup_type == "slow":
                self.actual_speed = max(2, self.actual_speed - 4) # Decreases snake speed

        # powerup collection Logic
        if self.powerup and self.snake[0].colliderect(self.powerup["pos"]):
            if self.settings.get("sound_on") and self.snd_powerup:
                self.snd_powerup.play()
            ptype = self.powerup["type"]
            if ptype == "shield":
                self.shield_active = True # Until triggered
            else:
                self.active_powerup_type = ptype
                self.effect_end_time = now + 5000 # 5 seconds duration
            self.powerup = None

        # Move Snake
        new_head = self.snake[0].move(self.dir)
        
        # Border Wrap
        new_head.x %= WIDTH
        new_head.y %= HEIGHT

        # Collision Check
        if new_head.collidelist(self.snake) != -1 or new_head.collidelist(self.obstacles) != -1:
            if self.shield_active:
                self.shield_active = False
            else:
                if self.settings.get("sound_on") and self.snd_gameover:
                    self.snd_gameover.play()
                db.save_score(self.username, self.score, self.level)
                self.SwitchToScene(GameOverScene(self.username, self.score, self.level, self.personal_best))
                return

        # spawn new head ahead
        self.snake.insert(0, new_head)

        # Eat Food
        if new_head.colliderect(self.food["pos"]):
            if self.settings.get("sound_on") and self.snd_food:
                self.snd_food.play()
            self.score += self.food["weight"]
            self.food = self.spawn_item("normal")
            self.update_level()
        elif new_head.colliderect(self.poison["pos"]):
            if self.settings.get("sound_on") and self.snd_food:
                self.snd_food.play()
            self.snake.pop(); self.snake.pop(); self.snake.pop() # Remove two extra and from head spawning
            if len(self.snake) <= 1:
                db.save_score(self.username, self.score, self.level)
                self.SwitchToScene(GameOverScene(self.username, self.score, self.level, self.personal_best))
            self.poison = self.spawn_item("poison")
        else:
            self.snake.pop() # if food is not found delete last body segment so snake doesn't grow from spawning new head

    def Render(self, screen):
        screen.fill(COLOR_BLACK)
        for seg in self.snake: pygame.draw.rect(screen, self.settings["snake_color"], seg)
        food_color = COLOR_GOLD if self.food["weight"] == 1 else (0, 255, 255) # Cyan for high value
        pygame.draw.rect(screen, food_color, self.food["pos"])
        pygame.draw.rect(screen, COLOR_POISON, self.poison["pos"])
        for obs in self.obstacles: pygame.draw.rect(screen, (100, 100, 100), obs)
        if self.powerup: pygame.draw.circle(screen, COLOR_BLUE, self.powerup["pos"].center, CELL//2)
        
        # Grid Overlay logic
        if self.settings["grid_on"]:
            for x in range(0, WIDTH, CELL):
                pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, HEIGHT))
            for y in range(0, HEIGHT, CELL):
                pygame.draw.line(screen, (40, 40, 40), (0, y), (WIDTH, y))
        
        # UI
        screen.blit(self.font.render(f"Score: {self.score}  Level: {self.level}", True, COLOR_WHITE), (10, 10))
        if self.shield_active: screen.blit(self.font.render("SHIELD ACTIVE", True, COLOR_BLUE), (10, 40))
        
        # Draw Personal Best during gameplay
        best_txt = self.font.render(f"Personal Best: {self.personal_best}", True, (200, 200, 200))
        screen.blit(best_txt, (10, 70))

class LeaderboardScene(SceneBase):

    def __init__(self):
        super().__init__()
        # Static leaderboard data (can be replaced with JSON loading)
        self.data = [
            ("Alex", 120, 5),
            ("Bob", 95, 4),
            ("Charlie", 80, 3),
            ("Dana", 70, 3), 
        ]
        # Font used for rendering leaderboard text
        self.font = pygame.font.SysFont("Verdana", 20)


    def ProcessInput(self, events, pressed_keys):
        # Any key press returns to main menu
        for event in events:
            if event.type == pygame.KEYDOWN: self.SwitchToScene(MenuScene())

    def Render(self, screen):
        # Clear screen with black background
        screen.fill(COLOR_BLACK)
        y = 50

        # Title of leaderboard screen
        screen.blit(self.font.render("TOP 10 SCORES (Press any key)", True, COLOR_GOLD), (150, 20))

        # Render each leaderboard entry
        for row in self.data:
            txt = f"{row[0]} - Score: {row[1]} - Lvl: {row[2]}"
            screen.blit(self.font.render(txt, True, COLOR_WHITE), (100, y))
            y += 30


class SettingsScene(SceneBase):

    def __init__(self):
        super().__init__()
        # Load saved settings from file
        self.settings = load_settings()

        # Available snake colors
        self.colors = [(0, 255, 0), (0, 255, 255), (255, 165, 0)] # Green, Cyan, Orange

        # Index of currently selected color
        self.color_idx = 0

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:

                # Toggle grid visibility
                if event.key == pygame.K_g:
                    self.settings["grid_on"] = not self.settings["grid_on"]

                # Change snake color
                if event.key == pygame.K_c:
                    self.color_idx = (self.color_idx + 1) % len(self.colors)
                    self.settings["snake_color"] = self.colors[self.color_idx]

                # Save settings and return to menu
                if event.key == pygame.K_s:
                    save_settings(self.settings)
                    self.SwitchToScene(MenuScene())

    def Render(self, screen):
        # Dark background for settings screen
        screen.fill((30, 30, 30))
        font = pygame.font.SysFont("Verdana", 25)

        # Display grid status
        grid_status = "ON" if self.settings["grid_on"] else "OFF"
        screen.blit(font.render(f"Grid (G): {grid_status}", True, (255, 255, 255)), (100, 150))

        # Display color change hint
        screen.blit(font.render(f"Press (C) to change Snake Color", True, self.settings["snake_color"]), (100, 200))

        # Display save instruction
        screen.blit(font.render("Press (S) to Save & Back", True, (255, 255, 0)), (100, 300))


class GameOverScene(SceneBase):
    def __init__(self, username, score, level, pb):
        super().__init__()

        # Player information and game results
        self.username = username
        self.score = score
        self.level = level
        self.pb = pb

        # Fonts for game over screen
        self.font_large = pygame.font.SysFont("Verdana", 40)
        self.font_small = pygame.font.SysFont("Verdana", 20)

    def ProcessInput(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Retry
                    self.SwitchToScene(GameScene(self.username))
                elif event.key == pygame.K_m:  # Main Menu
                    self.SwitchToScene(MenuScene())

    def Render(self, screen):
        screen.fill(COLOR_BLACK)
        
        # Display Stats
        title = self.font_large.render("GAME OVER", True, COLOR_RED)
        score_txt = self.font_small.render(f"Final Score: {self.score}", True, COLOR_WHITE)
        level_txt = self.font_small.render(f"Level Reached: {self.level}", True, COLOR_WHITE)
        pb_txt = self.font_small.render(f"Personal Best: {max(self.score, self.pb)}", True, COLOR_GOLD)
        
        screen.blit(title, (WIDTH//2 - 120, 100))
        screen.blit(score_txt, (WIDTH//2 - 80, 200))
        screen.blit(level_txt, (WIDTH//2 - 80, 240))
        screen.blit(pb_txt, (WIDTH//2 - 80, 280))
        
        # Buttons/Hints
        retry_hint = self.font_small.render("Press (R) to Retry", True, COLOR_GREEN)
        menu_hint = self.font_small.render("Press (M) for Main Menu", True, COLOR_BLUE)
        
        screen.blit(retry_hint, (WIDTH//2 - 80, 380))
        screen.blit(menu_hint, (WIDTH//2 - 110, 420))

# main loop
def run_game(width, height, fps, starting_scene):
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()
    active_scene = starting_scene
    while active_scene:
        events = pygame.event.get()
        if any(e.type == pygame.QUIT for e in events): break
        active_scene.ProcessInput(events, pygame.key.get_pressed())
        active_scene.Update()
        active_scene.Render(screen)
        active_scene = active_scene.next
        pygame.display.flip()
        clock.tick(fps if not isinstance(active_scene, GameScene) else active_scene.actual_speed)
    pygame.quit()

run_game(WIDTH, HEIGHT, FPS, MenuScene())