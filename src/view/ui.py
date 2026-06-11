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

class FitnessGraph:
    """Отрисовка графика фитнеса по поколениям в правом верхнем углу."""
    def __init__(self, screen_width: float, screen_height: float):
        self.width = 240   # ✅ Было 300, уменьшили
        self.height = 120  # ✅ Было 150, уменьшили
        self.x = screen_width - self.width - 20
        self.y = 20
        self.font = pygame.font.SysFont("consolas", 11)
        self.font_title = pygame.font.SysFont("consolas", 13, bold=True)
        self.visible = True

    def draw(self, surface: pygame.Surface, fitness_history: list[float], generation: int) -> None:
        if not self.visible or not fitness_history:
            return
        
        # Фон графика
        pygame.draw.rect(surface, (25, 25, 35, 200), (self.x, self.y, self.width, self.height), border_radius=6)
        pygame.draw.rect(surface, (80, 80, 100), (self.x, self.y, self.width, self.height), 1, border_radius=6)
        
        # Заголовок
        title = self.font_title.render(f"Фитнес (Gen {generation})", True, (220, 220, 220))
        surface.blit(title, (self.x + 10, self.y + 5))
        
        # Вычисляем масштаб
        max_fit = max(fitness_history) if fitness_history else 1
        min_fit = min(fitness_history) if fitness_history else 0
        range_fit = max_fit - min_fit if max_fit != min_fit else 1
        
        # Область графика
        graph_x = self.x + 10
        graph_y = self.y + 22
        graph_width = self.width - 20
        graph_height = self.height - 30
        
        # Сетка
        for i in range(4):
            y_pos = graph_y + (graph_height * i / 3)
            pygame.draw.line(surface, (50, 50, 65), (graph_x, int(y_pos)), (graph_x + graph_width, int(y_pos)), 1)
        
        # Линия фитнеса (последние 20 поколений)
        visible = fitness_history[-20:] if len(fitness_history) > 20 else fitness_history
        if len(visible) > 1:
            points = []
            for i, fit in enumerate(visible):
                x = graph_x + (i / max(1, len(visible) - 1)) * graph_width
                y = graph_y + graph_height - ((fit - min_fit) / range_fit) * graph_height
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.lines(surface, (100, 200, 100), False, points, 2)
        
        # Подписи осей
        min_label = self.font.render(f"{min_fit:.0f}", True, (150, 150, 150))
        max_label = self.font.render(f"{max_fit:.0f}", True, (150, 150, 150))
        surface.blit(min_label, (self.x + 5, int(graph_y + graph_height) - 6))
        surface.blit(max_label, (self.x + 5, int(graph_y)))


class GeneHistogram:
    """Гистограмма среднего значения генов популяции (компактная)."""
    def __init__(self, screen_width: float, screen_height: float):
        self.width = 240   # ✅ Совпадает с шириной FitnessGraph
        self.height = 90   # ✅ Было 110, уменьшили
        self.x = screen_width - self.width - 20
        # ✅ y = 20 (график) + 120 (высота графика) + 10 (отступ) = 150
        self.y = 150
        self.font = pygame.font.SysFont("consolas", 9)
        self.font_title = pygame.font.SysFont("consolas", 11, bold=True)
        self.visible = True

    def draw(self, surface: pygame.Surface, creatures: list) -> None:
        if not self.visible or not creatures:
            return
        
        # Вычисляем среднее значение каждого гена (показываем первые 5)
        genome_length = min(len(creatures[0].genome), 5)
        avg_genes = [0.0] * genome_length
        for c in creatures:
            for i in range(genome_length):
                avg_genes[i] += c.genome[i]
        avg_genes = [g / len(creatures) for g in avg_genes]
        
        # Фон
        pygame.draw.rect(surface, (20, 20, 30, 200), 
                        (self.x, self.y, self.width, self.height), border_radius=4)
        pygame.draw.rect(surface, (60, 60, 80), 
                        (self.x, self.y, self.width, self.height), 1, border_radius=4)
        
        # Заголовок
        title = self.font_title.render("Средние гены", True, (200, 200, 200))
        surface.blit(title, (self.x + 8, self.y + 5))
        
        # Базовая линия посередине
        baseline_y = self.y + self.height / 2  # = self.y + 45
        
        # Максимальная высота столбца
        max_bar_height = (self.height / 2) - 16  # = 29px
        max_val = max(abs(g) for g in avg_genes) if avg_genes else 1
        if max_val == 0:
            max_val = 1
        
        bar_width = (self.width - 16) / genome_length
        
        for i, gene in enumerate(avg_genes):
            bar_height = (abs(gene) / max_val) * max_bar_height
            x = self.x + 8 + i * bar_width
            
            if gene >= 0:
                y = baseline_y - bar_height
            else:
                y = baseline_y
            
            color = (60, 160, 60) if gene >= 0 else (160, 60, 60)
            pygame.draw.rect(surface, color, 
                           (x + 1, int(y), int(bar_width - 3), int(bar_height)))
        
        # Подпись "0" у базовой линии
        zero_label = self.font.render("0", True, (130, 130, 130))
        surface.blit(zero_label, (self.x + 2, int(baseline_y) - 5))

