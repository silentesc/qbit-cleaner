import qbittorrentapi
import typing
from qbittorrentapi import TorrentDictionary
from datetime import datetime
from loguru import logger

from src.utils.file_utils import FileUtils
from src.utils.datetime_utils import DateTimeUtils
from src.utils.discord_webhook_utils import DiscordWebhookUtils, DiscordWebhookType

from src.data.constants import env


class DeleteForgotten:
    def __init__(self) -> None:
        self.conn_info: dict[str, typing.Any] = dict(
            host=env.get_qbittorrent_host(),
            port=env.get_qbittorrent_port(),
            username=env.get_qbittorrent_username(),
            password=env.get_qbittorrent_password(),
        )


    def run(self) -> None:
        logger.info("Running 'delete_forgotten' job")

        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            file_utils = FileUtils(
                data_path=env.get_data_path(),
                torrents_path=env.get_torrents_path(),
                media_path=env.get_media_path(),
            )

            for torrent in qbt_client.torrents_info():
                torrent: TorrentDictionary
                name: str = torrent.name
                tags: str = torrent.tags
                seeding_time_days: int = torrent.seeding_time / 60 / 60 / 24
                content_path: str = env.get_qbittorrent_pre_path() + torrent.content_path
                completed_on_raw: int = torrent.completion_on

                # Ignore protected tags
                if env.get_qbittorrent_protected_tag() in tags.lower():
                    logger.debug(f"Ignoring {name} (has protection a tag)")
                    logger.trace(f"Tags of {name}: {tags}")
                    logger.trace(f"Protection tag: {env.get_qbittorrent_protected_tag()}")
                    continue
                # Ignore uncompleted torrents
                if completed_on_raw == -1:
                    logger.debug(f"Ignoring {name} (not completed)")
                    continue
                # Ignore torrents seeding less than x days
                if seeding_time_days < env.get_min_seeding_days():
                    logger.debug(f"Ignoring {name} (seeding less than {env.get_min_seeding_days()} days)")
                    logger.trace(f"Seeding days: {seeding_time_days}")
                    continue
                # Ignore torrents that have a connection to the media library
                if file_utils.is_content_in_media_library(content_path=content_path):
                    logger.debug(f"Ignoring {name} (has content in media library)")
                    continue

                logger.info(f"Found torrent that qualifies forgotten: {name}")
                # torrent.stop()
                # torrent.delete(delete_files=True)
                # self.send_delete_notification(torrent=torrent)


    def send_delete_notification(self, torrent: TorrentDictionary) -> None:
        name: str = torrent.name
        tracker: str = torrent.tracker
        ratio: float = torrent.ratio
        total_size_gb: int = torrent.total_size / 1000 / 1000
        seeding_time_days: int = torrent.seeding_time / 60 / 60 / 24
        completed_on_raw: int = torrent.completion_on
        completed_on: datetime = datetime.fromtimestamp(completed_on_raw)
        added_on_raw: int = torrent.added_on
        added_on: datetime = datetime.fromtimestamp(added_on_raw)

        DiscordWebhookUtils().send_webhook_embed(
            webhook_type=DiscordWebhookType.INFO,
            title="Job delete_forgotten",
            description="Deleted forgotten torrent",
            fields=[
                { "name": "Name", "value": name },
                { "name": "Tracker", "value": tracker },
                { "name": "Ratio", "value": ratio },
                { "name": "Size (GB)", "value": total_size_gb },
                { "name": "Added", "value": DateTimeUtils().get_datetime_readable(added_on) },
                { "name": "Completed", "value": DateTimeUtils().get_datetime_readable(completed_on) },
                { "name": "Seeding Days", "value": seeding_time_days },
            ]
        )
