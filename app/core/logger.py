"""日志: stdout + 滚动文件,access 单独一份审计"""
import logging
import sys
from logging.handlers import RotatingFileHandler

from .config import settings


def setup_logging() -> None:
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)
    root.handlers.clear()

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    app_handler = RotatingFileHandler(
        filename=settings.LOG_DIR / settings.LOG_FILE_NAME,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    app_handler.setFormatter(fmt)
    root.addHandler(app_handler)

    # access_logger = logging.getLogger("auth.access")
    # access_logger.setLevel(logging.INFO)
    # access_handler = RotatingFileHandler(
    #     filename=settings.LOG_DIR / "access.log",
    #     maxBytes=settings.LOG_MAX_BYTES,
    #     backupCount=settings.LOG_BACKUP_COUNT,
    #     encoding="utf-8",
    # )
    # access_handler.setFormatter(fmt)
    # access_logger.propagate = False
    # access_logger.addHandler(access_handler)
    # access_logger.addHandler(sh)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return None