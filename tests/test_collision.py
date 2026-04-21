"""Тесты для проверки коллизий и пространственной сетки.
Запуск: pytest tests/test_collision.py -v
"""
from utils.collision import check_circle_collision
from src.algorithms.spatial_grid import SpatialGrid

def test_circle_collision_touching():
    assert check_circle_collision((0, 0), 5.0, (10, 0), 5.0) is True

def test_circle_collision_overlapping():
    assert check_circle_collision((0, 0), 6.0, (8, 0), 5.0) is True

def test_circle_collision_separate():
    assert check_circle_collision((0, 0), 4.0, (10, 0), 4.0) is False

def test_grid_insert_and_query():
    grid = SpatialGrid(cell_size=50.0)
    grid.insert("A", (25.0, 25.0))
    grid.insert("B", (200.0, 25.0))
    grid.insert("C", (26.0, 26.0))

    nearby = grid.query_radius((25.0, 25.0), 10.0)
    assert "A" in nearby and "C" in nearby
    assert "B" not in nearby