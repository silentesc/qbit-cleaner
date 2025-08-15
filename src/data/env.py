import os
import dotenv


class Env:
    def __init__(self) -> None:
        dotenv.load_dotenv()


    def __get_var(self, var_name: str) -> str:
        env: str | None = os.getenv(var_name)
        if env is None:
            raise ValueError(f"Environment variable '{var_name}' is not set.")
        return env


    def get_qbittorrent_host(self) -> str:
        return self.__get_var("QBITTORRENT_HOST")


    def get_qbittorrent_port(self) -> str:
        return self.__get_var("QBITTORRENT_PORT")


    def get_qbittorrent_username(self) -> str:
        return self.__get_var("QBITTORRENT_USERNAME")


    def get_qbittorrent_password(self) -> str:
        return self.__get_var("QBITTORRENT_PASSWORD")
