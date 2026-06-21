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
        self.grid = SpatialGrid(cell_size=50.0)
        self.obstacles: list[tuple[int, int]] = []
        self.evolution_timer = 0.0
        self.particles: list[dict] = []

        # создаём pathfinder (он нужен для спавна и Population)
        self.pathfinder = AStarPathfinder(
            grid_width=cfg.GRID_WIDTH,
            grid_height=cfg.GRID_HEIGHT,
            cell_size=cfg.GRID_CELL_SIZE
        )

        # спавним популяцию 
        self._spawn_initial_population()

        self.population_manager = Population(self.creatures, self.pathfinder)

    def spawn_obstacle_at(self, x: float, y: float) -> None:
        """Создаёт препятствие в указанных координатах (для A* и рендера)."""
        # Добавляем в навигационную сетку A*
        self.pathfinder.add_obstacle(x, y)
        
        # Сохраняем СЕТОЧНЫЕ координаты для рендера
        grid_pos = self.pathfinder.world_to_grid(x, y)
        if grid_pos not in self.obstacles:  # ← Проверка на дубликаты
            self.obstacles.append(grid_pos)

    def remove_obstacle(self, x: float, y: float) -> bool:
        """
        Удаляет препятствие в указанной точке (если оно есть).
        Теперь работает при клике в ЛЮБУЮ точку квадрата!
        """
        # Получаем клетку, куда кликнули
        grid_pos = self.pathfinder.world_to_grid(x, y)
        
        # Проверяем, есть ли препятствие в этой клетке
        if grid_pos not in self.obstacles:
            return False
        
        # 1. Удаляем из навигационной сетки A*
        self.pathfinder.remove_obstacle(
            grid_pos[0] * self.pathfinder.cell_size,
            grid_pos[1] * self.pathfinder.cell_size
        )
        
        # 2. Удаляем из списка для рендера (теперь это просто!)
        self.obstacles.remove(grid_pos)
        
        return True

    def get_obstacles(self) -> list[tuple[float, float]]:
        """Возвращает список препятствий для рендера."""
        return self.obstacles

    def update(self, dt: float) -> None:
        if random.random() < cfg.FOOD_SPAWN_RATE:
            self._spawn_food()

        # Очищаем и заполняем сетку
        self.grid.clear()
        
        # Вставляем еду
        for f in self.food:
            self.grid.insert(f, (f[0], f[1]))
        
        # Вставляем существ 
        for c in self.creatures:
            self.grid.insert(c, (c.x, c.y))

        # Теперь query_radius найдёт и еду, и существ
        alive_creatures = []
        for c in self.creatures:
            nearby = self.grid.query_radius((c.x, c.y), cfg.PERCEPTION_RADIUS)
            food_only = [item for item in nearby if isinstance(item, tuple) and len(item) == 3]
            nearby_creatures = [item for item in nearby if isinstance(item, Creature)]

            if c.update(dt, food_only, self.pathfinder, nearby_creatures):
                alive_creatures.append(c)
        self.creatures = alive_creatures

        self._check_eating()

        # Создание потомка (размножение)
        new_children = []  # Собираем потомков отдельно, чтобы не ломать итерацию
        for i, c1 in enumerate(self.creatures):
            if c1.state != State.REPRODUCE or c1.energy < 40:
                continue
            for c2 in self.creatures[i+1:]:
                if c2.state == State.REPRODUCE and c2.energy > 40:
                    if check_circle_collision((c1.x, c1.y), c1.radius, (c2.x, c2.y), c2.radius):
                        # Создаем потомка
                        child_genome = ga.crossover(c1.genome, c2.genome)
                        child_genome = ga.mutate(child_genome, cfg.MUTATION_RATE, cfg.MUTATION_STRENGTH)
                        child = Creature(
                            x=(c1.x + c2.x) / 2, 
                            y=(c1.y + c2.y) / 2, 
                            genome=child_genome
                        )
                        child._pathfinder = self.pathfinder
                        new_children.append(child)
                        c1.energy -= 20  # Родители тратят энергию
                        c2.energy -= 20
                        break  # Один потомок за раз
        
        # Добавляем всех потомков после цикла
        self.creatures.extend(new_children)

        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt * 2  # Затухание за 0.5 сек
        self.particles = [p for p in self.particles if p['life'] > 0]

        # Эволюция
        self.evolution_timer += dt
        if self.evolution_timer > cfg.GENERATION_TIME and len(self.creatures) > 0:
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
                        # Создаём частицы
                        for _ in range(5):
                            self.particles.append({
                                'x': fx, 'y': fy,
                                'vx': random.uniform(-30, 30),
                                'vy': random.uniform(-30, 30),
                                'life': 1.0,
                                'color': (100, 255, 100)
                            })
                        eaten_ids.add(id(item))
        self.food = [f for f in self.food if id(f) not in eaten_ids]

    def spawn_food_at(self, x: float, y: float) -> None:
        """Создаёт еду в указанных координатах. Вызывается из Controller."""
        self.food.append((x, y, 15.0))