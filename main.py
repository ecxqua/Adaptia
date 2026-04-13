"""Точка входа в приложение.
Запускает игровой цикл. Логика инициализации вынесена в controller.
"""
from src.controller.game_loop import GameLoop

if __name__ == "__main__":
    GameLoop().run()