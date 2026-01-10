import os
import logging.config
import yaml
from dotenv import load_dotenv
from typing import Any

load_dotenv()

class Config:
    LOG_LEVEL:str = os.getenv("LOG_LEVEL") or "INFO"
    LOG_LEVELS:str = os.getenv("LOG_LEVELS") or ""#format: myapp.db=INFO,myapp.services.auth=WARNING

    DB_URI:str = os.getenv("DB_URI") or ""

    API_SECRET_WORD:str = os.getenv("API_SECRET_WORD") or "default_secret"

    WIREGUARD_MOCK_MODE:bool = os.getenv("WIREGUARD_MOCK_MODE", "false").lower() == "true"
    WORK_DIR:str = os.getenv("WORK_DIR") or "./"
    WIREGUARD_ADDRESS:str = os.getenv("WIREGUARD_ADDRESS") or "0.0.0.0:0000"
    SUDO_CMD:str = os.getenv("SUDO_CMD", "sudo") + ' '
    WIREGUARD_DNS:str = os.getenv("WIREGUARD_DNS") or "0.0.0.0, 0.0.0.0"
    WIREGUARD_PUBLIC_KEY:str = os.getenv("WIREGUARD_PUBLIC_KEY") or "public_key"
    OBFUSCATOR_IP:str = os.getenv("OBFUSCATOR_IP") or "null"




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
