import qbittorrentapi
import typing
from qbittorrentapi import TorrentDictionary, Tracker, TrackersList
from loguru import logger

from src.utils.discord_webhook_utils import DiscordWebhookUtils, EmbedColor
from src.utils.strike_utils import StrikeUtils, StrikeType

from src.data.config import CONFIG


class DeleteNotWorkingTrackers:
    def __init__(self) -> None:
        self.conn_info: dict[str, typing.Any] = dict(
            host=CONFIG["qbittorrent"]["host"],
            port=CONFIG["qbittorrent"]["port"],
            username=CONFIG["qbittorrent"]["username"],
            password=CONFIG["qbittorrent"]["password"],
        )


    def run(self) -> None:
        logger.info("Running 'delete_not_working_trackers' job")

        working_content_paths: set[str] = self.get_working_content_paths()

        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            for torrent in qbt_client.torrents_info():
                torrent: TorrentDictionary
                name: str = torrent.name
                content_path: str = torrent.content_path
                trackers: TrackersList = qbt_client.torrents_trackers(torrent.hash)

                if not self.is_criteria_matching(torrent=torrent, trackers=trackers):
                    continue

                logger.info(f"Found torrent without working trackers that matches criteria: {name}")
                self.take_action(torrent=torrent, content_path=content_path, working_content_paths=working_content_paths)
                self.send_discord_notification(torrent_name=name, trackers=trackers)

            hashes = [torrent.hash for torrent in qbt_client.torrents_info()]
            StrikeUtils(strike_type=StrikeType.DELETE_NOT_WORKING_TRACKERS, torrent_hash="unused").cleanup_db(hashes=hashes)

        logger.info(f"job delete_not_working_trackers finished, next run in {CONFIG["jobs"]["delete_not_working_trackers"]["interval_hours"]} hours")


    def get_working_content_paths(self) -> set[str]:
        content_paths: list[str] = []
        with qbittorrentapi.Client(**self.conn_info) as qbt_client:
            for torrent in qbt_client.torrents_info():
                torrent: TorrentDictionary
                content_path = torrent.content_path
                trackers: TrackersList = qbt_client.torrents_trackers(torrent.hash)

                # 0 = Disabled
                # 1 = Not contacted yet
                # 2 = Working
                # 3 = Updating
                # 4 = Not working
                working: bool = any(tracker["status"] == 2 for tracker in trackers)

                if working:
                    content_paths.append(content_path)
        return set(content_paths)


    def get_tracker_infos(self, name: str, trackers: TrackersList) -> list[str]:
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
            logger.debug(f"Not working tracker ({name}):\n{tracker_info}")
            tracker_infos.append(tracker_info)
        return tracker_infos


    def is_criteria_matching(self, torrent: TorrentDictionary, trackers: TrackersList) -> bool:
        name: str = torrent.name
        hash = torrent.hash
        tags: str = torrent.tags

        # 0 = Disabled
        # 1 = Not contacted yet
        # 2 = Working
        # 3 = Updating
        # 4 = Not working
        working: bool = any(tracker["status"] == 2 for tracker in trackers)

        strike_utils = StrikeUtils(strike_type=StrikeType.DELETE_NOT_WORKING_TRACKERS, torrent_hash=hash)

        # Ignore protected tags
        if CONFIG["qbittorrent"]["protected_tag"] in tags.lower():
            logger.debug(f"Ignoring {name} (has protection a tag)")
            logger.trace(f"Tags of {name}: {tags}")
            logger.trace(f"Protection tag: {CONFIG["qbittorrent"]["protected_tag"]}")
            strike_utils.reset_torrent()
            return False
        # Ignore working trackers
        if working:
            logger.debug(f"Ignoring {name} (trackers are working)")
            strike_utils.reset_torrent()
            return False
        # Ignore not reaching criteria
        is_torrent_limit_reached: bool = strike_utils.strike_torrent()
        if not is_torrent_limit_reached:
            required_strikes = CONFIG["jobs"]["delete_not_working_trackers"]["required_strikes"]
            min_strike_days = CONFIG["jobs"]["delete_not_working_trackers"]["min_strike_days"]
            logger.debug(f"{name} has no working trackers but doesn't reach criteria ({strike_utils.get_strikes()}/{required_strikes} strikes, {strike_utils.get_consecutive_days()}/{min_strike_days} days)")
            return False

        return True


    def take_action(self, torrent: TorrentDictionary, content_path: str, working_content_paths: set[str]) -> None:
        match CONFIG["jobs"]["delete_not_working_trackers"]["action"]:
            case "test":
                logger.info("Action = test | Torrent remains unhandled")
            case "stop":
                logger.info("Action = stop | Stopping torrent")
                torrent.stop()
            case "delete":
                logger.info("Action = delete | Deleting torrent + files")
                # Ignore if another working torrent has the same files
                if content_path in working_content_paths:
                    logger.warning(f"Only deleting torrent and not files for {torrent.name} Some other torrent that uses these files has working trackers")
                    torrent.delete(delete_files=False)
                else:
                    torrent.delete(delete_files=True)
            case _:
                logger.warning("Invalid action for delete_not_working_trackers job")


    def send_discord_notification(self, torrent_name: str, trackers: TrackersList) -> None:
        tracker_infos: list[str] = self.get_tracker_infos(name=torrent_name, trackers=trackers)

        fields: list[dict[str, str | bool]] = [
            { "name": "Action", "value": CONFIG["jobs"]["delete_not_working_trackers"]["action"] },
            { "name": "Torrent", "value": torrent_name },
        ]
        for tracker_info in tracker_infos:
            tracker_info: str
            fields.append(
                { "name": "Tracker", "value": tracker_info },
            )

        DiscordWebhookUtils().send_webhook_embed(
            embed_color=EmbedColor.GREEN,
            title="Found tracker not working",
            fields=fields,
        )
