"""GARUDA Launcher - Core constants and configuration."""

import sys
from pathlib import Path


class PathConfig:
    """All project paths."""

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    BACKEND_DIR = PROJECT_ROOT / "backend"
    FRONTEND_DIR = PROJECT_ROOT / "frontend"
    STORAGE_DIR = PROJECT_ROOT / "storage"
    CONFIG_DIR = PROJECT_ROOT / "config"
    LOG_DIR = PROJECT_ROOT / "storage" / "logs"
    CACHE_DIR = PROJECT_ROOT / "storage" / "cache"
    TEMP_DIR = PROJECT_ROOT / "storage" / "temp"
    EXPORT_DIR = PROJECT_ROOT / "storage" / "exports"
    PROJECTS_DIR = PROJECT_ROOT / "storage" / "projects"
    MODELS_DIR = PROJECT_ROOT / "storage" / "models"
    ENV_FILE = PROJECT_ROOT / ".env"
    ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
    DB_PATH = PROJECT_ROOT / "storage" / "garuda.db"
    BACKEND_PYTHON = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
    LAUNCHER_DIR = PROJECT_ROOT / "launcher"
    LAUNCHER_LOG = PROJECT_ROOT / "storage" / "logs" / "launcher.log"
    STARTUP_LOG = PROJECT_ROOT / "storage" / "logs" / "startup.log"
    SHUTDOWN_LOG = PROJECT_ROOT / "storage" / "logs" / "shutdown.log"


class ServerConfig:
    """Server configuration."""

    BACKEND_HOST = "127.0.0.1"
    BACKEND_PORT = 8000
    FRONTEND_PORT = 5173
    HEALTH_ENDPOINT = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/v1/health"
    HEALTH_TIMEOUT = 30
    HEALTH_INTERVAL = 0.5
    FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"


class PythonConfig:
    """Python requirements."""

    MIN_VERSION = (3, 12)
    REQUIRED_PACKAGES = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "loguru",
        "pydantic",
        "pydantic_settings",
        "geopandas",
        "shapely",
        "pyproj",
    ]


class StorageConfig:
    """Storage subdirectories."""

    SUBDIRS = ["cache", "exports", "logs", "models", "projects", "temp"]


class AppInfo:
    """Application metadata."""

    NAME = "GARUDA"
    VERSION = "1.0.0"
    BUILD = "2026.07.06"
    DESCRIPTION = "AI-powered Geospatial Intelligence and Monitoring Platform"
