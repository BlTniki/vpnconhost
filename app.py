import logging
from flask import Flask, Response, request, abort
from swagger_ui import api_doc # type: ignore
from vpnconhost.config import setup_logging, Config

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



# ===============================================
# Initialize API
# ===============================================
app = Flask(__name__)

@app.before_request
def authenticate():
    """ Простейшая аутентификация по секретному слову из заголовков Basic Auth
    Если аутентификация не пройдена, возвращается корректный ответ, чтобы
    браузер мог показать окно ввода логина и пароля.
    """
    auth = request.authorization
    if not auth or auth.password != Config.API_SECRET_WORD:
        logger.info("Unauthorized access attempt from %s", request.remote_addr)

        abort(Response(
            "Unauthorized",
            401,
            {"WWW-Authenticate": 'Basic realm="Login Required"'}
        ))

api_doc(app, config_path='openapi.yml', url_prefix='/api/doc', title='API doc')




if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
