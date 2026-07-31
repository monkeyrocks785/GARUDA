"""GARUDA - AI-powered Geospatial Intelligence and Monitoring Platform.

Main application entry point.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.v1.router import api_router
from config.settings import settings
from core.logging import setup_logging
from database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    setup_logging(log_level=settings.LOG_LEVEL, log_dir=settings.LOG_DIR)

    for dir_path in [
        settings.STORAGE_DIR,
        settings.CACHE_DIR,
        settings.TEMP_DIR,
        settings.EXPORT_DIR,
        settings.PROJECTS_DIR,
        settings.MODELS_DIR,
        settings.LOG_DIR,
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    init_db()
    logger.info("Database initialized")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered Geospatial Intelligence and Monitoring Platform",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Health", "description": "System health check endpoints"},
            {"name": "Projects", "description": "Project management endpoints"},
            {"name": "AOI", "description": "Area of Interest endpoints"},
            {"name": "Layers", "description": "Map layer endpoints"},
            {"name": "Import/Export", "description": "File import/export endpoints"},
            {"name": "Map State", "description": "Map state persistence endpoints"},
            {"name": "Knowledge Engine", "description": "Entity and knowledge graph management"},
            {"name": "Intelligence Query Engine", "description": "Structured querying of the knowledge base"},
            {"name": "Growth Analytics Engine", "description": "Growth metrics, forecasting, and trend analysis"},
            {"name": "Rules & Alert Engine", "description": "Intelligence rules, conditions, actions, and alerts"},
            {"name": "API", "description": "API v1 endpoints"},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_application()
