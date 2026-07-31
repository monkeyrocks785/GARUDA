"""GARUDA Launcher - Logging utilities."""

import logging
import sys
from datetime import datetime
from pathlib import Path

from launcher.config import PathConfig


def setup_launcher_logging() -> logging.Logger:
    """Configure launcher-specific logging."""
    logger = logging.getLogger("garuda.launcher")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.WARNING)
    console.setFormatter(fmt)
    logger.addHandler(console)

    PathConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(
        PathConfig.LAUNCHER_LOG, encoding="utf-8", mode="a"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


def log_startup(message: str) -> None:
    """Log to startup.log."""
    log_file = PathConfig.STARTUP_LOG
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")


def log_shutdown(message: str) -> None:
    """Log to shutdown.log."""
    log_file = PathConfig.SHUTDOWN_LOG
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")


launcher_logger = setup_launcher_logging()
