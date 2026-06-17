"""Система сохранения/загрузки состояния игры в JSON."""
import json
import os
from typing import Dict, List, Any
import config as cfg
from src.model.creature import Creature, State
from src.algorithms.astar import AStarPathfinder


def save_game(world: Any, filename: str = "save.json") -> bool:
    """
    Сохраняет текущее состояние мира в JSON файл.
    
    Args:
        world: Объект World с текущим состоянием
        filename: Имя файла для сохранения
    
    Returns:
        True если сохранение успешно, False иначе
    """
    try:
        # Собираем данные для сохранения
        save_data = {
            "version": "1.0",
            "generation": world.population_manager.generation,
            "best_fitness_history": world.population_manager.best_fitness_history,
            
            # Параметры среды (текущие значения из config)
            "config": {
                "MUTATION_RATE": cfg.MUTATION_RATE,
                "MUTATION_STRENGTH": cfg.MUTATION_STRENGTH,
                "FOOD_SPAWN_RATE": cfg.FOOD_SPAWN_RATE,
                "ENERGY_DECAY": cfg.ENERGY_DECAY,
                "PERCEPTION_RADIUS": cfg.PERCEPTION_RADIUS,
                "SEEK_SPEED": cfg.SEEK_SPEED,
                "MAX_STEERING_FORCE": cfg.MAX_STEERING_FORCE,
            },
            
            # Препятствия
            "obstacles": [{"x": x, "y": y} for x, y in world.obstacles],
            
            # Текущая еда
            "food": [{"x": x, "y": y, "energy": e} for x, y, e in world.food],
            
            # Существа
            "creatures": [
                {
                    "x": c.x,
                    "y": c.y,
                    "vx": c.vx,
                    "vy": c.vy,
                    "energy": c.energy,
                    "age": c.age,
                    "genome": c.genome,
                    "state": c.state.name,
                }
                for c in world.creatures
            ],
        }
        
        # Записываем в файл
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"[SAVE] Игра сохранена в {filename}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Не удалось сохранить игру: {e}")
        return False


def load_game(world: Any, filename: str = "save.json") -> bool:
    """
    Загружает состояние мира из JSON файла.
    
    Args:
        world: Объект World для загрузки данных
        filename: Имя файла для загрузки
    
    Returns:
        True если загрузка успешна, False иначе
    """
    if not os.path.exists(filename):
        print(f"[ERROR] Файл сохранения {filename} не найден")
        return False
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
        
        # Восстанавливаем параметры среды
        if "config" in save_data:
            for key, value in save_data["config"].items():
                if hasattr(cfg, key):
                    setattr(cfg, key, value)
        
        # Восстанавливаем поколение и историю фитнеса
        if "generation" in save_data:
            world.population_manager.generation = save_data["generation"]
        if "best_fitness_history" in save_data:
            world.population_manager.best_fitness_history = save_data["best_fitness_history"]
        
        # Восстанавливаем препятствия
        world.obstacles = []
        world.pathfinder.clear_obstacles()
        if "obstacles" in save_data:
            for obs in save_data["obstacles"]:
                world.spawn_obstacle_at(obs["x"], obs["y"])
        
        # Восстанавливаем еду
        world.food = []
        if "food" in save_data:
            for f in save_data["food"]:
                world.food.append((f["x"], f["y"], f["energy"]))
        
        # Восстанавливаем существ
        world.creatures = []
        if "creatures" in save_data:
            for c_data in save_data["creatures"]:
                creature = Creature(
                    x=c_data["x"],
                    y=c_data["y"],
                    vx=c_data["vx"],
                    vy=c_data["vy"],
                    energy=c_data["energy"],
                    age=c_data["age"],
                    genome=c_data["genome"],
                )
                
                # Восстанавливаем состояние
                state_name = c_data.get("state", "WANDER")
                try:
                    creature.state = State[state_name]
                except KeyError:
                    creature.state = State.WANDER
                
                # Привязываем pathfinder
                creature._pathfinder = world.pathfinder
                
                world.creatures.append(creature)
        
        print(f"[LOAD] Игра загружена из {filename}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить игру: {e}")
        return False