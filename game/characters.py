from abc import ABC, abstractmethod
import random
from typing import List, Dict
from game.core import Character, CritMixin
from game.skills import Skill, Effect, PoisonEffect, ShieldEffect
from game.exceptions import NotEnoughMPError, SkillOnCooldownError, CharacterDeadError, InvalidTargetError

# Базовые характеристики по уровням
BASE_STATS = {
    1: {'hp': 100, 'mp': 50, 'strength': 10, 'agility': 10, 'intellect': 10},
    5: {'hp': 150, 'mp': 75, 'strength': 15, 'agility': 15, 'intellect': 15},
    10: {'hp': 200, 'mp': 100, 'strength': 20, 'agility': 20, 'intellect': 20},
    20: {'hp': 300, 'mp': 150, 'strength': 30, 'agility': 30, 'intellect': 30}
}


def get_scaled_stats(level: int) -> dict:
    """Возвращает характеристики, масштабированные под уровень."""
    levels = sorted(BASE_STATS.keys())
    if level <= levels[0]:
        return BASE_STATS[levels[0]]
    elif level >= levels[-1]:
        return BASE_STATS[levels[-1]]
    else:
        # Интерполяция между ближайшими уровнями
        for i in range(len(levels) - 1):
            if levels[i] <= level <= levels[i + 1]:
                low_level = levels[i]
                high_level = levels[i + 1]
                ratio = (level - low_level) / (high_level - low_level)

                low_stats = BASE_STATS[low_level]
                high_stats = BASE_STATS[high_level]

                scaled_stats = {}
                for stat in low_stats.keys():
                    scaled_stats[stat] = int(low_stats[stat] + (high_stats[stat] - low_stats[stat]) * ratio)
                return scaled_stats
    return BASE_STATS[levels[0]]


# --- Навыки для игровых классов ---
class SwingSword(Skill):
    """Простая атака мечом для Воина."""

    def __init__(self):
        super().__init__(name="Swing Sword", mp_cost=0, cooldown=0)

    def use(self, user: Character, target: Character) -> str:
        if not target.is_alive:
            raise InvalidTargetError("Нельзя атаковать мертвого персонажа!")
        base_damage = user.strength + random.randint(1, 5)
        # Проверка на крит от пользователя (если он имеет CritMixin)
        if isinstance(user, CritMixin) and user._check_crit():
            base_damage = int(base_damage * user.crit_multiplier)
            target.hp -= base_damage
            return f"{user.name} наносит критический удар мечом {target.name} на {base_damage} урона!"
        else:
            target.hp -= base_damage
            return f"{user.name} атакует мечом {target.name} и наносит {base_damage} урона."


class HeavySlam(Skill):
    """Мощный удар воина."""

    def __init__(self):
        super().__init__(name="Heavy Slam", mp_cost=10, cooldown=3)

    def use(self, user, target):
        if not target.is_alive:
            raise InvalidTargetError("Нельзя атаковать мертвого персонажа!")
        if user.mp < self.mp_cost:
            raise NotEnoughMPError(f"Не хватает маны для использования {self.name}.")
        user.mp -= self.mp_cost
        damage = user.strength * 2 + random.randint(3, 7)
        target.hp -= damage
        return f"{user.name} обрушивает на {target.name} сокрушительный удар на {damage} урона!"


class Fireball(Skill):
    """Огненный шар для Мага."""

    def __init__(self):
        super().__init__(name="Fireball", mp_cost=15, cooldown=2)

    def use(self, user: Character, target: Character) -> str:
        if not target.is_alive:
            raise InvalidTargetError("Нельзя атаковать мертвого персонажа!")
        if user.mp < self.mp_cost:
            raise NotEnoughMPError(f"Не хватает маны для использования {self.name}. Нужно {self.mp_cost} MP.")
        user.mp -= self.mp_cost
        base_damage = user.intellect + random.randint(5, 10)
        target.hp -= base_damage
        # Шанс поджечь цель (эффект яда)
        if random.random() < 0.3:  # 30% шанс
            poison_effect = PoisonEffect(damage_per_turn=3, duration=3)
            if not hasattr(target, 'active_effects'):
                target.active_effects = []
            target.active_effects.append(poison_effect)
            return (f"{user.name} запускает огненный шар в {target.name} и наносит {base_damage} урона! "
                    f"{poison_effect.apply_start_effect(target)}")
        return f"{user.name} запускает огненный шар в {target.name} и наносит {base_damage} урона."


