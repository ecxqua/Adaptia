"""Модель мира.
Управляет списком существ, отвечает за их начальный спавн, обновление и удаление погибших.
"""
import random
import config as cfg
from src.model.creature import Creature, State
from utils.collision import check_circle_collision
from src.algorithms.spatial_grid import SpatialGrid
from src.model.population import Population
from src.algorithms.astar import AStarPathfinder
from src.algorithms import ga


class World:
    """Контейнер симуляции. Содержит все активные объекты."""
    
    def __init__(self):
        self.creatures: list[Creature] = []
        self.food: list[tuple[float, float, float]] = []
        self.grid = SpatialGrid(cell_size=cfg.GRID_CELL_SIZE)
        self.obstacles: list[tuple[int, int]] = []  # Сеточные координаты для рендера
        self.evolution_timer = 0.0
        self.particles: list[dict] = []

        # Создаём pathfinder (нужен для спавна и Population)
        self.pathfinder = AStarPathfinder(
            grid_width=cfg.GRID_WIDTH,
            grid_height=cfg.GRID_HEIGHT,
            cell_size=cfg.GRID_CELL_SIZE
        )

        # Спавним популяцию
        self._spawn_initial_population()
        self.population_manager = Population(self.creatures, self.pathfinder)

    # =========================================================================
    # УПРАВЛЕНИЕ ПРЕПЯТСТВИЯМИ
    # =========================================================================

    def spawn_obstacle_at(self, x: float, y: float) -> None:
        """Создаёт препятствие в указанных координатах (для A* и рендера)."""
        # Добавляем в навигационную сетку A*
        self.pathfinder.add_obstacle(x, y)
        
        # Сохраняем сеточные координаты для рендера (защита от дубликатов)
        grid_pos = self.pathfinder.world_to_grid(x, y)
        if grid_pos not in self.obstacles:
            self.obstacles.append(grid_pos)

    def remove_obstacle(self, x: float, y: float) -> bool:
        """
        Удаляет препятствие в указанной точке (если оно есть).
        Работает при клике в ЛЮБУЮ точку квадрата 50×50.
        """
        grid_pos = self.pathfinder.world_to_grid(x, y)
        
        if grid_pos not in self.obstacles:
            return False
        
        # Удаляем из навигационной сетки A* (передаём центр клетки для консистентности)
        center_x = grid_pos[0] * self.pathfinder.cell_size + self.pathfinder.cell_size / 2
        center_y = grid_pos[1] * self.pathfinder.cell_size + self.pathfinder.cell_size / 2
        self.pathfinder.remove_obstacle(center_x, center_y)
        
        # Удаляем из списка для рендера
        self.obstacles.remove(grid_pos)
        
        # Визуальная обратная связь — серые частицы
        world_x = grid_pos[0] * self.pathfinder.cell_size + self.pathfinder.cell_size / 2
        world_y = grid_pos[1] * self.pathfinder.cell_size + self.pathfinder.cell_size / 2
        for _ in range(8):
            self.particles.append({
                'x': world_x, 'y': world_y,
                'vx': random.uniform(-50, 50),
                'vy': random.uniform(-50, 50),
                'life': 1.0,
                'color': (200, 200, 200)
            })
        
        return True

    def get_obstacles(self) -> list[tuple[int, int]]:
        """Возвращает список препятствий (сеточные координаты) для рендера."""
        return self.obstacles

    # =========================================================================
    # ГЛАВНЫЙ ЦИКЛ ОБНОВЛЕНИЯ
    # =========================================================================

    def update(self, dt: float) -> None:
        """Обновляет состояние мира за один кадр."""
        # 1. Спавн еды
        if random.random() < cfg.FOOD_SPAWN_RATE:
            self._spawn_food()

        # 2. Пересборка Uniform Grid (объекты двигаются!)
        self.grid.clear()
        for f in self.food:
            self.grid.insert(f, (f[0], f[1]))
        for c in self.creatures:
            self.grid.insert(c, (c.x, c.y))

        # 3. Обновление существ
        alive_creatures = []
        for c in self.creatures:
            nearby = self.grid.query_radius((c.x, c.y), cfg.PERCEPTION_RADIUS)
            food_only = [item for item in nearby if isinstance(item, tuple) and len(item) == 3]
            nearby_creatures = [item for item in nearby if isinstance(item, Creature)]

            if c.update(dt, food_only, self.pathfinder, nearby_creatures):
                alive_creatures.append(c)
        self.creatures = alive_creatures

        # 4. Проверка поедания еды
        self._check_eating()

        # 5. Размножение (создание потомков)
        self._handle_reproduction()

        # 6. Обновление частиц
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt * 2  # Затухание за 0.5 сек
        self.particles = [p for p in self.particles if p['life'] > 0]

        # 7. Эволюция (раз в GENERATION_TIME секунд)
        self.evolution_timer += dt
        if self.evolution_timer > cfg.GENERATION_TIME and len(self.creatures) > 0:
            self.creatures = self.population_manager.next_generation()
            self.evolution_timer = 0.0

            hist = self.population_manager.best_fitness_history
            gen = self.population_manager.generation
            fit_str = f"{hist[-1]:.2f}" if hist else "N/A"
            print(f"[GEN {gen}] Fitness: {fit_str}")

    # =========================================================================
    # РАЗМНОЖЕНИЕ
    # =========================================================================

    def _handle_reproduction(self) -> None:
        """Создаёт потомков от пар существ в состоянии REPRODUCE."""
        new_children = []
        
        for i, c1 in enumerate(self.creatures):
            # Родитель должен быть в состоянии REPRODUCE с энергией > 40
            if c1.state != State.REPRODUCE or c1.energy < cfg.REPRODUCE_MIN_ENERGY:
                continue
            
            # Ищем партнёра среди оставшихся существ
            for c2 in self.creatures[i + 1:]:
                if c2.state == State.REPRODUCE and c2.energy > cfg.REPRODUCE_MIN_ENERGY:
                    # Проверяем столкновение (Circle-Circle)
                    if check_circle_collision((c1.x, c1.y), c1.radius, (c2.x, c2.y), c2.radius):
                        # Создаём потомка с генами от родителей
                        child_genome = ga.crossover(c1.genome, c2.genome)
                        child_genome = ga.mutate(child_genome, cfg.MUTATION_RATE, cfg.MUTATION_STRENGTH)
                        
                        child = Creature(
                            x=(c1.x + c2.x) / 2,
                            y=(c1.y + c2.y) / 2,
                            genome=child_genome
                        )
                        child._pathfinder = self.pathfinder
                        new_children.append(child)
                        
                        # Родители тратят энергию
                        c1.energy -= cfg.REPRODUCE_COST
                        c2.energy -= cfg.REPRODUCE_COST
                        
                        # Зелёные частицы при размножении
                        for _ in range(10):
                            self.particles.append({
                                'x': child.x, 'y': child.y,
                                'vx': random.uniform(-40, 40),
                                'vy': random.uniform(-40, 40),
                                'life': 1.5,
                                'color': (100, 255, 150)
                            })
                        
                        break  # Один потомок за раз
        
        # Добавляем всех потомков после цикла (не ломаем итерацию)
        self.creatures.extend(new_children)

    # =========================================================================
    # СПАВН
    # =========================================================================

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

    def _spawn_food(self) -> None:
        """Создаёт один кусок еды в случайной позиции."""
        x = random.uniform(10, cfg.SCREEN_WIDTH - 10)
        y = random.uniform(10, cfg.SCREEN_HEIGHT - 10)
        # Кортеж: (x, y, энергетическая ценность)
        self.food.append((x, y, cfg.FOOD_ENERGY))

    def spawn_food_at(self, x: float, y: float) -> None:
        """Создаёт еду в указанных координатах. Вызывается из Controller."""
        self.food.append((x, y, cfg.FOOD_ENERGY))

    # =========================================================================
    # ПОЕДАНИЕ ЕДЫ
    # =========================================================================

    def _check_eating(self) -> None:
        """Проверяет, съели ли существа еду (Uniform Grid + Circle-Circle)."""
        # Используем индексы вместо id() для надёжности
        eaten_indices = set()
        
        for c in self.creatures:
            # Запрос объектов в радиусе существа + радиус еды
            nearby = self.grid.query_radius((c.x, c.y), c.radius + cfg.FOOD_RADIUS)
            
            for item in nearby:
                if isinstance(item, tuple) and len(item) == 3:
                    fx, fy, fe = item
                    # Точная проверка столкновения
                    if check_circle_collision((c.x, c.y), c.radius, (fx, fy), cfg.FOOD_RADIUS):
                        c.energy += fe
                        
                        # Зелёные частицы при поедании
                        for _ in range(5):
                            self.particles.append({
                                'x': fx, 'y': fy,
                                'vx': random.uniform(-30, 30),
                                'vy': random.uniform(-30, 30),
                                'life': 1.0,
                                'color': (100, 255, 100)
                            })
                        
                        # Находим индекс еды в self.food
                        try:
                            idx = self.food.index(item)
                            eaten_indices.add(idx)
                        except ValueError:
                            pass  # Еда уже удалена
        
        # Удаляем съеденную еду (в обратном порядке, чтобы индексы не сдвигались)
        for idx in sorted(eaten_indices, reverse=True):
            self.food.pop(idx)

    # =========================================================================
    # УТИЛИТЫ
    # =========================================================================

    def get_creature_count(self) -> int:
        """Возвращает текущее количество живых существ для отладки и UI."""
        return len(self.creatures)