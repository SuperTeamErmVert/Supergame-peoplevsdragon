from game.characters import Healer, Warrior
import random
from typing import List, Iterator
from game.core import Character
from game.exceptions import CharacterDeadError, InvalidTargetError


class TurnOrder:
    """Итератор для определения порядка ходов на основе ловкости."""

    def __init__(self, participants: List[Character]):
        # Сортируем участников по ловкости (по убыванию)
        self.participants = sorted(participants, key=lambda char: char.agility, reverse=True)
        self.index = 0

    def __iter__(self) -> Iterator[Character]:
        return self

    def __next__(self) -> Character:
        if self.index >= len(self.participants):
            self.index = 0  # Сбрасываем индекс для нового раунда
            # Проверяем, есть ли живые участники
            alive_participants = [p for p in self.participants if p.is_alive]
            if not alive_participants:
                raise StopIteration
        # Берем следующего участника
        participant = self.participants[self.index]
        self.index += 1
        # Пропускаем мертвых
        if not participant.is_alive:
            return self.__next__()
        return participant


class EffectManager:
    """Класс для управления эффектами на персонажах."""

    @staticmethod
    def apply_end_of_turn_effects(character: Character) -> List[str]:
        """Применяет эффекты конца хода к персонажу и возвращает список сообщений."""
        results = []
        if not character.is_alive:
            return results
        if hasattr(character, 'active_effects'):
            # Проходим по копии списка, чтобы безопасно удалять элементы
            for effect in character.active_effects[:]:
                effect_message = effect.apply_end_of_turn_effect(character)
                if effect_message:
                    results.append(effect_message)
                effect.decrease_duration()
                if effect.is_expired():
                    character.active_effects.remove(effect)
                    results.append(effect.apply_end_effect(character))
        return results