class ArcaneMissile(Skill):
    """Магические снаряды для Мага."""

    def __init__(self):
        super().__init__(name="Arcane Missile", mp_cost=10, cooldown=2)

    def use(self, user, target):
        if not target.is_alive:
            raise InvalidTargetError("Нельзя атаковать мертвого персонажа!")
        if user.mp < self.mp_cost:
            raise NotEnoughMPError(f"Не хватает маны для использования {self.name}.")
        user.mp -= self.mp_cost
        damage = user.intellect + random.randint(3, 6)
        # Несколько снарядов
        missile_count = 3
        total_damage = 0
        for i in range(missile_count):
            total_damage += damage
            target.hp -= damage
        return f"{user.name} выпускает {missile_count} магических снаряда в {target.name} на общий урон {total_damage}!"


class Heal(Skill):
    """Лечение для Целителя."""

    def __init__(self):
        super().__init__(name="Heal", mp_cost=20, cooldown=3)

    def use(self, user: Character, target: Character) -> str:
        if user.mp < self.mp_cost:
            raise NotEnoughMPError(f"Не хватает маны для использования {self.name}. Нужно {self.mp_cost} MP.")
        heal_amount = user.intellect + random.randint(8, 12)
        target.hp += heal_amount
        user.mp -= self.mp_cost
        return f"{user.name} лечит {target.name} на {heal_amount} HP."


class DivineShield(Skill):
    """Божественный щит для Целителя."""

    def __init__(self):
        super().__init__(name="Divine Shield", mp_cost=25, cooldown=4)

    def use(self, user, target):
        if user.mp < self.mp_cost:
            raise NotEnoughMPError(f"Не хватает маны для использования {self.name}.")
        user.mp -= self.mp_cost
        shield_effect = ShieldEffect(shield_strength=20, duration=2)
        if not hasattr(target, 'active_effects'):
            target.active_effects = []
        target.active_effects.append(shield_effect)
        return f"{user.name} наделяет {target.name} божественным щитом! {shield_effect.apply_start_effect(target)}"


# --- Навыки для Босса ---
class DragonBreath(Skill):
    """Дыхание дракона - урон по площади с шансом поджечь."""

    def __init__(self):
        super().__init__(name="Dragon Breath", mp_cost=30, cooldown=3)

    def use(self, user: Character, target: Character) -> str:
        return "Дракон готовится к дыханию!"


class TailSwipe(Skill):
    """Удар хвостом - высокий урон одной цели с шансом оглушения."""

    def __init__(self):
        super().__init__(name="Tail Swipe", mp_cost=15, cooldown=2)

    def use(self, user: Character, target: Character) -> str:
        if not target.is_alive:
            raise InvalidTargetError("Нельзя атаковать мертвого персонажа!")
        damage = user.strength * 2 + random.randint(5, 10)
        target.hp -= damage
        # Шанс оглушения (пропуск хода)
        if random.random() < 0.25:  # 25% шанс
            target.stunned = True
            return f"{user.name} бьет хвостом {target.name} на {damage} урона и оглушает его!"
        return f"{user.name} бьет хвостом {target.name} на {damage} урона!"


class WingBuffet(Skill):
    """Удар крылом - отталкивание и урон всем целям."""

    def __init__(self):
        super().__init__(name="Wing Buffet", mp_cost=20, cooldown=2)

    def use(self, user: Character, target: Character) -> str:
        return "Дракон взмахивает крыльями!"


