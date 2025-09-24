class GameException(Exception):
    """Базовое исключение для всех ошибок в игре."""
    pass

class NotEnoughMPError(GameException):
    """Вызывается, когда не хватает маны для использования навыка."""
    pass

class SkillOnCooldownError(GameException):
    """Вызывается, когда навык еще на перезарядке."""
    pass

class CharacterDeadError(GameException):
    """Вызывается при попытке совершить действие мертвым персонажем."""
    pass

class InvalidTargetError(GameException):
    """Вызывается при неверной цели для навыка."""
    pass