import sys
from datetime import datetime
from loguru import logger

from src.jobs.delete_forgotten import DeleteForgotten
from src.jobs.delete_not_working_trackers import DeleteNotWorkingTrackers
from src.utils.datetime_utils import DateTimeUtils
from src.utils.db_manager import DbManager

from src.data.constants import env


def main() -> int:
    logger.remove(0)
    logger.add(f"logs/{DateTimeUtils().get_datetime_readable(datetime.now())}.log", level=env.get_log_level())
    logger.add(sys.stderr, level=env.get_log_level())

    DbManager.create_tables()

    # DeleteForgotten().run()
    # DeleteNotWorkingTrackers().run()

    return 0
