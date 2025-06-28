from datetime import datetime, timezone

from pydantic import BaseModel
from typing import Optional
from enum import Enum
from fastapi import status as http_status

class TaskStatus(str, Enum):
    """Enum for task status."""
    IN_PROGRESS = "PENDING"
    COMPLETED = "OK"
    FAILED = "ERROR"

class TaskModel(BaseModel):
    task_id: str
    user: str
    description: str
    status: TaskStatus = TaskStatus.IN_PROGRESS
    result: Optional[str] = None
    error: Optional[str] = None
    status_code: int = http_status.HTTP_200_OK
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

    def update_status(
            self,
            status: TaskStatus,
            result: Optional[str] = None,
            error: Optional[str] = None,
            status_code: int = http_status.HTTP_200_OK
    ):
        """Update the task status and related fields."""
        self.status = status
        self.result = result
        self.error = error
        self.status_code = status_code
        self.updated_at = datetime.now(timezone.utc)

