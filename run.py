import sys
import os
from loguru import logger


if __name__ == "__main__":
    logger.remove(0)
    logger.add(
        sys.stdout,
        level=os.getenv("log_level") or "INFO",
        format=("[{time:YYYY-MM-DD HH:mm:ss}] [<level>{level}</level>]: {message}"),
        colorize=True,
        backtrace=True,
        diagnose=False
    )

    from src import main
    sys.exit(main.main())
