from datetime import datetime
from datetime import timedelta
from loguru import logger

from src.utils.db_manager import DbManager
from src.data.constants import env


class StrikeUtils:
    def strike_torrent(self, torrent_hash: str) -> bool:
        """
        Strikes a torrent while keeping the MIN_NOT_WORKING_DAYS and REQUIRED_STRIKES in mind

        Args:
            torrent_hash (str): The unique hash of the torrent

        Returns:
            bool: True if limit has been reached, false otherwise
        """
        with DbManager() as db:
            row = db.execute_fetchone(query="SELECT * FROM strikes WHERE hash = ?", params=(torrent_hash,))
            if not row:
                logger.trace(f"Torrent with hash {torrent_hash} is not in db and will be created")
                db.execute(query="INSERT INTO strikes (hash, strikes, first_strike) VALUES (?, 1, ?)", params=(torrent_hash, datetime.now()))
                return False
            else:
                strikes = row["strikes"] + 1
                strike_days: timedelta = datetime.now() - datetime.strptime(row["first_strike"], "%Y-%m-%d %H:%M:%S.%f")
                if strikes >= env.get_required_strikes() and strike_days >= timedelta(days=env.get_min_not_working_days()):
                    logger.trace(f"Torrent with hash {torrent_hash} has reached {strikes} strikes in {strike_days} days - entry is being deleted")
                    db.execute(query="DELETE FROM strikes WHERE hash = ?", params=(torrent_hash,))
                    return True
                logger.trace(f"Torrent with hash {torrent_hash} doesn't meet criteria and will have strikes increased (strikes ({strikes}/{env.get_required_strikes()}) days ({strike_days}/{env.get_min_not_working_days()}))")
                db.execute(query="UPDATE strikes SET strikes = strikes + 1 WHERE hash = ?", params=(torrent_hash,))
        return False


    def reset_torrent(self, torrent_hash: str) -> None:
        with DbManager() as db:
            row = db.execute_fetchone(query="SELECT * FROM strikes WHERE hash = ?", params=(torrent_hash,))
            if not row:
                return
            logger.trace(f"Torrent with hash {torrent_hash} is being deleted due to manual reset")
            db.execute(query="DELETE FROM strikes WHERE hash = ?", params=(torrent_hash,))
