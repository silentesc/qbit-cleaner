import os
import qbittorrentapi
import typing
from datetime import datetime
from loguru import logger

from src.utils.datetime_utils import DateTimeUtils
from src.utils.discord_webhook_utils import DiscordWebhookUtils, EmbedColor
from src.utils.strike_utils import StrikeUtils, StrikeType

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
        def handle_path(path: str, is_file: bool) -> None:
            if path in qbit_file_paths:
                logger.debug(f"{path} is in qbit_file_paths, ignoring it")
                return
            if not is_file and len(os.listdir(path)) != 0:
                logger.debug(f"{path} is not empty, ignoring it")
                return
            orphaned_paths.append(path)
            strike_utils = StrikeUtils(strike_type=StrikeType.DELETE_ORPHANED, torrent_hash=path)
            if not strike_utils.strike_torrent():
                required_strikes = CONFIG["jobs"]["delete_orphaned"]["required_strikes"]
                min_strike_days = CONFIG["jobs"]["delete_orphaned"]["min_strike_days"]
                logger.debug(f"{path} is orphaned but doesn't reach criteria ({strike_utils.get_strikes()}/{required_strikes} strikes, {strike_utils.get_consecutive_days()}/{min_strike_days} days)")
                return
            logger.info(f"Found orphaned {"file" if is_file else "dir"}: {path}")
            stats = os.stat(path)
            self.take_action(is_file=is_file, path=path)
            self.send_discord_notification(embed_title=f"Found orphaned {"file" if is_file else "dir"}", file_path=path, stats=stats)

        logger.info("Running 'delete_orphaned' job")

        qbit_file_paths: set[str] = self.get_qbit_file_paths()
        logger.debug(f"Found {len(qbit_file_paths)} files in qbittorrent")

        orphaned_paths = []

        for root, dirnames, filenames in os.walk(ENV.get_torrents_path(), topdown=False):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                handle_path(path=file_path, is_file=True)
            for dirname in dirnames:
                dirpath = os.path.join(root, dirname)
                handle_path(path=dirpath, is_file=False)

        StrikeUtils(strike_type=StrikeType.DELETE_ORPHANED, torrent_hash="unused").cleanup_db(hashes=orphaned_paths)

        logger.info(f"job delete_orphaned finished, next run in {CONFIG["jobs"]["delete_orphaned"]["interval_hours"]} hours")


    def take_action(self, is_file: bool, path: str) -> None:
        match CONFIG["jobs"]["delete_orphaned"]["action"]:
            case "test":
                logger.info("Action = test | Doing nothing")
            case "delete":
                logger.info("Action = delete | Deleting files")
                if is_file:
                    os.remove(path)
                else:
                    os.rmdir(path)
            case _:
                logger.warning("Invalid action for delete_orphaned job")


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
