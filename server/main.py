import logging.config

import uvicorn
from fastapi import FastAPI

from .src import create_app

from .src.utils import config
from .src.utils.logger import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)


app: FastAPI = create_app()

def main():
    """
    Main entry point for the FastAPI application.
    """
    uvicorn.run("server.main:app", host="0.0.0.0", port=config.PORT, reload=config.DEBUG)

if __name__ == "__main__":
    main()
