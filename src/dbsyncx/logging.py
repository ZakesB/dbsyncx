import logging
import sys


def get_logger():
    logger = logging.getLogger("dbsyncx")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        "%H:%M:%S",
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


logger = get_logger()