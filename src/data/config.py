import os
import yaml
from loguru import logger

from src.data.constants import config_file_path


class Config:
    def __init__(self) -> None:
        logger.debug("Loading yaml config")
        self.config_yaml = None
        if os.path.exists(config_file_path):
            with open(config_file_path) as f:
                self.config_yaml = yaml.safe_load(f)
        else:
            logger.critical("Config does not exist, please create it")


    def get_config(self):
        if not self.config_yaml:
            raise FileNotFoundError()
        return self.config_yaml


CONFIG = Config().get_config()
