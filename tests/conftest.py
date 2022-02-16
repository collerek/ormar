import logging

from ormar import logger

disable_loggers = ["aiosqlite", "asyncio", "databases"]
logger.setLevel(logging.DEBUG)
high_format = "\n%(asctime)s:%(name)s:%(lineno)d %(levelname)s %(message)s"
logger.removeHandler(logger.handlers[0])
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(high_format)
handler.setFormatter(formatter)
logger.addHandler(handler)


def pytest_configure():
    for logger_name in disable_loggers:
        logger = logging.getLogger(logger_name)
        logger.disabled = True
