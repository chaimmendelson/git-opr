from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..db import reposFile, ReposFile
import jwt

from ..models.repos_file import AuthLevel

security = HTTPBearer()

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = creds.credentials
    try:
        # Decode without signature verification
        payload = jwt.decode(token, options={"verify_signature": False})
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Missing 'sub' in JWT")
        return sub
    except jwt.DecodeError:
        raise HTTPException(status_code=400, detail="Invalid JWT token")

def has_access_to_repo(repo_id: str, user: str, auth_level: AuthLevel) -> bool:
    repo = reposFile.get_repo(repo_id)

    if not repo:
        raise HTTPException(status_code=404, detail="Repo not found")

    return repo.has_permission(user, auth_level)

def verify_repo_access_with_level(required_level: AuthLevel = AuthLevel.READ):
    def verify(repo_id: str = Query(...), user: str = Depends(get_current_user)) -> str:
        has_access = has_access_to_repo(repo_id, user, auth_level=required_level)

        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied to the repository")

        return user

    return verify