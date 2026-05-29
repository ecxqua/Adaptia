from src.algorithms.spatial_grid import SpatialGrid

def __init__(self):
    self.creatures: list[Creature] = []
    self.food: list[tuple[float, float, float]] = []
    self.grid = SpatialGrid(cell_size=50.0)  # ← ДОБАВИТЬ
    self._spawn_initial_population()