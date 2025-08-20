import qbittorrentapi
import typing
from datetime import datetime
from qbittorrentapi import TorrentDictionary
from loguru import logger

from src.utils.file_utils import FileUtils
from src.utils.datetime_utils import DateTimeUtils
from src.utils.discord_webhook_utils import DiscordWebhookUtils, DiscordWebhookType

from src.data.env import ENV
from src.data.config import CONFIG


class DeleteForgotten:
    def __init__(self) -> None:
        self.conn_info: dict[str, typing.Any] = dict(
            host=CONFIG["qbittorrent"]["host"],
            port=CONFIG["qbittorrent"]["port"],
            username=CONFIG["qbittorrent"]["username"],
            password=CONFIG["qbittorrent"]["password"],
        )


    def run(self) -> None:
        logger.info("Running 'delete_forgotten' job")

        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            file_utils = FileUtils(
                data_path="/data",
                torrents_path=ENV.get_torrents_path(),
                media_path=ENV.get_media_path(),
            )

            for torrent in qbt_client.torrents_info():
                torrent: TorrentDictionary
                name: str = torrent.name
                tags: str = torrent.tags
                seeding_time_days: int = torrent.seeding_time / 60 / 60 / 24
                content_path: str = torrent.content_path
                completed_on_raw: int = torrent.completion_on

                # Ignore protected tags
                if CONFIG["qbittorrent"]["protected_tag"] in tags.lower():
                    logger.debug(f"Ignoring {name} (has protection a tag)")
                    logger.trace(f"Tags of {name}: {tags}")
                    logger.trace(f"Protection tag: {CONFIG["qbittorrent"]["protected_tag"]}")
                    continue
                # Ignore uncompleted torrents
                if completed_on_raw == -1:
                    logger.debug(f"Ignoring {name} (not completed)")
                    continue
                # Ignore torrents seeding less than x days
                if seeding_time_days < CONFIG["jobs"]["delete_forgotten"]["min_seeding_days"]:
                    logger.debug(f"Ignoring {name} (seeding less than {CONFIG["jobs"]["delete_forgotten"]["min_seeding_days"]} days)")
                    logger.trace(f"Seeding days: {seeding_time_days}")
                    continue
                # Ignore torrents that have a connection to the media library
                if file_utils.is_content_in_media_library(content_path=content_path):
                    logger.debug(f"Ignoring {name} (has content in media library)")
                    continue

                logger.info(f"Found torrent that qualifies forgotten: {name}")

                match CONFIG["jobs"]["delete_forgotten"]["action"]:
                    case "test":
                        logger.info("Action = test | Torrent remains unhandled")
                    case "stop":
                        logger.info("Action = stop | Stopping torrent")
                        torrent.stop()
                    case "delete":
                        logger.info("Action = delete | Deleting torrent + files")
                        torrent.delete(delete_files=True)
                    case _:
                        logger.warning("Invalid action for delete_forgotten job")

                self.send_discord_notification(embed_title="Found forgotten torrent", torrent=torrent)

        logger.info(f"job delete_forgotten finished, next run in {CONFIG["jobs"]["delete_forgotten"]["interval_hours"]} hours")


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
                webhook_type=DiscordWebhookType.INFO,
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
