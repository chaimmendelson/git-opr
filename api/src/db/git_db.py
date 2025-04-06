import os
import asyncio
from git import Repo, GitCommandError
from typing import Optional, Union


class AsyncGit:
    def __init__(self, repo_url: str, local_path: str, base_folder: str, main_branch: str = "master"):
        self.repo_url = repo_url
        self.local_path = os.path.abspath(local_path)
        self.base_folder = base_folder
        self.main_branch = main_branch
        self.repo: Optional[Repo] = None
        self.branch: str = main_branch

    # ────────────────────────────────────────────────
    # Repo Setup & Base Utilities
    # ────────────────────────────────────────────────

    async def clone_or_sync(self):
        """Clone the repo or update it to latest main branch."""
        if os.path.exists(self.local_path):
            await self._load_repo()
        else:
            self.repo = await asyncio.to_thread(Repo.clone_from, self.repo_url, self.local_path)

        self.repo.git.checkout(self.main_branch)
        await self._rebase()

    async def _load_repo(self):
        """Load the repo from the local path."""
        if not os.path.exists(self.local_path):
            raise FileNotFoundError(f"No repo found at {self.local_path}")
        self.repo = await asyncio.to_thread(Repo, self.local_path)

        if self.repo.bare:
            raise Exception("Repo is bare and unusable")

    async def _rebase(self):
        """Rebase the current branch onto the main branch (origin/{main_branch})."""
        await asyncio.to_thread(self.repo.git.reset, '--hard')
        await asyncio.to_thread(self.repo.git.clean, '-xdf')
        await asyncio.to_thread(self.repo.remotes.origin.fetch)
        await asyncio.to_thread(self.repo.git.rebase, f"origin/{self.main_branch}")

    # ────────────────────────────────────────────────
    # Git Operations
    # ────────────────────────────────────────────────

    async def pull(self):
        try:
            await self._load_repo()
            await asyncio.to_thread(self.repo.git.pull)
        except GitCommandError as e:
            raise Exception(f"Git error during pull: {e}")

    async def commit_and_push(self, message: str):
        try:
            await self._load_repo()
            await asyncio.to_thread(self.repo.git.add, "--all")
            await asyncio.to_thread(self.repo.git.commit, "-m", message)
            await asyncio.to_thread(self.repo.git.push)
        except GitCommandError as e:
            raise Exception(f"Git error during commit: {e}")

    async def clean(self):
        try:
            await self._load_repo()
            await asyncio.to_thread(self.repo.git.clean, '-xdf')
        except GitCommandError as e:
            raise Exception(f"Git error during clean: {e}")

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
                await asyncio.to_thread(self.repo.git.checkout, "-b", branch)
                await asyncio.to_thread(self.repo.git.push, "-u", "origin", branch)
            else:
                await asyncio.to_thread(self.repo.git.checkout, branch)

            await self._rebase()

            # Update the branch attribute
            self.branch = branch

        except GitCommandError as e:
            raise Exception(f"Git error during checkout and rebase to {branch}: {e}")

    # ────────────────────────────────────────────────
    # Folder & File Management
    # ────────────────────────────────────────────────

    async def make_folder(self, relative_path: str):
        await asyncio.to_thread(os.makedirs, self._abs_path(relative_path), exist_ok=True)

    async def delete_folder(self, relative_path: str):
        full_path = self._abs_path(relative_path)
        if os.path.exists(full_path):
            await asyncio.to_thread(os.rmdir, full_path)
        else:
            raise FileNotFoundError(f"No folder found at {full_path}")

    async def delete_file(self, relative_path: str):
        full_path = self._abs_path(relative_path)
        if os.path.exists(full_path):
            await asyncio.to_thread(os.remove, full_path)
        else:
            raise FileNotFoundError(f"No file found at {full_path}")

    async def write_file(self, relative_path: str, content: str):
        full_path = self._abs_path(relative_path)
        await asyncio.to_thread(os.makedirs, os.path.dirname(full_path), exist_ok=True)
        await asyncio.to_thread(self._write_text, full_path, content)

    async def read_file(self, relative_path: str) -> str:
        full_path = self._abs_path(relative_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"No file found at {full_path}")
        return await asyncio.to_thread(self._read_text, full_path)

    async def get_file_list(self, relative_path: str) -> list[str]:
        full_path = self._abs_path(relative_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"No folder found at {full_path}")
        return await asyncio.to_thread(os.listdir, full_path)

    def does_path_exist(self, relative_path: str) -> bool:
        return os.path.exists(self._abs_path(relative_path))

    # ────────────────────────────────────────────────
    # Internal Helpers
    # ────────────────────────────────────────────────

    def _abs_path(self, relative_path: str) -> str:
        return os.path.join(self.local_path, self.base_folder, relative_path)

    def _read_text(self, path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_text(self, path: str, content: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
