"""Модуль для работы с sql базой данных.
Гарантирует безопасную работу и корректную утилизацию ресурсов приложения
в окружении множества воркеров и множества потоков в параллели.

При корректном использовании модуля для каждого воркера будет свой пул соединений
и для каждого потока свой экзекьютер запросов, безопасно обрабатывая транзакции и избегая гонок

Пример корректного использования:
```python
from db import get_db_executor

# !!! Важно !!!
# Вызывать get_db_executor() нужно внутри функции, которая обрабатывает запрос
# Тем самым гарантируется, что для каждого потока будет свой экземпляр и свой пул
db_executor = get_db_executor()
db_executor.open()
try:
    db_executor.execute(...)
    ...
    db_executor.execute(...)
    db_executor.commit_and_close()
except Exception
    db_executor.rollback_and_close()
    ...

# Или, если используется аннотация "@auto_transaction()"
from db import get_db_executor, auto_transaction

@auto_transaction()
def foo(...):
    db_executor = get_db_executor()
    # Транзакция уже открыта
    db_executor.execute(...)
    # Корректная обработка вложенных вызовов аннотированных функций
    foo()
    # Транзакция закроется сама
    return ...
```
"""
import threading
from typing import Callable, TypeVar, ParamSpec
from functools import wraps
import weakref
import logging

from config import Config
from .db import DBExecutor, DataModel, UniqueConstraintError
from .sqllite_db import SQLiteExecutor, validate_connection

# Строгое ограничение для импорта внешним кодом
# Модуль может гарантировать что либо, только при правильном использовании
# Поэтому вставляю все палки в колёса необдуманному использованию
__all__ = ["DBExecutor", "get_db_executor", "auto_transaction",
           "validate_connection", "DataModel", "UniqueConstraintError"]
def __getattr__(name:str):
    if name not in __all__:
        raise ImportError(
            f"Restricted access! Cannot import '{name}' from {__name__}. Use only {__all__}"
        )
    return globals()[name]


logger = logging.getLogger(__name__)


_thread_local = threading.local()

def _create_executor() -> DBExecutor:
    """Создаёт `DBExecutor` и вешает на него хук для его закрытия перед удалением Garbage Collector
    """
    executor = SQLiteExecutor(Config.DB_URI)
    # Освободить ресурсы при уничтожении объекта
    # Думаю это можно назвать хуком, который будет вызван сборщиком мусора
    weakref.finalize(executor, executor.close)
    return executor


def get_db_executor() -> DBExecutor:
    """Возвращает `DBExecutor` для конкретного потока.
    Инициализирует `DBExecutor`, если он еще создан для потока
    """
    if not hasattr(_thread_local, "executor"):
        _thread_local.executor = _create_executor()
    return _thread_local.executor


P = ParamSpec("P")          # Параметры оборачиваемой функции
R = TypeVar("R")            # Возвращаемое значение оборачиваемой функции

def auto_transaction(
    always_rollback: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Враппер для функции.
    Управляет подключением и транзакцией `DBExecutor` на время работы функции.
    Открывает транзакцию на входе в функцию и закрывает её после выхода из функции.
    Также имеет флаг `always_rollback`, если мы всегда хотим откатить транзакцию в конце.
    Полезно для тестов.

    **Использование**: Добавить перед определением функции аннотацию `@auto_transaction()`.
    Обязательно со скобками.

    Враппер служит для упрощения работы с `DBExecutor`. Типовое использование предполагает
    использование в качестве аннотации для функции.
    В Аннотированной функции теперь достаточно получить `DBExecutor` через `get_db_executor()`
    и вызывать только `.execute(...)`, не заботясь о подключении и транзакции.

    Данный враппер учитывает повторное использование во вложенном вызове функции.
    То есть: транзакция откроется только на входе в первую аннотированную функцию
    и закроется только после выхода из первой функции.

    Таким образом общая рекомендация по использованию аннотации: добавлять её в любую функцию,
    где есть работа с `DBExecutor`
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            _thread_local.tx_depth = getattr(_thread_local, "tx_depth", 0) + 1
            logger.debug("auto_transaction: call depth: %d", _thread_local.tx_depth)

            db_executor = get_db_executor()

            if _thread_local.tx_depth == 1:
                logger.debug("auto_transaction: opening the transaction")
                db_executor.open()

            try:
                logger.debug("auto_transaction: call wrapped func")
                result = func(*args, **kwargs)

                if _thread_local.tx_depth == 1:
                    if always_rollback:
                        logger.debug(
                            "auto_transaction: always_rollback=True → rollback"
                        )
                        db_executor.rollback_and_close()
                    else:
                        logger.debug("auto_transaction: commit the transaction")
                        db_executor.commit_and_close()

                return result

            except Exception:
                logger.debug(
                    "auto_transaction: caught exception on call depth: %d",
                    _thread_local.tx_depth
                )

                if _thread_local.tx_depth == 1:
                    logger.debug("auto_transaction: rollback the transaction")
                    db_executor.rollback_and_close()
                raise

            finally:
                _thread_local.tx_depth -= 1

        return wrapper

    return decorator
