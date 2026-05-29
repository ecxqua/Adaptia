"""Проверка коллизий между объектами.
Использует только чистую математику, не зависит от pygame и модели.
"""
from typing import Tuple
from utils.math_helpers import distance_sq

def check_circle_collision(
    pos1: Tuple[float, float], r1: float,
    pos2: Tuple[float, float], r2: float
) -> bool:
    """Проверяет, пересекаются ли два круга.
    Сравнивает квадраты расстояний и квадраты суммы радиусов для скорости.
    """
    dist_sq = distance_sq(pos1, pos2)
    radii_sum_sq = (r1 + r2) ** 2
    return dist_sq <= radii_sum_sq