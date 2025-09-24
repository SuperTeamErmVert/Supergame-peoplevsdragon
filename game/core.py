from abc import ABC, abstractmethod
from typing import Any
from game.exceptions import GameException

# --- Дескриптор для ограниченных характеристик ---
class BoundedStat:
    """Дескриптор для проверки, что значение находится в заданных пределах (min, max)."""
    def __init__(self, min_value: float, max_value: float):
        self.min_value = min_value
        self.max_value = max_value
        # Создаем уникальное имя для хранения значения в экземпляре
        self.private_name = f"_{id(self)}"

    def __get__(self, obj: Any, objtype: Any = None) -> float:
        return getattr(obj, self.private_name, self.max_value)

    def __set__(self, obj: Any, value: float) -> None:
        # Проверяем границы
        if not (self.min_value <= value <= self.max_value):
            # Можно просто ограничивать значение, но лучше явно указывать ошибку в логике.
            # Для простоты ограничим.
            value = max(self.min_value, min(value, self.max_value))
        setattr(obj, self.private_name, value)


# --- Миксины ---
class CritMixin:
    """Миксин, добавляющий шанс критического удара."""
    crit_chance: float = 0.1  # 10% шанс по умолчанию
    crit_multiplier: float = 1.5

    def _check_crit(self) -> bool:
        import random
        return random.random() < self.crit_chance


class LoggerMixin:
    """Миксин для простого логирования действий."""
    def log(self, message: str):
        print(f"[{self.__class__.__name__}] {message}")


# --- Базовый класс Human ---
class Human(LoggerMixin):
    """Базовый класс для всех людей в игре."""
    # Используем дескрипторы для валидации
    hp = BoundedStat(0, 100)
    mp = BoundedStat(0, 100)
    strength = BoundedStat(1, 30)
    agility = BoundedStat(1, 30)
    intellect = BoundedStat(1, 30)

    def __init__(self, name: str, level: int = 1):
        self.name = name
        self.level = level

        # Инициализируем характеристики через дескрипторы
        self.hp = 100
        self.mp = 50
        self.strength = 10
        self.agility = 10
        self.intellect = 10

    @property
    def is_alive(self) -> bool:
        """Свойство, проверяющее, жив ли персонаж."""
        return self.hp > 0

    def __str__(self) -> str:
        return f"{self.name} (Lvl {self.level}) - HP: {self.hp}, MP: {self.mp}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}', {self.level})"


# --- Абстрактный класс Character ---
class Character(Human, ABC):
    """Абстрактный класс, представляющий игрового персонажа."""

    def __init__(self, name: str, level: int = 1):
        super().__init__(name, level)
        self._cooldowns = {}  # Словарь для отслеживания кулдаунов навыков {skill_name: rounds_left}

    @abstractmethod
    def basic_attack(self, target: 'Character') -> str:
        """Базовая атака. Должна быть реализована в подклассах."""
        pass

    @abstractmethod
    def use_skill(self, target: 'Character', skill_name: str) -> str:
        """Использование навыка. Должна быть реализована в подклассах."""
        pass

    def _end_turn(self):
        """Вызывается в конце хода для уменьшения кулдаунов."""
        for skill in list(self._cooldowns.keys()):
            self._cooldowns[skill] -= 1
            if self._cooldowns[skill] <= 0:
                del self._cooldowns[skill]

    def _put_skill_on_cooldown(self, skill_name: str, cooldown: int):
        """Помещает навык на перезарядку."""
        self._cooldowns[skill_name] = cooldown

    def is_skill_on_cooldown(self, skill_name: str) -> bool:
        """Проверяет, находится ли навык на перезарядке."""
        return skill_name in self._cooldowns and self._cooldowns[skill_name] > 0