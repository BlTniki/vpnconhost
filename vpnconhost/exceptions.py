
class EntityException(Exception):
    """Базовое исключение для ошибок работы с сущностями."""
    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message


class EntityValidationFailedException(EntityException):
    """Ошибка валидации сущности."""
    pass


class EntityNotExistsException(EntityException):
    """Сущность не найдена."""
    pass


class EntityAlreadyExistsException(EntityException):
    """Сущность уже существует или нарушено ограничение уникальности."""
    pass
