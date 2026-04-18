# src/model/world.py
"""Модель мира.
Управляет списком существ, отвечает за их начальный спавн, обновление и удаление погибших.
"""
import random
import config as cfg
from src.model.creature import Creature

class World:
    """Контейнер симуляции. Содержит все активные объекты."""
    def __init__(self):
        self.creatures: list[Creature] = []
        self._spawn_initial_population()

    def update(self, dt: float) -> None:
        """Обновляет всех существ за кадр. Погибшие удаляются из списка."""
        self.creatures = [c for c in self.creatures if c.update(dt)]

    def _spawn_initial_population(self) -> None:
        """Создаёт стартовую популяцию в случайных позициях с отступом от краёв."""
        margin = 50
        for _ in range(cfg.INIT_POP_SIZE):
            x = random.uniform(margin, cfg.SCREEN_WIDTH - margin)
            y = random.uniform(margin, cfg.SCREEN_HEIGHT - margin)
            self.creatures.append(Creature(x, y))

    def get_creature_count(self) -> int:
        """Возвращает текущее количество живых существ для отладки и UI."""
        return len(self.creatures)
    
    # ВРЕМЕННАЯ ОТЛАДКА (потом удалю)
    def update(self, dt: float) -> None:
        
        import sys
        if len(self.creatures) > 0:
            c = self.creatures[0]
            print(f"dt={dt:.4f} | vx={c.vx:.2f} | energy={c.energy:.2f}", end="\r", flush=True)
        
        self.creatures = [c for c in self.creatures if c.update(dt)]