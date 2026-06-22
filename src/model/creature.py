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
    # Перцептрон. repr=False скрывает объект мозга при отладке print()
    brain: Optional[SimplePerceptron] = field(default=None, repr=False)
    trail: list[tuple[float, float]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Инициализирует мозг из генома. Первые 7 генов → веса, последний → bias."""
        if self.brain is None:
            self.brain = SimplePerceptron(
                weights=self.genome[:-1],
                bias=self.genome[-1]
            )

    # =========================================================================
    # ГЛАВНЫЙ ЦИКЛ ОБНОВЛЕНИЯ
    # =========================================================================

    def update(
        self,
        dt: float,
        visible_food: List[Tuple[float, float, float]],
        pathfinder: Optional[AStarPathfinder] = None,
        nearby_creatures: Optional[List['Creature']] = None
    ) -> bool:
        """Обновляет параметры существа за кадр. Перцептрон управляет состоянием."""
        # 1. Трата энергии и проверка смерти
        self.energy -= cfg.ENERGY_DECAY * dt
        if self.energy <= 0:
            return False

        # 2. Обновляем ссылку на pathfinder
        if pathfinder is not None:
            self._pathfinder = pathfinder

        # 3. FSM: выбор состояния
        self._update_state(visible_food)

        # 4. Действие в зависимости от состояния
        if self.state == State.REPRODUCE:
            self._handle_reproduce(dt, nearby_creatures)
        elif self.state == State.SEEK:
            self._handle_seek(dt, visible_food, pathfinder)
        elif self.state == State.FLEE:
            self._handle_flee(dt)
        else:  # WANDER
            self._handle_wander(dt)

        # 5. Границы экрана, старение, след
        self._clamp_to_bounds()
        self.age += dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > 20:
            self.trail.pop(0)

        return True

    # =========================================================================
    # FSM: ВЫБОР СОСТОЯНИЯ
    # =========================================================================

    def _update_state(self, visible_food: List[Tuple[float, float, float]]) -> None:
        """Перцептрон принимает решение о смене состояния."""
        # Сытость имеет приоритет — не даём перцептрону переопределить
        if self.energy > 80.0:
            self.state = State.REPRODUCE
            return

        # Сенсоры для перцептрона (нормализованные значения)
        food_signal = 1.0 if visible_food else 0.0
        energy_signal = max(0.0, min(1.0, self.energy / 50.0))
        sensors = [food_signal, energy_signal, 0.0, 0.0, 0.0, 0.0, 0.0]

        decision = self.brain.compute(sensors)

        # Пороги создают "мёртвую зону" — существо не дёргается между состояниями
        if decision > 0.4:
            self.state = State.SEEK
        elif decision < -0.4:
            self.state = State.FLEE
        else:
            self.state = State.WANDER

    # =========================================================================
    # ДЕЙСТВИЯ ПО СОСТОЯНИЯМ
    # =========================================================================

    def _handle_reproduce(
        self,
        dt: float,
        nearby_creatures: Optional[List['Creature']]
    ) -> None:
        """REPRODUCE: ищем партнёра и двигаемся к нему."""
        partner = self._find_closest_partner(nearby_creatures)
        if partner is not None:
            self._apply_steering(dt, partner.x, partner.y)
        else:
            self._apply_wander(dt)

    def _handle_seek(
        self,
        dt: float,
        visible_food: List[Tuple[float, float, float]],
        pathfinder: Optional[AStarPathfinder]
    ) -> None:
        """SEEK: навигация к еде через A* или напрямую."""
        # Нет еды — переключаемся в WANDER
        if not visible_food:
            self.state = State.WANDER
            self._apply_wander(dt)
            return

        # Находим ближайшую еду
        closest_food = min(
            visible_food,
            key=lambda f: distance_sq((self.x, self.y), (f[0], f[1]))
        )
        dist_to_food = distance_sq((self.x, self.y), (closest_food[0], closest_food[1])) ** 0.5

        # Близко → идём напрямую (A* избыточен для близких целей)
        if dist_to_food < cfg.GRID_CELL_SIZE * 3:
            self._apply_steering(dt, closest_food[0], closest_food[1])
            self.current_path = None
            self.path_index = 0
            return

        # Далеко → используем A* с кешированием пути
        if not pathfinder:
            # Fallback: нет pathfinder — идём напрямую
            self._apply_steering(dt, closest_food[0], closest_food[1])
            return

        # Пересчитываем путь не каждый кадр (оптимизация)
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

        # Двигаемся по waypoints
        if self.current_path and self.path_index < len(self.current_path):
            target_x, target_y = self.current_path[self.path_index]
            dist_to_waypoint = distance_sq((self.x, self.y), (target_x, target_y))

            # Достигли waypoint → переходим к следующему
            if dist_to_waypoint < cfg.GRID_CELL_SIZE ** 2:
                self.path_index += 1

            if self.path_index < len(self.current_path):
                target_x, target_y = self.current_path[self.path_index]
                self._apply_steering(dt, target_x, target_y)
            else:
                # Путь закончился → идём напрямую к еде
                self._apply_steering(dt, closest_food[0], closest_food[1])
                self.current_path = None
        else:
            # Путь не найден → блуждаем
            self._apply_wander(dt)

    def _handle_flee(self, dt: float) -> None:
        """FLEE: паническое бегство в случайном направлении."""
        angle = random.uniform(0, math.pi * 2)
        force_x = math.cos(angle) * cfg.SEEK_SPEED
        force_y = math.sin(angle) * cfg.SEEK_SPEED
        self._apply_physics(dt, force_x, force_y)

    def _handle_wander(self, dt: float) -> None:
        """WANDER: случайное блуждание."""
        self._apply_wander(dt)

    # =========================================================================
    # ПОИСК ПАРТНЁРА (вынесен в отдельный метод — устранение дублирования)
    # =========================================================================

    def _find_closest_partner(
        self,
        nearby_creatures: Optional[List['Creature']]
    ) -> Optional['Creature']:
        """
        Ищет ближайшего партнёра для размножения.
        Критерии: не сам, в состоянии REPRODUCE, энергия > 40.
        """
        if not nearby_creatures or self.energy <= 40:
            return None

        closest = None
        min_dist = float('inf')

        for other in nearby_creatures:
            if other is self:
                continue
            if other.state == State.REPRODUCE and other.energy > 40:
                dist = distance_sq((self.x, self.y), (other.x, other.y))
                if dist < min_dist:
                    min_dist = dist
                    closest = other

        return closest

    # =========================================================================
    # ФИЗИКА ДВИЖЕНИЯ (общий метод — устранение дублирования)
    # =========================================================================

    def _apply_physics(self, dt: float, force_x: float, force_y: float) -> None:
        """
        Универсальная физика: интегрирует силу в скорость, ограничивает скорость,
        проверяет препятствия и обновляет координаты.
        Вызывается всеми методами движения (_apply_steering, _apply_wander, _handle_flee).
        """
        # Ограничиваем силу поворота/ускорения
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

        # Проверка препятствий через line sweep
        if self._check_obstacle_collision(new_x, new_y):
            # Препятствие! Разворачиваемся со случайным отклонением
            self.vx = -self.vx + random.uniform(-20, 20)
            self.vy = -self.vy + random.uniform(-20, 20)
            return

        self.x = new_x
        self.y = new_y

    def _apply_steering(self, dt: float, target_x: float, target_y: float) -> None:
        """Движение к конкретной точке через steering.seek (для A* waypoints, еды, партнёра)."""
        from src.algorithms import steering

        force_x, force_y = steering.seek(
            (self.x, self.y),
            (target_x, target_y),
            cfg.SEEK_SPEED,
            (self.vx, self.vy)
        )
        self._apply_physics(dt, force_x, force_y)

    def _apply_wander(self, dt: float) -> None:
        """Случайное блуждание — шумовые силы."""
        force_x = random.uniform(-cfg.MAX_STEERING_FORCE, cfg.MAX_STEERING_FORCE)
        force_y = random.uniform(-cfg.MAX_STEERING_FORCE, cfg.MAX_STEERING_FORCE)
        self._apply_physics(dt, force_x, force_y)

    # =========================================================================
    # ПРЕПЯТСТВИЯ И ГРАНИЦЫ
    # =========================================================================

    def _check_obstacle_collision(self, new_x: float, new_y: float) -> bool:
        """
        Проверяет, есть ли препятствие на пути от текущей позиции к новой.
        Использует line sweep для надёжной проверки (не пропускаем тонкие стены).
        """
        if self._pathfinder is None:
            return False

        # Число проверок зависит от длины траектории
        steps = max(2, int(distance_sq((self.x, self.y), (new_x, new_y)) ** 0.5 / (cfg.GRID_CELL_SIZE / 2)))

        for i in range(steps + 1):
            t = i / steps if steps > 0 else 0
            check_x = self.x + (new_x - self.x) * t
            check_y = self.y + (new_y - self.y) * t
            grid_pos = self._pathfinder.world_to_grid(check_x, check_y)
            if grid_pos in self._pathfinder.obstacles:
                return True

        return False

    def _clamp_to_bounds(self) -> None:
        """Удерживает существо в пределах экрана и отражает скорость от стен."""
        margin = self.radius + 2.0  # Небольшой отступ от края

        if self.x < margin:
            self.x = margin
            if self.vx < 0:
                self.vx = -self.vx * 0.5 + random.uniform(-10, 10)
        elif self.x > cfg.SCREEN_WIDTH - margin:
            self.x = cfg.SCREEN_WIDTH - margin
            if self.vx > 0:
                self.vx = -self.vx * 0.5 + random.uniform(-10, 10)

        if self.y < margin:
            self.y = margin
            if self.vy < 0:
                self.vy = -self.vy * 0.5 + random.uniform(-10, 10)
        elif self.y > cfg.SCREEN_HEIGHT - margin:
            self.y = cfg.SCREEN_HEIGHT - margin
            if self.vy > 0:
                self.vy = -self.vy * 0.5 + random.uniform(-10, 10)

    # =========================================================================
    # ИНТЕРФЕЙС ДЛЯ VIEW
    # =========================================================================

    def get_render_data(self) -> dict:
        """Возвращает чистые данные для View"""
        return {
            "pos": (self.x, self.y),
            "radius": self.radius,
            "state": self.state.name,
            "energy": self.energy
        }