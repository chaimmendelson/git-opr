import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
import asyncio
import os
import uvicorn
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from datetime import datetime, timedelta, UTC

from .src.utils import get_current_user, logger, config
from .src.db.gitDatabase import AsyncGit
from .src.models.responses import RepoInfo, ReposListResponse
from .src.db import reposFile
from .src.services.task_manager import (
    git_instances, git_locks,
    sync_repo_periodically,
    task_store
)

from .src.routes import (
    file_routes, folder_routes, git_routes, task_routes, file_system_routes
)
from .src.utils.logger import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

async def task_manager_cleanup_loop():
    while True:
        await asyncio.sleep(config.SYNC_INTERVAL)
        now = datetime.now(UTC)
        expired = [
            task_id for task_id, task in task_store.items()
            if (now - task.updated_at) > timedelta(minutes=config.TASK_EXPIRATION)
        ]
        for task_id in expired:
            del task_store[task_id]

@asynccontextmanager
async def lifespan(app: FastAPI):
    for repo_id, conf in reposFile.repos.root.items():
        git_instances[repo_id] = AsyncGit(
            repo_url=conf.repo_url,
            local_path=os.path.join(config.BASE_CLONE_PATH, conf.local_path),
            base_folder=conf.base_folder if conf.base_folder else "",
            main_branch=conf.main_branch if conf.main_branch else "master"
        )
        git_locks[repo_id] = asyncio.Lock()

    for repo_id, git_handler in git_instances.items():
        async with git_locks[repo_id]:
            await git_handler.clone_or_sync()

    for repo_id, git_handler in git_instances.items():
        asyncio.create_task(sync_repo_periodically(repo_id, git_handler))

    asyncio.create_task(task_manager_cleanup_loop())

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(file_routes.router)
app.include_router(folder_routes.router)
app.include_router(git_routes.router)
app.include_router(task_routes.router)
app.include_router(file_system_routes.router)


@app.get("/repos", response_model=ReposListResponse)
async def list_repos(
        user: str = Depends(get_current_user)
):
    repos = [
        RepoInfo(
            repo_id=repo_id,
            repo_url=handler.repo_url,
            branch=handler.branch,
            base_folder=handler.base_folder
        )

        for repo_id, handler in git_instances.items()
    ]
    return ReposListResponse(repos=repos)

# Override the default request logger
@app.middleware("http")
async def log_request(request: Request, call_next):
    logger.info(f"Request:  [{request.client.host}] {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: [{request.client.host}] {response.status_code}")
    return response

@app.exception_handler(PermissionError)
async def permission_exception_handler(request: Request, exc: PermissionError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
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

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=config.PORT, reload=True)
