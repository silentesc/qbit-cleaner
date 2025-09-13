import qbittorrentapi
import typing
from datetime import datetime
from qbittorrentapi import TorrentDictionary
from loguru import logger

from src.utils.file_utils import FileUtils
from src.utils.datetime_utils import DateTimeUtils
from src.utils.discord_webhook_utils import DiscordWebhookUtils, EmbedColor
from src.utils.strike_utils import StrikeUtils, StrikeType

from src.data.env import ENV
from src.data.constants import DATA_FOLDER_PATH
from src.data.config import CONFIG


class DeleteForgotten:
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
        logger.info("Running 'delete_forgotten' job")

        logger.trace("Getting not_criteria_matching_content_paths")
        not_criteria_matching_content_paths: set[str] = self.get_not_criteria_matching_content_paths()

        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            logger.trace("Checking torrents")
            for torrent in qbt_client.torrents_info():
                torrent: TorrentDictionary
                hash: str = torrent.hash
                name: str = torrent.name
                content_path: str = torrent.content_path

                strike_utils = StrikeUtils(strike_type=StrikeType.DELETE_FORGOTTEN, torrent_hash=hash)

                # Ignore if criteria not matching
                if not self.is_criteria_matching(torrent=torrent):
                    strike_utils.reset_torrent()
                    continue

                # Strike torrent and check if limit reached
                is_torrent_limit_reached: bool = strike_utils.strike_torrent()
                if not is_torrent_limit_reached:
                    required_strikes = CONFIG["jobs"]["delete_forgotten"]["required_strikes"]
                    min_strike_days = CONFIG["jobs"]["delete_forgotten"]["min_strike_days"]
                    logger.debug(f"{name} is forgotten but doesn't reach criteria ({strike_utils.get_strikes()}/{required_strikes} strikes, {strike_utils.get_consecutive_days()}/{min_strike_days} days)")
                    continue

                logger.info(f"Found torrent that qualifies forgotten: {name}")
                self.take_action(torrent=torrent, content_path=content_path, not_criteria_matching_content_paths=not_criteria_matching_content_paths)
                self.send_discord_notification(embed_title="Found forgotten torrent", torrent=torrent)

            hashes = [torrent.hash for torrent in qbt_client.torrents_info()]
            StrikeUtils(strike_type=StrikeType.DELETE_FORGOTTEN, torrent_hash="unused").cleanup_db(hashes=hashes)

        logger.info(f"job delete_forgotten finished, next run in {CONFIG["jobs"]["delete_forgotten"]["interval_hours"]} hours")


    def get_not_criteria_matching_content_paths(self) -> set[str]:
        content_paths: list[str] = []

        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            for torrent in qbt_client.torrents_info():
                torrent: TorrentDictionary
                content_path = torrent.content_path
                if not self.is_criteria_matching(torrent=torrent):
                    content_paths.append(content_path)

        return set(content_paths)


    def is_criteria_matching(self, torrent: TorrentDictionary) -> bool:
        name: str = torrent.name
        tags: str = torrent.tags
        seeding_time_days: int = torrent.seeding_time / 60 / 60 / 24
        content_path: str = torrent.content_path
        completed_on_raw: int = torrent.completion_on

        # Protected tags
        if CONFIG["qbittorrent"]["protected_tag"] in tags.lower():
            logger.debug(f"{name} doesn't match criteria (has protection a tag)")
            logger.trace(f"Tags of {name}: {tags}")
            logger.trace(f"Protection tag: {CONFIG["qbittorrent"]["protected_tag"]}")
            return False
        # Uncompleted torrents
        if completed_on_raw == -1:
            logger.debug(f"{name} doesn't match criteria (not completed)")
            return False
        # Torrents that have a connection to the media library
        if self.file_utils.is_content_in_media_library(content_path=content_path):
            logger.debug(f"{name} doesn't match criteria (has content in media library)")
            return False
        # Torrents seeding less than x days
        if seeding_time_days < CONFIG["jobs"]["delete_forgotten"]["min_seeding_days"]:
            logger.debug(f"Found torrent that qualifies forgotten, but ignoring due to not reaching criteria {name} (seeding {round(seeding_time_days, 2)}/{CONFIG["jobs"]["delete_forgotten"]["min_seeding_days"]} days)")
            return False

        return True


    def take_action(self, torrent: TorrentDictionary, content_path: str, not_criteria_matching_content_paths: set[str]) -> None:
        match CONFIG["jobs"]["delete_forgotten"]["action"]:
            case "test":
                logger.info("Action = test | Torrent remains unhandled")
            case "stop":
                logger.info("Action = stop | Stopping torrent")
                torrent.stop()
            case "delete":
                logger.info("Action = delete | Deleting torrent + files")
                if content_path in not_criteria_matching_content_paths:
                    logger.warning(f"Only deleting torrent and not files for {torrent.name} Some other torrent that uses these files doesn't match criteria")
                    torrent.delete(delete_files=False)
                else:
                    torrent.delete(delete_files=True)
            case _:
                logger.warning("Invalid action for delete_forgotten job")


    def send_discord_notification(self, embed_title: str, torrent: TorrentDictionary) -> None:
            name: str = torrent.name
            category: str = torrent.category
            tags: str = torrent.tags
            tracker: str = torrent.tracker
            ratio: float = torrent.ratio
            total_size_gib: int = torrent.total_size / 1024 / 1024 / 1024
            total_size_gb: int = torrent.total_size / 1000 / 1000 / 1000
            seeding_time_days: int = torrent.seeding_time / 60 / 60 / 24
            completed_on_raw: int = torrent.completion_on
            completed_on: datetime = datetime.fromtimestamp(completed_on_raw)
            added_on_raw: int = torrent.added_on
            added_on: datetime = datetime.fromtimestamp(added_on_raw)

            DiscordWebhookUtils().send_webhook_embed(
                embed_color=EmbedColor.BLUE,
                title=embed_title,
                fields=[
                    { "name": "Action", "value": CONFIG["jobs"]["delete_forgotten"]["action"] },
                    { "name": "Name", "value": name },
                    { "name": "Tracker", "value": tracker },

                    { "name": "Category", "value": category },
                    { "name": "Tags", "value": tags },

                    { "name": "Total Size", "value": f"{str(round(total_size_gib, 2))}GiB | {str(round(total_size_gb, 2))}GB" },
                    { "name": "Ratio", "value": str(round(ratio, 2)) },

                    { "name": "Added", "value": DateTimeUtils().get_datetime_readable(added_on) },
                    { "name": "Completed", "value": DateTimeUtils().get_datetime_readable(completed_on) },
                    { "name": "Seeding Days", "value": str(round(seeding_time_days, 2)) },
                ]
            )
