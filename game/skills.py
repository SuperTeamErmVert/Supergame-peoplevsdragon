from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List
from game.exceptions import InvalidTargetError, CharacterDeadError

if TYPE_CHECKING:
    from game.core import Character

# --- Система эффектов ---
class Effect(ABC):
    """Абстрактный базовый класс для всех эффектов (баффы, дебаффы)."""
    def __init__(self, name: str, duration: int):
        self.name = name
        self.duration = duration
        self.remaining_duration = duration

    @abstractmethod
    def apply_start_effect(self, target: 'Character') -> str:
        """Применяется при наложении эффекта."""
        pass

    @abstractmethod
    def apply_end_of_turn_effect(self, target: 'Character') -> str:
        """Применяется в конце хода цели (например, урон от яда)."""
        pass

    @abstractmethod
    def apply_end_effect(self, target: 'Character') -> str:
        """Применяется при снятии эффекта."""
        pass

    def is_expired(self) -> bool:
        """Проверяет, истекло ли время действия эффекта."""
        return self.remaining_duration <= 0

    def decrease_duration(self):
        """Уменьшает длительность эффекта на 1 ход."""
        self.remaining_duration -= 1

    def __str__(self):
        return f"{self.name} ({self.remaining_duration} turns)"


class PoisonEffect(Effect):
    """Эффект яда, наносит урон в конце хода."""
    def __init__(self, damage_per_turn: int, duration: int):
        super().__init__("Poison", duration)
        self.damage_per_turn = damage_per_turn

    def apply_start_effect(self, target: 'Character') -> str:
        return f"{target.name} отравлен! Будет терять {self.damage_per_turn} HP за ход."

    def apply_end_of_turn_effect(self, target: 'Character') -> str:
        if not target.is_alive:
            return ""
        target.hp -= self.damage_per_turn
        return f"{target.name} получает {self.damage_per_turn} урона от яда. Осталось HP: {target.hp}"

    def apply_end_effect(self, target: 'Character') -> str:
        return f"Эффект яда на {target.name} закончился."


class ShieldEffect(Effect):
    """Эффект щита, поглощает определенное количество урона."""
    def __init__(self, shield_strength: int, duration: int):
        super().__init__("Shield", duration)
        self.shield_strength = shield_strength
        self.initial_strength = shield_strength

    def apply_start_effect(self, target: 'Character') -> str:
        return f"{target.name} получает щит, поглощающий {self.shield_strength} урона."

    def apply_end_of_turn_effect(self, target: 'Character') -> str:
        # Щит не наносит урон/лечение в конце хода, просто висит
        return ""

    def apply_end_effect(self, target: 'Character') -> str:
        return f"Щит {target.name} иссяк."

    def absorb_damage(self, damage: int) -> int:
        """Поглощает урон. Возвращает оставшийся непоглощенный урон."""
        if damage <= self.shield_strength:
            self.shield_strength -= damage
            return 0
        else:
            remaining_damage = damage - self.shield_strength
            self.shield_strength = 0
            self.remaining_duration = 0  # Щит сломан
            return remaining_damage


# --- Базовый класс для навыков ---
class Skill(ABC):
    """Абстрактный базовый класс для навыков персонажей."""
    def __init__(self, name: str, mp_cost: int, cooldown: int):
        self.name = name
        self.mp_cost = mp_cost
        self.cooldown = cooldown

    @abstractmethod
    def use(self, user: 'Character', target: 'Character') -> str:
        """Использование навыка. Возвращает строку с результатом."""
        pass

    # ... существующие эффекты ...

    class StunEffect(Effect):
        """Эффект оглушения - персонаж пропускает ход."""

        def __init__(self, duration: int):
            super().__init__("Stun", duration)

        def apply_start_effect(self, target: 'Character') -> str:
            return f"{target.name} оглушен и пропустит ход!"

        def apply_end_of_turn_effect(self, target: 'Character') -> str:
            # В конце хода снимаем оглушение
            self.remaining_duration = 0
            return f"{target.name} больше не оглушен!"

        def apply_end_effect(self, target: 'Character') -> str:
            return f"Эффект оглушения на {target.name} закончился."

        def should_skip_turn(self) -> bool:
            """Проверяет, должен ли персонаж пропустить ход."""
            return self.remaining_duration > 0