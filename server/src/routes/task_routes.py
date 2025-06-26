from fastapi import APIRouter, HTTPException, Depends

from ..models.responses import TaskStatusResponse
from ..models.tasks import TaskModel
from ..services.task_manager import task_store
from ..utils import get_current_user
from ..utils.logger import logger


router = APIRouter(tags=["Task Management"], prefix="/v1/tasks")

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
        task_id: str,
        user: str = Depends(get_current_user)
):

    task: TaskModel = task_store.get(task_id)

    if not task:
        logger.info(f"Task ID '{task_id}' not found")
        raise HTTPException(status_code=404, detail="Task not found")

    if task.user != user:
        logger.info(f"User '{user}' is not authorized to access task {task_id}")
        raise HTTPException(status_code=403, detail="Not authorized to access this task")

    logger.info(f"Returning status for task {task_id}")

    return task

@router.get("/", response_model=list[TaskStatusResponse])
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
