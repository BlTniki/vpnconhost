import logging
from flask import Flask, Response, request, abort, jsonify
from swagger_ui import api_doc  # type: ignore

from config import setup_logging, Config
from vpnconhost.exceptions import (
    EntityValidationFailedException,
    EntityNotExistsException,
    EntityAlreadyExistsException,
    EntityException
)

_initialized = False


# ===============================================
# Error Handlers
# ===============================================

def handle_validation_error(error: EntityValidationFailedException):
    """Обработчик ошибок валидации (400 Bad Request)."""
    logger = logging.getLogger(__name__)
    logger.warning("Validation error: %s", error.message)
    return jsonify({
        'error': 'Validation Failed',
        'message': error.message or 'Entity validation failed'
    }), 400


def handle_not_found_error(error: EntityNotExistsException):
    """Обработчик ошибок отсутствия сущности (404 Not Found)."""
    logger = logging.getLogger(__name__)
    logger.warning("Entity not found: %s", error.message)
    return jsonify({
        'error': 'Not Found',
        'message': error.message or 'Entity not found'
    }), 404


def handle_already_exists_error(error: EntityAlreadyExistsException):
    """Обработчик ошибок дублирования сущности (409 Conflict)."""
    logger = logging.getLogger(__name__)
    logger.warning("Entity already exists: %s", error.message)
    return jsonify({
        'error': 'Conflict',
        'message': error.message or 'Entity already exists'
    }), 409


def handle_entity_error(error: EntityException):
    """Обработчик базовых ошибок сущностей (500 Internal Server Error)."""
    logger = logging.getLogger(__name__)
    logger.error("Entity error: %s", error.message, exc_info=True)
    return jsonify({
        'error': 'Internal Server Error',
        'message': error.message or 'An error occurred while processing the entity'
    }), 500


def handle_generic_error(error: Exception):
    """Обработчик всех остальных исключений (500 Internal Server Error)."""
    logger = logging.getLogger(__name__)
    logger.error("Unexpected error: %s", str(error), exc_info=True)
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


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

    greetings_text = """
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@          VPNCONHOST           @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

"""
    logger.info(greetings_text)
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

    # Регистрация API blueprint
    from vpnconhost import peers_bp
    app.register_blueprint(peers_bp)

    api_doc(app, config_path="openapi.yml", url_prefix="/api/doc", title="API doc")

    # Регистрация обработчиков ошибок
    app.register_error_handler(EntityValidationFailedException, handle_validation_error)
    app.register_error_handler(EntityNotExistsException, handle_not_found_error)
    app.register_error_handler(EntityAlreadyExistsException, handle_already_exists_error)
    app.register_error_handler(EntityException, handle_entity_error)
    app.register_error_handler(Exception, handle_generic_error)

    return app


# Важно: при импорте (gunicorn) будет создан app и выполнится init_modules()
app = create_app()


if __name__ == "__main__":
    # Для дева:
    # use_reloader=False, чтобы init_modules не выполнялся дважды из-за reloader
    app.run(debug=True, use_reloader=False)
