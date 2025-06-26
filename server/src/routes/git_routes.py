from fastapi import APIRouter, Query, Depends

from ..models.responses import TaskResponse
from ..services.task_manager import get_git_handler, enqueue_task
from ..utils import log_task_start, verify_repo_access_with_level
from ..models.repos_file import AuthLevel


router = APIRouter(tags=["Git Operations"], prefix="/v1/git")

@router.post("/pull", response_model=TaskResponse)
async def pull(
    repo_id: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.READ)),
):

    task = await enqueue_task(
        repo_id=repo_id,
        action=lambda: get_git_handler(repo_id).pull(),
        message="Manual pull",
        user=user
    )

    log_task_start(task)

    return TaskResponse(task_id=task.task_id)
