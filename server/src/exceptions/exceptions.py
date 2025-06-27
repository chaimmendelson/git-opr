# exceptions.py

class AppError(Exception):
    """Base exception for all application-level errors."""
    def __init__(self, message: str = "An unexpected error occurred."):
        super().__init__(message)
        self.message = message


# ───────────────────────────────────────────────
# Configuration & Environment
# ───────────────────────────────────────────────

class ConfigError(AppError):
    """Raised when there is an issue with application configuration."""


# ───────────────────────────────────────────────
# Authentication & Authorization
# ───────────────────────────────────────────────

class AuthError(AppError):
    """Base exception for authentication/authorization failures."""


class UnauthorizedError(AuthError):
    """Raised when the user is not authenticated."""
    def __init__(self, detail: str = "Unauthorized access."):
        super().__init__(detail)


class ForbiddenError(AuthError):
    """Raised when the user lacks permission to access a resource."""
    def __init__(self, detail: str = "Access forbidden."):
        super().__init__(detail)


# ───────────────────────────────────────────────
# Git-related Errors
# ───────────────────────────────────────────────

class GitError(AppError):
    """Base exception for Git operation errors."""

    default_message = "An unexpected error occurred."

    def __init__(self, message: str = None, repo: str = None):
        super().__init__(f"{message} [Repo: {repo}]")


class GitConnectionError(GitError):
    """Raised when Git remote is unreachable."""

    default_message = "Could not connect to remote"

class GitRebaseError(GitError):
    """Raised when a Git rebase fails."""

    default_message = "Git rebase failed."

class GitCommitError(GitError):
    """Raised when a Git commit fails."""

    default_message = "Git commit failed."

class GitPushError(GitError):
    """Raised when a Git push fails"""

    default_message = "Git push failed."

# ───────────────────────────────────────────────
# File & Path Management
# ───────────────────────────────────────────────

class FileError(AppError):
    """Base class for file-related errors."""

    default_message = "A file-related error occurred."

    def __init__(self, message: str = None, path: str = None, repo: str = None):
        if message is None:
            message = self.default_message
        if path:
            message = f"{message} [Path: {path}, Repo: {repo}]"
        super().__init__(message)
        self.path = path


class FileNotFound(FileError):
    """Raised when a file is not found."""

    default_message = "File not found."


class FolderNotFound(FileError):
    """Raised when a folder is not found."""

    default_message = "Folder not found."


class InvalidPathError(FileError):
    """Raised when a path is invalid or outside allowed scope."""

    default_message = "Invalid path."


class PathAccessDenied(FileError):
    """Raised when trying to access a restricted path."""

    default_message = "Access to the specified path is denied."


# ───────────────────────────────────────────────
# API Communication
# ───────────────────────────────────────────────

class APIError(AppError):
    """Base class for API request errors."""
    def __init__(self, message: str, error: str = "", status_code: int = 400):
        super().__init__(message)
        self.error = error
        self.status_code = status_code


class RemoteServiceError(APIError):
    """Raised when a third-party API call fails."""


# ───────────────────────────────────────────────
# Task Management
# ───────────────────────────────────────────────

class TaskError(AppError):
    """Base class for task-related errors."""

    default_message = "A task-related error occurred."

    def __init__(self, message: str = None, task_id: str = None):
        if message is None:
            message = self.default_message
        if task_id:
            message = f"{message} [Task ID: {task_id}]"
        super().__init__(message)
        self.task_id = task_id


class TaskNotFound(TaskError):
    """Raised when a task ID is not found in the store."""

    default_message = "Task not found."


class TaskTimeout(TaskError):
    """Raised when a task expires or takes too long."""

    default_message = "Task timed out."


# ───────────────────────────────────────────────
# Validation
# ───────────────────────────────────────────────

class ValidationError(AppError):
    """Generic input validation error."""


class JWTDecodeError(AuthError):
    """Raised when JWT cannot be decoded (even without verifying)."""

