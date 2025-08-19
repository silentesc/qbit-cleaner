import sys
from datetime import datetime
from loguru import logger

from src.jobs.delete_forgotten import DeleteForgotten
from src.jobs.delete_not_working_trackers import DeleteNotWorkingTrackers
from src.utils.datetime_utils import DateTimeUtils
from src.utils.db_scripts import DbScripts

from src.data.config import CONFIG


def main() -> int:
    logger.remove(0)
    logger.add(f"logs/{DateTimeUtils().get_datetime_readable(datetime.now())}.log", level=CONFIG["logging"]["log_level"])
    logger.add(sys.stderr, level=CONFIG["logging"]["log_level"])

    DbScripts().create_tables()

    # DeleteForgotten().run()
    DeleteNotWorkingTrackers().run()

    return 0
