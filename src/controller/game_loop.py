# src/controller/game_loop.py
import pygame
import config as cfg

from src.model.world import World
from src.view.renderer import Renderer
from enum import Enum, auto

class GameMode(Enum):
    MENU = auto()
    RUNNING = auto()
    PAUSED = auto()
    SETTINGS = auto()

class GameLoop:
    """Контроллер игрового цикла.
    
    Инициализирует pygame, создаёт экземпляры мира и рендерера,
    запускает основной цикл с фиксированным FPS.
    """
    
    def __init__(self) -> None:
        """Инициализирует pygame, окно, часы и компоненты MVC."""
        pygame.init()
        # Размер окна берётся из config.py для соблюдения DRY.
        self.screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT))
        pygame.display.set_caption("Adaptia")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Модель и View создаются отдельно. GameLoop только оркестрирует их.
        self.world = World()
        self.renderer = Renderer(self.screen)
    
    def run(self) -> None:
        """Запускает основной игровой цикл.
        
        Цикл работает д тех пор, пока self.running == True.
        Каждый кадр: обработка событий → обновление логики → отрисовка.
        """
        while self.running:
            # dt передаётся в секундах для физической корректности
            # независимо от FPS.
            dt = self.clock.tick(cfg.FPS) / 1000.0
            
            self._handle_events()
            self._update(dt)
            self._render()
            
            
        pygame.quit()

    def _handle_events(self) -> None:
        """Обрабатывает события pygame (закрытие окна, ввод клавиш)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            # TODO: Добавить обработку ESC (пауза) и цифр 1/2/5 (ускорение)
            # Обработка ввода вынесена в отдельный метод для SRP (Single Responsibility Principle).

    def _update(self, dt: float) -> None:
        """Обновляет состояние мира на один кадр.
        
        Args:
            dt: Дельта времени в секундах с предыдущего кадра.
        """
        # Делегируем обновление модели. Controller не должен знать,
        # как именно обновляются существа, еда или препятствия.
        if self.mode != GameMode.RUNNING:
            return  # Пауза/меню: логика не обновляется
        effective_dt = dt * self.speed_multiplier
        self.world.update(effective_dt)

    def _render(self) -> None:
        """Отрисовывает текущее состояние мира на экран."""
        # Очистка экрана перед отрисовкой предотвращает артефакты.
        # Цвет фона (20, 20, 25) соответствует минималистичному стилю ТЗ.
        self.screen.fill((20, 20, 25))
        self.renderer.draw_world(self.world)
        pygame.display.flip()