# src/model/population.py
"""Управление поколениями: фитнес, элитизм, создание новых существ."""
import config as cfg
import random
from typing import Optional, Tuple
from src.algorithms import ga
from src.algorithms.astar import AStarPathfinder
from src.model.creature import Creature, State


class Population:
    def __init__(self, creatures: list[Creature], pathfinder: Optional[AStarPathfinder] = None):
        self.creatures = creatures
        self.generation = 0
        self.current_mutation_rate = cfg.MUTATION_RATE
        self.best_fitness_history = []
        # Сохраняем ссылку на pathfinder, чтобы передавать её новым существам
        self._pathfinder = pathfinder

    def evaluate_fitness(self, creature: Creature) -> float:
        """Рассчитывает приспособленность существа.
        Чем выше число, тем лучше гены.
        Подсказка: используй energy, время жизни, или количество съеденной еды.
        """
        fitness = creature.energy + (creature.age * cfg.FITNESS_AGE_REWARD)
        
        # отладка
        # print(f"[FITNESS] Energy={creature.energy:.1f}, Age={creature.age:.1f} → {fitness:.2f}")
        
        return fitness

    def _spawn_safe_position(self) -> Tuple[float, float]:
        """Находит случайную позицию, не занятую препятствием.
        why: без этой проверки существа могут спавниться внутри стен и застревать.
        """
        attempts = 0
        while attempts < 100:
            x = random.uniform(10, cfg.SCREEN_WIDTH - 10)
            y = random.uniform(10, cfg.SCREEN_HEIGHT - 10)
            if self._pathfinder is not None:
                grid_pos = self._pathfinder.world_to_grid(x, y)
                if grid_pos in self._pathfinder.obstacles:
                    attempts += 1
                    continue
            return (x, y)
        return (x, y)

    def next_generation(self) -> list[Creature]:
        """Создаёт новое поколение через ГА. Гарантирует сохранение метрик."""
        if not self.creatures:
            print("[WARN] next_generation called with empty population. Skipping.")
            return []

        # Оценка фитнеса
        fitnesses: list[float] = [self.evaluate_fitness(c) for c in self.creatures]
        if not fitnesses:
            print("[WARN] All fitnesses are zero/empty. Cannot evolve.")
            self.generation += 1
            return []

        # Адаптация мутации (безопасно)
        diversity = ga.calculate_diversity(self.creatures)
        self.current_mutation_rate = ga.adapt_mutation_rate(self.current_mutation_rate, diversity)

        new_gen: list[Creature] = []

        # Элитизм
        if len(self.creatures) >= cfg.ELITISM_COUNT:
            paired = list(zip(self.creatures, fitnesses))
            paired.sort(key=lambda x: x[1], reverse=True)
            for i in range(cfg.ELITISM_COUNT):
                elite = paired[i][0]
                x, y = self._spawn_safe_position()
                new_creature = Creature(
                    x=x, y=y,
                    genome=elite.genome.copy(),
                    energy=50.0,
                    age=0.0,
                    state=State.WANDER
                )
                new_creature._pathfinder = self._pathfinder
                new_gen.append(new_creature)

        # Генерация остатка популяции
        while len(new_gen) < cfg.POPULATION_SIZE:
            p1 = ga.tournament_selection(self.creatures, fitnesses, cfg.TOURNAMENT_SIZE)
            p2 = ga.tournament_selection(self.creatures, fitnesses, cfg.TOURNAMENT_SIZE)
            child_genome = ga.crossover(p1.genome, p2.genome)
            child_genome = ga.mutate(child_genome, self.current_mutation_rate, cfg.MUTATION_STRENGTH)
            x, y = self._spawn_safe_position()
            new_creature = Creature(
                x=x, y=y,
                genome=child_genome,
                energy=50.0,
                age=0.0,
                state=State.WANDER
            )
            new_creature._pathfinder = self._pathfinder
            new_gen.append(new_creature)

        # сохранение метрик и инкремент поколения
        best_fitness = max(fitnesses)
        self.best_fitness_history.append(best_fitness)
        self.generation += 1

        # Замена популяции
        self.creatures = new_gen
        return new_gen