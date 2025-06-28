from fastapi import status


class AppError(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        detail: str = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(message)
        self.message = message
        self.detail = detail or message
        self.status_code = status_code


# ──────────────────────────────────────────────────────────
# Configuration & Environment
# ────────────────────────────────────────────────────

class ConfigError(AppError):
    """Raised when there is an issue with application configuration."""

    def __init__(self, message: str = "Invalid or missing configuration."):
        super().__init__(message, message, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ────────────────────────────────────────────────────
# Authentication & Authorization
# ────────────────────────────────────────────────────

class AuthError(AppError):
    """Base exception for authentication/authorization failures."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = status.HTTP_401_UNAUTHORIZED
    ):
        super().__init__(message, message, status_code)


class UnauthorizedError(AuthError):
    """Raised when the user is not authenticated."""

    def __init__(self, message: str = "Unauthorized access."):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AuthError):
    """Raised when the user lacks permission to access a resource."""

    def __init__(self, message: str = "Access forbidden."):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class JWTDecodeError(AuthError):
    """Raised when JWT cannot be decoded (even without verifying)."""

    def __init__(self):
        super().__init__("Invalid JWT token.", status.HTTP_400_BAD_REQUEST)


# ────────────────────────────────────────────────────
# Git-related Errors
# ────────────────────────────────────────────────────

class GitError(AppError):
    """Base exception for Git operation errors."""

    default_message = "An unexpected Git error occurred."

    def __init__(self, message: str = None, repo: str = None):
        if message is None:
            message = self.default_message
        full_message = f"{message} [Repo: {repo}]" if repo else message
        super().__init__(message, full_message, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.repo = repo


class GitConnectionError(GitError):
    """Raised when Git remote is unreachable."""
    default_message = "Could not connect to remote."


class GitRebaseError(GitError):
    """Raised when a Git rebase fails."""
    default_message = "Git rebase failed."


class GitCommitError(GitError):
    """Raised when a Git commit fails."""
    default_message = "Git commit failed."


class GitPushError(GitError):
    """Raised when a Git push fails."""
    default_message = "Git push failed."


# ────────────────────────────────────────────────────
# File & Path Management
# ────────────────────────────────────────────────────

class FileError(AppError):
    """Base class for file-related errors."""

    def __init__(
        self,
        message: str = "A file-related error occurred.",
        path: str = None,
        repo: str = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        full_message = f"{message} [Path: {path or 'Unknown'}, Repo: {repo or 'Unknown'}]"
        super().__init__(message, full_message, status_code)
        self.path = path
        self.repo = repo


class FileNotFound(FileError):
    """Raised when a file is not found."""

    def __init__(self, path: str = None, repo: str = None):
        super().__init__("File not found.", path, repo, status.HTTP_404_NOT_FOUND)


class FolderNotFound(FileError):
    """Raised when a folder is not found."""

    def __init__(self, path: str = None, repo: str = None):
        super().__init__("Folder not found.", path, repo, status.HTTP_404_NOT_FOUND)


class InvalidPathError(FileError):
    """Raised when a path is invalid or outside allowed scope."""

    def __init__(self, path: str = None, repo: str = None):
        super().__init__("Invalid path.", path, repo, status.HTTP_400_BAD_REQUEST)


class PathAccessDenied(FileError):
    """Raised when trying to access a restricted path."""

    def __init__(self, path: str = None, repo: str = None):
        super().__init__("Access to the specified path is denied.", path, repo, status.HTTP_403_FORBIDDEN)


# ────────────────────────────────────────────────────
# API Communication
# ────────────────────────────────────────────────────

class APIError(AppError):
    """Base class for API request errors."""

    def __init__(self, message: str, error: str = "", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message, message, status_code)
        self.error = error


class RemoteServiceError(APIError):
    """Raised when a third-party API call fails."""

    def __init__(self, message: str = "Remote service communication failed.", error: str = ""):
        super().__init__(message, error, status.HTTP_502_BAD_GATEWAY)


# ────────────────────────────────────────────────────
# Task Management
# ────────────────────────────────────────────────────

class TaskError(AppError):
    """Base class for task-related errors."""

    default_message = "A task-related error occurred."

    def __init__(self, message: str = None, task_id: str = None):
        if message is None:
            message = self.default_message
        full_message = f"{message} [Task ID: {task_id}]" if task_id else message
        super().__init__(message, full_message, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.task_id = task_id


class TaskNotFound(TaskError):
    """Raised when a task ID is not found in the store."""
    default_message = "Task not found."

    def __init__(self, task_id: str = None):
        super().__init__(self.default_message, task_id)
        self.status_code = status.HTTP_404_NOT_FOUND


class TaskTimeout(TaskError):
    """Raised when a task expires or takes too long."""
    default_message = "Task timed out."

    def __init__(self, task_id: str = None):
        super().__init__(self.default_message, task_id)
        self.status_code = status.HTTP_408_REQUEST_TIMEOUT


# ────────────────────────────────────────────────────
# Validation
# ────────────────────────────────────────────────────

class ValidationError(AppError):
    """Generic input validation error."""

    def __init__(self, message: str = "Invalid input."):
        super().__init__(message, message, status.HTTP_422_UNPROCESSABLE_ENTITY)
