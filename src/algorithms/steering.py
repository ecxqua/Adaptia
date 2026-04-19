# src/algorithms/steering.py
"""Steering Behaviors: плавное движение через векторные силы.
Чистые функции, не зависят от pygame или модели.
"""
from typing import Tuple
from utils.math_helpers import normalize, distance_sq

def seek(position: Tuple[float, float], target: Tuple[float, float], max_speed: float) -> Tuple[float, float]:
    """Возвращает вектор силы, направленный к цели."""

    pass

def flee(position: Tuple[float, float], threat: Tuple[float, float], max_speed: float) -> Tuple[float, float]:
    """Возвращает вектор силы, направленный ОТ угрозы."""

    pass

def separation(position: Tuple[float, float], neighbors: list[Tuple[float, float]], radius: float, max_force: float) -> Tuple[float, float]:
    """Возвращает вектор отталкивания от ближайших соседей."""

    pass