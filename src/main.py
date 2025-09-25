import signal
import time
from typing import Optional, Callable
from loguru import logger

from src.jobs.delete_orphaned import DeleteOrphaned
from src.jobs.delete_forgotten import DeleteForgotten
from src.jobs.delete_not_working_trackers import DeleteNotWorkingTrackers
from src.utils.db_scripts import DbScripts
from src.utils.job_manager import JobManager

from src.data.config import CONFIG


def main() -> int:
    def shutdown(signum, frame):
        logger.info("Shutting down scheduler...")
        job_manager.running = False
        logger.info("Logging out of Qbittorrent")
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

    # Define shutdown on signal
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # Job setup
    job_manager = JobManager()
    for job_name, job_method in jobs.items():
        interval_hours = int(CONFIG["jobs"][job_name]["interval_hours"])
        if interval_hours != 0:
            job_manager.add_job(job_method=job_method, interval_hours=interval_hours)
            logger.info(f"job {job_name} has been added, next run in {interval_hours} hours")

    try:
        logger.info("Startup complete, starting scheduler")
        job_manager.start_blocking_scheduler()
    except (KeyboardInterrupt, SystemExit):
        shutdown(signal.SIGINT, None)

    # Exit with code 0
    return 0
