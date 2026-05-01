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
from src.algorithms.perceptron import SimplePerceptron  # ← Путь к твоему перцептрону


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
    
    # Поле для перцептрона. repr=False скрывает объект мозга при отладке print()
    brain: Optional[SimplePerceptron] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Инициализирует мозг из генома. Первые 7 генов → веса, последний → bias."""
        if self.brain is None:
            self.brain = SimplePerceptron(
                weights=self.genome[:-1], 
                bias=self.genome[-1]
            )

    def update(self, dt: float, visible_food: List[Tuple[float, float, float]]) -> bool:
        """Обновляет параметры существа за кадр. Перцептрон управляет состоянием."""
        self.energy -= cfg.ENERGY_DECAY * dt
        if self.energy <= 0:
            return False

        # Подготовка сенсоров (входы перцептрона)
        # Нормализация к [0, 1] стабилизирует работу tanh и ускоряет эволюцию
        food_signal = 1.0 if visible_food else 0.0
        energy_signal = max(0.0, min(1.0, self.energy / 50.0))
        # Дополняем до 7 входов под размер genome[:-1]
        sensors = [food_signal, energy_signal, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Запрос решения у перцептрона
        decision = self.brain.compute(sensors)  # Возвращает float ∈ [-1, 1]

        if decision > 0.4:
            self.state = State.SEEK
        elif decision < -0.4:
            self.state = State.FLEE
        else:
            self.state = State.WANDER

        # Применение сил и физика (steering-логика остаётся в _apply_movement)
        self._apply_movement(dt, visible_food)
        self._clamp_to_bounds()
        self.age += dt
        return True

    # теперь состоянием управляет перцептрон!

    def _apply_movement(self, dt: float, visible_food: List[Tuple[float, float, float]]) -> None:
        """Применяет силы управления к скорости существа (Steering Behaviors)."""
        from src.algorithms import steering

        force_x, force_y = 0.0, 0.0

        if self.state == State.SEEK and visible_food:
            closest_food_pos = None
            min_dist = float('inf')
            for fx, fy, _ in visible_food:
                dist_sq = (self.x - fx) ** 2 + (self.y - fy) ** 2
                if dist_sq < min_dist:
                    min_dist = dist_sq
                    closest_food_pos = (fx, fy)

            if closest_food_pos is not None:
                fx, fy = steering.seek(
                    (self.x, self.y), closest_food_pos, cfg.SEEK_SPEED, (self.vx, self.vy)
                )
                force_x += fx
                force_y += fy

        elif self.state == State.WANDER:
            force_x = random.uniform(-cfg.MAX_STEERING_FORCE, cfg.MAX_STEERING_FORCE)
            force_y = random.uniform(-cfg.MAX_STEERING_FORCE, cfg.MAX_STEERING_FORCE)

        elif self.state == State.FLEE:
            angle = random.uniform(0, math.pi * 2)
            force_x = math.cos(angle) * cfg.SEEK_SPEED
            force_y = math.sin(angle) * cfg.SEEK_SPEED

        elif self.state == State.REPRODUCE:
            force_x = random.uniform(-5.0, 5.0)
            force_y = random.uniform(-5.0, 5.0)

        # Ограничиваем силу поворота/ускорения
        force_len = (force_x ** 2 + force_y ** 2) ** 0.5
        if force_len > cfg.MAX_STEERING_FORCE:
            force_x = (force_x / force_len) * cfg.MAX_STEERING_FORCE
            force_y = (force_y / force_len) * cfg.MAX_STEERING_FORCE

        # Интегрируем силу в скорость (физика: v += a * dt)
        self.vx += force_x * dt
        self.vy += force_y * dt

        # Ограничиваем максимальную скорость
        max_speed = 150.0
        current_speed = (self.vx ** 2 + self.vy ** 2) ** 0.5
        if current_speed > max_speed:
            self.vx = (self.vx / current_speed) * max_speed
            self.vy = (self.vy / current_speed) * max_speed

        # Обновляем позицию
        self.x += self.vx * dt
        self.y += self.vy * dt

    def _clamp_to_bounds(self) -> None:
        """Удерживает существо в пределах игрового окна."""
        self.x = max(self.radius, min(self.x, cfg.SCREEN_WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, cfg.SCREEN_HEIGHT - self.radius))

    def get_render_data(self) -> dict:
        """Возвращает чистые данные для View. Модель не должна знать про pygame.draw."""
        return {
            "pos": (self.x, self.y),
            "radius": self.radius,
            "state": self.state.name,
            "energy": self.energy
        }