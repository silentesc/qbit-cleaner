from qbittorrentapi import TorrentDictionary
from datetime import datetime

from src.utils.datetime_utils import DateTimeUtils
from src.utils.discord_webhook_utils import DiscordWebhookUtils, DiscordWebhookType


class TorrentNotificationUtils:
    def send_delete_notification(self, embed_title: str, torrent: TorrentDictionary) -> None:
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
                { "name": "Name", "value": name },
                { "name": "Tracker", "value": tracker },

                { "name": "Category", "value": category, "inline": True },
                { "name": "Tags", "value": tags, "inline": True },
                { "name": "\u200b", "value": "\u200b", "inline": True },

                { "name": "Total Size", "value": f"{str(round(total_size_gib, 2))}GiB | {str(round(total_size_gb, 2))}GB", "inline": True },
                { "name": "Ratio", "value": str(round(ratio, 2)), "inline": True },
                { "name": "\u200b", "value": "\u200b", "inline": True },

                { "name": "Added", "value": DateTimeUtils().get_datetime_readable(added_on), "inline": True },
                { "name": "Completed", "value": DateTimeUtils().get_datetime_readable(completed_on), "inline": True },
                { "name": "Seeding Days", "value": str(round(seeding_time_days, 2)), "inline": True },
            ]
        )
