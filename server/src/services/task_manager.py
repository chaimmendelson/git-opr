import asyncio
from typing import Dict, Callable
import uuid
from ..db.gitDatabase import AsyncGit
from ..models.tasks import TaskModel, TaskStatus
from ..utils import logger, config, log_task_failure, log_task_completion

git_instances: Dict[str, AsyncGit] = {}
git_locks: Dict[str, asyncio.Lock] = {}
task_store: Dict[str, TaskModel] = {}

def get_git_handler(repo_id: str) -> AsyncGit:
    logger.debug(f"Getting git handler for {repo_id}")
    if repo_id not in git_instances:
        raise Exception(f"Repo ID '{repo_id}' not found")
    return git_instances[repo_id]


def get_git_lock(repo_id: str) -> asyncio.Lock:
    return git_locks[repo_id]


def create_task(user: str, description: str) -> str:
    logger.debug(f"Creating task for user {user} with description: {description}")
    task_id = str(uuid.uuid4())
    task_store[task_id] = TaskModel(task_id=task_id, user=user, description=description)
    logger.debug(f"Task created with ID: {task_id} for user {user}")
    return task_id


def set_task_result(task_id: str, status: TaskStatus, result: str = None, error: str = None):
    task = task_store.get(task_id)
    if task:
        logger.debug(f"Setting result for task {task_id} with status: {status}")
        task.update_status(status=status, result=result, error=error)
    else:
        logger.debug(f"Task ID {task_id} not found for updating status")


async def enqueue_task(repo_id: str, action: Callable, message: str, user: str) -> TaskModel:
    task_id = create_task(user, message)

    async def run():
        logger.debug(f"Running task {task_id} for user {user} on repo {repo_id}")
        try:
            git_handler = get_git_handler(repo_id)
            async with get_git_lock(repo_id):
                logger.debug(f"Acquired lock for repo {repo_id} for task {task_id}")
                await git_handler.clone_or_sync()
                logger.debug(f"Repo {repo_id} cloned or synced for task {task_id}")
                await action()
                logger.debug(f"Action completed for task {task_id} for user {user}")
                await git_handler.commit_and_push(f"API commit for {user}, {message}")
                logger.debug(f"Task {task_id} completed successfully for user {user}")

            set_task_result(task_id, TaskStatus.COMPLETED, result=message)
            log_task_completion(task_store[task_id])

        except Exception as e:
            set_task_result(task_id, TaskStatus.FAILED, error=str(e))
            log_task_failure(task_store[task_id])

    asyncio.create_task(run())
    return task_store[task_id]
