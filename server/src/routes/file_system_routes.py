from fastapi import APIRouter, Query, Depends, status, Response

from ..models.responses import ListContentResponse, TaskResponse
from ..services.task_manager import get_git_handler, enqueue_task
from ..models.repos_file import AuthLevel
from ..utils import verify_repo_access_with_level, log_action, log_task_start


router = APIRouter(tags=["File System"], prefix="/v1/fs")


@router.patch("/rename", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def rename_path(
    repo_id: str = Query(...),
    old_path: str = Query(...),
    new_path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.WRITE)),
):

    task = await enqueue_task(
        repo_id=repo_id,
        action=lambda: get_git_handler(repo_id).rename_path(old_path, new_path),
        message=f"Rename file from {old_path} to {new_path}",
        user=user
    )

    log_task_start(task)

    return TaskResponse(task_id=task.task_id)


@router.get("/list", response_model=ListContentResponse, status_code=status.HTTP_200_OK)
async def list_contents(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.READ))
):

    git_handler = get_git_handler(repo_id)

    log_action(user, f"List contents of path '{path}' in repo '{repo_id}'")

    files = await git_handler.list_files_only(path)
    folders = await git_handler.list_folders_only(path)

    return ListContentResponse(folders=folders, files=files)



@router.get("/exists")
async def path_exists(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.READ))
):

    git_handler = get_git_handler(repo_id)

    exists = git_handler.does_path_exist(path)

    log_action(user, f"Checked existence of path '{path}' in repo '{repo_id}': {exists}")

    if exists:
        return Response(status_code=status.HTTP_200_OK, content="Path exists")

    return Response(status_code=status.HTTP_404_NOT_FOUND, content="Path not found")

@router.get("/tree", response_model=dict, status_code=status.HTTP_200_OK)
async def get_directory_tree(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.READ))
):
    git_handler = get_git_handler(repo_id)

    log_action(user, f"Requested directory tree for path '{path}' in repo '{repo_id}'")

    tree = await git_handler.get_tree(path)

    return tree