class Battle:
    """Основной класс, управляющий ходом боя."""

    def __init__(self, party: List[Character], boss: Character):
        self.party = party
        self.boss = boss
        self.turn_order = TurnOrder(self.party + [self.boss])
        self.round_number = 0
        self.effect_manager = EffectManager()
        self.log = []  # Лог боя

    def _log_event(self, event: str):
        """Добавляет событие в лог и выводит на экран."""
        self.log.append(event)
        print(event)

    def _is_valid_target(self, user: Character, target: Character, skill_type: str = "attack") -> bool:
        """Проверяет, является ли цель валидной для навыка."""
        if not target.is_alive:
            return False

        # Герои не могут лечить или защищать босса
        if user in self.party and target == self.boss:
            if skill_type in ["heal", "shield", "buff"]:
                return False

        # Босс не может лечить или защищать героев
        if user == self.boss and target in self.party:
            if skill_type in ["heal", "shield", "buff"]:
                return False

        return True

    def check_win_conditions(self) -> bool:
        """Проверяет условия окончания боя. Возвращает True, если бой окончен."""
        if not self.boss.is_alive:
            self._log_event(f">>> Победа! {self.boss.name} повержен! <<<")
            return True
        if all(not char.is_alive for char in self.party):
            self._log_event(f">>> Поражение! Все члены пати мертвы. <<<")
            return True
        return False

    def start(self):
        """Запускает основной игровой цикл."""
        self._log_event("=== НАЧАЛО БОЯ ===")
        self._log_event(f"Пати: {[char.name for char in self.party]} против Босса: {self.boss.name}")

        # Основной цикл раундов
        for current_actor in self.turn_order:
            if self.check_win_conditions():
                break

            # Начало раунда, если первый участник в порядке хода
            if self.turn_order.index == 1:
                self.round_number += 1
                self._log_event(f"\n--- Раунд {self.round_number} ---")

            self._log_event(f"\nХод {current_actor.name}:")

            # Проверяем оглушение
            if hasattr(current_actor, 'stunned') and current_actor.stunned:
                self._log_event(f"  {current_actor.name} оглушен и пропускает ход!")
                current_actor.stunned = False
                current_actor._end_turn()
                continue

            # Ход персонажа пати
            if current_actor in self.party:
                self._handle_party_member_turn(current_actor)
            # Ход босса
            else:
                self._handle_boss_turn(current_actor)

            # Применяем эффекты конца хода для текущего действующего лица
            effect_messages = self.effect_manager.apply_end_of_turn_effects(current_actor)
            for msg in effect_messages:
                self._log_event(f"  [Эффект] {msg}")

            # Проверяем условия после хода
            if self.check_win_conditions():
                break

        self._log_event("\n=== БОЙ ОКОНЧЕН ===")

    def _handle_party_member_turn(self, character: Character):
        """Обрабатывает ход члена пати."""
        try:
            if character.is_alive:
                # Умный ИИ для пати: выбирает действие в зависимости от ситуации
                action_result = self._choose_party_action(character)
                self._log_event(f"  {action_result}")
        except CharacterDeadError:
            self._log_event(f"  {character.name} мертв и не может действовать.")
        except InvalidTargetError as e:
            self._log_event(f"  {e}")
        except Exception as e:
            self._log_event(f"  Ошибка во время хода {character.name}: {e}")

        # Завершаем ход персонажа (уменьшаем кулдауны)
        character._end_turn()

    def _choose_party_action(self, character: Character) -> str:
        """Выбирает оптимальное действие для персонажа пати."""
        # Определяем тип персонажа
        is_healer = isinstance(character, Healer)
        is_tank = isinstance(character, Warrior)

        # Находим цели
        alive_allies = [char for char in self.party if char != character and char.is_alive]
        wounded_allies = [char for char in alive_allies if char.hp < char.hp * 0.6]  # Союзники с HP < 60%

        # Логика для целителя
        if is_healer and wounded_allies:
            # Целитель лечит раненых союзников
            target = min(wounded_allies, key=lambda char: char.hp)
            if hasattr(character, 'skills') and 'heal' in character.skills:
                skill = character.skills['heal']
                if not character.is_skill_on_cooldown('heal') and character.mp >= skill.mp_cost:
                    if self._is_valid_target(character, target, "heal"):
                        return character.use_skill(target, 'heal')

        # Логика для танка (воина)
        if is_tank and hasattr(character, 'skills') and 'divine_shield' in character.skills:
            # Танк защищает самого раненого союзника
            if wounded_allies:
                target = min(wounded_allies, key=lambda char: char.hp)
                skill = character.skills['divine_shield']
                if not character.is_skill_on_cooldown('divine_shield') and character.mp >= skill.mp_cost:
                    if self._is_valid_target(character, target, "shield"):
                        return character.use_skill(target, 'divine_shield')

        # Все атакуют босса (если он жив)
        if self.boss.is_alive:
            # 70% шанс использовать базовую атаку, 30% - навык
            if random.random() < 0.7 or not hasattr(character, 'skills'):
                return character.basic_attack(self.boss)
            else:
                # Ищем доступный атакующий навык (не лечение/щит)
                attack_skills = [sk_name for sk_name in character.skills.keys()
                                 if sk_name not in ['heal', 'divine_shield']]
                for skill_name in attack_skills:
                    skill = character.skills[skill_name]
                    if (not character.is_skill_on_cooldown(skill_name) and
                            character.mp >= skill.mp_cost):
                        return character.use_skill(self.boss, skill_name)
                # Если нет доступных атакующих навыков - базовая атака
                return character.basic_attack(self.boss)
        else:
            return f"{character.name} ищет цель, но все враги повержены!"

    def _handle_boss_turn(self, boss: Character):
        """Обрабатывает ход босса."""
        try:
            action_result = boss.take_turn(self.party)
            self._log_event(f"  {action_result}")
        except CharacterDeadError:
            self._log_event(f"  {boss.name} мертв и не может действовать.")
        # Завершаем ход босса
        boss._end_turn()