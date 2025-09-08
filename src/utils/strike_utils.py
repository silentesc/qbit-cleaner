from datetime import date, datetime, timedelta
from enum import Enum
from loguru import logger

from src.utils.db_manager import DbManager
from src.data.config import CONFIG


class StrikeType(Enum):
    DELETE_NOT_WORKING_TRACKERS = "delete_not_working_trackers"
    DELETE_FORGOTTEN = "delete_forgotten"
    DELETE_ORPHANED = "delete_orphaned"


class StrikeUtils:
    def __init__(self, strike_type: StrikeType, torrent_hash: str) -> None:
        self.strike_type = strike_type
        self.torrent_hash = torrent_hash


    def strike_torrent(self) -> bool:
        """
        Strikes a torrent while keeping the min days and required strikes in mind

        Returns:
            bool: True if limit has been reached, false otherwise
        """
        logger.trace(f"Striking torrent with hash {self.torrent_hash}")

        # Insert to strike
        with DbManager() as db:
            db.execute(query=f"INSERT INTO {self.strike_type.value}_strikes (hash, timestamp) VALUES (?, ?)", params=(self.torrent_hash, datetime.now()))

        strikes: int = self.get_strikes()
        consecutively_days: int = self.get_consecutive_days()

        # If required strikes and min not working days are reached, delete torrent and return true
        if strikes >= CONFIG["jobs"][self.strike_type.value]["required_strikes"] and consecutively_days >= CONFIG["jobs"][self.strike_type.value]["min_strike_days"]:
            logger.trace(f"Torrent with hash {self.torrent_hash} has reached {strikes} strikes in {consecutively_days} days - entry is being deleted")
            self.reset_torrent()
            return True

        logger.trace(f"Torrent with hash {self.torrent_hash} has not reached it's limit ({strikes} strikes, {consecutively_days} days)")
        return False


    def reset_torrent(self) -> None:
        with DbManager() as db:
            row = db.execute_fetchone(query=f"SELECT * FROM {self.strike_type.value}_strikes WHERE hash = ?", params=(self.torrent_hash,))
            if not row:
                return
            logger.trace(f"Torrent with hash {self.torrent_hash} is being deleted")
            db.execute(query=f"DELETE FROM {self.strike_type.value}_strikes WHERE hash = ?", params=(self.torrent_hash,))


    def cleanup_db(self, hashes: list[str]) -> None:
        with DbManager() as db:
            rows = db.execute_fetchall(query=f"SELECT hash FROM {self.strike_type.value}_strikes GROUP BY hash")

        for row in rows:
            torrent_hash = row["hash"]
            logger.trace(f"not torrent_hash in hashes | not {torrent_hash} in hashes | {not torrent_hash in hashes}")
            if not torrent_hash in hashes:
                StrikeUtils(strike_type=self.strike_type, torrent_hash=torrent_hash).reset_torrent()
                logger.debug(f"Deleted torrent with hash {torrent_hash} from db because it's not in qbittorrent anymore")


    # Utils


    def get_strikes(self) -> int:
        with DbManager() as db:
            row = db.execute_fetchone(query=f"SELECT COUNT(*) as strikes FROM {self.strike_type.value}_strikes WHERE hash = ?", params=(self.torrent_hash,))

        if not row:
            return 0
        
        return row["strikes"]


    def get_consecutive_days(self) -> int:
        with DbManager() as db:
            rows = db.execute_fetchall(query=f"SELECT * FROM {self.strike_type.value}_strikes WHERE hash = ? ORDER BY timestamp DESC", params=(self.torrent_hash,))

        if not rows:
            return 0

        consecutively_days = 0
        last_date: date | None = None
        for row in rows:
            row_date = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S.%f").date()
            if last_date is None:
                last_date = row_date
                consecutively_days += 1
                logger.trace("row_date is none")
                continue
            elif row_date == last_date:
                logger.trace(f"row_date == last_date | {row_date} == {last_date} | {row_date == last_date}")
                continue
            else: # row_date is not None and row_date != last_date
                if row_date == last_date - timedelta(days=1):
                    logger.trace(f"row_date == last_date - timedelta(days=1) | {row_date} == {last_date - timedelta(days=1)} | {row_date == last_date - timedelta(days=1)}")
                    last_date = row_date
                    consecutively_days += 1
                else:
                    logger.trace(f"row_date == last_date - timedelta(days=1) | {row_date} == {last_date - timedelta(days=1)} | {row_date == last_date - timedelta(days=1)}")
                    break

            logger.trace(f"consecutively_days: {consecutively_days}")
            logger.trace(f"last_date {last_date}")

        return consecutively_days
