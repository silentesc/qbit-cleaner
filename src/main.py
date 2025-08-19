import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from src.jobs.delete_forgotten import DeleteForgotten
from src.jobs.delete_not_working_trackers import DeleteNotWorkingTrackers
from src.utils.datetime_utils import DateTimeUtils
from src.utils.db_scripts import DbScripts

from src.data.config import CONFIG
from src.data.env import ENV


def main() -> int:
    # Logging setup
    logger.remove(0)
    logger.add(f"{ENV.get_config_path()}/logs/{DateTimeUtils().get_datetime_readable(datetime.now())}.log", level=CONFIG["logging"]["log_level"])
    logger.add(sys.stderr, level=CONFIG["logging"]["log_level"])

    # Db setup
    DbScripts().create_tables()

    match CONFIG["testing"]["job"]:
        case "delete_forgotten":
            logger.info("Testing delete_forgotten")
            DeleteForgotten().run()
            return 0
        case "delete_not_working_trackers":
            logger.info("Testing delete_not_working_trackers")
            DeleteNotWorkingTrackers().run()
            return 0

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
