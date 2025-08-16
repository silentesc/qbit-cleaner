import qbittorrentapi
import typing
from qbittorrentapi import TorrentDictionary
from datetime import datetime, timedelta

from src.file_utils import FileUtils

from src.data.constants import env


def main() -> int:
    conn_info: dict[str, typing.Any] = dict(
        host=env.get_qbittorrent_host(),
        port=env.get_qbittorrent_port(),
        username=env.get_qbittorrent_username(),
        password=env.get_qbittorrent_password(),
    )

    with qbittorrentapi.Client(**conn_info) as qbt_client:
        file_utils = FileUtils(
            data_path=env.get_data_path(),
            torrents_path=env.get_torrents_path(),
            media_path=env.get_media_path(),
        )

        for torrent in qbt_client.torrents_info():
            torrent: TorrentDictionary
            name: str = torrent.name
            tags: str = torrent.tags
            content_path: str = env.get_qbittorrent_pre_path() + torrent.content_path
            completed_on_raw: int = torrent.completion_on
            completed_on: datetime = datetime.fromtimestamp(completed_on_raw)

            # Ignore protected tags
            if env.get_qbittorrent_protected_tag() in tags.lower():
                continue
            # Ignore torrents younger that x days
            if completed_on_raw == -1 or completed_on > (datetime.now() - timedelta(days=env.get_min_torrent_age_days())):
                continue
            # Ignore torrents that have a connection to the media library
            if file_utils.is_content_in_media_library(content_path=content_path):
                continue

            print(name)

    return 0
