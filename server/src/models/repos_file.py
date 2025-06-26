from pydantic import BaseModel, RootModel
from typing import Dict, Optional, List
from enum import Enum

class AuthLevel(int, Enum):
    READ = 3
    WRITE = 2
    ADMIN = 1

class Permissions(BaseModel):
    read: Optional[List[str]] = []
    write: Optional[List[str]] = []
    admin: Optional[List[str]] = []

class RepoConfig(BaseModel):
    repo_url: str
    local_path: str
    base_folder: Optional[str] = ""
    main_branch: Optional[str] = "master"
    permissions: Optional[Permissions] = Permissions()

    def has_permission(self, username: str, authLevel: AuthLevel) -> bool:
        if username in self.permissions.admin:
            return authLevel >= AuthLevel.ADMIN
        if username in self.permissions.write:
            return authLevel >= AuthLevel.WRITE
        if username in self.permissions.read:
            return authLevel >= AuthLevel.READ
        return False

class ReposConfig(RootModel[Dict[str, RepoConfig]]):
    pass
