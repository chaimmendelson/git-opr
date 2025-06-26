from pydantic import BaseModel

class FileRenameRequest(BaseModel):
    old_path: str
    new_path: str
