"""UI-оверлеи: HUD, меню, подсказки, панель настроек.
Только отрисовка и обработка ввода UI. Не хранит состояние игры.
"""
import pygame
import config as cfg
from typing import List, Callable, Tuple, Optional


class UIManager:
    """Отвечает за отрисовку текста и интерфейса поверх мира (HUD)."""
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font = pygame.font.SysFont("consolas", 14)

    def draw_hud(self, creature_count: int, mode_name: str, speed: float) -> None:
        """Отрисовывает счётчик существ, режим, скорость и текущие параметры."""
        lines = [
            f"Существа: {creature_count}",
            f"Режим: {mode_name}",
            f"Скорость: x{speed:.1f}",
            f"Мутация: {cfg.MUTATION_RATE:.2f}",           
            f"Сила мутации: {cfg.MUTATION_STRENGTH:.2f}",  
            f"Плотность еды: {cfg.FOOD_SPAWN_RATE:.3f}",  
            f"Расход энергии: {cfg.ENERGY_DECAY:.1f}",     
        ]
        y_offset = 10
        for text in lines:
            surface = self.font.render(text, True, (220, 220, 220))
            self.screen.blit(surface, (10, y_offset))
            y_offset += 18


class Slider:
    """Горизонтальный ползунок для настройки float-параметров."""
    
    def __init__(
        self,
        label: str,
        x: float, y: float,
        width: float,
        min_val: float, max_val: float,
        get_value: Callable[[], float],
        set_value: Callable[[float], None],
        decimals: int = 2
    ):
        self.label = label
        self.x = x
        self.y = y
        self.width = width
        self.height = 8
        self.min_val = min_val
        self.max_val = max_val
        self.get_value = get_value
        self.set_value = set_value
        self.decimals = decimals
        self.dragging = False
        self.font = pygame.font.SysFont("consolas", 14)

    def _value_to_x(self, value: float) -> float:
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return self.x + ratio * self.width

    def _x_to_value(self, x: float) -> float:
        ratio = max(0.0, min(1.0, (x - self.x) / self.width))
        return self.min_val + ratio * (self.max_val - self.min_val)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            handle_x = self._value_to_x(self.get_value())
            if abs(mx - handle_x) < 12 and abs(my - (self.y + self.height / 2)) < 12:
                self.dragging = True
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            new_value = self._x_to_value(event.pos[0])
            new_value = round(new_value, self.decimals)
            self.set_value(new_value)
            return True
        
        return False

    def draw(self, surface: pygame.Surface) -> None:
        track_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, (80, 80, 80), track_rect, border_radius=4)
        
        handle_x = self._value_to_x(self.get_value())
        if handle_x > self.x:
            fill_rect = pygame.Rect(self.x, self.y, handle_x - self.x, self.height)
            pygame.draw.rect(surface, (100, 200, 100), fill_rect, border_radius=4)
        
        pygame.draw.circle(
            surface, (255, 255, 255),
            (int(handle_x), int(self.y + self.height / 2)),
            6
        )
        
        value_text = f"{self.get_value():.{self.decimals}f}"
        label_surf = self.font.render(f"{self.label}: {value_text}", True, (220, 220, 220))
        surface.blit(label_surf, (self.x, self.y - 18))


