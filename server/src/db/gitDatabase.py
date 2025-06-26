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
        self.allowed_path: str = os.path.join(self.local_path, self.base_folder)

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
        await asyncio.to_thread(self.repo.git.reset, '--hard', f"origin/{self.main_branch}")
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
    async def manage_git_keep(self, relative_path: str):
        contents = await self.list_all(relative_path)
        git_keep_path = os.path.join(relative_path, ".gitkeep")
        if len(contents) == 0:
            await self.write_file(git_keep_path, "")
        elif len(contents) > 1 and ".gitkeep" in contents:
            await self.delete_file(git_keep_path)

    async def make_folder(self, relative_path: str):
        await asyncio.to_thread(os.makedirs, self._abs_path(relative_path), exist_ok=True, mode=0o755)
        await self.manage_git_keep(relative_path)

    async def delete_folder(self, relative_path: str):
        full_path = self._abs_path(relative_path)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            raise FileNotFoundError(f"No folder found at {relative_path}")

        if full_path.removesuffix("/") == self.allowed_path.removesuffix("/"):
            raise PermissionError("Attempted to delete base directory")

        await asyncio.to_thread(os.rmdir, full_path)
        await self.manage_git_keep(os.path.dirname(relative_path))


    async def delete_file(self, relative_path: str):
        full_path = self._abs_path(relative_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            await asyncio.to_thread(os.remove, full_path)
            await self.manage_git_keep(os.path.dirname(relative_path))
        else:
            raise FileNotFoundError(f"No file found at {relative_path}")

    async def write_file(self, relative_path: str, content: str):
        full_path = self._abs_path(relative_path)
        await asyncio.to_thread(os.makedirs, os.path.dirname(full_path), exist_ok=True, mode=0o755)
        await asyncio.to_thread(self._write_text, full_path, content)
        await self.manage_git_keep(os.path.dirname(relative_path))

    async def read_file(self, relative_path: str) -> str:
        full_path = self._abs_path(relative_path)
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            raise FileNotFoundError(f"No file found at {relative_path}")

        return await asyncio.to_thread(self._read_text, full_path)

    async def rename_path(self, old_relative_path: str, new_relative_path: str):
        old_full_path = self._abs_path(old_relative_path)
        new_full_path = self._abs_path(new_relative_path)

        if not os.path.exists(old_full_path):
            raise FileNotFoundError(f"Source path does not exist: {old_full_path}")

        # Ensure destination folder exists
        await asyncio.to_thread(os.makedirs, os.path.dirname(new_full_path), exist_ok=True)

        # Perform rename (move)
        await asyncio.to_thread(os.rename, old_full_path, new_full_path)

        # Manage .gitkeep files in old and new parent folders
        await self.manage_git_keep(os.path.dirname(old_relative_path))
        await self.manage_git_keep(os.path.dirname(new_relative_path))

    async def list_files_only(self, relative_path: str) -> list[str]:
        full_path = self._abs_path(relative_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"No folder found at {relative_path}")

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
            raise FileNotFoundError(f"No folder found at {relative_path}")

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
            raise FileNotFoundError(f"No folder found at {relative_path}")
        return await asyncio.to_thread(os.listdir, full_path)

    def does_path_exist(self, relative_path: str) -> bool:
        return os.path.exists(self._abs_path(relative_path))

    async def get_tree(self, relative_path: str) -> dict:
        abs_path = self._abs_path(relative_path)
        self._ensure_within_repo(abs_path, relative_path)
        return await get_tree(abs_path)

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
            raise PermissionError(f"Access denied, outside repository root: {relative_path}")
        if abs_path.endswith(".git") or abs_path.find(".git/") != -1:
            raise PermissionError(f"Access denied, Attempting to access .git: {relative_path}")


async def get_tree(base_path: str) -> dict:
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
            raise FileNotFoundError(f"Path not found: {path}")
        return tree

    abs_path = os.path.abspath(base_path)
    return await asyncio.to_thread(build_tree, abs_path)
