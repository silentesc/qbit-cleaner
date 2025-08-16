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


    def get_qbittorrent_pre_path(self) -> str:
        return self.__get_var("QBITTORRENT_PRE_PATH")


    def get_qbittorrent_protected_tag(self) -> str:
        return self.__get_var("QBITTORRENT_PROTECTED_TAG")


    def get_min_torrent_age_days(self) -> int:
        return int(self.__get_var("MIN_TORRENT_AGE_DAYS"))


    def get_data_path(self) -> str:
        return self.__get_var("DATA_PATH")


    def get_torrents_path(self) -> str:
        return self.__get_var("TORRENTS_PATH")


    def get_media_path(self) -> str:
        return self.__get_var("MEDIA_PATH")
