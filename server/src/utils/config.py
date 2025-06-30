import os
from dotenv import load_dotenv


def get_env_var(env_var: str, default=None) -> str:
    value = os.getenv(env_var)
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"{env_var} is required but not set.")
    return value


class Config:
    """Loads environment variables from a .env file and provides access to them."""

    def __init__(self):

        # Declare all attributes
        self.PORT: int = 5000
        self.DEBUG: bool = False
        self.LOG_LEVEL: str = "INFO"
        self.GIT_PRIVATE_KEY_PATH: str = "./id_rsa"
        self.BASE_CLONE_PATH: str = "./server/repos"
        self.CONFIG_FILE: str = "./config.yaml"
        self.LOG_FILE_PATH: str = "./server/logs/app.log"
        self.SYNC_INTERVAL: int = 60
        self.TASK_EXPIRATION: int = 10

        self.load_vars()

    def load_vars(self):
        load_dotenv(override=True)

        self.PORT = int(get_env_var("PORT", self.PORT))
        self.DEBUG = get_env_var("DEBUG", str(self.DEBUG)).lower() in ("true", "1", "yes")
        self.LOG_LEVEL = get_env_var("LOG_LEVEL", str(self.LOG_LEVEL)).upper()

        git_key_path = get_env_var("GIT_PRIVATE_KEY_PATH", self.GIT_PRIVATE_KEY_PATH)
        self.GIT_PRIVATE_KEY_PATH = os.path.abspath(git_key_path)

        os.chmod(self.GIT_PRIVATE_KEY_PATH, 0o600)

        os.environ["GIT_SSH_COMMAND"] = (
            f'ssh -i "{self.GIT_PRIVATE_KEY_PATH}" -o StrictHostKeyChecking=no'
        )

        self.BASE_CLONE_PATH = get_env_var("BASE_CLONE_PATH", self.BASE_CLONE_PATH)
        self.CONFIG_FILE = get_env_var("CONFIG_FILE", self.CONFIG_FILE)
        self.LOG_FILE_PATH = get_env_var("LOG_FILE_PATH", self.LOG_FILE_PATH)
        self.SYNC_INTERVAL = int(get_env_var("SYNC_INTERVAL", str(self.SYNC_INTERVAL)))
        self.TASK_EXPIRATION = int(get_env_var("TASK_EXPIRATION", str(self.TASK_EXPIRATION)))

    def reload(self):
        """Reload the environment variables, preserving current values if env is missing."""
        self.load_vars()


# Usage
config = Config()