class FearRoar(Skill):
    """Рык страха - снижение характеристик пати."""

    def __init__(self):
        super().__init__(name="Fear Roar", mp_cost=25, cooldown=4)

    def use(self, user: Character, target: Character) -> str:
        return "Дракон издает устрашающий рык!"


class SummonMinions(Skill):
    """Призыв миньонов - добавляет временных помощников."""

    def __init__(self):
        super().__init__(name="Summon Minions", mp_cost=40, cooldown=5)

    def use(self, user: Character, target: Character) -> str:
        return "Дракон призывает миньонов на помощь!"


class MeteorShower(Skill):
    """Метеоритный дождь - очень мощная АОЕ атака."""

    def __init__(self):
        super().__init__(name="Meteor Shower", mp_cost=50, cooldown=4)

    def use(self, user: Character, target: Character) -> str:
        return "Дракон призывает метеоритный дождь!"


class Earthquake(Skill):
    """Землетрясение - урон и снижение характеристик."""

    def __init__(self):
        super().__init__(name="Earthquake", mp_cost=40, cooldown=3)

    def use(self, user: Character, target: Character) -> str:
        return "Дракон вызывает землетрясение!"


# --- Игровые классы персонажей ---
class Warrior(Character, CritMixin):
    """Класс Воин. Сильный и живучий боец ближнего боя."""

    def __init__(self, name: str, level: int = 1):
        super().__init__(name, level)

        base_stats = get_scaled_stats(level)

        self.hp = int(base_stats['hp'] * 1.2)
        self.mp = int(base_stats['mp'] * 0.8)
        self.strength = int(base_stats['strength'] * 1.3)
        self.agility = int(base_stats['agility'] * 1.1)
        self.intellect = int(base_stats['intellect'] * 0.7)

        self.crit_chance = 0.10 + (level * 0.005)
        self.crit_multiplier = 1.5

        self.skills: Dict[str, Skill] = {
            "attack": SwingSword(),
            "heavy_slam": HeavySlam()
        }

    def basic_attack(self, target: Character) -> str:
        return self.skills["attack"].use(self, target)

    def use_skill(self, target: Character, skill_name: str = "heavy_slam") -> str:
        if skill_name not in self.skills:
            return f"У {self.name} нет навыка {skill_name}."
        skill = self.skills[skill_name]
        if self.is_skill_on_cooldown(skill_name):
            raise SkillOnCooldownError(f"Навык {skill_name} на перезарядке.")
        result = skill.use(self, target)
        self._put_skill_on_cooldown(skill_name, skill.cooldown)
        return result


class Mage(Character):
    """Класс Маг. Мощный заклинатель."""

    def __init__(self, name: str, level: int = 1):
        super().__init__(name, level)

        base_stats = get_scaled_stats(level)

        self.hp = int(base_stats['hp'] * 0.8)
        self.mp = int(base_stats['mp'] * 1.4)
        self.strength = int(base_stats['strength'] * 0.7)
        self.agility = int(base_stats['agility'] * 0.9)
        self.intellect = int(base_stats['intellect'] * 1.4)

        self.skills: Dict[str, Skill] = {
            "attack": Fireball(),
            "arcane_missile": ArcaneMissile()
        }

    def basic_attack(self, target: Character) -> str:
        return self.skills["attack"].use(self, target)

    def use_skill(self, target: Character, skill_name: str = "arcane_missile") -> str:
        if skill_name not in self.skills:
            return f"У {self.name} нет навыка {skill_name}."
        skill = self.skills[skill_name]
        if self.is_skill_on_cooldown(skill_name):
            raise SkillOnCooldownError(f"Навык {skill_name} на перезарядке.")
        result = skill.use(self, target)
        self._put_skill_on_cooldown(skill_name, skill.cooldown)
        return result


