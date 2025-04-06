from .git_db import AsyncGit
import re

CLONE_PATH = "./repos"

async def get_repo(repo_url: str, base_folder: str, main_branch: str = "master") -> AsyncGit:
    """
    Given a repo URL, return the repo name and the local path to the repo.
    """
    # Extract the repo name from the URL
    match = re.search(r"([^/]+)\.git$", repo_url)

    if not match:
        raise ValueError(f"Invalid repo URL: {repo_url}")

    repo_name = match.group(1)
    local_path = f"{CLONE_PATH}/{repo_name}"

    repo = AsyncGit(repo_url, local_path, base_folder, main_branch)

    await repo.clone_or_sync()

    return repo
