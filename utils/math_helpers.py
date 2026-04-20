"""Вспомогательные математические функции.
Вынесены отдельно, чтобы избежать дублирования векторной логики в разных модулях.
"""
import math
from typing import Tuple

def distance_sq(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Возвращает квадрат расстояния между двумя точками.
    Быстрее, чем вычисление полного корня, подходит для сравнений.
    """
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return dx * dx + dy * dy

def normalize(vec: Tuple[float, float]) -> Tuple[float, float]:
    """Приводит вектор к единичной длине. Возвращает (0, 0), если длина равна 0."""
    length = math.hypot(vec[0], vec[1])
    if length == 0:
        return (0.0, 0.0)
    return (vec[0] / length, vec[1] / length)

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Ограничивает значение заданным диапазоном [min_val, max_val]."""
    return max(min_val, min(value, max_val))