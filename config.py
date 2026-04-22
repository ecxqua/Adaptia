# config.py
from typing import Final

# Окно и рендеринг
SCREEN_WIDTH: Final[int] = 1024
SCREEN_HEIGHT: Final[int] = 768
FPS: Final[int] = 60
DEBUG_MODE: Final[bool] = True

# Мир и популяция
INIT_POP_SIZE: Final[int] = 20
FOOD_SPAWN_RATE: Final[float] = 0.02  # вероятность спавна еды за кадр
ENERGY_DECAY: Final[float] = 1.0      # потеря энергии за кадр
ENERGY_THRESHOLD: Final[float] = 40.0  # мин. энергия для размножения
SEEK_SPEED: Final[float] = 80.0          # Скорость движения к еде
PERCEPTION_RADIUS: Final[float] = 100.0  # Радиус "зрения" существа

# ГА
POPULATION_SIZE: Final[int] = 20      # Размер популяции
ELITISM_COUNT: Final[int] = 2         # Сколько лучших сохраняются без изменений
TOURNAMENT_SIZE: Final[int] = 3       # Размер турнира для отбора
MUTATION_RATE: Final[float] = 0.1     # Базовая вероятность мутации гена
MUTATION_STRENGTH: Final[float] = 0.2 # Насколько сильно может измениться ген
MIN_MUTATION_RATE: Final[float] = 0.02  # Для адаптивности
MAX_MUTATION_RATE: Final[float] = 0.3
DIVERSITY_THRESHOLD: Final[float] = 0.15  # Порог для адаптивной мутации
MAX_STEERING_FORCE: Final[float] = 20.0  # Максимальная сила поворота/ускоренияz
MUTATION_UP_FACTOR: Final[float] = 1.2
MUTATION_DOWN_FACTOR: Final[float] = 0.95