class StatsScreen:
    """Полноэкранный режим просмотра статистики."""
    def __init__(self, screen_width: float, screen_height: float):
        self.width = screen_width
        self.height = screen_height
        self.font_title = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_subtitle = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_text = pygame.font.SysFont("consolas", 14)
        self.font_small = pygame.font.SysFont("consolas", 12)
        
        # ✅ УВЕЛИЧЕННЫЕ отступы, чтобы ничего не перекрывалось
        self.title_y = 30
        self.subtitle_y = 70        # Подзаголовок
        self.graph_y = 110          # ✅ Было 80, сдвинули вниз на 30px
        self.histogram_y = 310      # ✅ Было 280, сдвинули вниз
        self.table_y = 500          # ✅ Было 420, сдвинули вниз

    def draw(self, surface: pygame.Surface, fitness_history: list[float], 
             generation: int, creatures: list) -> None:
        # Фон
        surface.fill((15, 15, 25))
        
        # Заголовок
        title = self.font_title.render("СТАТИСТИКА ЭВОЛЮЦИИ", True, (255, 255, 255))
        surface.blit(title, ((self.width - title.get_width()) / 2, self.title_y))
        
        # ✅ Подзаголовок рисуется на отдельной позиции (между заголовком и графиком)
        subtitle = self.font_subtitle.render(f"Поколение: {generation}", True, (180, 180, 180))
        surface.blit(subtitle, ((self.width - subtitle.get_width()) / 2, self.subtitle_y))
        
        # График фитнеса (большой)
        self._draw_large_graph(surface, fitness_history)
        
        # Гистограмма генов
        self._draw_large_histogram(surface, creatures)
        
        # Таблица последних поколений
        self._draw_stats_table(surface, fitness_history)
        
        # Подсказки
        hints = [
            "[C] Экспорт в CSV",
            "[ESC] Назад в меню",
            "[G] Скрыть/показать графики"
        ]
        for i, hint in enumerate(hints):
            text = self.font_small.render(hint, True, (120, 120, 120))
            surface.blit(text, (20, self.height - 60 + i * 20))

    def _draw_large_graph(self, surface: pygame.Surface, fitness_history: list[float]) -> None:
        """Большой график фитнеса."""
        if not fitness_history:
            text = self.font_text.render("Нет данных (запустите симуляцию)", True, (150, 150, 150))
            surface.blit(text, ((self.width - text.get_width()) / 2, self.graph_y + 80))
            return
        
        # Фон графика
        graph_width = self.width - 100
        graph_height = 160
        graph_x = 50
        graph_y = self.graph_y
        
        pygame.draw.rect(surface, (30, 30, 45), (graph_x, graph_y, graph_width, graph_height), border_radius=8)
        pygame.draw.rect(surface, (90, 90, 120), (graph_x, graph_y, graph_width, graph_height), 2, border_radius=8)
        
        # Заголовок графика
        title = self.font_subtitle.render("Динамика фитнеса", True, (220, 220, 220))
        surface.blit(title, (graph_x + 15, graph_y + 10))
        
        # Масштаб
        max_fit = max(fitness_history)
        min_fit = min(fitness_history)
        range_fit = max_fit - min_fit if max_fit != min_fit else 1
        
        # Сетка
        for i in range(5):
            y = graph_y + 30 + (graph_height - 40) * i / 4
            pygame.draw.line(surface, (50, 50, 70), (graph_x + 10, int(y)), (graph_x + graph_width - 10, int(y)), 1)
        
        # Линия (последние 30 поколений)
        visible = fitness_history[-30:] if len(fitness_history) > 30 else fitness_history
        if len(visible) > 1:
            points = []
            for i, fit in enumerate(visible):
                x = graph_x + 10 + (i / max(1, len(visible) - 1)) * (graph_width - 20)
                y = graph_y + graph_height - 10 - ((fit - min_fit) / range_fit) * (graph_height - 40)
                points.append((int(x), int(y)))
            
            if len(points) > 1:
                pygame.draw.lines(surface, (100, 220, 100), False, points, 3)
        
        # Подписи осей
        min_label = self.font_small.render(f"{min_fit:.1f}", True, (130, 130, 130))
        max_label = self.font_small.render(f"{max_fit:.1f}", True, (130, 130, 130))
        surface.blit(min_label, (graph_x + 5, int(graph_y + graph_height) - 12))
        surface.blit(max_label, (graph_x + 5, graph_y + 28))

    def _draw_large_histogram(self, surface: pygame.Surface, creatures: list) -> None:
        """Большая гистограмма генов."""
        if not creatures:
            return
        
        # Вычисляем средние гены
        genome_length = len(creatures[0].genome)
        avg_genes = [0.0] * genome_length
        for c in creatures:
            for i, gene in enumerate(c.genome):
                avg_genes[i] += gene
        avg_genes = [g / len(creatures) for g in avg_genes]
        
        # Фон
        hist_width = self.width - 100
        hist_height = 150
        hist_x = 50
        hist_y = self.histogram_y
        
        pygame.draw.rect(surface, (30, 30, 45), (hist_x, hist_y, hist_width, hist_height), border_radius=8)
        pygame.draw.rect(surface, (90, 90, 120), (hist_x, hist_y, hist_width, hist_height), 2, border_radius=8)
        
        title = self.font_subtitle.render("Средние значения генов", True, (220, 220, 220))
        surface.blit(title, (hist_x + 15, hist_y + 10))
        
        # ✅ БАЗОВАЯ ЛИНИЯ ПО ЦЕНТРУ — положительные вверх, отрицательные вниз
        baseline_y = hist_y + hist_height / 2  # = hist_y + 75
        
        # ✅ Максимальная высота столбца: половина окна минус отступы
        # hist_height/2 = 75, минус 25px под заголовок и 15px снизу = 35px макс
        max_bar_height = (hist_height / 2) - 25  # = 50px
        
        bar_width = (hist_width - 30) / genome_length
        max_val = max(abs(g) for g in avg_genes) if avg_genes else 1
        if max_val == 0:
            max_val = 1
        
        for i, gene in enumerate(avg_genes):
            bar_height = (abs(gene) / max_val) * max_bar_height
            x = hist_x + 15 + i * bar_width
            
            if gene >= 0:
                # ✅ Растёт ВВЕРХ от базовой линии
                y = baseline_y - bar_height
            else:
                # ✅ Растёт ВНИЗ от базовой линии
                y = baseline_y
            
            color = (80, 200, 80) if gene >= 0 else (200, 80, 80)
            pygame.draw.rect(surface, color, (x + 2, int(y), int(bar_width - 4), int(bar_height)))
        
        # ✅ Нулевая линия (визуальный ориентир)
        pygame.draw.line(surface, (100, 100, 120), 
                        (hist_x + 10, int(baseline_y)), 
                        (hist_x + hist_width - 10, int(baseline_y)), 1)
        
        # Подпись оси
        label = self.font_small.render("Gen: 0", True, (130, 130, 130))
        surface.blit(label, (hist_x + 15, int(baseline_y) + 5))

    def _draw_stats_table(self, surface: pygame.Surface, fitness_history: list[float]) -> None:
        """Таблица последних поколений."""
        if not fitness_history:
            return
        
        # Заголовок таблицы
        table_title = self.font_subtitle.render("Последние поколения", True, (220, 220, 220))
        surface.blit(table_title, (50, self.table_y))
        
        # Заголовки столбцов
        headers = ["Поколение", "Лучший фитнес", "Средний фитнес"]
        for i, header in enumerate(headers):
            text = self.font_text.render(header, True, (180, 180, 180))
            surface.blit(text, (50 + i * 200, self.table_y + 30))
        
        # Данные (последние 8 поколений)
        recent = fitness_history[-8:] if len(fitness_history) > 8 else fitness_history
        start_gen = len(fitness_history) - len(recent)
        
        for i, fit in enumerate(recent):
            gen_num = start_gen + i + 1
            row_data = [str(gen_num), f"{fit:.2f}", f"{sum(recent)/len(recent):.2f}"]
            for j, val in enumerate(row_data):
                text = self.font_text.render(val, True, (200, 200, 200))
                surface.blit(text, (50 + j * 200, self.table_y + 55 + i * 25))

