# src/algorithms/steering.py
"""Steering Behaviors: плавное движение через векторные силы.
Чистые функции, возвращают силу (ускорение), не меняют внешнее состояние.
"""
import math
from typing import Tuple, List

def seek(
    pos: Tuple[float, float], 
    target: Tuple[float, float], 
    max_speed: float, 
    current_vel: Tuple[float, float]
) -> Tuple[float, float]:
    """Возвращает вектор силы, направленный к цели (desired_velocity - current_velocity)."""
    dx = target[0] - pos[0] # Насколько цель правее/левее нас
    dy = target[1] - pos[1]
    dist_sq = dx * dx + dy * dy
    if dist_sq < 0.01:
        return (0.0, 0.0) # Цель достигнута, сила не нужна
    
    dist = math.sqrt(dist_sq)
    # Желаемая скорость: направление к цели * max_speed
    desired_vx = (dx / dist) * max_speed
    desired_vy = (dy / dist) * max_speed
    
    # Сила управления = desired - current
    steer_x = desired_vx - current_vel[0]
    steer_y = desired_vy - current_vel[1]
    return (steer_x, steer_y)
