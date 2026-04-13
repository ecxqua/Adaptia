# config.py
from typing import Final

# Окно и рендеринг
SCREEN_WIDTH: Final[int] = 1024
SCREEN_HEIGHT: Final[int] = 768
FPS: Final[int] = 60
DEBUG_MODE: Final[bool] = False

# Мир и популяция
INIT_POP_SIZE: Final[int] = 20
FOOD_SPAWN_RATE: Final[float] = 0.02  # вероятность спавна еды за кадр
ENERGY_DECAY: Final[float] = 0.1      # потеря энергии за кадр
ENERGY_THRESHOLD: Final[float] = 5.0  # мин. энергия для размножения

# ГА (заглушки на потом)
MUTATION_RATE: Final[float] = 0.1
TOURNAMENT_SIZE: Final[int] = 3