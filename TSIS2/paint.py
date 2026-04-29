import pygame
import os
from datetime import datetime
from tools import TOOLBAR_HEIGHT, WHITE, draw_shape, flood_fill

pygame.init()

# Window
WIDTH = 900
HEIGHT = 600
CANVAS_HEIGHT = HEIGHT - TOOLBAR_HEIGHT

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Paint application TSIS 2")

# Folder for uploaded icons
BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
print(os.path.abspath("assets/brush.png"))
print(os.path.exists("assets/brush.png"))

# Colors
BLACK = (0, 0, 0)
RED = (230, 70, 70)
GREEN = (70, 180, 90)
BLUE = (70, 120, 230)
YELLOW = (240, 210, 70)
PURPLE = (160, 90, 200)

LIGHT_GRAY = (245, 247, 250)
GRAY = (220, 225, 235)
DARK_GRAY = (70, 70, 80)

# Fonts
font = pygame.font.SysFont("Arial", 16)
text_font = pygame.font.SysFont("Arial", 28)

# Canvas
canvas = pygame.Surface((WIDTH, CANVAS_HEIGHT))
canvas.fill(WHITE)

# Current settings
current_tool = "brush"
current_color = BLACK
brush_size = 5

# Drawing state
drawing = False
start_pos = None
last_pos = None

# Text state
typing = False
text_pos = None
typed_text = ""


def load_icon(filename):
    path = os.path.join(ASSETS_DIR, filename)
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, (22, 22))

asset_icons = {
    "brush": load_icon("brush.png"),
    "eraser": load_icon("eraser.png"),
    "fill": load_icon("fill.png"),
    "line": load_icon("line.png")
}


tool_buttons = {
    "brush": pygame.Rect(10, 10, 90, 32),
    "line": pygame.Rect(110, 10, 80, 32),
    "eraser": pygame.Rect(200, 10, 90, 32),
    "fill": pygame.Rect(300, 10, 80, 32),
    "text": pygame.Rect(390, 10, 80, 32),
    "clear": pygame.Rect(480, 10, 80, 32),
    "rectangle": pygame.Rect(570, 10, 115, 32),
    "circle": pygame.Rect(695, 10, 90, 32),
    "square": pygame.Rect(795, 10, 90, 32),

    "right triangle": pygame.Rect(10, 52, 130, 32),
    "equilateral": pygame.Rect(150, 52, 120, 32),
    "rhombus": pygame.Rect(280, 52, 110, 32)
}

color_buttons = [
    (BLACK, pygame.Rect(10, 95, 32, 32)),
    (RED, pygame.Rect(50, 95, 32, 32)),
    (GREEN, pygame.Rect(90, 95, 32, 32)),
    (BLUE, pygame.Rect(130, 95, 32, 32)),
    (YELLOW, pygame.Rect(170, 95, 32, 32)),
    (PURPLE, pygame.Rect(210, 95, 32, 32))
]

size_buttons = {
    2: pygame.Rect(270, 95, 65, 32),
    5: pygame.Rect(345, 95, 65, 32),
    10: pygame.Rect(420, 95, 70, 32)
}


def screen_to_canvas(pos):
    return (pos[0], pos[1] - TOOLBAR_HEIGHT)


def is_on_canvas(pos):
    return pos[1] >= TOOLBAR_HEIGHT


def save_canvas():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    paintings_folder = os.path.join(BASE_DIR, "paintings")

    if not os.path.exists(paintings_folder):
        os.makedirs(paintings_folder)

    filename = f"paint_{timestamp}.png"
    filepath = os.path.join(paintings_folder, filename)

    # Only canvas is saved, not toolbar or console area
    pygame.image.save(canvas, filepath)

    print("Saved:", filepath)


def clear_canvas():
    canvas.fill(WHITE)
    print("Canvas cleared")


def draw_icon_with_pygame(tool, rect):
    # For brush, line, eraser, fill: use uploaded icons
    if tool in asset_icons:
        screen.blit(asset_icons[tool], (rect.x + 5, rect.y + 5))
        return

    # For other tools: draw simple icon directly using pygame.draw
    x = rect.x + 6
    y = rect.y + 6

    if tool == "text":
        pygame.draw.line(screen, BLACK, (x + 2, y), (x + 18, y), 2)
        pygame.draw.line(screen, BLACK, (x + 10, y), (x + 10, y + 20), 2)

    elif tool == "clear":
        pygame.draw.line(screen, BLACK, (x + 3, y + 3), (x + 18, y + 18), 3)
        pygame.draw.line(screen, BLACK, (x + 18, y + 3), (x + 3, y + 18), 3)

    elif tool == "rectangle":
        pygame.draw.rect(screen, BLACK, (x, y + 4, 20, 13), 2)

    elif tool == "circle":
        pygame.draw.circle(screen, BLACK, (x + 11, y + 11), 9, 2)

    elif tool == "square":
        pygame.draw.rect(screen, BLACK, (x + 3, y + 3, 16, 16), 2)

    elif tool == "right triangle":
        points = [(x + 2, y + 2), (x + 2, y + 20), (x + 20, y + 20)]
        pygame.draw.polygon(screen, BLACK, points, 2)

    elif tool == "equilateral":
        points = [(x + 11, y + 2), (x + 2, y + 20), (x + 20, y + 20)]
        pygame.draw.polygon(screen, BLACK, points, 2)

    elif tool == "rhombus":
        points = [(x + 11, y + 2), (x + 20, y + 11), (x + 11, y + 20), (x + 2, y + 11)]
        pygame.draw.polygon(screen, BLACK, points, 2)


