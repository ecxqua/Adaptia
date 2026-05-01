# src/algorithms/perceptron.py
"""Простой перцептрон с одной линейной активацией.
Чистая математика: не зависит от pygame, модели или конфигов.
"""
import math
from typing import List

class SimplePerceptron:
    """Линейный классификатор/регрессор с функцией активации tanh."""
    
    def __init__(self, weights: list[float], bias: float):
        # Веса и смещение приходят из генома существа
        self.weights = weights
        self.bias = bias

    def compute(self, inputs: list[float]) -> float:
        """
        Вычисляет взвешенную сумму входов + смещение, применяет tanh.
        Возвращает значение в диапазоне [-1, 1].
        """
        weighted_sum = sum(w * i for w, i in zip(self.weights, inputs))
        
        net_input = weighted_sum + self.bias
        
        return math.tanh(net_input)