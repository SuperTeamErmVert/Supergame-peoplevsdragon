import random
from game.characters import Warrior, Mage, Healer, Boss


def select_character_class(name: str) -> object:
    """Позволяет пользователю выбрать класс для персонажа."""
    print(f"\nВыберите класс для персонажа {name}:")
    print("1. Воин (Warrior) - высокий урон, много HP")
    print("2. Маг (Mage) - магические атаки, контроль")
    print("3. Целитель (Healer) - лечение, поддержка")

    while True:
        try:
            choice = int(input("Введите номер класса (1-3): "))
            if choice == 1:
                return Warrior
            elif choice == 2:
                return Mage
            elif choice == 3:
                return Healer
            else:
                print("Пожалуйста, введите число от 1 до 3")
        except ValueError:
            print("Пожалуйста, введите корректное число")


def create_party() -> list:
    """Создает пати персонажей с настройками от пользователя."""
    party = []
    print("=== СОЗДАНИЕ ПАТИ ===")

    # Запрашиваем количество персонажей
    while True:
        try:
            party_size = int(input("Сколько персонажей будет в пати (3-4)? "))
            if 3 <= party_size <= 4:
                break
            else:
                print("Пожалуйста, введите 3 или 4")
        except ValueError:
            print("Пожалуйста, введите корректное число")

    # Создаем каждого персонажа
    for i in range(party_size):
        print(f"\n--- Персонаж {i + 1} ---")

        # Имя персонажа
        name = input(f"Введите имя персонажа {i + 1}: ").strip()
        if not name:
            name = f"Герой {i + 1}"

        # Уровень персонажа
        while True:
            try:
                level = int(input(f"Введите уровень для {name} (1-10): "))
                if 1 <= level <= 10:
                    break
                else:
                    print("Пожалуйста, введите число от 1 до 10")
            except ValueError:
                print("Пожалуйста, введите корректное число")

        # Класс персонажа
        char_class = select_character_class(name)
        character = char_class(name, level)
        party.append(character)

        print(f"Создан: {character}")

    return party


def configure_boss() -> Boss:
    """Настраивает босса."""
    print("\n=== НАСТРОЙКА БОССА ===")

    # Имя босса
    name = input("Введите имя босса (или нажмите Enter для стандартного): ").strip()
    if not name:
        name = "Дракон Урлог"

    # Уровень босса
    while True:
        try:
            level = int(input("Введите уровень босса (5-20): "))
            if 5 <= level <= 20:
                break
            else:
                print("Пожалуйста, введите число от 5 до 20")
        except ValueError:
            print("Пожалуйста, введите корректное число")

    boss = Boss(name, level)
    print(f"Создан босс: {boss}")
    return boss


def set_random_seed():
    """Устанавливает seed для генератора случайных чисел."""
    print("\n=== НАСТРОЙКА СЛУЧАЙНОСТИ ===")
    print("Хотите установить seed для повторяемости результатов?")
    print("1. Да, установить конкретный seed")
    print("2. Нет, использовать полностью случайную генерацию")

    while True:
        try:
            choice = int(input("Введите номер варианта (1-2): "))
            if choice == 1:
                seed = input("Введите числовой seed: ").strip()
                if seed.isdigit():
                    random.seed(int(seed))
                    print(f"Установлен seed: {seed}")
                else:
                    random.seed(hash(seed))
                    print(f"Установлен seed на основе строки: {seed}")
                break
            elif choice == 2:
                print("Используется случайная генерация")
                break
            else:
                print("Пожалуйста, введите 1 или 2")
        except ValueError:
            print("Пожалуйста, введите корректное число")


def display_party_info(party: list):
    """Отображает информацию о пати."""
    print("\n=== ВАША ПАТИ ===")
    for i, character in enumerate(party, 1):
        print(f"{i}. {character}")
        if hasattr(character, 'skills'):
            print(f"   Навыки: {', '.join(character.skills.keys())}")


def main():
    print("Добро пожаловать в мини-игру 'Пати против Босса'!")
    print("=" * 50)

    # Настройка случайности
    set_random_seed()

    # Создание пати
    party = create_party()

    # Настройка босса
    boss = configure_boss()

    # Показываем информацию о командах
    display_party_info(party)
    print(f"\nБосс: {boss}")

    # Подтверждение начала боя
    input("\nНажмите Enter чтобы начать бой...")

    # Импортируем Battle здесь, чтобы избежать циклических импортов
    from game.battle import Battle

    # Создаем и начинаем бой
    battle = Battle(party, boss)
    battle.start()


if __name__ == "__main__":
    main()