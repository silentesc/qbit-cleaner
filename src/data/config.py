import yaml
from loguru import logger

from src.data.constants import config_file_path


class Config:
    def __init__(self) -> None:
        logger.debug("Loading yaml config")
        with open(config_file_path) as f:
            self.config_yaml = yaml.safe_load(f)


    def get_config(self):
        return self.config_yaml


CONFIG = Config().get_config()
