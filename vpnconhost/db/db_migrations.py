"""Модуль для управления миграциями и валидацией схемы БД.
Собирает миграции из папки `.migrations` и применяет их по необходимости.
Также инициализирует таблицу версий схемы БД при первой миграции.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, LiteralString
import logging
import sqlite3
import os
import importlib

from vpnconhost.config import Config


logger = logging.getLogger(__name__)





# SQL экзекьютор для выполнения миграций и валидации схемы БД
class MigrationExecutor(ABC):
    """Обёртка вокруг драйвера БД. Используется только для миграций и валидации схемы БД.
    Не предоставляет управление транзакциями,
    подключение открывается и закрывается для каждого запроса.
    """
    @staticmethod
    @abstractmethod
    def execute(queries: list[LiteralString], **kwargs: Any) -> list[list[tuple[Any, ...]]]:
        """Выполняет переданные запросы с параметрами
          и возвращает ответ в виде списка списка кортежей."""


class SQLiteMigrationExecutor(MigrationExecutor):
    """Реализация `MigrationExecutor` для работы с sqlite.
    Более подробное описание назначения можно увидеть в `MigrationExecutor`
    """

    @staticmethod
    def execute(queries: list[LiteralString], **kwargs: Any) -> list[list[tuple[Any, ...]]]:
        logger.debug("Opening new connection for migration executor")
        with sqlite3.connect(Config.DB_URI, timeout=20) as conn:
            logger.debug("Connection opened")
            cur = conn.cursor()
            results:list[list[tuple[Any, ...]]] = []
            for query in queries:
                logger.debug("Executing query: %s", query)
                cur.execute(query, kwargs)
                results.append(cur.fetchall())
        return results

# дата класс для хранения миграции
@dataclass(frozen=True)
class Migration:
    """
    Представляет миграцию схемы БД.
    """
    prefix: str
    version: int
    name: str
    scripts: list[LiteralString]

    @staticmethod
    def build(filename: str, scripts: list[LiteralString]) -> "Migration":
        parts = filename.split('_', 2)
        if len(parts) != 3 or not parts[1].isdigit():
            raise ValueError(f"Invalid migration filename format: {filename}")
        return Migration(
            prefix=parts[0],
            version=int(parts[1]),
            name=parts[2],
            scripts=scripts
        )

    def __str__(self) -> str:
        return f"{self.prefix}_{self.version:04d}_{self.name}"


class DbMigrator:
    """Класс для управления миграциями и валидацией схемы БД.
    Использует `MigrationExecutor` для выполнения запросов.
    """
    def __init__(self, executor: type[MigrationExecutor]) -> None:
        self.executor = executor

    def _load_migrations(self) -> list[Migration]:
        """Загружает список миграций из папки `migrations`
        """
        migrations_dir = os.path.dirname(__file__) + '/migrations'
        logger.debug("Loading migrations from directory: %s", migrations_dir)
        migration_files = [
            f for f in os.listdir(migrations_dir) if f.startswith('M_') and f.endswith('.py')
        ]
        migrations:list[Migration] = []
        for fname in migration_files:
            mod_name = f'.migrations.{fname[:-3]}'
            mod = importlib.import_module(mod_name, package=__package__)
            mod_scripts = getattr(mod, 'scripts')
            if mod_scripts:
                migrations.append(Migration.build(fname, mod_scripts))
        migrations.sort(key=lambda m: m.version)
        return migrations

    def _get_current_schema_version(self) -> int | None:
        """Получает текущую версию схемы из таблицы schema_migrations.
        Если таблицы нет, возвращает None.
        """
        table_name = 'schema_migrations'
        check_table_query = """
            SELECT 1
            FROM sqlite_master
            WHERE type='table' AND name = :table_name
            LIMIT 1
        """

        table_exists = self.executor.execute(
            [check_table_query],
            table_name=table_name
        )
        if not table_exists or not table_exists[0]:
            return None
        get_version_query = f"SELECT version FROM {table_name} order by version desc limit 1"
        version_result = self.executor.execute([get_version_query])
        if version_result[0] and version_result[0][0][0] is not None:
            return version_result[0][0][0]
        return None

    def _apply_migration(self, migration:Migration) -> None:
        """
        Применяет миграцию и
        Обновляет текущую версию схемы в таблице schema_migrations
        """
        # По сути просто дописываем в конец обновление версии в schema_migrations
        # Чтобы это точно было в одной транзакции
        migration_queries:list[LiteralString] = [
            *migration.scripts,
            """
            INSERT INTO schema_migrations (version, full_name)
            VALUES (:version, :full_name)
            """
        ]
        self.executor.execute(
            migration_queries,
            version=migration.version,
            full_name=str(migration)
        )

    def apply_migrations(self) -> None:
        """
        Сверяет текущую версию схемы БД с версиями миграций, приставленных в `.migrations`.
        Если текущая версия меньше, чем последняя миграция, применяет все необходимые миграции
        """
        # 1. Получить список миграций
        migrations = self._load_migrations()
        if not migrations or migrations[0].version != 0:
            logger.fatal(
                "Migration directory is empty or missing the initial migration." \
                " There must be at least the M_0000_init_schema_migrations migration."
            )
            raise RuntimeError("No migrations found.")

        # 2. Определяем текущую версию схемы
        current_version = self._get_current_schema_version()
        logger.info("Current DB schema version: %s", current_version)

        # 3. Фильтруем миграции, которые нужно применить
        migrations_to_apply_filter = filter(
            lambda m: current_version is None or m.version > current_version, migrations
        )

        # 4. Применить недостающие миграции
        for migration in migrations_to_apply_filter:
            logger.info("Applying migration: %s", migration)
            self._apply_migration(migration)
            logger.info("Migration applied: %s", migration)

        logger.info("DB schema is up to date")
