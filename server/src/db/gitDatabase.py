import os
import asyncio

from git import Repo, GitCommandError
from typing import Optional
from ..utils import logger

from ..exceptions.exceptions import (
    GitError,
    GitConnectionError,
    GitRebaseError,
    GitCommitError,
    FolderNotFound,
    InvalidPathError,
    PathAccessDenied
)


class AsyncGit:
    def __init__(self, repo_url: str, local_path: str, base_folder: str, main_branch: str = "master"):
        self.repo_url = repo_url
        self.local_path = os.path.abspath(local_path)
        self.base_folder = base_folder
        self.main_branch = main_branch
        self.repo: Optional[Repo] = None
        self.branch: str = main_branch
        self.allowed_path: str = os.path.join(self.local_path, self.base_folder)

    # ────────────────────────────────────────────────
    # Repo Setup & Base Utilities
    # ────────────────────────────────────────────────

    async def clone_or_sync(self):
        """Clone the repo or update it to latest main branch."""

        if os.path.exists(self.local_path):
            logger.debug(f"Repo already exists at {self.local_path}, loading...")
            await self._load_repo()

        else:

            try:

                logger.debug(f"Cloning {self.repo_url} to {self.local_path}")
                self.repo = await asyncio.to_thread(Repo.clone_from, self.repo_url, self.local_path)

            except GitCommandError as e:

                if "Could not resolve hostname" in f"{e}":
                    raise GitConnectionError(repo=self.repo_url) from e

                raise GitError("Failed to clone repository", repo=self.repo_url) from e

        logger.debug(f"Checking out main branch: {self.main_branch}")

        self.repo.git.checkout(self.main_branch)

        await self._rebase()

    async def _load_repo(self):
        """Load the repo from the local path."""

        logger.debug(f"Loading {self.repo_url} to {self.base_folder}")

        if not os.path.exists(self.local_path):
            raise InvalidPathError(path=self.base_folder)

        self.repo = await asyncio.to_thread(Repo, self.local_path)

        if self.repo.bare:
            raise GitError("Repository is bare and cannot be used", repo=self.repo_url)

    async def _rebase(self):
        """Rebase the current branch onto the main branch (origin/{main_branch})."""

        try:

            logger.debug(f"Resetting {self.repo_url} to {self.main_branch}")
            await asyncio.to_thread(self.repo.git.reset, '--hard', f"origin/{self.main_branch}")

            logger.debug(f"cleaning {self.repo_url}")
            await asyncio.to_thread(self.repo.git.clean, '-xdf')

            logger.debug(f"Fetching latest changes from origin/{self.main_branch}")
            await asyncio.to_thread(self.repo.remotes.origin.fetch)

            logger.debug(f"Rebasing current branch onto origin/{self.main_branch}")
            await asyncio.to_thread(self.repo.git.rebase, f"origin/{self.main_branch}")

        except GitCommandError as e:

            if "Could not read from remote repository" in str(e):

                logger.debug(f"Connection error while rebasing {self.repo_url}: {e}")
                raise GitConnectionError(repo=self.repo_url) from e

            logger.debug(f"Failed to rebase: {e}")

            raise GitRebaseError(repo=self.repo_url) from e

    # ────────────────────────────────────────────────
    # Git Operations
    # ────────────────────────────────────────────────

    async def pull(self):

        try:

            logger.debug(f"Pulling latest changes for {self.repo_url}")

            await self._load_repo()
            await asyncio.to_thread(self.repo.git.pull)

        except GitCommandError as e:

            if "Could not resolve hostname" in f"{e}":

                logger.debug(f"Connection error while pulling {self.repo_url}: {e}")
                raise GitConnectionError(repo=self.repo_url) from e

            logger.debug(f"Failed to pull: {e}")
            raise GitError("Failed to pull", repo=self.repo_url) from e

    async def commit_and_push(self, message: str):

        try:
            await self._load_repo()

            logger.debug(f"Committing changes with message: {message}")
            await asyncio.to_thread(self.repo.git.add, "--all")

            try:
                await asyncio.to_thread(self.repo.git.commit, "-m", message)
            except GitCommandError as e:
                if "nothing to commit" in str(e):
                    logger.debug("No changes to commit.")
                    return
                raise e

            else:
                logger.debug(f"Pushing changes to {self.repo_url}")
                await asyncio.to_thread(self.repo.git.push)

        except GitCommandError as e:

            logger.debug(f"Failed to commit and push changes: {e}")
            raise GitCommitError(repo=self.repo_url) from e

    async def clean(self):

        try:
            await self._load_repo()

            logger.debug(f"Cleaning untracked files in {self.repo_url}")
            await asyncio.to_thread(self.repo.git.clean, '-xdf')

        except GitCommandError as e:

            logger.debug(f"Failed to clean untracked files: {e}")
            raise GitError(f"Git error during clean: {e}", repo=self.repo_url) from e

    # ────────────────────────────────────────────────
    # Branch Operations
    # ────────────────────────────────────────────────

    async def checkout(self, branch: str = None):
        """Checkout to another branch and rebase it to the main branch."""

        if branch is None:
            branch = self.main_branch

        if branch == self.branch:
            return

        try:
            await self._load_repo()
            # Checkout to the requested branch

            if branch not in self.repo.branches:

                logger.debug(f"Branch {branch} does not exist, creating it.")
                await asyncio.to_thread(self.repo.git.checkout, "-b", branch)
                await asyncio.to_thread(self.repo.git.push, "-u", "origin", branch)

            else:

                logger.debug(f"Checking out existing branch: {branch}")
                await asyncio.to_thread(self.repo.git.checkout, branch)

            # Update the branch attribute
            self.branch = branch

            # Rebase the current branch onto the main branch
            await self._rebase()

        except GitCommandError as e:

            logger.debug(f"Failed to checkout {branch}: {e}")
            raise GitError(
                f"Error during checkout and rebase to {branch}",
                repo=self.repo_url
            ) from e

    # ────────────────────────────────────────────────
    # Folder & File Management
    # ────────────────────────────────────────────────
    async def manage_git_keep(self, relative_path: str):

        contents = await self.list_all(relative_path)
        git_keep_path = os.path.join(relative_path, ".gitkeep")

        logger.debug(f"Checking if .gitkeep is needed in {relative_path}")

        if len(contents) == 0:
            logger.debug(f"No files in {relative_path}, creating .gitkeep")
            await self.write_file(git_keep_path, "")

        elif len(contents) > 1 and ".gitkeep" in contents:
            logger.debug(f"Multiple files in {relative_path}, removing .gitkeep")
            await self.delete_file(git_keep_path)

    async def make_folder(self, relative_path: str):
        logger.debug(f"Creating folder at {relative_path}")

        await asyncio.to_thread(os.makedirs, self._abs_path(relative_path), exist_ok=True, mode=0o755)
        await self.manage_git_keep(relative_path)

    async def delete_folder(self, relative_path: str):
        full_path = self._abs_path(relative_path)
        logger.debug(f"Deleting folder at {relative_path}")

        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            raise FolderNotFound(
                path=relative_path,
                repo=self.repo_url
            )

        if full_path.removesuffix("/") == self.allowed_path.removesuffix("/"):
            raise PathAccessDenied(
                path=relative_path,
                repo=self.repo_url
            )

        # Remove the folder and its contents
        logger.debug(f"Removing folder and its contents at {full_path}")
        await asyncio.to_thread(os.rmdir, full_path)
        await self.manage_git_keep(os.path.dirname(relative_path))


    async def delete_file(self, relative_path: str):
        full_path = self._abs_path(relative_path)

        if os.path.exists(full_path) and os.path.isfile(full_path):

            logger.debug(f"Deleting file at {relative_path}")

            await asyncio.to_thread(os.remove, full_path)
            await self.manage_git_keep(os.path.dirname(relative_path))

        else:
            raise FolderNotFound(
                path=relative_path,
                repo=self.repo_url
            )

    async def write_file(self, relative_path: str, content: str):
        full_path = self._abs_path(relative_path)

        logger.debug(f"Writing file at {relative_path}")
        await asyncio.to_thread(os.makedirs, os.path.dirname(full_path), exist_ok=True, mode=0o755)

        logger.debug(f"Writing file content at {relative_path}")
        await asyncio.to_thread(self._write_text, full_path, content)

        await self.manage_git_keep(os.path.dirname(relative_path))

    async def read_file(self, relative_path: str) -> str:
        full_path = self._abs_path(relative_path)

        logger.debug(f"Reading file at {relative_path}")

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise FolderNotFound(
                path=relative_path,
                repo=self.repo_url
            )

        return await asyncio.to_thread(self._read_text, full_path)

    async def rename_path(self, old_relative_path: str, new_relative_path: str):
        old_full_path = self._abs_path(old_relative_path)
        new_full_path = self._abs_path(new_relative_path)

        if not os.path.exists(old_full_path):
            raise InvalidPathError(
                path=old_relative_path,
                repo=self.repo_url
            )

        logger.debug(f"Ensuring new path does exist: {new_relative_path}")

        await asyncio.to_thread(os.makedirs, os.path.dirname(new_full_path), exist_ok=True, mode=0o755)

        logger.debug(f"Renaming {old_relative_path} to {new_relative_path}")

        # Perform rename (move)
        await asyncio.to_thread(os.rename, old_full_path, new_full_path)

        # Manage .gitkeep files in old and new parent folders
        await self.manage_git_keep(os.path.dirname(old_relative_path))
        await self.manage_git_keep(os.path.dirname(new_relative_path))

    async def list_files_only(self, relative_path: str) -> list[str]:
        full_path = self._abs_path(relative_path)

        if not os.path.exists(full_path):
            raise InvalidPathError(
                path=relative_path,
                repo=self.repo_url
            )

        logger.debug(f"Listing files in {relative_path}")

        entries = await asyncio.to_thread(os.listdir, full_path)
        files = []
        for entry in entries:
            entry_path = os.path.join(full_path, entry)
            if os.path.isfile(entry_path):
                files.append(entry)
        return files

    async def list_folders_only(self, relative_path: str) -> list[str]:
        full_path = self._abs_path(relative_path)

        if not os.path.exists(full_path):
            raise InvalidPathError(
                path=relative_path,
                repo=self.repo_url
            )

        logger.debug(f"Listing folders in {relative_path}")

        entries = await asyncio.to_thread(os.listdir, full_path)
        folders = []
        for entry in entries:
            entry_path = os.path.join(full_path, entry)
            if os.path.isdir(entry_path):
                folders.append(entry)
        return folders

    async def list_all(self, relative_path: str) -> list[str]:
        full_path = self._abs_path(relative_path)
        if not os.path.exists(full_path):
            raise InvalidPathError(
                path=relative_path,
                repo=self.repo_url
            )

        logger.debug(f"Listing all contents in {relative_path}")

        return await asyncio.to_thread(os.listdir, full_path)

    def does_path_exist(self, relative_path: str) -> bool:
        """Check if a file or folder exists at the given relative path."""

        logger.debug(f"Checking if path exists: {relative_path}")
        return os.path.exists(self._abs_path(relative_path))

    async def get_tree(self, relative_path: str) -> dict:

        abs_path = self._abs_path(relative_path)
        logger.debug(f"Getting tree structure for {relative_path}")
        return await get_tree(abs_path, self.repo_url)

    # ────────────────────────────────────────────────
    # Internal Helpers
    # ────────────────────────────────────────────────

    def _abs_path(self, relative_path: str) -> str:
        abs_path = os.path.abspath(os.path.join(self.local_path, self.base_folder, relative_path))
        self._ensure_within_repo(abs_path, relative_path)
        return abs_path

    def _read_text(self, path: str) -> str:
        path = self._abs_path(path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_text(self, path: str, content: str):
        path = self._abs_path(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _ensure_within_repo(self, abs_path: str, relative_path: str):

        repo_root = os.path.abspath(os.path.join(self.local_path, self.base_folder))
        abs_path = os.path.abspath(abs_path)

        if not abs_path.startswith(repo_root):
            raise PathAccessDenied(
                path=relative_path,
                repo=self.repo_url
            )

        if abs_path.endswith(".git") or abs_path.find(".git/") != -1:
            raise PathAccessDenied(
                path=relative_path,
                repo=self.repo_url
            )


async def get_tree(base_path: str, repo_url: str) -> dict:
    def build_tree(path):
        tree = {"name": os.path.basename(path), "type": "folder", "children": []}
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.name == ".git":
                        continue

                    if entry.is_dir(follow_symlinks=False):
                        tree["children"].append(build_tree(entry.path))
                    else:
                        tree["children"].append({
                            "name": entry.name,
                            "type": "file"
                        })
        except FileNotFoundError:
            raise FolderNotFound(
                path=path,
                repo=repo_url
            )
        return tree

    abs_path = os.path.abspath(base_path)
    return await asyncio.to_thread(build_tree, abs_path)
