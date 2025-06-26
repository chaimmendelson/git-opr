import asyncio
from typing import Dict, Callable
import uuid
from ..db.gitDatabase import AsyncGit
from ..models.tasks import TaskModel, TaskStatus
from ..utils import logger, config, log_task_failure, log_task_completion

git_instances: Dict[str, AsyncGit] = {}
git_locks: Dict[str, asyncio.Lock] = {}
task_store: Dict[str, TaskModel] = {}


async def sync_repo_periodically(repo_id: str, git_handler: AsyncGit):
    while True:
        async with git_locks[repo_id]:
            try:
                await git_handler.pull()
                logger.info(f"Periodic sync successful for {repo_id}")
            except Exception as e:
                logger.warning(f"Periodic sync failed for {repo_id}: {e}")
        await asyncio.sleep(config.SYNC_INTERVAL)


def get_git_handler(repo_id: str) -> AsyncGit:
    if repo_id not in git_instances:
        raise Exception(f"Repo ID '{repo_id}' not found")
    return git_instances[repo_id]


def get_git_lock(repo_id: str) -> asyncio.Lock:
    return git_locks[repo_id]


def create_task(user: str, description: str) -> str:
    task_id = str(uuid.uuid4())
    task_store[task_id] = TaskModel(task_id=task_id, user=user, description=description)
    return task_id


def set_task_result(task_id: str, status: TaskStatus, result: str = None, error: str = None):
    task = task_store.get(task_id)
    if task:
        task.update_status(status=status, result=result, error=error)


async def enqueue_task(repo_id: str, action: Callable, message: str, user: str) -> TaskModel:
    task_id = create_task(user, message)

    async def run():
        try:
            git_handler = get_git_handler(repo_id)
            async with get_git_lock(repo_id):
                await git_handler.clone_or_sync()
                await action()
                await git_handler.commit_and_push(f"API commit for {user}, {message}")

            set_task_result(task_id, TaskStatus.COMPLETED, result=message)
            log_task_completion(task_store[task_id])

        except Exception as e:
            set_task_result(task_id, TaskStatus.FAILED, error=str(e))
            log_task_failure(task_store[task_id])

    asyncio.create_task(run())
    return task_store[task_id]
