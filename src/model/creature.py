"""Модель существа.
Отвечает за координаты, энергию, смену состояний FSM и базовое движение.
Не импортирует pygame, работает только с числами и типами Python.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple
import config as cfg
import random
import math
from utils.math_helpers import distance_sq
from src.algorithms.perceptron import SimplePerceptron
from src.algorithms.astar import AStarPathfinder


class State(Enum):
    """Состояния конечного автомата существа."""
    WANDER = auto()     # Рандомное движение
    SEEK = auto()       # Активный поиск еды
    FLEE = auto()       # Избегание опасности / паника
    REPRODUCE = auto()  # Сытость


@dataclass
class Creature:
    """Сущность существа. Хранит физические параметры и текущее состояние."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    energy: float = 50.0
    age: float = 0.0
    radius: float = 6.0
    state: State = State.WANDER
    genome: list[float] = field(default_factory=lambda: [0.0] * 8)
    # Навигация по A*
    current_path: Optional[List[Tuple[float, float]]] = field(default=None, repr=False)
    path_index: int = 0
    # Ссылка на pathfinder для проверки препятствий во всех состояниях
    _pathfinder: Optional[AStarPathfinder] = field(default=None, repr=False)
    # Таймер для ограничения частоты пересчёта пути (оптимизация)
    _last_path_recalc: float = 0.0

    # Поле для перцептрона. repr=False скрывает объект мозга при отладке print()
    brain: Optional[SimplePerceptron] = field(default=None, repr=False)

    trail: list[tuple[float, float]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Инициализирует мозг из генома. Первые 7 генов → веса, последний → bias."""
        if self.brain is None:
            self.brain = SimplePerceptron(
                weights=self.genome[:-1],
                bias=self.genome[-1]
            )

    def update(
        self,
        dt: float,
        visible_food: List[Tuple[float, float, float]],
        pathfinder: Optional[AStarPathfinder] = None
    ) -> bool:
        """Обновляет параметры существа за кадр. Перцептрон управляет состоянием."""
        self.energy -= cfg.ENERGY_DECAY * dt
        if self.energy <= 0:
            return False

        # Обновляем ссылку на pathfinder (на случай если не была установлена)
        if pathfinder is not None:
            self._pathfinder = pathfinder

        # Подготовка сенсоров (входы перцептрона)
        food_signal = 1.0 if visible_food else 0.0
        energy_signal = max(0.0, min(1.0, self.energy / 50.0))
        sensors = [food_signal, energy_signal, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Запрос решения у перцептрона
        decision = self.brain.compute(sensors)

        if decision > 0.4:
            self.state = State.SEEK
        elif decision < -0.4:
            self.state = State.FLEE
        else:
            self.state = State.WANDER

        # Навигация
        if self.state == State.SEEK and visible_food and pathfinder:
            closest_food = min(visible_food, key=lambda f: distance_sq((self.x, self.y), (f[0], f[1])))
            dist_to_food = distance_sq((self.x, self.y), (closest_food[0], closest_food[1])) ** 0.5

            # Если еда близко (< 3 клеток), идём напрямую
            if dist_to_food < cfg.GRID_CELL_SIZE * 3:
                self._apply_steering(dt, closest_food[0], closest_food[1])
                self.current_path = None
                self.path_index = 0
            else:
                # Пересчитываем путь только если:
                # 1. Пути нет
                # 2. Путь закончился
                # 3. Прошло больше 1 секунды с последнего пересчёта
                should_recalculate = (
                    self.current_path is None or
                    self.path_index >= len(self.current_path) or
                    (self.age - self._last_path_recalc) > 1.0
                )

                if should_recalculate:
                    self.current_path = pathfinder.find_path(
                        self.x, self.y,
                        closest_food[0], closest_food[1]
                    )
                    self.path_index = 0
                    self._last_path_recalc = self.age

                # Двигаемся по пути
                if self.current_path and self.path_index < len(self.current_path):
                    target_x, target_y = self.current_path[self.path_index]
                    dist_to_waypoint = distance_sq((self.x, self.y), (target_x, target_y))
                    
                    # Порог достижения waypoint = полная клетка
                    if dist_to_waypoint < cfg.GRID_CELL_SIZE ** 2:
                        self.path_index += 1

                    if self.path_index < len(self.current_path):
                        self._apply_steering(dt, target_x, target_y)
                    else:
                        self._apply_steering(dt, closest_food[0], closest_food[1])
                        self.current_path = None
                else:
                    # Путь не найден → блуждаем
                    self._apply_wander(dt)
        else:
            # Не SEEK → обычное поведение с проверкой препятствий
            self._apply_movement(dt, visible_food)

        self._clamp_to_bounds()
        self.age += dt
        # Сохраняем позицию в след (максимум 20 точек)
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)
        return True

    def _check_obstacle_collision(self, new_x: float, new_y: float) -> bool:
        """
        Проверяет, есть ли препятствие на пути от текущей позиции к новой.
        Использует line sweep для надёжной проверки.
        Returns True если есть препятствие.
        """
        if self._pathfinder is None:
            return False

        # Проверяем несколько точек вдоль траектории (line sweep)
        steps = max(2, int(distance_sq((self.x, self.y), (new_x, new_y)) ** 0.5 / (cfg.GRID_CELL_SIZE / 2)))
        
        for i in range(steps + 1):
            t = i / steps if steps > 0 else 0
            check_x = self.x + (new_x - self.x) * t
            check_y = self.y + (new_y - self.y) * t
            grid_pos = self._pathfinder.world_to_grid(check_x, check_y)
            if grid_pos in self._pathfinder.obstacles:
                return True
        
        return False

    def _apply_movement(self, dt: float, visible_food: List[Tuple[float, float, float]]) -> None:
        """Применяет силы управления к скорости существа (Steering Behaviors)."""
        from src.algorithms import steering

        force_x, force_y = 0.0, 0.0

        if self.state == State.WANDER:
            force_x = random.uniform(-cfg.MAX_STEERING_FORCE, cfg.MAX_STEERING_FORCE)
            force_y = random.uniform(-cfg.MAX_STEERING_FORCE, cfg.MAX_STEERING_FORCE)

        elif self.state == State.FLEE:
            angle = random.uniform(0, math.pi * 2)
            force_x = math.cos(angle) * cfg.SEEK_SPEED
            force_y = math.sin(angle) * cfg.SEEK_SPEED

        elif self.state == State.REPRODUCE:
            force_x = random.uniform(-5.0, 5.0)
            force_y = random.uniform(-5.0, 5.0)

        # Ограничиваем силу
        force_len = (force_x ** 2 + force_y ** 2) ** 0.5
        if force_len > cfg.MAX_STEERING_FORCE:
            force_x = (force_x / force_len) * cfg.MAX_STEERING_FORCE
            force_y = (force_y / force_len) * cfg.MAX_STEERING_FORCE

        # Интегрируем силу в скорость
        self.vx += force_x * dt
        self.vy += force_y * dt

        # Ограничиваем максимальную скорость
        max_speed = 150.0
        current_speed = (self.vx ** 2 + self.vy ** 2) ** 0.5
        if current_speed > max_speed:
            self.vx = (self.vx / current_speed) * max_speed
            self.vy = (self.vy / current_speed) * max_speed

        # Вычисляем новую позицию
        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt

        # Проверяем препятствия с помощью line sweep
        if self._check_obstacle_collision(new_x, new_y):
            # Препятствие! Разворачиваемся
            self.vx = -self.vx + random.uniform(-20, 20)
            self.vy = -self.vy + random.uniform(-20, 20)
            # Не обновляем позицию
            return

        # Обновляем позицию
        self.x = new_x
        self.y = new_y

    def _clamp_to_bounds(self) -> None:
        """Удерживает существо в пределах игрового окна."""
        self.x = max(self.radius, min(self.x, cfg.SCREEN_WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, cfg.SCREEN_HEIGHT - self.radius))

    def get_render_data(self) -> dict:
        """Возвращает чистые данные для View."""
        return {
            "pos": (self.x, self.y),
            "radius": self.radius,
            "state": self.state.name,
            "energy": self.energy
        }

    def _apply_steering(self, dt: float, target_x: float, target_y: float) -> None:
        """Движение к конкретной точке (для A* waypoints)."""
        from src.algorithms import steering

        force_x, force_y = steering.seek(
            (self.x, self.y),
            (target_x, target_y),
            cfg.SEEK_SPEED,
            (self.vx, self.vy)
        )

        # Ограничиваем силу
        force_len = (force_x ** 2 + force_y ** 2) ** 0.5
        if force_len > cfg.MAX_STEERING_FORCE:
            force_x = (force_x / force_len) * cfg.MAX_STEERING_FORCE
            force_y = (force_y / force_len) * cfg.MAX_STEERING_FORCE

        # Применяем физику
        self.vx += force_x * dt
        self.vy += force_y * dt

        max_speed = 150.0
        current_speed = (self.vx ** 2 + self.vy ** 2) ** 0.5
        if current_speed > max_speed:
            self.vx = (self.vx / current_speed) * max_speed
            self.vy = (self.vy / current_speed) * max_speed

        # Вычисляем новую позицию
        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt

        # Проверяем препятствия
        if self._check_obstacle_collision(new_x, new_y):
            # Препятствие! Разворачиваемся
            self.vx = -self.vx + random.uniform(-20, 20)
            self.vy = -self.vy + random.uniform(-20, 20)
            return

        self.x = new_x
        self.y = new_y

    def _apply_wander(self, dt: float) -> None:
        """Случайное блуждание."""
        force_x = random.uniform(-cfg.MAX_STEERING_FORCE, cfg.MAX_STEERING_FORCE)
        force_y = random.uniform(-cfg.MAX_STEERING_FORCE, cfg.MAX_STEERING_FORCE)

        self.vx += force_x * dt
        self.vy += force_y * dt

        max_speed = 150.0
        current_speed = (self.vx ** 2 + self.vy ** 2) ** 0.5
        if current_speed > max_speed:
            self.vx = (self.vx / current_speed) * max_speed
            self.vy = (self.vy / current_speed) * max_speed

        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt

        # Проверяем препятствия
        if self._check_obstacle_collision(new_x, new_y):
            self.vx = -self.vx + random.uniform(-20, 20)
            self.vy = -self.vy + random.uniform(-20, 20)
            return

        self.x = new_x
        self.y = new_y