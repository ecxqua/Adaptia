# src/controller/game_loop.py
import pygame
import config as cfg
import csv
import os
from src.model.world import World
from src.view.renderer import Renderer
from enum import Enum, auto
from src.view.ui import UIManager, SettingsPanel, MainMenu, FitnessGraph, GeneHistogram, StatsScreen, PauseOverlay
from utils.save_system import save_game, load_game

class GameMode(Enum):
    MENU = auto()
    RUNNING = auto()
    PAUSED = auto()
    SETTINGS = auto()
    STATS = auto() 

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
        
        pygame.mixer.init() # музыка

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

        self.mode = GameMode.MENU  # Стартуем с меню
        self.main_menu = MainMenu(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.pause_overlay = PauseOverlay(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT) 

        # Графики статистики
        self.fitness_graph = FitnessGraph(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.gene_histogram = GeneHistogram(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        self.stats_screen = StatsScreen(cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)

        # ЗАГРУЗКА МУЗЫКИ (с защитой от падения, если файла нет)
        self.is_music_playing = True
        try:
            pygame.mixer.music.load('music.mp3')  # Убедись, что файл в корне проекта!
            pygame.mixer.music.set_volume(0.3)    # Громкость 30%
            pygame.mixer.music.play(-1)           # -1 означает бесконечный цикл
            print("[AUDIO] Музыка успешно загружена и запущена.")
        except Exception as e:
            print(f"[WARN] Не удалось загрузить музыку: {e}")
    
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
                continue

            # 1. Главное меню (старт игры)
            if self.mode == GameMode.MENU:
                action = self.main_menu.handle_event(event)
                if action == "start":
                    self.mode = GameMode.RUNNING
                    self.main_menu.visible = False
                elif action == "settings":
                    self.settings_panel.toggle()
                elif action == "stats":
                    self.mode = GameMode.STATS
                    self.main_menu.visible = False
                elif action == "exit":
                    self.running = False
                continue

            # 2. Экран паузы (во время игры)
            if self.mode == GameMode.PAUSED:
                action = self.pause_overlay.handle_event(event)
                if action == "resume":
                    self.mode = GameMode.RUNNING
                    self.pause_overlay.visible = False
                elif action == "stats":
                    self.mode = GameMode.STATS
                    self.pause_overlay.visible = False
                elif action == "settings":
                    self.settings_panel.toggle()
                elif action == "menu":
                    self.mode = GameMode.MENU
                    self.main_menu.visible = True
                    self.pause_overlay.visible = False
                continue

            # 3. Панель настроек (работает всегда, кроме MENU)
            if self.settings_panel.handle_event(event):
                continue

            # 4. Горячие клавиши
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.mode == GameMode.RUNNING:
                        self.mode = GameMode.PAUSED
                        self.pause_overlay.visible = True
                    elif self.mode == GameMode.PAUSED:
                        self.mode = GameMode.RUNNING
                        self.pause_overlay.visible = False
                    elif self.mode == GameMode.STATS:
                        self.mode = GameMode.PAUSED
                        self.pause_overlay.visible = True
                
                elif event.key == pygame.K_m:  # звук вкл/выкл
                    self.is_music_playing = not self.is_music_playing
                    if self.is_music_playing:
                        pygame.mixer.music.unpause()
                        print("[AUDIO] Музыка включена")
                    else:
                        pygame.mixer.music.pause()
                        print("[AUDIO] Музыка выключена")
                
                elif event.key == pygame.K_s:
                    self.settings_panel.toggle()                
                elif event.key == pygame.K_F5:
                    save_game(self.world)
                elif event.key == pygame.K_F9:
                    load_game(self.world)                        
                elif event.key == pygame.K_c:
                    self._export_stats()
                elif event.key == pygame.K_g:
                    self.fitness_graph.visible = not self.fitness_graph.visible
                    self.gene_histogram.visible = not self.gene_histogram.visible
                
                elif self.mode == GameMode.RUNNING:
                    if event.key == pygame.K_1: self.speed_multiplier = 1.0
                    elif event.key == pygame.K_2: self.speed_multiplier = 2.0
                    elif event.key == pygame.K_5: self.speed_multiplier = 5.0

            # 5. Мышь (спавн еды/препятствий)
            elif event.type == pygame.MOUSEBUTTONDOWN and self.mode == GameMode.RUNNING:
                x, y = event.pos
                if event.button == 1:
                    self.world.spawn_food_at(x, y)
                elif event.button == 3:
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
        self.screen.fill((20, 20, 25))
        
        self.renderer.draw_world(self.world)
        
        # HUD
        self.ui_manager.draw_hud(self.world.get_creature_count(), self.mode.name, self.speed_multiplier)
        
        # Мини-графики в углу (только в RUNNING/PAUSED)
        if self.mode in (GameMode.RUNNING, GameMode.PAUSED) and self.world.population_manager.best_fitness_history:
            self.fitness_graph.draw(self.screen, self.world.population_manager.best_fitness_history, self.world.population_manager.generation)
            self.gene_histogram.draw(self.screen, self.world.creatures)
        
        # Полноэкранный режим статистики
        if self.mode == GameMode.STATS:
            self.stats_screen.draw(self.screen, self.world.population_manager.best_fitness_history, self.world.population_manager.generation, self.world.creatures)
        
        
        # Главное меню
        if self.mode == GameMode.MENU:
            self.main_menu.draw(self.screen)
            
        # Экран паузы
        if self.mode == GameMode.PAUSED:
            self.pause_overlay.draw(self.screen)
        
        self.settings_panel.draw(self.screen)

        pygame.display.flip()
    
    def _export_stats(self) -> None:
        """Экспортирует статистику в CSV файл."""
        filename = f"stats_gen{self.world.population_manager.generation}.csv"
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Поколение", "Лучший фитнес", "Мутация", "Плотность еды", "Расход энергии"])
                
                history = self.world.population_manager.best_fitness_history
                for i, fit in enumerate(history):
                    writer.writerow([
                        i + 1,
                        f"{fit:.2f}",
                        cfg.MUTATION_RATE,
                        cfg.FOOD_SPAWN_RATE,
                        cfg.ENERGY_DECAY
                    ])
            
            print(f"[INFO] Статистика экспортирована в {filename}")
        except Exception as e:
            print(f"[ERROR] Не удалось экспортировать статистику: {e}")