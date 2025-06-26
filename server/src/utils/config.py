import os
from dotenv import load_dotenv


def get_env_var(env_var: str, default=None) -> str:
    """
    Get an environment variable, raise error if not found and no default provided.

    Args:
        env_var (str): The environment variable name.
        default (any, optional): The default value if env var is missing.

    Returns:
        str: The environment variable value or the default.

    Raises:
        ValueError: If env var is not set and no default is provided.
    """
    value = os.getenv(env_var)
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"{env_var} is required but not set.")
    return value


class Config:
    """Loads environment variables from a .env file and provides access to them."""

    def __init__(self, env_file: str = ".env"):
        load_dotenv(env_file, override=True)  # Load .env variables

        self.PORT = int(get_env_var("PORT", 5000))

        self.DEBUG = get_env_var("DEBUG", "false").lower() in ("true", "1", "yes")

        git_key_path = get_env_var("GIT_PRIVATE_KEY_PATH", "./id_rsa")
        self.GIT_PRIVATE_KEY_PATH = (
            os.path.abspath(git_key_path) if git_key_path else None
        )

        if self.GIT_PRIVATE_KEY_PATH:
            os.chmod(self.GIT_PRIVATE_KEY_PATH, 0o600)
            os.environ[
                "GIT_SSH_COMMAND"
            ] = f'ssh -i "{self.GIT_PRIVATE_KEY_PATH}" -o StrictHostKeyChecking=no'

        self.BASE_CLONE_PATH = get_env_var("BASE_CLONE_PATH", "./repos")

        self.CONFIG_FILE = get_env_var("CONFIG_FILE", "./config.yaml")

        self.SYNC_INTERVAL: int = int(get_env_var("SYNC_INTERVAL", "60"))

# Usage:
config = Config()
