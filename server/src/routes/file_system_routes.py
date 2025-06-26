from fastapi import APIRouter, Query, HTTPException, Depends

from ..models.responses import FileListResponse, FolderListResponse, PathExistsResponse
from ..services.task_manager import get_git_handler, get_git_lock
from ..models.repos_file import AuthLevel
from ..utils import verify_repo_access_with_level, log_action
from ..utils.logger import logger


router = APIRouter(tags=["File System"], prefix="/v1/fs")



@router.get("/list", response_model=dict)
async def list_contents(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.READ))
):

    git_handler = get_git_handler(repo_id)

    log_action(user, f"List contents of path '{path}' in repo '{repo_id}'")

    try:
        files = await git_handler.list_files_only(path)
        folders = await git_handler.list_folders_only(path)

        return {
            "files": files,
            "folders": folders
        }

    except FileNotFoundError as e:
        log_action(user, f"Path '{path}' not found in repo '{repo_id}'")
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/exists", response_model=PathExistsResponse)
async def path_exists(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.READ))
):

    git_handler = get_git_handler(repo_id)

    exists = git_handler.does_path_exist(path)

    log_action(user, f"Checked existence of path '{path}' in repo '{repo_id}': {exists}")

    return PathExistsResponse(exists=exists)

@router.get("/tree")
async def get_directory_tree(
    repo_id: str = Query(...),
    path: str = Query(...),
    user: str = Depends(verify_repo_access_with_level(AuthLevel.READ))
):
    git_handler = get_git_handler(repo_id)

    log_action(user, f"Requested directory tree for path '{path}' in repo '{repo_id}'")

    try:
        tree = await git_handler.get_tree(path)
        return tree

    except FileNotFoundError:
        log_action(user, f"Tree path '{path}' not found in repo '{repo_id}'")
        raise HTTPException(status_code=404, detail="Path not found")
