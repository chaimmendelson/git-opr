from fastapi import APIRouter, Depends

from ..db import reposFile
from ..models.repos_file import AuthLevel
from ..models.responses import ReposListResponse, RepoInfo
from ..utils import get_current_user

router = APIRouter(tags=["Repos Management"], prefix="/v1/repos")


@router.get("", response_model=ReposListResponse)
async def list_repos(
        user: str = Depends(get_current_user)
):
    repos = [
        RepoInfo(
            repo_id=repo_id,
            repo_url=repo.repo_url,
            branch=repo.main_branch,
            base_folder=repo.base_folder
        )

        for repo_id, repo in reposFile.repos.root.items()
        if repo.has_permission(user, AuthLevel.READ)
    ]

    return ReposListResponse(repos=repos)
