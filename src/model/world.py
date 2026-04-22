# src/model/world.py
"""Модель мира.
Управляет списком существ, отвечает за их начальный спавн, обновление и удаление погибших.
"""
import random
import config as cfg
from src.model.creature import Creature
from utils.collision import check_circle_collision

class World:
    """Контейнер симуляции. Содержит все активные объекты."""
    def __init__(self):
        self.creatures: list[Creature] = []
        self.food: list[tuple[float, float, float]] = []
        self._spawn_initial_population()

    def update(self, dt: float) -> None:
        """Обновляет всех существ за кадр. Погибшие удаляются из списка."""
        # 1. Спавн еды (если повезло по вероятности)
        if random.random() < cfg.FOOD_SPAWN_RATE:
            self._spawn_food()

        # 2. Обновление существ с передачей списка еды
        # ВАЖНО: используем явный цикл, чтобы передать visible_food вторым аргументом
        alive_creatures = []
        for c in self.creatures:
            nearby_food = self.food  # Пока передаём весь список еды
            # Вызываем update с ДВУМЯ аргументами: dt и visible_food
            if c.update(dt, nearby_food):
                alive_creatures.append(c)
        self.creatures = alive_creatures

        # 3. Проверка поедания (существа восстанавливают энергию)
        self._check_eating()

    def _spawn_initial_population(self) -> None:
        """Создаёт стартовую популяцию в случайных позициях с отступом от краёв."""
        margin = 50
        for _ in range(cfg.INIT_POP_SIZE):
            x = random.uniform(margin, cfg.SCREEN_WIDTH - margin)
            y = random.uniform(margin, cfg.SCREEN_HEIGHT - margin)
            self.creatures.append(Creature(x, y))

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
        """Проверяет, съели ли существа еду. Восстанавливает энергию, удаляет съеденное."""
        eaten_ids = set()  # Храним id съеденной еды для безопасного удаления
        
        for c in self.creatures:
            for f in self.food:
                # f — это кортеж (x, y, energy_value)
                food_x, food_y, food_energy = f
                # Проверяем коллизию: круг существа и круг еды (радиус еды = 4.0)
                if check_circle_collision((c.x, c.y), c.radius, (food_x, food_y), 4.0):
                    c.energy += food_energy  # Восстанавливаем энергию
                    eaten_ids.add(id(f))      # Помечаем еду как съеденную
        
        # Удаляем съеденную еду после полного прохода (безопасно!)
        self.food = [f for f in self.food if id(f) not in eaten_ids]
    