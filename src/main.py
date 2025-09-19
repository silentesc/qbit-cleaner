import signal
import time
from typing import Optional, Callable
from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from src.jobs.delete_orphaned import DeleteOrphaned
from src.jobs.delete_forgotten import DeleteForgotten
from src.jobs.delete_not_working_trackers import DeleteNotWorkingTrackers
from src.utils.db_scripts import DbScripts

from src.data.config import CONFIG


def main() -> int:
    def shutdown(signum, frame):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=True)
        try:
            QBIT_CONNECTION.get_client().auth_log_out()
        except ConnectionError:
            pass
        return 0

    # Db setup
    DbScripts().create_tables()

    # Login to qbittorrent
    from src.utils.qbit_connection import QBIT_CONNECTION
    try:
        QBIT_CONNECTION.get_client()
    except ConnectionError:
        logger.critical("Couldn't establish connection with qbittorrent, exiting")
        return 1

    # Jobs
    jobs: dict[str, Callable[[], None]] = {
        "delete_orphaned": DeleteOrphaned().run,
        "delete_forgotten": DeleteForgotten().run,
        "delete_not_working_trackers": DeleteNotWorkingTrackers().run,
    }

    # Testing
    testing_job: str | None = CONFIG["testing"]["job"]
    if testing_job:
        job_method: Optional[Callable[[], None]] = jobs.get(testing_job)
        if not job_method:
            logger.critical(f"Job {CONFIG["testing"]["job"]} does not exist.")
            return 1
        logger.info(f"Testing {testing_job}")
        job_method()
        logger.info(f"Testing {testing_job} finished, sleeping now")
        while True:
            time.sleep(1)

    # Job setup
    scheduler = BlockingScheduler()
    for job_name, job_method in jobs.items():
        if CONFIG["jobs"][job_name]["interval_hours"] != 0:
            scheduler.add_job(job_method, "interval", hours=CONFIG["jobs"][job_name]["interval_hours"])
            logger.info(f"job {job_name} has been added, next run in {CONFIG["jobs"][job_name]["interval_hours"]} hours")

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        logger.info("Startup complete, starting scheduler")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Exiting, shutting down scheduler")
        scheduler.shutdown(wait=True)

    # Exit with code 0
    return 0
