from pydantic import BaseModel
from typing import List
from .tasks import TaskModel

class ListContentResponse(BaseModel):
    folders: List[str]
    files: List[str]

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