class SettingsPanel:
    """Панель настроек среды. Открывается по клавише S."""
    
    def __init__(self, screen_width: float, screen_height: float):
        self.visible = False
        self.width = 320
        self.height = 260
        self.x = screen_width - self.width - 20
        self.y = 20
        
        self.sliders: List[Slider] = [
            Slider(
                "Мутация (rate)",
                self.x + 20, self.y + 40, 240,
                min_val=0.01, max_val=0.5,
                get_value=lambda: cfg.MUTATION_RATE,
                set_value=lambda v: setattr(cfg, 'MUTATION_RATE', v),
                decimals=2
            ),
            Slider(
                "Сила мутации",
                self.x + 20, self.y + 90, 240,
                min_val=0.05, max_val=1.0,
                get_value=lambda: cfg.MUTATION_STRENGTH,
                set_value=lambda v: setattr(cfg, 'MUTATION_STRENGTH', v),
                decimals=2
            ),
            Slider(
                "Плотность еды",
                self.x + 20, self.y + 140, 240,
                min_val=0.005, max_val=0.1,
                get_value=lambda: cfg.FOOD_SPAWN_RATE,
                set_value=lambda v: setattr(cfg, 'FOOD_SPAWN_RATE', v),
                decimals=3
            ),
            Slider(
                "Расход энергии",
                self.x + 20, self.y + 190, 240,
                min_val=1.0, max_val=15.0,
                get_value=lambda: cfg.ENERGY_DECAY,
                set_value=lambda v: setattr(cfg, 'ENERGY_DECAY', v),
                decimals=1
            ),
        ]
        
        self.font_title = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_hint = pygame.font.SysFont("consolas", 12)

    def toggle(self) -> None:
        self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        
        for slider in self.sliders:
            if slider.handle_event(event):
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, (30, 30, 40), panel_rect, border_radius=8)
        pygame.draw.rect(surface, (100, 100, 120), panel_rect, 2, border_radius=8)
        
        title = self.font_title.render("Настройки среды", True, (255, 255, 255))
        surface.blit(title, (self.x + 20, self.y + 12))
        
        hint = self.font_hint.render("[S] закрыть", True, (150, 150, 150))
        surface.blit(hint, (self.x + self.width - 90, self.y + 14))
        
        for slider in self.sliders:
            slider.draw(surface)

class MainMenu:
    """Главное меню. Отвечает за отрисовку кнопок и обработку кликов."""
    def __init__(self, screen_width: float, screen_height: float):
        self.visible = True
        self.width = 420
        self.height = 320
        self.x = (screen_width - self.width) / 2
        self.y = (screen_height - self.height) / 2 - 40

        self.buttons = [
            {"text": "Запуск", "action": "start", "y": 40},
            {"text": "Настройки", "action": "settings", "y": 100},
            {"text": "Статистика", "action": "stats", "y": 160},
            {"text": "Выход", "action": "exit", "y": 220},
        ]
        self.hovered_index = -1
        self.font_title = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_btn = pygame.font.SysFont("consolas", 20)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Возвращает строку-действие при клике или None."""
        if not self.visible:
            return None
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered_index = -1
            for i, btn in enumerate(self.buttons):
                btn_rect = pygame.Rect(self.x + 60, self.y + btn["y"], self.width - 120, 44)
                if btn_rect.collidepoint(mx, my):
                    self.hovered_index = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for btn in self.buttons:
                btn_rect = pygame.Rect(self.x + 60, self.y + btn["y"], self.width - 120, 44)
                if btn_rect.collidepoint(mx, my):
                    return btn["action"]
        return None

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        # Затемнение фона
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((15, 15, 20, 200))
        surface.blit(overlay, (0, 0))

        # Окно меню
        pygame.draw.rect(surface, (25, 25, 35), (self.x, self.y, self.width, self.height), border_radius=12)
        pygame.draw.rect(surface, (80, 80, 100), (self.x, self.y, self.width, self.height), 2, border_radius=12)

        title = self.font_title.render("Adaptia", True, (240, 240, 240))
        surface.blit(title, (self.x + (self.width - title.get_width()) / 2, self.y + 15))

        for i, btn in enumerate(self.buttons):
            btn_rect = pygame.Rect(self.x + 60, self.y + btn["y"], self.width - 120, 44)
            color = (50, 100, 50) if i == self.hovered_index else (35, 35, 45)
            pygame.draw.rect(surface, color, btn_rect, border_radius=8)
            if i == self.hovered_index:
                pygame.draw.rect(surface, (70, 130, 70), btn_rect, 2, border_radius=8)

            text_surf = self.font_btn.render(btn["text"], True, (220, 220, 220))
            surface.blit(text_surf, (btn_rect.centerx - text_surf.get_width() / 2,
                                     btn_rect.centery - text_surf.get_height() / 2))            