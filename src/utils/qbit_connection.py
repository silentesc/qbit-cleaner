import qbittorrentapi
import typing
import time
from loguru import logger

from src.data.config import CONFIG


class QbitConnection:
    def __init__(self) -> None:
        self.max_login_try_count = 3

        self.conn_info: dict[str, typing.Any] = dict(
            host=CONFIG["qbittorrent"]["host"],
            port=CONFIG["qbittorrent"]["port"],
            username=CONFIG["qbittorrent"]["username"],
            password=CONFIG["qbittorrent"]["password"],
        )
        self.client = self.__make_client()
        self.__login()


    def __make_client(self) -> qbittorrentapi.Client:
        return qbittorrentapi.Client(**self.conn_info)


    def __login(self, try_count: int = 1) -> bool:
        try:
            self.client.auth_log_in()
            logger.info("Logged into qbittorrent")
            return True
        except (qbittorrentapi.LoginFailed, qbittorrentapi.APIConnectionError) as e:
            if try_count < self.max_login_try_count:
                logger.error(f"Failed to login to qbittorrent on try {try_count}/{self.max_login_try_count}, waiting 10 seconds and trying again...")
                time.sleep(10)
                return self.__login(try_count=try_count+1)
            else:
                logger.critical(f"Failed to login to qbittorrent after {try_count} tries: {e}")
                return False


    def __is_connection_ok(self) -> bool:
        try:
            self.client.app_version()
            logger.trace("Connection check successful")
            return True
        except (qbittorrentapi.Unauthorized401Error, qbittorrentapi.Forbidden403Error):
            return self.__login()
        except qbittorrentapi.LoginFailed:
            try:
                self.client.auth_log_out()
            finally:
                self.client = self.__make_client()
                return self.__login()


    def get_client(self) -> qbittorrentapi.Client:
        if self.__is_connection_ok():
            return self.client
        else:
            raise ConnectionError("Unable to establish a connection to qBittorrent.")


QBIT_CONNECTION = QbitConnection()
