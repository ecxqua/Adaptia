# src/controller/game_loop.py
import pygame
import config as cfg

from src.model.world import World
from src.view.renderer import Renderer
from enum import Enum, auto
from src.view.ui import UIManager, SettingsPanel

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

        self.mode = GameMode.RUNNING          # Стартовый режим
        self.speed_multiplier = 1.0           # Множитель времени

        self.ui = UIManager(self.screen)

        self.settings_panel = SettingsPanel(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT) # Добавили

        self.ui_manager = UIManager(self.screen)
        self.settings_panel = SettingsPanel(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
    
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.settings_panel.handle_event(event):
                continue  # Если ползунок "съел" клик, дальше не обрабатываем   
                     
            # Обработка клавиш
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.mode = GameMode.PAUSED if self.mode == GameMode.RUNNING else GameMode.RUNNING
                elif self.mode == GameMode.RUNNING:
                    if event.key == pygame.K_1:
                        self.speed_multiplier = 1.0
                    elif event.key == pygame.K_2:
                        self.speed_multiplier = 2.0
                    elif event.key == pygame.K_5:
                        self.speed_multiplier = 5.0
                    elif event.key == pygame.K_s:
                        self.settings_panel.toggle() # Открыть/закрыть настройки

            # Обработка мыши 
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if event.button == 1:  # ЛКМ = еда
                    self.world.spawn_food_at(x, y)
                elif event.button == 3:  # ПКМ = препятствие
                    self.world.spawn_obstacle_at(x, y)

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
        self.screen.fill((20, 20, 25)) # Фон
        
        self.renderer.draw_world(self.world) # Мир
        
        # HUD (счетчики)
        self.ui_manager.draw_hud(
            self.world.get_creature_count(),
            self.mode.name,
            self.speed_multiplier
        )
        
        # Панель настроек (рисуется поверх всего)
        self.settings_panel.draw(self.screen)
        
        pygame.display.flip()