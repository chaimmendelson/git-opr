from .repos_file import ReposFile
from ..utils.config import config

reposFile: ReposFile = ReposFile(config.CONFIG_FILE)