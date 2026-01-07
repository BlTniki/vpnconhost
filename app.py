import logging
from flask import Flask, Response, request, abort
from swagger_ui import api_doc # type: ignore

# ===============================================
# Setup logging
# ===============================================
from vpncon.config import setup_logging, Config

setup_logging()
logger = logging.getLogger(__name__)
logger.info("Logging is set up")

# ===============================================
# Setup SMTP Notifier
# ===============================================
from vpncon.smtp_notifier import notify

logger.info("SMTP Notifier initialized")



# ===============================================
# Initialize DB
# ===============================================
from vpncon.db import validate_connection
from vpncon.db.db_migrations import DbMigrator, PostgresMigrationExecutor

logger.debug("Initializing the DB module")
validate_connection()
logger.debug("Connection validated")


logger.info("Applying DB migrations if needed")
DbMigrator(PostgresMigrationExecutor).apply_migrations()
logger.info("DB module is initialized")



# ===============================================
# Initialize API
# ===============================================
from vpncon.users import users_bp
from vpncon.subscriptions import subscriptions_bp
from vpncon.user_subscriptions import user_subscriptions_bp

app = Flask(__name__)
app.register_blueprint(users_bp)
app.register_blueprint(subscriptions_bp)
app.register_blueprint(user_subscriptions_bp)

@app.before_request
def authenticate():
    """ Простейшая аутентификация по секретному слову из заголовков Basic Auth
    Если аутентификация не пройдена, возвращается корректный ответ, чтобы
    браузер мог показать окно ввода логина и пароля.
    """
    auth = request.authorization
    if not auth or auth.password != Config.API_SECRET_WORD:
        logger.info("Unauthorized access attempt from %s", request.remote_addr)

        notify(
            "Unauthorized access attempt",
            f"IP Address: {request.remote_addr}\n"
            f"Requested Endpoint: {request.path}\n"
            f"HTTP Method: {request.method}\n"
            f"Full URL: {request.url}\n"
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}\n"
            f"Authorization Header: {request.headers.get('Authorization', 'None')}"
        )

        abort(Response(
            "Unauthorized",
            401,
            {"WWW-Authenticate": 'Basic realm="Login Required"'}
        ))

api_doc(app, config_path='openapi.yml', url_prefix='/api/doc', title='API doc')




if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
