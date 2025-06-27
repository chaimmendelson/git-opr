from fastapi import APIRouter, Query, Depends

from ..models.responses import TaskResponse
from ..services.task_manager import (
    get_git_handler,
    enqueue_task
)

from ..utils import (
    verify_repo_access_with_level,
    log_task_start,
)
from ..models.repos_file import AuthLevel


router = APIRouter(tags=["Folder Management"], prefix="/v1/folder")



@router.post("", response_model=TaskResponse)
async def make_folder(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.WRITE)),
):

    task = await enqueue_task(
        repo_id=repo_id,
        action=lambda: get_git_handler(repo_id).make_folder(path),
        message=f"Create folder: {path}",
        user=user
    )

    log_task_start(task)

    return TaskResponse(task_id=task.task_id)



@router.delete("", response_model=TaskResponse)
async def delete_folder(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.WRITE)),
):

    task = await enqueue_task(
        repo_id=repo_id,
        action=lambda: get_git_handler(repo_id).delete_folder(path),
        message=f"Delete folder: {path}",
        user=user
    )

    log_task_start(task)

    return TaskResponse(task_id=task.task_id)