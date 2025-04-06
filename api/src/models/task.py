from pydantic import BaseModel
from typing import Optional, List
import datetime
from uuid import UUID, uuid4
from enum import Enum

class TaskStatus(str, Enum):
    """Enum for task status."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):
    """Task model."""
    id: UUID
    name: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }

    @staticmethod
    def generate(name: str) -> "Task":
        """Generate a new task."""
        return Task(
            id=uuid4(),
            name=name,
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime.datetime.now(datetime.UTC),
            updated_at=datetime.datetime.now(datetime.UTC),
        )

    def complete(self):
        """Mark the task as completed."""
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.datetime.now(datetime.UTC)

    def fail(self, description: str):
        """Mark the task as failed."""
        self.status = TaskStatus.FAILED
        self.description = description
        self.updated_at = datetime.datetime.now(datetime.UTC)