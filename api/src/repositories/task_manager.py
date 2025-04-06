import asyncio
import time
from typing import Callable, Any, List
from ..db import AsyncGit
from ..models import Task, TaskStatus

class GitTaskManager:
    def __init__(self):
        self.tasks: {str: Task} = {}  # Dictionary to hold task states
        self.task_lock = asyncio.Lock()  # Lock to ensure sequential task processing

    async def execute_git_function(
            self, git_repo: AsyncGit,
            git_function: Callable[[AsyncGit], Any],
            commit_message: str
    ) -> str:

        """Add a task and return a unique UUID for tracking."""
        task = Task.generate(commit_message)
        task_id = str(task.id)

        self.tasks[task_id] = task

        # Start processing the task
        await self._process_task(task_id, git_repo, git_function, commit_message)

        return task_id

    async def _process_task(self, task_id: str, git_repo: AsyncGit, git_function: Callable[[AsyncGit], Any], commit_message: str):
        """Process a task sequentially, ensuring no concurrent tasks."""
        self._expire_tasks()
        
        async with self.task_lock:
            task: Task = self.tasks[task_id]
            try:
                await git_function(git_repo)  # Run the provided git function

                # Commit and push changes
                await git_repo.commit_and_push(commit_message)

                # Update the task state to complete and add the time of completion
                task.complete()

            except Exception as e:
                # If an error occurs, update the task state to failed
                task.fail(str(e))

    def get_task_state(self, task_id: str) -> Task:
        """Return the current state of a task."""
        task_state = self.tasks.get(task_id)

        if task_state:
            return task_state

        else:
            raise ValueError(f"Task with ID {task_id} not found.")

    def _expire_tasks(self):
        """Remove tasks that are older than 10 minutes."""
        current_time = time.time()
        expired_tasks = [
            task_id for task_id, 
            task in self.tasks.items() 
            if (current_time - task.created_at.timestamp()) > 600 and
               task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]

        for task_id in expired_tasks:
            del self.tasks[task_id]

