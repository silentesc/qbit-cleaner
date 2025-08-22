import sys
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from src.jobs.delete_forgotten import DeleteForgotten
from src.jobs.delete_not_working_trackers import DeleteNotWorkingTrackers
from src.utils.datetime_utils import DateTimeUtils
from src.utils.db_scripts import DbScripts

from src.data.config import CONFIG


def main() -> int:
    # Logging setup
    readable_datetime_now: str = DateTimeUtils().get_datetime_readable(datetime.now())
    custom_log_level: str = CONFIG["logging"]["log_level"]
    logger.remove(0)
    logger.add(f"/config/logs/{readable_datetime_now}/info.log", level="INFO")
    logger.add(f"/config/logs/{readable_datetime_now}/debug.log", level="DEBUG")
    if custom_log_level != "INFO" and custom_log_level != "DEBUG":
        logger.add(f"/config/logs/{readable_datetime_now}/custom.log", level=custom_log_level)
    logger.add(sys.stderr, level=custom_log_level)

    # Db setup
    DbScripts().create_tables()

    match CONFIG["testing"]["job"]:
        case "delete_forgotten":
            logger.info("Testing delete_forgotten")
            DeleteForgotten().run()
            logger.info("Testing delete_forgotten finished, sleeping now")
            while True:
                time.sleep(1)
        case "delete_not_working_trackers":
            logger.info("Testing delete_not_working_trackers")
            DeleteNotWorkingTrackers().run()
            logger.info("Testing delete_not_working_trackers finished, sleeping now")
            while True:
                time.sleep(1)

    # Job setup
    scheduler = BlockingScheduler()
    if CONFIG["jobs"]["delete_forgotten"]["interval_hours"] != 0:
        scheduler.add_job(DeleteForgotten().run, "interval", hours=CONFIG["jobs"]["delete_forgotten"]["interval_hours"])
        logger.info(f"job delete_forgotten has been added, next run in {CONFIG["jobs"]["delete_forgotten"]["interval_hours"]} hours")
    if CONFIG["jobs"]["delete_not_working_trackers"]["interval_hours"] != 0:
        scheduler.add_job(DeleteNotWorkingTrackers().run, "interval", hours=CONFIG["jobs"]["delete_not_working_trackers"]["interval_hours"])
        logger.info(f"job delete_not_working_trackers has been added, next run in {CONFIG["jobs"]["delete_not_working_trackers"]["interval_hours"]} hours")

    try:
        logger.info("Startup complete, starting scheduler")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting, shutting down scheduler")
        scheduler.shutdown(wait=True)

    # Exit with code 0
    return 0
