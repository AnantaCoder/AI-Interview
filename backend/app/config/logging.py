import logging
import sys
from typing import Optional

from app.config.settings import get_settings


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    settings = get_settings()
    level = log_level or settings.log_level
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("ai_interview")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.addHandler(handler)
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"ai_interview.{name}")
