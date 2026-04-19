"""Модель существа.
Отвечает за координаты, энергию, смену состояний FSM и базовое движение.
Не импортирует pygame, работает только с числами и типами Python.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
import config as cfg
import random
from utils.math_helpers import distance_sq

class State(Enum):
    """Состояния конечного автомата существа."""
    WANDER = auto() # Рандомное движение
    SEEK = auto() # Активный поиск
    FLEE = auto() # Паника/поиск еды
    REPRODUCE = auto() # Сытость

@dataclass
class Creature:
    """Сущность существа. Хранит физические параметры и текущее состояние."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    energy: float = 50.0
    radius: float = 6.0
    state: State = State.WANDER
    # Гены будут использоваться позже для перцептрона и ген. алг-ма.
    genome: list[float] = field(default_factory=lambda: [0.0] * 8)

    def update(self, dt: float, visible_food: list[tuple[float, float, float]]) -> bool:
        """Обновляет параметры существа за кадр. Возвращает False, если энергия <= 0."""
        self.energy -= cfg.ENERGY_DECAY * dt
        if self.energy <= 0:
            return False

        self._update_state()
        self._apply_movement(dt, visible_food)  # ← передаём visible_food
        self._clamp_to_bounds()
        return True

    def _update_state(self) -> None:
        """Переключает состояние FSM в зависимости от уровня энергии."""
        if self.energy < 15.0:
            # Критически мало энергии — пытаемся убежать/искать еду срочно
            self.state = State.FLEE
        elif self.energy > 40.0:
            # Много энергии — можно подумать о размножении
            self.state = State.REPRODUCE
        elif self.energy > 30.0:
            # Средняя энергия — активно ищем еду
            self.state = State.SEEK
        else:
            # Нормальное состояние 15-30 — спокойное блуждание
            self.state = State.WANDER

    def _apply_movement(self, dt: float, visible_food: list[tuple[float, float, float]]) -> None:
        """Применяет силы управления к скорости существа (Steering Behaviors)."""
        from src.algorithms import steering

        force_x, force_y = 0.0, 0.0

        # Рассчитываем силу в зависимости от состояния FSM
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
            # Паника: резкое ускорение в случайном направлении
            angle = random.uniform(0, math.pi * 2)
            force_x = math.cos(angle) * cfg.SEEK_SPEED
            force_y = math.sin(angle) * cfg.SEEK_SPEED

        elif self.state == State.REPRODUCE:
            force_x = random.uniform(-5.0, 5.0)
            force_y = random.uniform(-5.0, 5.0)

        # Ограничиваем силу поворота/ускорения (MAX_STEERING_FORCE)
        force_len = (force_x ** 2 + force_y ** 2) ** 0.5
        if force_len > cfg.MAX_STEERING_FORCE:
            force_x = (force_x / force_len) * cfg.MAX_STEERING_FORCE
            force_y = (force_y / force_len) * cfg.MAX_STEERING_FORCE

        # Интегрируем силу в скорость (физика: v += a * dt)
        self.vx += force_x * dt
        self.vy += force_y * dt

        # Ограничиваем максимальную скорость (не зависит от силы)
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