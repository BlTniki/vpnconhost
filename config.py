import os
import logging.config
import yaml
from dotenv import load_dotenv
from typing import Any
import multiprocessing

load_dotenv()

class Config:
    LOG_LEVEL:str = os.getenv("LOG_LEVEL", "INFO")
    LOG_LEVELS:str = os.getenv("LOG_LEVELS", "")#example: myapp.db=INFO,myapp.services.auth=WARNING

    DB_URI:str = os.getenv("DB_URI", "")

    API_SECRET_WORD:str = os.getenv("API_SECRET_WORD", "default_secret")

    WORK_DIR:str = os.getenv("WORK_DIR", "./")


    # WIREGUARD
    SUDO_CMD:str = os.getenv("SUDO_CMD", "/usr/bin/sudo")
    WG_CMD:str = os.getenv("WG_CMD", "/usr/bin/wg")
    WG_MOCK_MODE:bool = os.getenv("WG_MOCK_MODE", "false").lower() == "true"
    WG_EXTERNAL_IFACE:str = os.getenv("WG_EXTERNAL_IFACE", "")
    WG_PRIVATE_KEY:str = os.getenv("WG_PRIVATE_KEY", "")
    WG_PUBLIC_KEY:str = os.getenv("WG_PUBLIC_KEY", "public_key")
    WG_ADDRESS:str = os.getenv("WG_ADDRESS", "10.8.0.1/24")
    WG_SERVER_ADDRESS:str = os.getenv("WG_SERVER_ADDRESS", "0.0.0.0")
    WG_DNS:str = os.getenv("WG_DNS", "0.0.0.0, 0.0.0.0")
    WG_LISTEN_PORT:str = os.getenv("WG_LISTEN_PORT", "51820")

    # Gunicorn
    GUNICORN_WORKERS: int = int(os.getenv("GUNICORN_WORKERS", "0"))
    GUNICORN_THREADS: int = int(os.getenv("GUNICORN_THREADS", "0"))
    GUNICORN_WORKER_CLASS: str = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
    GUNICORN_PRELOAD: bool = os.getenv("GUNICORN_PRELOAD", "true").lower() == "true"

    GUNICORN_TIMEOUT: int = int(os.getenv("GUNICORN_TIMEOUT", "120"))
    GUNICORN_GRACEFUL_TIMEOUT: int = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
    GUNICORN_KEEPALIVE: int = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

    @staticmethod
    def effective_gunicorn_workers() -> int:
        cpu = multiprocessing.cpu_count()
        return Config.GUNICORN_WORKERS if Config.GUNICORN_WORKERS > 0 else max(2, cpu)

    @staticmethod
    def effective_gunicorn_threads() -> int:
        cpu = multiprocessing.cpu_count()
        return Config.GUNICORN_THREADS if Config.GUNICORN_THREADS > 0 else max(4, cpu * 4)




def setup_logging(
    default_path:str="logging.yml"
):
    """
    Настройка логирования через logging.yml и .env

    Поддержка .env:
      LOG_LEVEL=DEBUG
      LOG_LEVELS=myapp.db=INFO,myapp.services.auth=ERROR
    """
    # root уровень
    root_level = Config.LOG_LEVEL

    # Таргетированные уровни
    raw_levels = Config.LOG_LEVELS
    overrides:dict[str, str] = {}
    for pair in raw_levels.split(","):
        if "=" in pair:
            name, level = pair.split("=", 1)
            overrides[name.strip()] = level.strip()

    # Загружаем logging.yml
    if os.path.exists(default_path):
        with open('logging.yml', 'r', encoding='utf-8') as f:
            config:dict[str, Any] = yaml.safe_load(f)
    else:
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "root": {"level": root_level, "handlers": ["console"]},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                }
            },
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
        }

    # Применяем root
    config["root"]["level"] = root_level

    # Применяем overrides
    if overrides:
        if "loggers" not in config:
            config["loggers"] = {}
        for logger_name, level in overrides.items():
            if logger_name not in config["loggers"]:
                config["loggers"][logger_name] = {"handlers": [], "propagate": True}
            config["loggers"][logger_name]["level"] = level

    logging.config.dictConfig(config)
