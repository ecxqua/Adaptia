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
        for creature in world.creatures:
            data = creature.get_render_data()
            color = STATE_COLORS.get(data["state"], (255, 255, 255))
            pygame.draw.circle(self.screen, color, data["pos"], data["radius"])

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

                # Отрисовка пути A* (только если путь длинный и полезный)
                if c.current_path and len(c.current_path) > 2:
                    for i in range(len(c.current_path) - 1):
                        p1 = (int(c.current_path[i][0]), int(c.current_path[i][1]))
                        p2 = (int(c.current_path[i+1][0]), int(c.current_path[i+1][1]))
                        pygame.draw.line(self.screen, (0, 255, 255), p1, p2, 2)