class PauseOverlay:
    """Экран паузы. Открывается по ESC во время игры."""
    def __init__(self, screen_width: float, screen_height: float):
        self.visible = False
        self.width = 320
        self.height = 240
        self.x = (screen_width - self.width) / 2
        self.y = (screen_height - self.height) / 2
        
        self.buttons = [
            {"text": "Продолжить", "action": "resume", "y": 30},
            {"text": "Статистика", "action": "stats", "y": 90},
            {"text": "Настройки", "action": "settings", "y": 150},
            {"text": "В главное меню", "action": "menu", "y": 210},
        ]
        self.hovered_index = -1
        self.font_title = pygame.font.SysFont("consolas", 24, bold=True)
        self.font_btn = pygame.font.SysFont("consolas", 18)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if not self.visible:
            return None
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered_index = -1
            for i, btn in enumerate(self.buttons):
                rect = pygame.Rect(self.x + 40, self.y + btn["y"], self.width - 80, 40)
                if rect.collidepoint(mx, my):
                    self.hovered_index = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for btn in self.buttons:
                rect = pygame.Rect(self.x + 40, self.y + btn["y"], self.width - 80, 40)
                if rect.collidepoint(mx, my):
                    return btn["action"]
        return None

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        
        # Затемнение фона
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Окно паузы
        pygame.draw.rect(surface, (20, 20, 30), (self.x, self.y, self.width, self.height), border_radius=10)
        pygame.draw.rect(surface, (90, 90, 110), (self.x, self.y, self.width, self.height), 2, border_radius=10)

        title = self.font_title.render("ПАУЗА", True, (240, 240, 240))
        surface.blit(title, (self.x + (self.width - title.get_width()) / 2, self.y + 10))

        for i, btn in enumerate(self.buttons):
            rect = pygame.Rect(self.x + 40, self.y + btn["y"], self.width - 80, 40)
            color = (60, 110, 60) if i == self.hovered_index else (30, 30, 40)
            pygame.draw.rect(surface, color, rect, border_radius=6)
            if i == self.hovered_index:
                pygame.draw.rect(surface, (80, 140, 80), rect, 2, border_radius=6)

            text = self.font_btn.render(btn["text"], True, (220, 220, 220))
            surface.blit(text, (rect.centerx - text.get_width() / 2,
                                rect.centery - text.get_height() / 2))