"""
结构化日志系统
"""
import logging
import sys
from typing import Optional

from backend.config import settings


def setup_logger(name: str = "fit_saas", level: Optional[int] = None) -> logging.Logger:
    """配置并获取日志器"""
    logger = logging.getLogger(name)

    if level is not None:
        logger.setLevel(level)
    elif settings.DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()
