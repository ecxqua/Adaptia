# src/view/ui.py
"""UI-оверлеи: HUD, меню, подсказки.
Только отрисовка. Не хранит состояние игры.
"""
import pygame
import config as cfg

class UIManager:
    """Отвечает за отрисовку текста и интерфейса поверх мира."""
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.SysFont("consolas", 14)

    def draw_hud(self, creature_count: int, mode_name: str, speed: float) -> None:
        """Отрисовывает счётчик существ, режим и скорость в левом верхнем углу."""
        lines = [
            f"Существа: {creature_count}",
            f"Режим: {mode_name}",
            f"Скорость: x{speed:.1f}"
        ]
        y_offset = 10
        for text in lines:
            surface = self.font.render(text, True, (220, 220, 220))
            self.screen.blit(surface, (10, y_offset))
            y_offset += 18