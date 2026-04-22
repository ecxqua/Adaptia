# src/model/population.py
"""Управление поколениями: фитнес, элитизм, создание новых существ."""
import config as cfg
import random
from src.algorithms import ga
from src.model.creature import Creature

class Population:
    def __init__(self, creatures: list[Creature]):
        self.creatures = creatures
        self.generation = 0
        self.current_mutation_rate = cfg.MUTATION_RATE
        self.best_fitness_history = []

    def evaluate_fitness(self, creature: Creature) -> float:
        """Рассчитывает приспособленность существа.
        Чем выше число, тем лучше гены.
        Подсказка: используй energy, время жизни, или количество съеденной еды.
        """
        return creature.energy + (creature.age * cfg.FITNESS_AGE_REWARD)

    def next_generation(self) -> list[Creature]:
        """Создаёт новое поколение через ГА."""
        fitnesses = [self.evaluate_fitness(c) for c in self.creatures]
        diversity = ga.calculate_diversity(self.creatures)
        self.current_mutation_rate = ga.adapt_mutation_rate(self.current_mutation_rate, diversity)
        
        new_gen = []
        
        paired = list(zip(self.creatures, fitnesses))
        paired.sort(key=lambda x: x[1], reverse=True)  # Сортируем по фитнесу по убыванию

        # Элитизм: копируем лучших в новое поколение
        for i in range(cfg.ELITISM_COUNT):
            best_creature = paired[i][0]
            new_gen.append(Creature(
                x=random.uniform(10, cfg.SCREEN_WIDTH - 10),
                y=random.uniform(10, cfg.SCREEN_HEIGHT - 10),
                genome=best_creature.genome.copy(),  
                energy=50.0,                         # Сбрасываем энергию для нового поколения
                age=0.0                              # Сбрасываем возраст
            ))

        
        # Создание остальной популяции
        while len(new_gen) < cfg.POPULATION_SIZE:
           parent1 = ga.tournament_selection(self.creatures, fitnesses, cfg.TOURNAMENT_SIZE)
           parent2 = ga.tournament_selection(self.creatures, fitnesses, cfg.TOURNAMENT_SIZE)
           child_genome = ga.crossover(parent1, parent2)
           child_genome = ga.mutate(child_genome, self.current_mutation_rate, cfg.MUTATION_STRENGTH)
           new_gen.append(Creature(
            x=random.uniform(10, cfg.SCREEN_WIDTH - 10),
            y=random.uniform(10, cfg.SCREEN_HEIGHT - 10),
            genome=child_genome,
            energy=50.0,   # Новорождённый стартует полным
            age=0.0,       # Возраст сбрасывается для честного отбора
            state=State.WANDER
            ))

        
        self.generation += 1
        self.creatures = new_gen
        return new_gen