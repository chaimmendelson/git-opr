from .logger import get_logger
from ..models.tasks import TaskModel

logger = get_logger()

def log_task_start(task: TaskModel) -> None:
    """Log the start of a task."""
    logger.info(f"Task {task.description} with id {task.task_id} enquired by {task.user} started.")

def log_task_completion(task: TaskModel) -> None:
    """Log the completion of a task."""
    logger.info(f"Task {task.description} with id {task.task_id} for {task.user} completed.")

def log_task_failure(task: TaskModel) -> None:
    """Log the failure of a task."""
    logger.info(
        f"Task {task.description} with id {task.task_id} for {task.user} failed. Error: {task.error}"
    )

def log_action(user: str, action: str) -> None:
    """Log a user action."""
    logger.info(f"User {user}, {action}.")