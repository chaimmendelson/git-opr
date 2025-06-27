from pydantic import BaseModel
from typing import List, Union, Optional
from .tasks import TaskModel

class PathExistsResponse(BaseModel):
    exists: bool

class RepoInfo(BaseModel):
    repo_id: str
    repo_url: str
    branch: str
    base_folder: str

class ReposListResponse(BaseModel):
    repos: List[RepoInfo]

class TaskResponse(BaseModel):
    task_id: str

class TaskStatusResponse(TaskModel):
    pass
