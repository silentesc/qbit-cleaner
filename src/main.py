import sys
from datetime import datetime

from loguru import logger

from src.data.constants import env
from src.jobs.delete_forgotten import DeleteForgotten


def main() -> int:
    logger.remove(0)
    logger.add(f"logs/{datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")}.log", level=env.get_log_level())
    logger.add(sys.stderr, level=env.get_log_level())

    delete_forgotten_job = DeleteForgotten()
    delete_forgotten_job.run()

    return 0
