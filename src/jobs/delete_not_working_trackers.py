import qbittorrentapi
import typing
from qbittorrentapi import TorrentDictionary, Tracker, TrackersList
from loguru import logger

from src.utils.discord_webhook_utils import DiscordWebhookUtils, DiscordWebhookType

from src.data.constants import env


class DeleteNotWorkingTrackers:
    def __init__(self) -> None:
        self.conn_info: dict[str, typing.Any] = dict(
            host=env.get_qbittorrent_host(),
            port=env.get_qbittorrent_port(),
            username=env.get_qbittorrent_username(),
            password=env.get_qbittorrent_password(),
        )


    def run(self) -> None:
        logger.info("Running 'delete_not_working_trackers' job")

        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            for torrent in qbt_client.torrents_info():
                torrent: TorrentDictionary
                name: str = torrent.name
                tags: str = torrent.tags
                trackers: TrackersList = qbt_client.torrents_trackers(torrent.hash)

                # 0 = Disabled
                # 1 = Not contacted yet
                # 2 = Working
                # 3 = Updating
                # 4 = Not working
                working: bool = any(tracker["status"] == 2 for tracker in trackers)
                
                # Ignore protected tags
                if env.get_qbittorrent_protected_tag() in tags.lower():
                    logger.debug(f"Ignoring {name} (has protection a tag)")
                    logger.trace(f"Tags of {name}: {tags}")
                    logger.trace(f"Protection tag: {env.get_qbittorrent_protected_tag()}")
                    continue
                if working:
                    logger.debug(f"Ignoring {name} trackers are working")
                    continue

                logger.info(f"Found torrent without working trackers: {name}")

                tracker_infos: list[str] = []
                for tracker in trackers:
                    tracker: Tracker
                    tracker_url = str(tracker["url"])
                    tracker_msg = str(tracker["msg"])
                    tracker_status = str(tracker["status"]) if not str(tracker["status"]).isdigit() else int(str(tracker["status"]))
                    match tracker_status:
                        case 0: tracker_status = "Disabled"
                        case 1: tracker_status = "Not contacted yet"
                        case 3: tracker_status = "Updating"
                        case 4: tracker_status = "Not working"
                        case _: tracker_status = str(tracker_status)
                    if "dht" in tracker_url.lower() or "pex" in tracker_url.lower() or "lsd" in tracker_url.lower():
                        continue
                    tracker_info: str = ""
                    tracker_info += f"URL: {tracker_url}\n"
                    tracker_info += f"Status: {tracker_status}\n"
                    tracker_info += f"Message: {tracker_msg}\n"
                    tracker_infos.append(tracker_info)

                # TODO Handle torrent
                # torrent.stop()

                fields: list[dict[str, str | bool]] = [
                    { "name": "Torrent", "value": name },
                ]
                for tracker_info in tracker_infos:
                    tracker_info: str
                    fields.append(
                        { "name": "Tracker", "value": tracker_info },
                    )

                DiscordWebhookUtils().send_webhook_embed(
                    webhook_type=DiscordWebhookType.ERROR,
                    title="Trackers not working",
                    fields=fields,
                )
