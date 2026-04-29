import pygame
import math
from collections import deque

TOOLBAR_HEIGHT = 140
WHITE = (255, 255, 255)


def draw_rectangle(surface, color, start, end, size):
    x = min(start[0], end[0])
    y = min(start[1], end[1])
    w = abs(end[0] - start[0])
    h = abs(end[1] - start[1])
    pygame.draw.rect(surface, color, (x, y, w, h), size)


def draw_square(surface, color, start, end, size):
    side = min(abs(end[0] - start[0]), abs(end[1] - start[1]))

    x = start[0]
    y = start[1]

    if end[0] < start[0]:
        x = start[0] - side
    if end[1] < start[1]:
        y = start[1] - side

    pygame.draw.rect(surface, color, (x, y, side, side), size)


def draw_circle(surface, color, start, end, size):
    radius = int(math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2))
    pygame.draw.circle(surface, color, start, radius, size)


def draw_right_triangle(surface, color, start, end, size):
    x1, y1 = start
    x2, y2 = end
    points = [(x1, y1), (x1, y2), (x2, y2)]
    pygame.draw.polygon(surface, color, points, size)


def draw_equilateral(surface, color, start, end, size):
    x1, y1 = start
    x2, y2 = end

    side = abs(x2 - x1)
    height = int((math.sqrt(3) / 2) * side)

    p1 = (x1, y1)
    p2 = (x1 + side, y1)

    if y2 >= y1:
        p3 = (x1 + side // 2, y1 + height)
    else:
        p3 = (x1 + side // 2, y1 - height)

    pygame.draw.polygon(surface, color, [p1, p2, p3], size)


def draw_rhombus(surface, color, start, end, size):
    x1, y1 = start
    x2, y2 = end

    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2

    points = [
        (cx, y1),
        (x2, cy),
        (cx, y2),
        (x1, cy)
    ]

    pygame.draw.polygon(surface, color, points, size)


def draw_shape(surface, tool, color, start, end, size):
    if tool == "line":
        pygame.draw.line(surface, color, start, end, size)
    elif tool == "rectangle":
        draw_rectangle(surface, color, start, end, size)
    elif tool == "circle":
        draw_circle(surface, color, start, end, size)
    elif tool == "square":
        draw_square(surface, color, start, end, size)
    elif tool == "right triangle":
        draw_right_triangle(surface, color, start, end, size)
    elif tool == "equilateral":
        draw_equilateral(surface, color, start, end, size)
    elif tool == "rhombus":
        draw_rhombus(surface, color, start, end, size)


def flood_fill(surface, start_pos, fill_color):
    width, height = surface.get_size()
    x, y = start_pos

    if x < 0 or x >= width or y < 0 or y >= height:
        return

    target_color = surface.get_at((x, y))
    fill_color = pygame.Color(fill_color)

    if target_color == fill_color:
        return

    queue = deque()
    queue.append((x, y))

    while queue:
        x, y = queue.popleft()

        if x < 0 or x >= width or y < 0 or y >= height:
            continue

        if surface.get_at((x, y)) != target_color:
            continue

        surface.set_at((x, y), fill_color)

        queue.append((x + 1, y))
        queue.append((x - 1, y))
        queue.append((x, y + 1))
        queue.append((x, y - 1))