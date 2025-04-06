import json
import os

from fastapi import FastAPI, Request, HTTPException, Response

from .utils import logger

def get_app() -> FastAPI:

    app = FastAPI()

    # Override the default request logger
    @app.middleware("http")
    async def log_request(request: Request, call_next):
        logger.info(f"Request:  [{request.client.host}] {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: [{request.client.host}] {response.status_code}")
        return response

    # Handle httpException
    @app.exception_handler(HTTPException)
    async def log_http_exception(request: Request, exc: HTTPException):
        logger.info(f"HTTPException: [{request.client.host}] {exc}")

        raise exc

    # Override the default error logger
    @app.exception_handler(Exception)
    async def log_exception(request: Request, exc: Exception):
        logger.error(f"Exception: [{request.client.host}] {exc}")

        raise HTTPException(status_code=500, detail="Internal Server Error")

    return app