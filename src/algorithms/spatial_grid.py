"""Uniform Grid для ускорения пространственных запросов.
Разбивает игровое поле на ячейки и хранит объекты по их координатам.
Позволяет искать соседей за O(1) вместо O(N²).
"""
import math
from typing import List, Tuple, Any
import config as cfg

class SpatialGrid:
    """Пространственная сетка для быстрого поиска объектов в радиусе."""
    def __init__(self, cell_size: float = 50.0):
        self.cell_size = cell_size
        self.cols = math.ceil(cfg.SCREEN_WIDTH / cell_size)
        self.rows = math.ceil(cfg.SCREEN_HEIGHT / cell_size)
        # Создаём двумерный список (матрицу) пустых ячеек
        self.grid = [[[] for _ in range(self.cols)] for _ in range(self.rows)]

    def clear(self) -> None:
        """Очищает все ячейки перед новым кадром."""
        for row in self.grid:
            for cell in row:
                cell.clear()

    def insert(self, obj: Any, pos: Tuple[float, float]) -> None:
        """Добавляет объект в соответствующую ячейку по его позиции."""
        col = int(pos[0] // self.cell_size)
        row = int(pos[1] // self.cell_size)
         # Проверяем, что координаты в пределах сетки
        if 0 <= col < self.cols and 0 <= row < self.rows:
            self.grid[row][col].append(obj)

    def query_radius(self, center: Tuple[float, float], radius: float) -> List[Any]:
        """Возвращает все объекты из ячеек, попадающих в круг заданного радиуса."""
        result = []
        min_col = int((center[0] - radius) // self.cell_size)
        max_col = int((center[0] + radius) // self.cell_size)
        min_row = int((center[1] - radius) // self.cell_size)
        max_row = int((center[1] + radius) // self.cell_size)

        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    result.extend(self.grid[r][c])
        return result