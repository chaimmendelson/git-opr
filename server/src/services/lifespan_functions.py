import asyncio
import os
from contextlib import asynccontextmanager
from datetime import timedelta, datetime, timezone

from fastapi import FastAPI

from ..db.gitDatabase import AsyncGit
from ..utils import logger, config
from ..utils.logger import update_log_level
from ..db import reposFile
from .task_manager import git_instances, git_locks, sync_repo_periodically, task_store


async def reload_environment_variables():
    while True:
        await asyncio.sleep(config.SYNC_INTERVAL)

        logger.info("[Config] Reloading environment variables")
        config.reload()
        update_log_level()
        logger.debug("[Config] Environment variables reloaded successfully")

async def task_manager_cleanup_loop():
    while True:
        await asyncio.sleep(config.SYNC_INTERVAL)

        now = datetime.now(timezone.utc)

        expired = [
            task_id for task_id, task in task_store.items()
            if (now - task.updated_at) > timedelta(minutes=config.TASK_EXPIRATION)
        ]

        if expired:
            logger.info(f"[TaskManager] Expiring {len(expired)} stale tasks (older than {config.TASK_EXPIRATION} minutes)")
            for task_id in expired:
                logger.debug(f"[TaskManager] Removing expired task: {task_id}")
                del task_store[task_id]
        else:
            logger.debug("[TaskManager] No expired tasks found.")


async def reload_repo_config_periodically():
    while True:
        await asyncio.sleep(config.SYNC_INTERVAL)
        logger.info("[Config] Reloading repositories configuration")

        reposFile.reload()

        new_repo_ids = set(reposFile.repos.root.keys())
        existing_repo_ids = set(git_instances.keys())

        # Remove repos that no longer exist in the config
        for removed_repo in existing_repo_ids - new_repo_ids:
            logger.info(f"[Config] Removing stale repo '{removed_repo}'")
            del git_instances[removed_repo]
            del git_locks[removed_repo]

        # Add new repos
        for repo_id in new_repo_ids - existing_repo_ids:
            conf = reposFile.repos.root[repo_id]

            logger.info(f"[Config] Adding new repo '{repo_id}'")

            git_handler = AsyncGit(
                repo_url=conf.repo_url,
                local_path=os.path.join(config.BASE_CLONE_PATH, conf.local_path),
                base_folder=conf.base_folder or "",
                main_branch=conf.main_branch or "master",
            )

            git_instances[repo_id] = git_handler
            git_locks[repo_id] = asyncio.Lock()

            async with git_locks[repo_id]:
                await git_handler.clone_or_sync()

            asyncio.create_task(sync_repo_periodically(repo_id, git_handler))


# ─────────────────────────────────────────────
# FastAPI Lifespan Setup
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[Startup] Loading initial repository configurations")

    for repo_id, conf in reposFile.repos.root.items():
        git_handler = AsyncGit(
            repo_url=conf.repo_url,
            local_path=os.path.join(config.BASE_CLONE_PATH, conf.local_path),
            base_folder=conf.base_folder or "",
            main_branch=conf.main_branch or "master",
        )
        git_instances[repo_id] = git_handler
        git_locks[repo_id] = asyncio.Lock()

    for repo_id, git_handler in git_instances.items():
        async with git_locks[repo_id]:
            try:
                await git_handler.clone_or_sync()
            except Exception as e:
                logger.warn(f"Failed to sync repo '{repo_id}': {e}")

    for repo_id, git_handler in git_instances.items():
        asyncio.create_task(sync_repo_periodically(repo_id, git_handler))

    asyncio.create_task(reload_repo_config_periodically())
    asyncio.create_task(task_manager_cleanup_loop())
    asyncio.create_task(reload_environment_variables())

    logger.info("[Startup] Lifespan ready")
    yield
    logger.info("[Shutdown] Lifespan complete")