class Healer(Character):
    """Класс Целитель. Лечит союзников и накладывает баффы."""

    def __init__(self, name: str, level: int = 1):
        super().__init__(name, level)

        base_stats = get_scaled_stats(level)

        self.hp = int(base_stats['hp'] * 1.0)
        self.mp = int(base_stats['mp'] * 1.3)
        self.strength = int(base_stats['strength'] * 0.8)
        self.agility = int(base_stats['agility'] * 1.0)
        self.intellect = int(base_stats['intellect'] * 1.3)

        self.skills: Dict[str, Skill] = {
            "attack": Heal(),
            "divine_shield": DivineShield()
        }

    def basic_attack(self, target: Character) -> str:
        return self.skills["attack"].use(self, target)

    def use_skill(self, target: Character, skill_name: str = "divine_shield") -> str:
        if skill_name not in self.skills:
            return f"У {self.name} нет навыка {skill_name}."
        skill = self.skills[skill_name]
        if self.is_skill_on_cooldown(skill_name):
            raise SkillOnCooldownError(f"Навык {skill_name} на перезарядке.")
        result = skill.use(self, target)
        self._put_skill_on_cooldown(skill_name, skill.cooldown)
        return result


# --- Класс Босса ---
class Boss(Character):
    """Класс Босса. Меняет фазы в зависимости от HP и использует различные навыки."""

    class Strategy(ABC):
        @abstractmethod
        def execute(self, boss: 'Boss', party: List[Character]) -> str:
            pass

    class AggressiveStrategy(Strategy):
        def execute(self, boss: 'Boss', party: List[Character]) -> str:
            if random.random() < 0.8:
                return boss.use_random_skill(party)
            else:
                return boss.basic_attack_random_target(party)

    class AOEStrategy(Strategy):
        def execute(self, boss: 'Boss', party: List[Character]) -> str:
            if random.random() < 0.9:
                return boss.use_aoe_skill(party)
            else:
                return boss.basic_attack_random_target(party)

    class EnragedStrategy(Strategy):
        def execute(self, boss: 'Boss', party: List[Character]) -> str:
            if random.random() < 0.95:
                return boss.use_powerful_skill(party)
            else:
                return boss.basic_attack_random_target(party)

    def __init__(self, name: str, level: int = 5):
        super().__init__(name, level)

        base_stats = get_scaled_stats(level)

        self.hp = int(base_stats['hp'] * 3.0)
        self.mp = int(base_stats['mp'] * 2.0)
        self.strength = int(base_stats['strength'] * 2.0)
        self.agility = int(base_stats['agility'] * 1.5)
        self.intellect = int(base_stats['intellect'] * 1.8)

        self.max_hp = self.hp

        self.skills: Dict[str, Skill] = {
            "dragon_breath": DragonBreath(),
            "tail_swipe": TailSwipe(),
            "wing_buffet": WingBuffet(),
            "fear_roar": FearRoar(),
            "summon_minions": SummonMinions(),
            "meteor_shower": MeteorShower(),
            "earthquake": Earthquake()
        }

        self._strategies = {
            'aggressive': self.AggressiveStrategy(),
            'aoe': self.AOEStrategy(),
            'enraged': self.EnragedStrategy()
        }
        self._current_strategy = self._strategies['aggressive']

        self.minions = []
        self.phase = 1

    def basic_attack(self, target: Character) -> str:
        damage = self.strength + random.randint(5, 12)
        target.hp -= damage
        return f"{self.name} яростно атакует {target.name} и наносит {damage} урона!"

    def basic_attack_random_target(self, party: List[Character]) -> str:
        alive_targets = [char for char in party if char.is_alive]
        if not alive_targets:
            return "Все цели уже мертвы!"
        target = random.choice(alive_targets)
        return self.basic_attack(target)

    def use_skill(self, target: Character, skill_name: str = "") -> str:
        return self.use_random_skill([target] if target else [])

    def use_random_skill(self, party: List[Character]) -> str:
        alive_targets = [char for char in party if char.is_alive]
        if not alive_targets:
            return "Все цели мертвы!"

        available_skills = []
        for skill_name, skill in self.skills.items():
            if (not self.is_skill_on_cooldown(skill_name) and
                    self.mp >= skill.mp_cost):
                available_skills.append((skill_name, skill))

        if not available_skills:
            return self.basic_attack_random_target(party)

        skill_name, skill = random.choice(available_skills)
        self.mp -= skill.mp_cost
        self._put_skill_on_cooldown(skill_name, skill.cooldown)

        if skill_name == "dragon_breath":
            return self._use_dragon_breath(alive_targets)
        elif skill_name == "tail_swipe":
            target = random.choice(alive_targets)
            return skill.use(self, target)
        elif skill_name == "wing_buffet":
            return self._use_wing_buffet(alive_targets)
        elif skill_name == "fear_roar":
            return self._use_fear_roar(alive_targets)
        elif skill_name == "summon_minions":
            return self._use_summon_minions()
        elif skill_name == "meteor_shower":
            return self._use_meteor_shower(alive_targets)
        elif skill_name == "earthquake":
            return self._use_earthquake(alive_targets)
        else:
            target = random.choice(alive_targets)
            return skill.use(self, target)

    def use_aoe_skill(self, party: List[Character]) -> str:
        alive_targets = [char for char in party if char.is_alive]
        if not alive_targets:
            return "Все цели мертвы!"

        aoe_skills = ["dragon_breath", "wing_buffet", "meteor_shower", "earthquake"]
        available_aoe_skills = []

        for skill_name in aoe_skills:
            skill = self.skills.get(skill_name)
            if (skill and not self.is_skill_on_cooldown(skill_name) and
                    self.mp >= skill.mp_cost):
                available_aoe_skills.append((skill_name, skill))

        if available_aoe_skills:
            skill_name, skill = random.choice(available_aoe_skills)
            self.mp -= skill.mp_cost
            self._put_skill_on_cooldown(skill_name, skill.cooldown)

            if skill_name == "dragon_breath":
                return self._use_dragon_breath(alive_targets)
            elif skill_name == "wing_buffet":
                return self._use_wing_buffet(alive_targets)
            elif skill_name == "meteor_shower":
                return self._use_meteor_shower(alive_targets)
            elif skill_name == "earthquake":
                return self._use_earthquake(alive_targets)
        else:
            return self.use_random_skill(party)

    def use_powerful_skill(self, party: List[Character]) -> str:
        alive_targets = [char for char in party if char.is_alive]
        if not alive_targets:
            return "Все цели мертвы!"

        powerful_skills = ["meteor_shower", "earthquake", "dragon_breath", "summon_minions"]
        available_powerful_skills = []

        for skill_name in powerful_skills:
            skill = self.skills.get(skill_name)
            if (skill and not self.is_skill_on_cooldown(skill_name) and
                    self.mp >= skill.mp_cost):
                available_powerful_skills.append((skill_name, skill))

        if available_powerful_skills:
            skill_name, skill = random.choice(available_powerful_skills)
            self.mp -= skill.mp_cost
            self._put_skill_on_cooldown(skill_name, skill.cooldown)

            if skill_name == "dragon_breath":
                return self._use_dragon_breath(alive_targets)
            elif skill_name == "meteor_shower":
                return self._use_meteor_shower(alive_targets)
            elif skill_name == "earthquake":
                return self._use_earthquake(alive_targets)
            elif skill_name == "summon_minions":
                return self._use_summon_minions()
        else:
            return self.use_aoe_skill(party)

    def _use_dragon_breath(self, targets: List[Character]) -> str:
        results = []
        for target in targets:
            damage = self.intellect + random.randint(15, 25)
            target.hp -= damage
            results.append(f"{target.name} получает {damage} урона от дыхания")

            if random.random() < 0.6:
                poison_effect = PoisonEffect(damage_per_turn=8, duration=3)
                if not hasattr(target, 'active_effects'):
                    target.active_effects = []
                target.active_effects.append(poison_effect)
                results.append(f"и горит!")

        return f"{self.name} извергает пламя! " + ". ".join(results)

    def _use_wing_buffet(self, targets: List[Character]) -> str:
        results = []
        for target in targets:
            damage = self.strength // 2 + random.randint(8, 15)
            target.hp -= damage
            results.append(f"{target.name} отброшен на {damage} урона")

            if random.random() < 0.5:
                target.agility = max(1, target.agility - 8)
                results.append(f"и дезориентирован")

        return f"{self.name} взмахивает крыльями! " + ". ".join(results)

    def _use_fear_roar(self, targets: List[Character]) -> str:
        results = []
        for target in targets:
            target.strength = max(1, target.strength - 5)
            target.intellect = max(1, target.intellect - 5)
            target.agility = max(1, target.agility - 3)
            results.append(f"{target.name} напуган")

        return f"{self.name} издает ужасающий рык! " + ". ".join(results) + ". Характеристики снижены!"

    def _use_summon_minions(self) -> str:
        minion_count = random.randint(2, 4)
        self.minions = [f"Миньон {i + 1}" for i in range(minion_count)]
        return f"{self.name} призывает {minion_count} миньонов! Они присоединятся к атаке в следующем раунде."

    def _use_meteor_shower(self, targets: List[Character]) -> str:
        results = []
        for target in targets:
            damage = self.intellect * 2 + random.randint(20, 35)
            target.hp -= damage
            results.append(f"{target.name} получает {damage} урона от метеоритов")

            if random.random() < 0.4:
                target.stunned = True
                results.append(f"и оглушен")

        return f"{self.name} призывает метеоритный дождь! " + ". ".join(results)

    def _use_earthquake(self, targets: List[Character]) -> str:
        results = []
        for target in targets:
            damage = self.strength + random.randint(10, 20)
            target.hp -= damage

            target.strength = max(1, target.strength - 4)
            target.intellect = max(1, target.intellect - 4)
            target.agility = max(1, target.agility - 6)

            results.append(f"{target.name} получает {damage} урона и ослаблен")

        return f"{self.name} вызывает землетрясение! " + ". ".join(results)

    def choose_strategy(self, party: List[Character]):
        hp_percentage = self.hp / self.max_hp

        if hp_percentage < 0.2:
            self._current_strategy = self._strategies['enraged']
            if self.phase != 3:
                self.phase = 3
                self.log(f"{self.name} впадает в ЯРОСТЬ! Его атаки становятся смертоносными!")
        elif hp_percentage < 0.5:
            self._current_strategy = self._strategies['aoe']
            if self.phase != 2:
                self.phase = 2
                self.log(f"{self.name} впадает в ярость и начинает атаковать всех сразу!")
        else:
            self._current_strategy = self._strategies['aggressive']
            if self.phase != 1:
                self.phase = 1

    def take_turn(self, party: List[Character]) -> str:
        if not self.is_alive:
            raise CharacterDeadError("Босс мертв и не может действовать.")

        self.choose_strategy(party)
        result = self._current_strategy.execute(self, party)

        if self.minions:
            minion_attack = self._minions_attack(party)
            if minion_attack:
                result += " " + minion_attack

        return result

    def _minions_attack(self, party: List[Character]) -> str:
        alive_targets = [char for char in party if char.is_alive]
        if not alive_targets or not self.minions:
            return ""

        results = []
        for minion in self.minions:
            target = random.choice(alive_targets)
            damage = random.randint(5, 10)
            target.hp -= damage
            results.append(f"{minion} атакует {target.name} на {damage} урона")

        if random.random() < 0.3:
            self.minions = []
            results.append("Миньоны исчезают!")

        return ". ".join(results)