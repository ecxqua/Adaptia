# src/view/renderer.py
"""Заглушка Renderer. Будет заполнена похже"""
"""Рендерер.
Отвечает только за отрисовку объектов на экран. НЕ изменяет данные модели.
"""
import pygame
from src.model.world import World

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

        # Отладочная инфа в углу экрана
        if hasattr(world, 'get_creature_count'):
            font = pygame.font.SysFont("consolas", 12)
            text = f"Creatures: {world.get_creature_count()}"
            self.screen.blit(font.render(text, True, (200, 200, 200)), (10, 10))