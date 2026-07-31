"""Database models for the Intelligence Query Engine.

Stores saved queries, query history, and query result caches.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database.connection import Base


class SavedQuery(Base):
    """A persisted structured query that can be re-run."""

    __tablename__ = "saved_queries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    filters_json: Mapped[str] = mapped_column(Text)
    sort_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_direction: Mapped[str] = mapped_column(String(10), default="asc")
    max_results: Mapped[int] = mapped_column(Integer, default=500)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "filters_json": self.filters_json,
            "sort_by": self.sort_by,
            "sort_direction": self.sort_direction,
            "max_results": self.max_results,
            "favorite": self.favorite,
            "pinned": self.pinned,
            "tags_json": self.tags_json,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }


class QueryHistory(Base):
    """A record of a query that was executed."""

    __tablename__ = "query_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    saved_query_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    filters_json: Mapped[str] = mapped_column(Text)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "saved_query_id": self.saved_query_id,
            "filters_json": self.filters_json,
            "result_count": self.result_count,
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
            "error_message": self.error_message,
            "executed_by": self.executed_by,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class QueryResultCache(Base):
    """Cached query results for fast re-execution."""

    __tablename__ = "query_results_cache"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    query_hash: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False
    )
    project_id: Mapped[str] = mapped_column(String(36), index=True)
    results_json: Mapped[str] = mapped_column(Text)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query_hash": self.query_hash,
            "project_id": self.project_id,
            "results_json": self.results_json,
            "total_count": self.total_count,
            "execution_time_ms": self.execution_time_ms,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
