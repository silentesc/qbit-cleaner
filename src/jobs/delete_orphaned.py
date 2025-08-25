import os
import qbittorrentapi
import typing
from datetime import datetime
from loguru import logger

from src.utils.datetime_utils import DateTimeUtils
from src.utils.discord_webhook_utils import DiscordWebhookUtils, EmbedColor

from src.data.env import ENV
from src.data.config import CONFIG


class DeleteOrphaned:
    def __init__(self) -> None:
        self.conn_info: dict[str, typing.Any] = dict(
            host=CONFIG["qbittorrent"]["host"],
            port=CONFIG["qbittorrent"]["port"],
            username=CONFIG["qbittorrent"]["username"],
            password=CONFIG["qbittorrent"]["password"],
        )


    def run(self) -> None:
        logger.info("Running 'delete_orphaned' job")

        qbit_file_paths: list[str] = self.get_qbit_file_paths()
        logger.debug(f"Found {len(qbit_file_paths)} files in qbittorrent")

        file_count = 0
        for root, _, files in os.walk(ENV.get_torrents_path()):
            for filename in files:
                file_count += 1
                file_path = os.path.join(root, filename)
                if not file_path in qbit_file_paths:
                    stats = os.stat(file_path)
                    match CONFIG["jobs"]["delete_orphaned"]["action"]:
                        case "test":
                            logger.info("Action = test | Doing nothing")
                        case "delete":
                            logger.info("Action = delete | Deleting files")
                            os.remove(file_path)
                        case _:
                            logger.warning("Invalid action for delete_orphaned job")
                    self.send_discord_notification(embed_title="Found orphaned torrent", file_path=file_path, stats=stats)
        logger.debug(f"Found {file_count} files in torrent folder")

        if len(qbit_file_paths) != file_count:
            logger.warning(f"qbittorrent file count does not match torrent folder file count ({len(qbit_file_paths)} != {file_count})")

        logger.info(f"job delete_orphaned finished, next run in {CONFIG["jobs"]["delete_orphaned"]["interval_hours"]} hours")


    def get_qbit_file_paths(self) -> list[str]:
        qbit_paths = []
        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            for torrent in qbt_client.torrents_info():
                if os.path.isfile(torrent.content_path):
                    qbit_paths.append(torrent.content_path)
                    continue
                for root, _, files in os.walk(torrent.content_path):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        if file_path in qbit_paths:
                            continue
                        qbit_paths.append(file_path)
        return qbit_paths


    def send_discord_notification(self, embed_title: str, file_path: str, stats: os.stat_result) -> None:
            DiscordWebhookUtils().send_webhook_embed(
                embed_color=EmbedColor.PURPLE,
                title=embed_title,
                fields=[
                    { "name": "Action", "value": CONFIG["jobs"]["delete_orphaned"]["action"] },
                    { "name": "File", "value": file_path },
                    { "name": "Size", "value": f"{stats.st_size / 1000 / 1000 / 1000}GB" },
                    { "name": "Created", "value": DateTimeUtils().get_datetime_readable(datetime.fromtimestamp(stats.st_ctime)) },
                    { "name": "Modified", "value": DateTimeUtils().get_datetime_readable(datetime.fromtimestamp(stats.st_mtime)) },
                ]
            )
