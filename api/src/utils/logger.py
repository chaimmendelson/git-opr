import logging
from colorama import init as colorama_init, Fore, Style
from .config import config
import logging.config

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


# Logging configuration dictionary
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'colored': {
            '()': ColoredFormatter,  # Apply the custom ColoredFormatter
            'fmt': '%(asctime)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if config.debug else 'INFO',  # Set level based on config
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        }
    },
    'loggers': {
        'app': {
            'level': 'DEBUG' if config.debug else 'INFO',  # Set level based on config
            'handlers': ['console'],
            'propagate': False,
        },
        'uvicorn': {
            'level': 'INFO',  # Uvicorn logger level
            'handlers': ['console'],
            'propagate': False,
        },
        'uvicorn.access': {
            'level': 'INFO',  # Uvicorn access logger level
            'handlers': [],
            'propagate': False,
        },
    }
}

# Apply the logging configuration
logging.config.dictConfig(LOGGING_CONFIG)

# Get the logger
logger = logging.getLogger("app")


def get_logger():
    return logger
