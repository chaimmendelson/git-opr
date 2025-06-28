from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from .utils import logger, config

from .routes import (
    file_routes,
    folder_routes,
    git_routes,
    task_routes,
    file_system_routes,
    repos_route
)

from .services.lifespan_functions import lifespan
from .exceptions.exceptions import AppError


def create_app() -> FastAPI:

    app = FastAPI(lifespan=lifespan)

    app.include_router(file_routes.router)
    app.include_router(folder_routes.router)
    app.include_router(git_routes.router)
    app.include_router(task_routes.router)
    app.include_router(file_system_routes.router)

    app.include_router(repos_route.router)

    app.get("/health", include_in_schema=False)(
        lambda: JSONResponse(content={"status": "ok"})
    )

    app.get("/", include_in_schema=False)(
        lambda: JSONResponse(content={"message": "Welcome to the Git Server API"})
    )

    # Override the default request logger
    @app.middleware("http")
    async def log_request(request: Request, call_next):
        if request.url.path.removesuffix("/") in ["/docs", "/openapi.json", "/redoc"]:
            # Skip logging for docs and openapi.json
            return await call_next(request)

        logger.info(f"Request:  [{request.client.host}] {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Response: [{request.client.host}] {response.status_code}")
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.info(f"AppError: [{request.client.host}] {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc.message)}
        )

    # Handle httpException
    @app.exception_handler(HTTPException)
    async def log_http_exception(request: Request, exc: HTTPException):
        logger.info(f"HTTPException: [{request.client.host}] {exc}")
        return JSONResponse(
            content={"detail": exc.detail},
            status_code=exc.status_code
        )

    # Override the default error logger
    @app.exception_handler(Exception)
    async def log_exception(request: Request, exc: Exception):
        logger.error(f"Exception: [{request.client.host}] {exc}")
        return JSONResponse(
            content={"detail": "Internal Server Error"},
            status_code=500
        )

    return app