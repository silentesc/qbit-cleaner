import os
import qbittorrentapi
import typing
from datetime import datetime
from loguru import logger

from src.utils.datetime_utils import DateTimeUtils
from src.utils.discord_webhook_utils import DiscordWebhookUtils, EmbedColor
from src.utils.file_utils import FileUtils

from src.data.env import ENV
from src.data.constants import DATA_FOLDER_PATH
from src.data.config import CONFIG


class DeleteOrphaned:
    def __init__(self) -> None:
        self.conn_info: dict[str, typing.Any] = dict(
            host=CONFIG["qbittorrent"]["host"],
            port=CONFIG["qbittorrent"]["port"],
            username=CONFIG["qbittorrent"]["username"],
            password=CONFIG["qbittorrent"]["password"],
        )
        self.file_utils = FileUtils(
            data_path=DATA_FOLDER_PATH,
            torrents_path=ENV.get_torrents_path(),
            media_path=ENV.get_media_path(),
        )


    def run(self) -> None:
        logger.info("Running 'delete_orphaned' job")

        qbit_file_paths: set[str] = self.get_qbit_file_paths()
        logger.debug(f"Found {len(qbit_file_paths)} files in qbittorrent")

        self.handle_orphaned_files(qbit_file_paths=qbit_file_paths)
        self.handle_orphaned_empty_dirs(qbit_file_paths=qbit_file_paths)

        logger.info(f"job delete_orphaned finished, next run in {CONFIG["jobs"]["delete_orphaned"]["interval_hours"]} hours")


    def handle_orphaned_files(self, qbit_file_paths: set[str]) -> None:
        file_count = 0
        for root, _, files in os.walk(ENV.get_torrents_path()):
            for filename in files:
                file_count += 1
                file_path = os.path.join(root, filename)
                # If this happens, the file is not in qbittorrent anymore and can be deleted since no other torrent uses it bc then it would be in qbit_file_paths
                if not file_path in qbit_file_paths:
                    logger.info(f"Found orphaned file: {file_path}")
                    stats = os.stat(file_path)
                    match CONFIG["jobs"]["delete_orphaned"]["action"]:
                        case "test":
                            logger.info("Action = test | Doing nothing")
                        case "delete":
                            logger.info("Action = delete | Deleting files")
                            os.remove(file_path)
                        case _:
                            logger.warning("Invalid action for delete_orphaned job")
                    self.send_discord_notification(embed_title="Found orphaned files", file_path=file_path, stats=stats)
        logger.debug(f"Found {file_count} files in torrent folder")

        if len(qbit_file_paths) != file_count:
            logger.warning(f"qbittorrent file count does not match torrent folder file count ({len(qbit_file_paths)} != {file_count})")


    def handle_orphaned_empty_dirs(self, qbit_file_paths: set[str]) -> None:
        for dirpath in self.file_utils.get_empty_dirs():
            if dirpath in qbit_file_paths:
                logger.debug(f"{dirpath} is in qbit_file_paths, ignoring it")
                continue
            logger.info(f"Found orphaned dir: {dirpath}")
            stats = os.stat(dirpath)
            match CONFIG["jobs"]["delete_orphaned"]["action"]:
                case "test":
                    logger.info("Action = test | Doing nothing")
                case "delete":
                    logger.info("Action = delete | Deleting dir")
                    os.rmdir(dirpath)
                case _:
                    logger.warning("Invalid action for delete_orphaned job")
            self.send_discord_notification(embed_title="Found empty orphaned dir", file_path=dirpath, stats=stats)


    def get_qbit_file_paths(self) -> set[str]:
        qbit_paths = []
        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            for torrent in qbt_client.torrents_info():
                if os.path.isfile(torrent.content_path):
                    qbit_paths.append(torrent.content_path)
                    continue
                files = [f"{torrent.content_path}/{"/".join(str(file.name).split("/")[1:])}" for file in torrent.files]
                qbit_paths.extend(files)
        return set(qbit_paths)


    def send_discord_notification(self, embed_title: str, file_path: str, stats: os.stat_result) -> None:
            DiscordWebhookUtils().send_webhook_embed(
                embed_color=EmbedColor.PURPLE,
                title=embed_title,
                fields=[
                    { "name": "Action", "value": CONFIG["jobs"]["delete_orphaned"]["action"] },
                    { "name": "File", "value": file_path },
                    { "name": "Size", "value": f"{round(stats.st_size / 1000 / 1000 / 1000, 2)}GB" },
                    { "name": "Created", "value": DateTimeUtils().get_datetime_readable(datetime.fromtimestamp(stats.st_ctime)) },
                    { "name": "Modified", "value": DateTimeUtils().get_datetime_readable(datetime.fromtimestamp(stats.st_mtime)) },
                ]
            )
