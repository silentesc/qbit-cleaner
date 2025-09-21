import sys
import os
from loguru import logger


if __name__ == "__main__":
    log_level = os.getenv("LOG_LEVEL") or "INFO"
    if log_level == "TRACE":
        log_format = "[{time:YYYY-MM-DD HH:mm:ss}] [<level>{level}</level>] [{file}:{function}:{line}]: {message}"
    else:
        log_format = "[{time:YYYY-MM-DD HH:mm:ss}] [<level>{level}</level>]: {message}"

    logger.remove(0)
    logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        colorize=True,
        backtrace=True,
        diagnose=False
    )

    from src import main
    sys.exit(main.main())
