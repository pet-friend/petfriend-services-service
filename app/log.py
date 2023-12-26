import logging
from .config import settings

FORMAT = "{asctime} | {levelname} | {funcName} | {message}"


def setup_logs() -> None:
    if settings.DEBUG:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format=FORMAT, style="{")
