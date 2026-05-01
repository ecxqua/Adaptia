# src/algorithms/astar.py
"""A* Pathfinding на фиксированной сетке.
Упрощённая реализация для навигации существ к ресурсам.
Соответствует методичке как «Лёгкий» алгоритм.
"""
import heapq
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field
import config as cfg


@dataclass(order=True)
class Node:
    """Узел для приоритетной очереди в A*."""
    f_score: float
    position: Tuple[int, int] = field(compare=False)
    g_score: float = field(default=float('inf'), compare=False)
    parent: Optional['Node'] = field(default=None, compare=False)


class AStarPathfinder:
    """A* поиск пути на сетке с учётом препятствий."""
    
    def __init__(self, grid_width: int, grid_height: int, cell_size: float):
        """
        Инициализация навигационной сетки.
        
        Args:
            grid_width: Ширина мира в клетках
            grid_height: Высота мира в клетках
            cell_size: Размер одной клетки в пикселях
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.cell_size = cell_size
        self.obstacles: Set[Tuple[int, int]] = set()
    
    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Преобразует мировые координаты в координаты сетки."""
        grid_x = int(x // self.cell_size)
        grid_y = int(y // self.cell_size)
        # Ограничиваем в пределах сетки
        grid_x = max(0, min(grid_x, self.grid_width - 1))
        grid_y = max(0, min(grid_y, self.grid_height - 1))
        return (grid_x, grid_y)
    
    def grid_to_world(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """Преобразует координаты сетки в мировые (центр клетки)."""
        world_x = (grid_x * self.cell_size) + (self.cell_size / 2)
        world_y = (grid_y * self.cell_size) + (self.cell_size / 2)
        return (world_x, world_y)
    
    def add_obstacle(self, x: float, y: float) -> None:
        """Добавляет препятствие в сетку по мировым координатам."""
        grid_pos = self.world_to_grid(x, y)
        self.obstacles.add(grid_pos)
    
    def remove_obstacle(self, x: float, y: float) -> None:
        """Удаляет препятствие из сетки."""
        grid_pos = self.world_to_grid(x, y)
        self.obstacles.discard(grid_pos)
    
    def clear_obstacles(self) -> None:
        """Очищает все препятствия."""
        self.obstacles.clear()
    
    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Эвристическая функция: манхэттенское расстояние."""
        # why: Манхэттенское расстояние быстрее вычисляется и хорошо работает
        # для сеток с 4-направленным движением. Для 8-направленного можно
        # использовать диагональное расстояние, но это усложняет код без
        # существенного выигрыша в качестве пути.
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def _get_neighbors(self, node: Node) -> List[Tuple[int, int]]:
        """Возвращает соседние клетки (4-направленное движение)."""
        x, y = node.position
        neighbors = [
            (x + 1, y),  # Вправо
            (x - 1, y),  # Влево
            (x, y + 1),  # Вниз
            (x, y - 1),  # Вверх
        ]
        # Фильтруем выходящие за границы и препятствия
        valid_neighbors = []
        for nx, ny in neighbors:
            if (0 <= nx < self.grid_width and 
                0 <= ny < self.grid_height and 
                (nx, ny) not in self.obstacles):
                valid_neighbors.append((nx, ny))
        return valid_neighbors
    
    def find_path(self, start_x: float, start_y: float, 
                  goal_x: float, goal_y: float) -> Optional[List[Tuple[float, float]]]:
        """
        Находит путь от стартовой точки до цели.
        
        Args:
            start_x, start_y: Начальная позиция (мировые координаты)
            goal_x, goal_y: Целевая позиция (мировые координаты)
        
        Returns:
            Список мировых координат пути или None, если путь не найден.
        """
        start_grid = self.world_to_grid(start_x, start_y)
        goal_grid = self.world_to_grid(goal_x, goal_y)
        
        # Проверка: если старт или цель в препятствии
        if start_grid in self.obstacles or goal_grid in self.obstacles:
            return None
        
        # Проверка: если старт == цель
        if start_grid == goal_grid:
            return [self.grid_to_world(*start_grid)]
        
        # Инициализация открытого списка (priority queue)
        open_set: List[Node] = []
        start_node = Node(
            f_score=self._heuristic(start_grid, goal_grid),
            position=start_grid,
            g_score=0.0
        )
        heapq.heappush(open_set, start_node)
        
        # Закрытый список (посещённые узлы)
        closed_set: Set[Tuple[int, int]] = set()
        
        # Для восстановления пути
        came_from: dict[Tuple[int, int], Node] = {}
        g_scores: dict[Tuple[int, int], float] = {start_grid: 0.0}
        
        while open_set:
            # Берём узел с наименьшим f_score
            current = heapq.heappop(open_set)
            
            # Если достигли цели
            if current.position == goal_grid:
                # Восстанавливаем путь
                path = self._reconstruct_path(came_from, current)
                return path
            
            # Добавляем в закрытый список
            closed_set.add(current.position)
            
            # Проверяем соседей
            for neighbor_pos in self._get_neighbors(current):
                if neighbor_pos in closed_set:
                    continue
                
                # g_score для соседа (стоимость шага = 1)
                tentative_g = current.g_score + 1.0
                
                # Если нашли лучший путь
                if neighbor_pos not in g_scores or tentative_g < g_scores[neighbor_pos]:
                    g_scores[neighbor_pos] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor_pos, goal_grid)
                    
                    neighbor_node = Node(
                        f_score=f_score,
                        position=neighbor_pos,
                        g_score=tentative_g
                    )
                    
                    came_from[neighbor_pos] = current
                    heapq.heappush(open_set, neighbor_node)
        
        # Путь не найден
        return None
    
    def _reconstruct_path(self, came_from: dict, current: Node) -> List[Tuple[float, float]]:
        """Восстанавливает путь от цели к старту и преобразует в мировые координаты."""
        path = [self.grid_to_world(*current.position)]
        while current.position in came_from:
            current = came_from[current.position]
            path.append(self.grid_to_world(*current.position))
        path.reverse()
        return path