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
        """Применяет скорость к координатам. Добавляет небольшой случайный импульс."""
        # Базовый случайный импульс для всех состояний, чтобы не застревать на 0
        self.vx += random.uniform(-0.5, 0.5)
        self.vy += random.uniform(-0.5, 0.5)
        
        if self.state == State.SEEK:
            closest_food_pos = None
            min_dist = float('inf')

            # Ищем ближайший кусок еды в переданном списке
            for fx, fy, _ in visible_food:
                dist_sq = (self.x - fx) ** 2 + (self.y - fy) ** 2
                if dist_sq < min_dist:
                    min_dist = dist_sq
                    closest_food_pos = (fx, fy)

            if closest_food_pos is not None:
                target_x, target_y = closest_food_pos
                dx = target_x - self.x
                dy = target_y - self.y

                # Нормализация вектора: превращаем направление в единичный вектор
                length = (dx ** 2 + dy ** 2) ** 0.5
                if length > 0.1:  # Защита от деления на ноль и дрожания на цели
                    dx /= length
                    dy /= length
                    # Явно задаём скорость к цели (не +=, чтобы не накапливалась)
                    self.vx = dx * cfg.SEEK_SPEED
                    self.vy = dy * cfg.SEEK_SPEED
                else:
                    # Цель достигнута — применяем базовый случайный импульс
                    self.vx += random.uniform(-0.5, 0.5)
                    self.vy += random.uniform(-0.5, 0.5)
            else:
                # Еды в радиусе видимости нет — продолжаем блуждать
                self.vx += random.uniform(-0.5, 0.5)
                self.vy += random.uniform(-0.5, 0.5)

        # Дополнительные поведения по состояниям
        if self.state == State.WANDER:
            self.vx += random.uniform(-1.5, 1.5)
            self.vy += random.uniform(-1.5, 1.5)
        elif self.state == State.FLEE:
            self.vx *= 1.1
            self.vy *= 1.1
        elif self.state == State.REPRODUCE:
            # Медленное блуждание при размножении
            self.vx += random.uniform(-0.3, 0.3)
            self.vy += random.uniform(-0.3, 0.3)

        # Ограничиваем максимальную скорость
        max_speed = 150.0
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