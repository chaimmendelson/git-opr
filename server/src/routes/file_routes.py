from io import BytesIO

from fastapi import APIRouter, Query, Body, HTTPException, Depends, UploadFile, File
from starlette.responses import StreamingResponse

from ..utils.logger import logger
from ..utils import (
    log_task_start,
    verify_repo_access_with_level,
    log_action
)

from ..models.repos_file import AuthLevel
from ..models.requests import (
    FileRenameRequest
)
from ..models.responses import TaskResponse

from ..services.task_manager import (
    get_git_handler,
    enqueue_task
)


router = APIRouter(tags=["File Management"], prefix="/v1/file")


@router.post("", response_model=TaskResponse)
async def upload_file(
    repo_id: str = Query(...),
    path: str = Query(..., description="Destination file path"),
    file: UploadFile = File(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.WRITE)),
):

    content = await file.read()

    task = await enqueue_task(
        repo_id,
        lambda: get_git_handler(repo_id).write_file(path, content.decode("utf-8")),
        f"Upload file to: {path}",
        user
    )

    log_task_start(task)

    return TaskResponse(task_id=task.task_id)



@router.get("")
async def download_file(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.READ)),
):

    git_handler = get_git_handler(repo_id)

    logger.info(f"User {user} requested file download: {path} from repo {repo_id}")

    try:
        content = await git_handler.read_file(path)
        return StreamingResponse(
            BytesIO(content.encode("utf-8")),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={path.split('/')[-1]}"}
        )

    except FileNotFoundError:
        log_action(user, f"Download failed. File {path} not found in repo {repo_id}")
        raise HTTPException(status_code=404, detail="File not found")



@router.delete("", response_model=TaskResponse)
async def delete_file(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.WRITE)),
):

    task = await enqueue_task(
        repo_id,
        lambda: get_git_handler(repo_id).delete_file(path),
        f"Delete file: {path}",
        user
    )

    return TaskResponse(task_id=task.task_id)