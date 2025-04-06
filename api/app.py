import uvicorn
import logging.config
from src import get_app
from src.utils.logger import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

app = get_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)