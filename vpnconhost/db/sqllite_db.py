from typing import Any, LiteralString
import logging
import sqlite3

from sqlite3 import Connection, Cursor

from vpnconhost.config import Config

from .db import DBExecutor, UniqueConstraintError


logger = logging.getLogger(__name__)



def validate_connection() -> None:
    """
    Проверяет, что можно выполнить простейший запрос к базе.
    Создаёт временное соединение с таймаутом 20 секунд
    """
    logger.debug("Trying to connect to the database...")
    with sqlite3.connect(Config.DB_URI) as conn:
        logger.debug("Connection to the database established.")
        cur = conn.cursor()
        logger.debug("Executing test query...")
        cur.execute("SELECT 1").fetchone()
    logger.debug("Database connection validated successfully")


class SQLiteExecutor(DBExecutor):
    """Реализация `DBExecutor` для работы с sqlite.
    Более подробное описание назначения можно увидеть в `DBExecutor`
    """

    def __init__(self, db_uri: str) -> None:
        self.db_uri = db_uri
        self.conn: Connection | None = None
        self.cur: Cursor | None = None

    def open(self) -> None:
        if self.conn:
            raise RuntimeError(
                "Incorrect use: repeated .open() method"
                + " invocation when the connection is already open"
            )
        logger.debug("Opening new connection to the database")
        self.conn = sqlite3.connect(self.db_uri, timeout=20)
        self.cur = self.conn.cursor()

    def close(self) -> None:
        logger.debug("Closing connection")
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        self.conn = None
        self.cur = None

    def commit_and_close(self) -> None:
        logger.debug("Closing connection with commit")
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.commit()
            self.conn.close()
        self.conn = None
        self.cur = None

    def rollback_and_close(self) -> None:
        logger.debug("Closing connection with rollback")
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.rollback()
            self.conn.close()
        self.conn = None
        self.cur = None

    def execute(self, query: LiteralString, **kwargs: Any) -> list[tuple[Any, ...]]:
        if not self.conn or not self.cur:
            raise RuntimeError("Connection is not open. Use 'open()' method first.")
        try:
            logger.debug("Executing query: `%s`, with param `%s`", query, kwargs)
            self.cur.execute(query, kwargs)
            if self.cur.description:
                return self.cur.fetchall()
            return []
        except sqlite3.IntegrityError as exc:
            # Абстрагированная проверка по имени класса
            if exc.sqlite_errorname.find("UNIQUE") != -1:
                raise UniqueConstraintError() from exc
            raise