def draw_toolbar():
    pygame.draw.rect(screen, LIGHT_GRAY, (0, 0, WIDTH, TOOLBAR_HEIGHT))
    pygame.draw.line(screen, GRAY, (0, TOOLBAR_HEIGHT - 1), (WIDTH, TOOLBAR_HEIGHT - 1), 2)

    # Tool buttons
    for tool, rect in tool_buttons.items():
        if tool == current_tool:
            button_color = BLUE
            text_color = WHITE
        else:
            button_color = WHITE
            text_color = BLACK

        pygame.draw.rect(screen, button_color, rect, border_radius=8)
        pygame.draw.rect(screen, DARK_GRAY, rect, 1, border_radius=8)

        draw_icon_with_pygame(tool, rect)

        label = font.render(tool, True, text_color)
        screen.blit(label, (rect.x + 32, rect.y + 8))

    # Color buttons
    for color, rect in color_buttons:
        pygame.draw.rect(screen, color, rect, border_radius=8)

        if color == current_color:
            pygame.draw.rect(screen, BLUE, rect, 4, border_radius=8)
        else:
            pygame.draw.rect(screen, DARK_GRAY, rect, 1, border_radius=8)

    # Size buttons
    for size, rect in size_buttons.items():
        if size == brush_size:
            button_color = BLUE
            text_color = WHITE
        else:
            button_color = WHITE
            text_color = BLACK

        pygame.draw.rect(screen, button_color, rect, border_radius=8)
        pygame.draw.rect(screen, DARK_GRAY, rect, 1, border_radius=8)

        label = font.render(str(size) + " px", True, text_color)
        screen.blit(label, (rect.x + 10, rect.y + 8))

    help_text = "1 small | 2 medium | 3 large | Ctrl+S save"
    label = font.render(help_text, True, DARK_GRAY)
    screen.blit(label, (510, 102))


running = True
clock = pygame.time.Clock()

while running:
    screen.fill(WHITE)

    # Canvas is shown below toolbar
    screen.blit(canvas, (0, TOOLBAR_HEIGHT))

    # Live preview for line and shapes
    if drawing and start_pos is not None and current_tool in [
        "line", "rectangle", "circle", "square",
        "right triangle", "equilateral", "rhombus"
    ]:
        temp = canvas.copy()
        mouse_pos = pygame.mouse.get_pos()

        if is_on_canvas(mouse_pos):
            end_pos = screen_to_canvas(mouse_pos)
            draw_shape(temp, current_tool, current_color, start_pos, end_pos, brush_size)

        screen.blit(temp, (0, TOOLBAR_HEIGHT))

    # Live text preview
    if typing and text_pos is not None:
        text_surface = text_font.render(typed_text, True, current_color)
        screen.blit(text_surface, (text_pos[0], text_pos[1] + TOOLBAR_HEIGHT))

    draw_toolbar()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if typing:
                if event.key == pygame.K_RETURN:
                    text_surface = text_font.render(typed_text, True, current_color)
                    canvas.blit(text_surface, text_pos)
                    typing = False
                    text_pos = None
                    typed_text = ""
                elif event.key == pygame.K_ESCAPE:
                    typing = False
                    text_pos = None
                    typed_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    typed_text = typed_text[:-1]
                else:
                    typed_text += event.unicode
            else:
                if event.key == pygame.K_1:
                    brush_size = 2
                elif event.key == pygame.K_2:
                    brush_size = 5
                elif event.key == pygame.K_3:
                    brush_size = 10
                elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    save_canvas()

                elif event.key == pygame.K_DELETE:
                    clear_canvas()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Select tool
            for tool, rect in tool_buttons.items():
                if rect.collidepoint(mouse_pos):
                    current_tool = tool
                    typing = False

            # Select color
            for color, rect in color_buttons:
                if rect.collidepoint(mouse_pos):
                    current_color = color

            # Select brush size
            for size, rect in size_buttons.items():
                if rect.collidepoint(mouse_pos):
                    brush_size = size

            # Use tool only inside canvas
            if is_on_canvas(mouse_pos):
                canvas_pos = screen_to_canvas(mouse_pos)

                if current_tool == "clear":
                    clear_canvas()

                elif current_tool == "fill":
                    flood_fill(canvas, canvas_pos, current_color)

                elif current_tool == "text":
                    typing = True
                    text_pos = canvas_pos
                    typed_text = ""

                else:
                    drawing = True
                    start_pos = canvas_pos
                    last_pos = canvas_pos

                    if current_tool == "brush":
                        pygame.draw.circle(canvas, current_color, canvas_pos, max(1, brush_size // 2))

                    elif current_tool == "eraser":
                        pygame.draw.circle(canvas, WHITE, canvas_pos, brush_size)

        elif event.type == pygame.MOUSEMOTION:
            if drawing and is_on_canvas(event.pos):
                canvas_pos = screen_to_canvas(event.pos)

                if current_tool == "brush":
                    pygame.draw.line(canvas, current_color, last_pos, canvas_pos, brush_size)
                    last_pos = canvas_pos

                elif current_tool == "eraser":
                    pygame.draw.line(canvas, WHITE, last_pos, canvas_pos, brush_size)
                    last_pos = canvas_pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if drawing and is_on_canvas(event.pos):
                end_pos = screen_to_canvas(event.pos)

                if current_tool in [
                    "line", "rectangle", "circle", "square",
                    "right triangle", "equilateral", "rhombus"
                ]:
                    draw_shape(canvas, current_tool, current_color, start_pos, end_pos, brush_size)

            drawing = False
            start_pos = None
            last_pos = None

    pygame.display.update()
    clock.tick(60)

pygame.quit()