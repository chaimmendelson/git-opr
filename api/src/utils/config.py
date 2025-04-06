import os
from dotenv import load_dotenv
load_dotenv(override=True)

class Config:

    def __init__(self):
        self.debug = os.getenv("DEBUG", False)
        self.port = os.getenv("PORT", 8000)

def load_env_or_raise(key: str, default=None):
    value = os.getenv(key, default)
    if not value:
        raise ValueError(f"Missing environment variable {key}")
    return value

config = Config()