import json
import os
from typing import Optional

from pydantic import ValidationError

from ..models.repos_file import ReposConfig, RepoConfig
from ..utils.logger import logger
from ..exceptions.exceptions import (
    ConfigError
)


def load_config(file_path: str) -> ReposConfig:
    if not os.path.exists(file_path):
        raise ConfigError("Config file not found")

    with open(file_path, "r") as f:
        raw_data = json.load(f)

    try:
        return ReposConfig.model_validate(raw_data)

    except ValidationError as e:
        logger.error("Invalid config:", e)
        raise ConfigError("Invalid configuration format") from e

class ReposFile:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.repos: ReposConfig = ReposConfig({})
        self.reload()

    def get_repo(self, repo_id: str) -> Optional[RepoConfig]:
        """
        Get a specific repository configuration by its ID.
        """
        return self.repos.root.get(repo_id, None)

    def reload(self):
        """
        Reload the configuration from the file.
        """
        try:

            self.repos = load_config(self.file_path)
            logger.debug("Configuration reloaded successfully")

        except ConfigError as e:
            logger.info(f"Failed to reload configuration: {e}")

        except Exception as e:
            logger.error(f"Unexpected error while reloading configuration: {e}")