from abc import ABC, abstractmethod
from typing import Any, LiteralString
import logging
import dataclasses


logger = logging.getLogger(__name__)

class UniqueConstraintError(Exception):
    """Raised when a unique constraint is violated in the database."""


class DBExecutor(ABC):
    """Обёртка вокруг драйвера ДБ.
    Предоставляет абстрагированный от конкретной реализации драйвера функционал:
    - Управление соединением к ДБ (открытие, закрытие, использование пула)
    - Управление транзакциями

    Использование предполагает что на каждый поток один `DBExecutor`
    """
    @abstractmethod
    def open(self) -> None:
        """Открывает соединение и транзакцию. Позволяет вызывать `.execute()`.

        Если соединение уже открыто, то повторный вызов метода бросит исключение.
        Это делается для исключения повторного вызова метода во вложенной функции.
        `DBExecutor` не даёт гарантий, что если во вложенной функции
        будет вызван метод `.close()`, то он не закроет соединение на всех уровнях
        """

    @abstractmethod
    def close(self) -> None:
        """Закрывает соединение"""

    @abstractmethod
    def commit_and_close(self) -> None:
        """Закрывает соединение и коммитит транзакцию"""

    @abstractmethod
    def rollback_and_close(self) -> None:
        """Закрывает соединение и откатывает транзакцию"""

    @abstractmethod
    def execute(self, query: LiteralString, **kwargs: Any) -> list[tuple[Any, ...]]:
        """Выполняет переданный запрос с параметрами и возвращает ответ в виде списка кортежей.

        Перед вызовом метода необходимо открыть соединение, вызвав `.open()`
        """


class DataModel(object):
    """Базовый класс для моделей данных, реализованных через dataclass.
    """
    @classmethod
    def get_model_fields(cls) -> list[str]:
        """
        Возвращает список полей модели в порядке их объявления.
        Работает для всех dataclass, унаследованных от DataModel.
        """
        # Проверяем, что cls является dataclass
        if not dataclasses.is_dataclass(cls):
            raise TypeError(f"{cls.__name__} is not a dataclass")
        return [field.name for field in dataclasses.fields(cls)]

    @classmethod
    def get_model_fields_joined(cls, sep:str=', ') -> LiteralString:
        """
        Возвращает строку с перечислением полей модели в порядке их объявления, разделённых `sep`.
        Работает для всех dataclass, унаследованных от DataModel.

        По сути, это просто для каста `get_model_fields()` в `LiteralString`,
        чтобы типизатор не ругался.
        """
        # Trust me, pyright, it's LiteralString
        joined_fields:LiteralString = sep.join(
            cls.get_model_fields()
        ) # pyright: ignore[reportAssignmentType]
        return joined_fields
