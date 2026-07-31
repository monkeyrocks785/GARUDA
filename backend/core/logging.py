import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_level: str = "DEBUG", log_dir: str | None = None) -> None:
    """Configure centralized logging with Loguru.

    Args:
        log_level: Minimum log level for console output.
        log_dir: Directory for log file output.
    """
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_path / "backend.log"),
            format=log_format,
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            compression="gz",
            enqueue=True,
        )

        logger.add(
            str(log_path / "errors.log"),
            format=log_format,
            level="ERROR",
            rotation="10 MB",
            retention="90 days",
            compression="gz",
            enqueue=True,
        )

        logger.add(
            str(log_path / "worker.log"),
            format=log_format,
            level="INFO",
            rotation="10 MB",
            retention="14 days",
            compression="gz",
            enqueue=True,
            filter=lambda record: "worker" in record["extra"].get("module", ""),
        )

    logger.info("Logging system initialized")
