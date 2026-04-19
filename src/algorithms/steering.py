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
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    dist_sq = dx * dx + dy * dy
    if dist_sq < 0.01:
        return (0.0, 0.0)
    
    dist = math.sqrt(dist_sq)
    # Желаемая скорость: направление к цели * max_speed
    desired_vx = (dx / dist) * max_speed
    desired_vy = (dy / dist) * max_speed
    
    # Сила управления = desired - current
    steer_x = desired_vx - current_vel[0]
    steer_y = desired_vy - current_vel[1]
    return (steer_x, steer_y)

def flee(
    pos: Tuple[float, float], 
    threat: Tuple[float, float], 
    max_speed: float, 
    current_vel: Tuple[float, float]
) -> Tuple[float, float]:
    """Возвращает вектор силы, направленный ОТ угрозы."""
    # Просто инвертируем координаты цели и используем seek
    dx = pos[0] - threat[0]
    dy = pos[1] - threat[1]
    return seek(pos, (pos[0] + dx, pos[1] + dy), max_speed, current_vel)

def separation(
    pos: Tuple[float, float], 
    neighbors: List[Tuple[float, float]], 
    radius: float, 
    max_force: float
) -> Tuple[float, float]:
    """Возвращает усреднённый вектор отталкивания от соседей."""
    force_x, force_y = 0.0, 0.0
    count = 0
    
    for nx, ny in neighbors:
        dx = pos[0] - nx
        dy = pos[1] - ny
        dist_sq = dx * dx + dy * dy
        
        if dist_sq < radius * radius and dist_sq > 0.01:
            dist = math.sqrt(dist_sq)
            # Чем ближе сосед, тем сильнее отталкивание
            force_x += dx / dist
            force_y += dy / dist
            count += 1

    if count == 0:
        return (0.0, 0.0)

    # Усредняем
    force_x /= count
    force_y /= count
    
    # Ограничиваем максимальной силой
    length = math.hypot(force_x, force_y)
    if length > max_force:
        force_x = (force_x / length) * max_force
        force_y = (force_y / length) * max_force

    return (force_x, force_y)