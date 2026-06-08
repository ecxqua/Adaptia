# src/view/renderer.py
"""Заглушка Renderer. Будет заполнена похже"""
"""Рендерер.
Отвечает только за отрисовку объектов на экран. НЕ изменяет данные модели.
"""
import pygame
from src.model.world import World
import config as cfg

# Цвета для визуализации состояний (R, G, B)
STATE_COLORS = {
    "WANDER": (180, 180, 180),   # светло-серый
    "SEEK": (0, 255, 0),         # ярко-зелёный
    "FLEE": (255, 0, 0),         # ярко-красный
    "REPRODUCE": (0, 100, 255)   # насыщенный синий
}

class Renderer:
    """Класс для отрисовки игрового мира."""
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def draw_world(self, world: World) -> None:
        """Отрисовывает все существа из переданного мира."""
        # Отрисовка следов
        for creature in world.creatures:
            if len(creature.trail) > 1:
                for i in range(len(creature.trail) - 1):
                    alpha = int(255 * (i / len(creature.trail)))
                    color = (100, 100, 100, alpha // 3)  # Полупрозрачный серый
                    pygame.draw.line(
                        self.screen, color,
                        (int(creature.trail[i][0]), int(creature.trail[i][1])),
                        (int(creature.trail[i+1][0]), int(creature.trail[i+1][1])),
                        1
                    )
                    
        for creature in world.creatures:
            data = creature.get_render_data()
            color = STATE_COLORS.get(data["state"], (255, 255, 255))
            pos = (int(data["pos"][0]), int(data["pos"][1]))
            radius = int(data["radius"])
            
            if data["state"] == "WANDER":
                pygame.draw.circle(self.screen, color, pos, radius)
            elif data["state"] == "SEEK":
                # Треугольник
                points = [
                    (pos[0], pos[1] - radius),
                    (pos[0] - radius, pos[1] + radius),
                    (pos[0] + radius, pos[1] + radius)
                ]
                pygame.draw.polygon(self.screen, color, points)
            elif data["state"] == "FLEE":
                # Квадрат
                rect = pygame.Rect(pos[0] - radius, pos[1] - radius, radius*2, radius*2)
                pygame.draw.rect(self.screen, color, rect)
            else:
                pygame.draw.circle(self.screen, color, pos, radius)

            # Отрисовка препятствий ← ДОБАВИТЬ
        for ox, oy in world.get_obstacles():
            # Рисуем квадрат 20x20 пикселей (размер клетки A*)
            rect = pygame.Rect(int(ox) - 10, int(oy) - 10, 20, 20)
            pygame.draw.rect(self.screen, (128, 128, 128), rect)  # Серый цвет


        for food_x, food_y, _ in world.food:
            # Маленькая зелёная точка, радиус 4
            pygame.draw.circle(
                self.screen,
                (0, 255, 0),  # ярко-зелёный
                (int(food_x), int(food_y)),
                4  # радиус еды меньше, чем у существ (6)
            )
        # Отрисовка частиц
        for p in world.particles:
            # pygame.draw.circle не поддерживает альфа-канал напрямую,
            # поэтому делаем эффект затухания через уменьшение размера
            radius = max(1, int(3 * p['life']))
            pygame.draw.circle(self.screen, p['color'], (int(p['x']), int(p['y'])), radius)
        # # Отладочная инфа в углу экрана
        # if hasattr(world, 'get_creature_count'):
        #     font = pygame.font.SysFont("consolas", 12)
        #     text = f"Creatures: {world.get_creature_count()}"
        #     self.screen.blit(font.render(text, True, (200, 200, 200)), (10, 10))
        
        # отладка
        if cfg.DEBUG_MODE:
            for c in world.creatures:
                start_pos = (int(c.x), int(c.y))
                end_pos = (int(c.x + c.vx * 2), int(c.y + c.vy * 2))
                pygame.draw.line(self.screen, (255, 255, 0), start_pos, end_pos, 1)
