# src/algorithms/ga.py
"""Генетический алгоритм: отбор, скрещивание, мутация.
Чистые функции, не зависят от pygame или модели.
"""

import random
import config as cfg
from typing import List, Callable, Any

def tournament_selection(population: List[Any], fitnesses: List[float], k: int) -> Any:
    """Отбирает одного родителя через турнир размера k."""
    contenders = random.sample(range(len(population)), k)
    best_idx = max(contenders, key=lambda idx: fitnesses[idx])

    return population[best_idx]


def crossover(parent1: List[float], parent2: List[float]) -> List[float]:
    """Одноточечный кроссовер: ребёнок = часть генов от папы + часть от мамы."""
    point = random.randint(1, len(parent1) - 1)

    return parent1[:point] + parent2[point:]


def mutate(genome: List[float], rate: float, strength: float) -> List[float]:
    """С вероятностью rate изменяет каждый ген на случайное значение в диапазоне ±strength."""
    child_genome = []
    for gene in genome:
        if random.random() < rate:
            # Гауссово распределение: чаще малые изменения, реже крупные скачки
            new_gene = gene + random.gauss(0, strength)
        else:
            new_gene = gene
        child_genome.append(new_gene)

    return child_genome


def calculate_diversity(population: List[List[float]]) -> float:
    """Возвращает среднее попарное расстояние между геномами (нормализованное 0..1)."""
    genomes = [individual.genome for individual in population]

    if len(genomes) < 2:
        return 0.0

    total_dist = 0.0
    pair_count = 0

    for i in range(len(genomes) - 1):
        dist_sq = 0
        for j in range(i + 1, len(genomes)):
            for k in range(len(genomes[0])):
                dist_sq += (genomes[i][k] - genomes[j][k]) ** 2
            total_dist += dist_sq**0.5
            pair_count += 1

    D_avg = total_dist / pair_count

    return min(1.0, D_avg / (len(genomes[0]) * 2.0))


def adapt_mutation_rate(current_rate: float, diversity: float) -> float:
    """Адаптирует скорость мутации: если разнообразие низкое → увеличиваем мутацию."""
    if diversity < cfg.DIVERSITY_THRESHOLD:
        new_rate = current_rate * cfg.MUTATION_UP_FACTOR  # множитель на увеличение
    else:
        new_rate = current_rate * cfg.MUTATION_DOWN_FACTOR # множитель на снижение
     # Ограничение диапазона + возврат
    return max(cfg.MIN_MUTATION_RATE, min(cfg.MAX_MUTATION_RATE, new_rate))
