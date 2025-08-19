from datetime import datetime
from datetime import timedelta
from enum import Enum
from loguru import logger

from src.utils.db_manager import DbManager
from src.data.config import CONFIG


class StrikeType(Enum):
    DELETE_NOT_WORKING_TRACKERS = "delete_not_working_trackers"


class StrikeUtils:
    def strike_torrent(self, strike_type: StrikeType, torrent_hash: str) -> bool:
        """
        Strikes a torrent while keeping the MIN_NOT_WORKING_DAYS and REQUIRED_STRIKES in mind

        Args:
            torrent_hash (str): The unique hash of the torrent

        Returns:
            bool: True if limit has been reached, false otherwise
        """
        # If max. 1 required strike and min not working days, criteria is always reached
        if CONFIG["jobs"][strike_type.value]["required_strikes"] <= 1 and CONFIG["jobs"][strike_type.value]["min_not_working_days"] <= 0:
            return True

        with DbManager() as db:
            row = db.execute_fetchone(query=f"SELECT * FROM {strike_type.value}_strikes WHERE hash = ?", params=(torrent_hash,))
            # If not existing record, create one
            if not row:
                logger.trace(f"Torrent with hash {torrent_hash} is not in db and will be created")
                db.execute(query=f"INSERT INTO {strike_type.value}_strikes (hash, strikes, first_strike) VALUES (?, 1, ?)", params=(torrent_hash, datetime.now()))
                return False
            # If existing record, check strikes and days not working
            else:
                strikes = row["strikes"] + 1
                strike_days: timedelta = datetime.now() - datetime.strptime(row["first_strike"], "%Y-%m-%d %H:%M:%S.%f")
                # If required strikes and min not working days are reached, delete torrent and return true
                if strikes >= CONFIG["jobs"][strike_type.value]["required_strikes"] and strike_days >= timedelta(days=CONFIG["jobs"][strike_type.value]["min_not_working_days"]):
                    logger.trace(f"Torrent with hash {torrent_hash} has reached {strikes} strikes in {strike_days} days - entry is being deleted")
                    db.execute(query=f"DELETE FROM {strike_type.value}_strikes WHERE hash = ?", params=(torrent_hash,))
                    return True
                # Else, increment strikes
                logger.trace(f"Torrent with hash {torrent_hash} doesn't meet criteria and will have strikes increased (strikes ({strikes}/{CONFIG["jobs"][strike_type.value]["required_strikes"]}) days ({strike_days}/{CONFIG["jobs"][strike_type.value]["min_not_working_days"]}))")
                db.execute(query=f"UPDATE {strike_type.value}_strikes SET strikes = strikes + 1 WHERE hash = ?", params=(torrent_hash,))
        return False


    def reset_torrent(self, strike_type: StrikeType, torrent_hash: str) -> None:
        with DbManager() as db:
            row = db.execute_fetchone(query=f"SELECT * FROM {strike_type.value}_strikes WHERE hash = ?", params=(torrent_hash,))
            if not row:
                return
            logger.trace(f"Torrent with hash {torrent_hash} is being deleted due to manual reset")
            db.execute(query=f"DELETE FROM {strike_type.value}_strikes WHERE hash = ?", params=(torrent_hash,))
