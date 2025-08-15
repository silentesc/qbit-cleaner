import qbittorrentapi
import typing

from src.data.constants import env


def main() -> int:
    conn_info: dict[str, typing.Any] = dict(
        host=env.get_qbittorrent_host(),
        port=env.get_qbittorrent_port(),
        username=env.get_qbittorrent_username(),
        password=env.get_qbittorrent_password(),
    )

    with qbittorrentapi.Client(**conn_info) as qbt_client:
        for torrent in qbt_client.torrents_info():
            print(torrent)
            break
            # print(f"{torrent.hash[-6:]}: {torrent.name} ({torrent.state})")

    return 0
