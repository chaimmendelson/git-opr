from fastapi import APIRouter, HTTPException, Depends, status

from ..models.responses import TaskStatusResponse
from ..models.tasks import TaskModel
from ..services.task_manager import task_store
from ..utils import get_current_user
from ..utils.logger import logger
from ..exceptions.exceptions import TaskNotFound, UnauthorizedError


router = APIRouter(tags=["Task Management"], prefix="/v1/tasks")

@router.get("/{task_id}", response_model=TaskStatusResponse, status_code=status.HTTP_200_OK)
async def get_task_status(
        task_id: str,
        user: str = Depends(get_current_user)
):

    task: TaskModel = task_store.get(task_id)

    if not task:
        logger.info(f"Task ID '{task_id}' not found")
        raise TaskNotFound(task_id)

    if task.user != user:
        logger.info(f"User '{user}' is not authorized to access task {task_id}")
        raise UnauthorizedError(f"User '{user}' is not authorized to access task {task_id}")

    logger.info(f"Returning status for task {task_id}")

    return task

@router.get("", response_model=list[TaskStatusResponse], status_code=status.HTTP_200_OK)
async def list_tasks(
        user: str = Depends(get_current_user)
):
    tasks = list(task_store.values())

    tasks = [task for task in tasks if task.user == user]

    if not tasks:
        logger.info("No tasks found")
        return []

    logger.info(f"Returning {len(tasks)} tasks")

    return tasks
