"""Модель существа.
Отвечает за координаты, энергию, смену состояний FSM и базовое движение.
Не импортирует pygame, работает только с числами и типами Python.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
import config as cfg
import random

class State(Enum):
    """Состояния конечного автомата существа."""
    WANDER = auto()
    SEEK = auto()
    FLEE = auto()
    REPRODUCE = auto()

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

    def update(self, dt: float) -> bool:
        """Обновляет параметры существа за кадр. Возвращает False, если энергия <= 0."""
        self.energy -= cfg.ENERGY_DECAY * dt
        if self.energy <= 0:
            return False

        self._update_state()
        self._apply_movement(dt)
        self._clamp_to_bounds()
        return True

    def _update_state(self) -> None:
        """Переключает состояние FSM в зависимости от уровня энергии."""
        if self.energy < 15.0:
            self.state = State.FLEE
        elif self.energy > cfg.ENERGY_THRESHOLD:
            self.state = State.REPRODUCE
        elif self.energy > 30.0:
            self.state = State.SEEK
        else:
            self.state = State.WANDER

    def _apply_movement(self, dt: float) -> None:
        """Применяет скорость к координатам. Добавляет случайное смещение в режиме WANDER."""
        if self.state == State.WANDER:
            self.vx += random.uniform(-1.0, 1.0)
            self.vy += random.uniform(-1.0, 1.0)
        elif self.state == State.FLEE:
            # Временное ускорение до внедрения steering behaviors
            self.vx *= 1.05
            self.vy *= 1.05

        # Ограничиваем максимальную скорость
        max_speed = 60.0
        current_speed = (self.vx ** 2 + self.vy ** 2) ** 0.5
        if current_speed > max_speed:
            self.vx = (self.vx / current_speed) * max_speed
            self.vy = (self.vy / current_speed) * max_speed

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