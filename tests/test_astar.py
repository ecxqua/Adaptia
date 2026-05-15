# tests/test_astar.py
"""Тесты для A* Pathfinding."""
import pytest
from src.algorithms.astar import AStarPathfinder


class TestAStarPathfinder:
    """Тестирование базовой функциональности A*."""
    
    def setup_method(self):
        """Создаёт тестовую сетку 10x10."""
        self.pathfinder = AStarPathfinder(
            grid_width=10,
            grid_height=10,
            cell_size=40.0
        )
    
    def test_direct_path(self):
        """Прямой путь без препятствий."""
        path = self.pathfinder.find_path(0, 0, 100, 100)
        assert path is not None
        assert len(path) >= 2
        assert path[0] == (20.0, 20.0)  # Старт (центр клетки)
    
    def test_path_with_obstacle(self):
        """Путь с обходом препятствия."""
        # Добавляем препятствие посередине
        self.pathfinder.add_obstacle(200, 200)
        
        path = self.pathfinder.find_path(0, 0, 400, 400)
        assert path is not None
        # Проверяем, что путь не проходит через препятствие
        for x, y in path:
            grid_pos = self.pathfinder.world_to_grid(x, y)
            assert grid_pos not in self.pathfinder.obstacles
    
    def test_no_path(self):
        """Ситуация, когда путь невозможен."""
        # Окружаем старт препятствиями
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    self.pathfinder.add_obstacle(200 + dx*40, 200 + dy*40)
        
        path = self.pathfinder.find_path(200, 200, 400, 400)
        assert path is None
    
    def test_start_equals_goal(self):
        """Старт и цель совпадают."""
        path = self.pathfinder.find_path(100, 100, 100, 100)
        assert path is not None
        assert len(path) == 1
    
    def test_grid_conversion(self):
        """Проверка преобразования координат."""
        grid_x, grid_y = self.pathfinder.world_to_grid(100, 150)
        world_x, world_y = self.pathfinder.grid_to_world(grid_x, grid_y)
        
        assert isinstance(grid_x, int)
        assert isinstance(grid_y, int)
        assert 0 <= grid_x < 10
        assert 0 <= grid_y < 10