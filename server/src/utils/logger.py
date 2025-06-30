import os
import logging
import logging.config
from colorama import init as colorama_init, Fore, Style
from .config import config

colorama_init(autoreset=True)

LOG_COLORS = {
    "DEBUG": Fore.CYAN,
    "INFO": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.MAGENTA,
}


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color = LOG_COLORS.get(record.levelname, "")
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"


def get_log_level():
    """Retrieve and validate the configured log level."""
    level = getattr(config, "LOG_LEVEL", "INFO").upper()
    return level if level in LOG_COLORS else "INFO"

# Ensure the log directory exists
os.makedirs(os.path.dirname(config.LOG_FILE_PATH), exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'colored': {
            '()': ColoredFormatter,
            'fmt': '%(asctime)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'standard': {
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'handlers': {
        'console': {
            'level': get_log_level(),
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
        'file': {
            'level': get_log_level(),
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': config.LOG_FILE_PATH,
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8',
        }
    },
    'loggers': {
        'app': {
            'level': get_log_level(),
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        'uvicorn': {
            'level': get_log_level(),
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        'uvicorn.access': {
            'level': 'INFO',
            'handlers': [],
            'propagate': False,
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger("app")


def update_log_level():
    """Update logger level dynamically based on config.LOG_LEVEL."""
    new_level = get_log_level()

    if logger.level == logging.getLevelName(new_level):
        return

    for name in ("app", "uvicorn"):
        logging.getLogger(name).setLevel(new_level)

    for handler in logging.getLogger("app").handlers:
        handler.setLevel(new_level)

    logger.debug(f"Log level updated to: {new_level}")


def get_logger():
    return logger