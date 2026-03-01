import logging
from flask import Flask, Response, request, abort
from swagger_ui import api_doc  # type: ignore

from config import setup_logging, Config

_initialized = False


def init_modules() -> None:
    """
    Инициализирует все модули приложения.
    Должно быть вызвано до создания воркеров gunicorn (т.е. при --preload).
    """
    global _initialized
    if _initialized:
        return

    # ===============================================
    # Setup logging
    # ===============================================
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Logging is set up")

    # ===============================================
    # Initialize DB
    # ===============================================
    from vpnconhost.db import validate_connection
    from vpnconhost.db.db_migrations import DbMigrator, SQLiteMigrationExecutor

    logger.debug("Initializing the DB module")
    validate_connection()
    logger.debug("Connection validated")

    logger.info("Applying DB migrations if needed")
    DbMigrator(SQLiteMigrationExecutor).apply_migrations()
    logger.info("DB module is initialized")

    _initialized = True


def create_app() -> Flask:
    init_modules()

    logger = logging.getLogger(__name__)
    app = Flask(__name__)

    @app.before_request
    def authenticate():
        auth = request.authorization
        if not auth or auth.password != Config.API_SECRET_WORD:
            logger.info("Unauthorized access attempt from %s", request.remote_addr)
            abort(Response(
                "Unauthorized",
                401,
                {"WWW-Authenticate": 'Basic realm="Login Required"'}
            ))

    api_doc(app, config_path="openapi.yml", url_prefix="/api/doc", title="API doc")
    return app


# Важно: при импорте (gunicorn) будет создан app и выполнится init_modules()
app = create_app()


if __name__ == "__main__":
    # Для дева:
    # use_reloader=False, чтобы init_modules не выполнялся дважды из-за reloader
    app.run(debug=True, use_reloader=False)
