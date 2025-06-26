from fastapi import APIRouter, HTTPException

from ..models.responses import TaskStatusResponse
from ..models.tasks import TaskModel
from ..services.task_manager import task_store
from ..utils.logger import logger


router = APIRouter(tags=["Task Management"], prefix="/v1/tasks")

@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):

    task: TaskModel = task_store.get(task_id)

    if not task:
        logger.warning(f"Task ID '{task_id}' not found")
        raise HTTPException(status_code=404, detail="Task not found")

    logger.info(f"Returning status for task {task_id}")

    return task
