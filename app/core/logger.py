import logging.config
import os
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "text_default": {
            "format": "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json_formatter": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "text_default",
            "stream": "ext://sys.stdout",
        },
        "file_daily": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "json_formatter",
            "filename": str(LOGS_DIR / "app.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file_daily"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "sqlalchemy.engine": {
            "handlers": ["file_daily"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)