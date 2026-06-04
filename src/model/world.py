"""Модель мира.
Управляет списком существ, отвечает за их начальный спавн, обновление и удаление погибших.
"""
import random
import config as cfg
from src.model.creature import Creature
from utils.collision import check_circle_collision
from src.algorithms.spatial_grid import SpatialGrid
from src.model.population import Population
from src.algorithms.astar import AStarPathfinder


class World:
    """Контейнер симуляции. Содержит все активные объекты."""
    def __init__(self):
        self.creatures: list[Creature] = []
        self.food: list[tuple[float, float, float]] = []
        self.grid = SpatialGrid(cell_size=50.0)
        self.obstacles: list[tuple[float, float]] = []
        self.population_manager = Population(self.creatures, self.pathfinder)
        self.evolution_timer = 0.0

        self._spawn_initial_population()

        # Инициализация A* навигации
        self.pathfinder = AStarPathfinder(
            grid_width=cfg.GRID_WIDTH,
            grid_height=cfg.GRID_HEIGHT,
            cell_size=cfg.GRID_CELL_SIZE
        )

        # Передаём pathfinder всем начальным существам
        for c in self.creatures:
            c._pathfinder = self.pathfinder

    def spawn_obstacle_at(self, x: float, y: float) -> None:
        """Создаёт препятствие в указанных координатах (для A* и рендера)."""
        # 1. Добавляем в навигационную сетку A* (чтобы существа обходили)
        self.pathfinder.add_obstacle(x, y)

        # 2. Добавляем в список для визуализации
        self.obstacles.append((x, y))

    def remove_obstacle(self, x: float, y: float) -> None:
        """Удаляет препятствие."""
        self.pathfinder.remove_obstacle(x, y)
        # Удаляем из списка рендера
        self.obstacles = [(ox, oy) for ox, oy in self.obstacles if (ox, oy) != (x, y)]

    def get_obstacles(self) -> list[tuple[float, float]]:
        """Возвращает список препятствий для рендера."""
        return self.obstacles

    def update(self, dt: float) -> None:
        if random.random() < cfg.FOOD_SPAWN_RATE:
            self._spawn_food()

        self.grid.clear()
        for f in self.food:
            self.grid.insert(f, (f[0], f[1]))

        alive_creatures = []
        for c in self.creatures:
            nearby = self.grid.query_radius((c.x, c.y), cfg.PERCEPTION_RADIUS)
            food_only = [item for item in nearby if isinstance(item, tuple) and len(item) == 3]

            # Передаём pathfinder в update!
            if c.update(dt, food_only, self.pathfinder):
                alive_creatures.append(c)
        self.creatures = alive_creatures

        self._check_eating()

        # Эволюция
        self.evolution_timer += dt
        if self.evolution_timer > 15.0 and len(self.creatures) > 0:
            self.creatures = self.population_manager.next_generation()
            self.evolution_timer = 0.0

            hist = self.population_manager.best_fitness_history
            gen = self.population_manager.generation
            fit_str = f"{hist[-1]:.2f}" if hist else "N/A"
            print(f"[GEN {gen}] Fitness: {fit_str}")

    def _spawn_initial_population(self) -> None:
        """Создаёт стартовую популяцию, избегая препятствий."""
        margin = 50
        for _ in range(cfg.INIT_POP_SIZE):
            attempts = 0
            # Пытаемся найти свободное место (максимум 100 попыток)
            while attempts < 100:
                x = random.uniform(margin, cfg.SCREEN_WIDTH - margin)
                y = random.uniform(margin, cfg.SCREEN_HEIGHT - margin)
                grid_pos = self.pathfinder.world_to_grid(x, y)
                
                # Если клетка не в препятствиях — выходим из цикла
                if grid_pos not in self.pathfinder.obstacles:
                    break
                attempts += 1
            
            creature = Creature(x, y)
            creature._pathfinder = self.pathfinder
            self.creatures.append(creature)

    def get_creature_count(self) -> int:
        """Возвращает текущее количество живых существ для отладки и UI."""
        return len(self.creatures)

    def _spawn_food(self) -> None:
        """Создаёт один кусок еды в случайной позиции."""
        x = random.uniform(10, cfg.SCREEN_WIDTH - 10)
        y = random.uniform(10, cfg.SCREEN_HEIGHT - 10)
        # Кортеж: (x, y, энергетическая ценность)
        self.food.append((x, y, 15.0))

    def _check_eating(self) -> None:
        eaten_ids = set()
        for c in self.creatures:
            # Запрос объектов в радиусе существа + радиус еды
            nearby = self.grid.query_radius((c.x, c.y), c.radius + 4.0)
            for item in nearby:
                if isinstance(item, tuple) and len(item) == 3:
                    fx, fy, fe = item
                    if check_circle_collision((c.x, c.y), c.radius, (fx, fy), 4.0):
                        c.energy += fe
                        eaten_ids.add(id(item))
        self.food = [f for f in self.food if id(f) not in eaten_ids]

    def spawn_food_at(self, x: float, y: float) -> None:
        """Создаёт еду в указанных координатах. Вызывается из Controller."""
        self.food.append((x, y, 15.0))