"""Query History Service.

Manages saved queries, query history, and result caching.
"""

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from query_engine.config import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_SAVED_QUERIES_PER_PROJECT,
    MAX_HISTORY_ENTRIES,
    QUERY_CACHE_TTL_SECONDS,
)
from query_engine.database.models import (
    QueryHistory,
    QueryResultCache,
    SavedQuery,
)

logger = logging.getLogger("garuda.query.history")


class QueryHistoryService:
    """Manages query persistence and caching."""

    # ── Saved Queries ─────────────────────────────────────────────────────────

    @staticmethod
    def save_query(
        db: Session,
        project_id: str,
        name: str,
        filters_json: str,
        description: str | None = None,
        sort_by: str | None = None,
        sort_direction: str = "asc",
        max_results: int = 500,
        tags_json: str | None = None,
        created_by: str | None = None,
    ) -> SavedQuery:
        """Save a structured query."""
        count = (
            db.query(SavedQuery)
            .filter(SavedQuery.project_id == project_id)
            .count()
        )
        if count >= MAX_SAVED_QUERIES_PER_PROJECT:
            raise ValueError(
                f"Maximum of {MAX_SAVED_QUERIES_PER_PROJECT} saved queries "
                f"per project reached."
            )

        sq = SavedQuery(
            project_id=project_id,
            name=name,
            description=description,
            filters_json=filters_json,
            sort_by=sort_by,
            sort_direction=sort_direction,
            max_results=max_results,
            tags_json=tags_json,
            created_by=created_by,
        )
        db.add(sq)
        db.commit()
        db.refresh(sq)
        logger.info(f"Saved query: {name}")
        return sq

    @staticmethod
    def get_saved_query(db: Session, query_id: str) -> SavedQuery | None:
        """Get a saved query by ID."""
        return (
            db.query(SavedQuery)
            .filter(SavedQuery.id == query_id)
            .first()
        )

    @staticmethod
    def list_saved_queries(
        db: Session,
        project_id: str,
        favorite_only: bool = False,
        pinned_only: bool = False,
        search: str | None = None,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[SavedQuery], int]:
        """List saved queries for a project."""
        q = db.query(SavedQuery).filter(
            SavedQuery.project_id == project_id
        )
        if favorite_only:
            q = q.filter(SavedQuery.favorite == True)
        if pinned_only:
            q = q.filter(SavedQuery.pinned == True)
        if search:
            term = f"%{search}%"
            q = q.filter(SavedQuery.name.ilike(term))

        total = q.count()
        items = (
            q.order_by(SavedQuery.pinned.desc(), SavedQuery.name)
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def update_saved_query(
        db: Session,
        query_id: str,
        name: str | None = None,
        description: str | None = None,
        filters_json: str | None = None,
        sort_by: str | None = None,
        sort_direction: str | None = None,
        max_results: int | None = None,
        favorite: bool | None = None,
        pinned: bool | None = None,
        tags_json: str | None = None,
    ) -> SavedQuery | None:
        """Update a saved query."""
        sq = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if sq is None:
            return None

        if name is not None:
            sq.name = name
        if description is not None:
            sq.description = description
        if filters_json is not None:
            sq.filters_json = filters_json
        if sort_by is not None:
            sq.sort_by = sort_by
        if sort_direction is not None:
            sq.sort_direction = sort_direction
        if max_results is not None:
            sq.max_results = max_results
        if favorite is not None:
            sq.favorite = favorite
        if pinned is not None:
            sq.pinned = pinned
        if tags_json is not None:
            sq.tags_json = tags_json

        db.commit()
        db.refresh(sq)
        logger.info(f"Updated saved query: {sq.name}")
        return sq

    @staticmethod
    def delete_saved_query(db: Session, query_id: str) -> bool:
        """Delete a saved query."""
        sq = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if sq is None:
            return False
        db.delete(sq)
        db.commit()
        logger.info(f"Deleted saved query: {sq.name}")
        return True

    @staticmethod
    def toggle_favorite(db: Session, query_id: str) -> SavedQuery | None:
        """Toggle the favorite status of a saved query."""
        sq = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if sq is None:
            return None
        sq.favorite = not sq.favorite
        db.commit()
        db.refresh(sq)
        return sq

    @staticmethod
    def toggle_pinned(db: Session, query_id: str) -> SavedQuery | None:
        """Toggle the pinned status of a saved query."""
        sq = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if sq is None:
            return None
        sq.pinned = not sq.pinned
        db.commit()
        db.refresh(sq)
        return sq

    # ── Query History ─────────────────────────────────────────────────────────

    @staticmethod
    def record_execution(
        db: Session,
        project_id: str,
        filters_json: str,
        result_count: int,
        execution_time_ms: float,
        status: str = "completed",
        error_message: str | None = None,
        saved_query_id: str | None = None,
        executed_by: str | None = None,
    ) -> QueryHistory:
        """Record a query execution in history."""
        entry = QueryHistory(
            project_id=project_id,
            saved_query_id=saved_query_id,
            filters_json=filters_json,
            result_count=result_count,
            execution_time_ms=execution_time_ms,
            status=status,
            error_message=error_message,
            executed_by=executed_by,
        )
        db.add(entry)
        db.commit()

        # Prune old entries
        total = db.query(QueryHistory).filter(
            QueryHistory.project_id == project_id
        ).count()
        if total > MAX_HISTORY_ENTRIES:
            oldest = (
                db.query(QueryHistory)
                .filter(QueryHistory.project_id == project_id)
                .order_by(QueryHistory.executed_at.asc())
                .limit(total - MAX_HISTORY_ENTRIES)
                .all()
            )
            for o in oldest:
                db.delete(o)
            db.commit()

        return entry

    @staticmethod
    def list_history(
        db: Session,
        project_id: str,
        saved_query_id: str | None = None,
        status: str | None = None,
        page: int = 0,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> tuple[list[QueryHistory], int]:
        """List query history for a project."""
        q = db.query(QueryHistory).filter(
            QueryHistory.project_id == project_id
        )
        if saved_query_id:
            q = q.filter(QueryHistory.saved_query_id == saved_query_id)
        if status:
            q = q.filter(QueryHistory.status == status)

        total = q.count()
        items = (
            q.order_by(desc(QueryHistory.executed_at))
            .offset(page * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def get_history_entry(db: Session, history_id: str) -> QueryHistory | None:
        """Get a specific history entry."""
        return (
            db.query(QueryHistory)
            .filter(QueryHistory.id == history_id)
            .first()
        )

    @staticmethod
    def delete_history_entry(db: Session, history_id: str) -> bool:
        """Delete a history entry."""
        entry = db.query(QueryHistory).filter(
            QueryHistory.id == history_id
        ).first()
        if entry is None:
            return False
        db.delete(entry)
        db.commit()
        return True

    @staticmethod
    def clear_history(db: Session, project_id: str) -> int:
        """Clear all history for a project."""
        deleted = (
            db.query(QueryHistory)
            .filter(QueryHistory.project_id == project_id)
            .delete()
        )
        db.commit()
        return deleted

    # ── Query Result Caching ──────────────────────────────────────────────────

    @staticmethod
    def get_cached_result(
        db: Session,
        query_hash: str,
        project_id: str,
    ) -> dict | None:
        """Get a cached query result if valid."""
        cache = (
            db.query(QueryResultCache)
            .filter(
                QueryResultCache.query_hash == query_hash,
                QueryResultCache.project_id == project_id,
            )
            .first()
        )
        if cache is None:
            return None

        now = datetime.utcnow()
        if cache.expires_at and now > cache.expires_at:
            db.delete(cache)
            db.commit()
            return None

        return {
            "results_json": cache.results_json,
            "total_count": cache.total_count,
            "execution_time_ms": cache.execution_time_ms,
            "cached": True,
        }

    @staticmethod
    def cache_result(
        db: Session,
        query_hash: str,
        project_id: str,
        results_json: str,
        total_count: int,
        execution_time_ms: float,
        ttl_seconds: int = QUERY_CACHE_TTL_SECONDS,
    ) -> QueryResultCache:
        """Cache a query result."""
        # Remove existing cache for this hash
        existing = (
            db.query(QueryResultCache)
            .filter(
                QueryResultCache.query_hash == query_hash,
                QueryResultCache.project_id == project_id,
            )
            .all()
        )
        for e in existing:
            db.delete(e)

        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        cache = QueryResultCache(
            query_hash=query_hash,
            project_id=project_id,
            results_json=results_json,
            total_count=total_count,
            execution_time_ms=execution_time_ms,
            expires_at=expires_at,
        )
        db.add(cache)
        db.commit()
        return cache

    @staticmethod
    def clear_cache(db: Session, project_id: str | None = None) -> int:
        """Clear cached results. Optionally scoped to a project."""
        q = db.query(QueryResultCache)
        if project_id:
            q = q.filter(QueryResultCache.project_id == project_id)
        deleted = q.delete()
        db.commit()
        return deleted
