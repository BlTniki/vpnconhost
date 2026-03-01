import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from config import Config  # noqa: E402

bind = os.getenv("GUNICORN_BIND", "unix:/run/vpnconhost/vpnconhost.sock")
umask = 0o007

worker_class = "gthread"
workers = Config.effective_gunicorn_workers()
threads = Config.effective_gunicorn_threads()
preload_app = Config.GUNICORN_PRELOAD

accesslog = "-"
errorlog = "-"
loglevel = (Config.LOG_LEVEL or "INFO").lower()
