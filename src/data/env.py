import os
import dotenv
from loguru import logger


class Env:
    def __init__(self) -> None:
        logger.debug("Loading env")
        dotenv.load_dotenv()


    def __get_var(self, var_name: str) -> str:
        env: str | None = os.getenv(var_name)
        if env is None:
            raise ValueError(f"Environment variable '{var_name}' is not set.")
        return env


    def get_torrents_path(self) -> str:
        return self.__get_var("TORRENTS_PATH")


    def get_media_path(self) -> str:
        return self.__get_var("MEDIA_PATH")


ENV = Env()
