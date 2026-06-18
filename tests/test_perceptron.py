"""Тесты простого перцептрона."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.algorithms.perceptron import SimplePerceptron


class TestSimplePerceptron:
    """Тесты перцептрона."""

    def test_output_range(self):
        """Выход перцептрона должен быть в диапазоне [-1, 1] (tanh)."""
        perceptron = SimplePerceptron(weights=[0.5, -0.3, 0.8], bias=0.1)
        
        # Тестируем на разных входах
        for inputs in [
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [-1.0, -1.0, -1.0],
            [0.5, -0.5, 0.5],
            [100.0, -100.0, 50.0],  # Экстремальные значения
        ]:
            output = perceptron.compute(inputs)
            assert -1.0 <= output <= 1.0, f"Output {output} out of range for inputs {inputs}"

    def test_zero_weights_zero_bias(self):
        """При нулевых весах и bias выход должен быть 0."""
        perceptron = SimplePerceptron(weights=[0.0, 0.0, 0.0], bias=0.0)
        
        output = perceptron.compute([1.0, 2.0, 3.0])
        
        assert abs(output) < 0.001  # tanh(0) = 0

    def test_positive_bias_shifts_output(self):
        """Положительный bias должен сдвигать выход в положительную сторону."""
        perceptron_pos = SimplePerceptron(weights=[0.0, 0.0], bias=1.0)
        perceptron_neg = SimplePerceptron(weights=[0.0, 0.0], bias=-1.0)
        
        output_pos = perceptron_pos.compute([0.0, 0.0])
        output_neg = perceptron_neg.compute([0.0, 0.0])
        
        assert output_pos > output_neg

    def test_weights_affect_output(self):
        """Разные веса должны давать разные выходы."""
        perceptron1 = SimplePerceptron(weights=[1.0, 1.0], bias=0.0)
        perceptron2 = SimplePerceptron(weights=[-1.0, -1.0], bias=0.0)
        
        inputs = [0.5, 0.5]
        output1 = perceptron1.compute(inputs)
        output2 = perceptron2.compute(inputs)
        
        assert output1 != output2

    def test_correct_number_of_weights(self):
        """Перцептрон должен принимать ровно столько входов, сколько весов."""
        perceptron = SimplePerceptron(weights=[0.1, 0.2, 0.3], bias=0.0)
        
        # Правильное количество входов
        output = perceptron.compute([1.0, 2.0, 3.0])
        assert -1.0 <= output <= 1.0