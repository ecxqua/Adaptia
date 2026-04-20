"""Модель мира.
Управляет списком существ, еды и препятствий. Отвечает за обновление логики,
спавн ресурсов и проверку взаимодействий через Uniform Grid.
"""
import random
import config as cfg
from src.model.creature import Creature
from src.algorithms.spatial_grid import SpatialGrid
from utils.collision import check_circle_collision

class World:
    """Контейнер симуляции. Содержит все активные объекты и пространственную сетку."""
    def __init__(self):
        self.creatures: list[Creature] = []
        self.food: list[tuple[float, float, float]] = []  # x, y, energy_value
        self.grid = SpatialGrid(cell_size=50.0)
        self._spawn_initial_population()

    def update(self, dt: float) -> None:
        """Обновляет всех существ за кадр. Погибшие удаляются из списка."""
        alive_creatures = [c for c in self.creatures if c.update(dt)]
        self.creatures = alive_creatures

        # Заполняем сетку для быстрых запросов (существа + еда)
        self.grid.clear()
        for c in self.creatures:
            self.grid.insert(c, (c.x, c.y))
        for f in self.food:
            self.grid.insert(f, (f[0], f[1]))

        self._check_eating()

        if random.random() < cfg.FOOD_SPAWN_RATE:
            self._spawn_food()

    def _spawn_initial_population(self) -> None:
        margin = 50
        for _ in range(cfg.INIT_POP_SIZE):
            x = random.uniform(margin, cfg.SCREEN_WIDTH - margin)
            y = random.uniform(margin, cfg.SCREEN_HEIGHT - margin)
            self.creatures.append(Creature(x, y))

    def _spawn_food(self) -> None:
        x = random.uniform(10, cfg.SCREEN_WIDTH - 10)
        y = random.uniform(10, cfg.SCREEN_HEIGHT - 10)
        self.food.append((x, y, 15.0))

    def _check_eating(self) -> None:
        """Проверяет поедание еды и восстанавливает энергию существам."""
        eaten_ids = set()
        for c in self.creatures:
            nearby_food = self.grid.query_radius((c.x, c.y), c.radius + 5.0)
            for f in nearby_food:
                if isinstance(f, tuple) and len(f) == 3:
                    if check_circle_collision((c.x, c.y), c.radius, (f[0], f[1]), 4.0):
                        c.energy += f[2]
                        eaten_ids.add(id(f))
        self.food = [f for f in self.food if id(f) not in eaten_ids]

    def get_creature_count(self) -> int:
        return len(self.creatures)