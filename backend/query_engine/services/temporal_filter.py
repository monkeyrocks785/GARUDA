"""Temporal Filter Service.

Applies temporal filter operations to entity queries.
"""

import logging
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from knowledge_engine.database.models import Entity, EntityEvent, EntityObservation

logger = logging.getLogger("garuda.query.temporal")


class TemporalFilterService:
    """Applies temporal constraints to entity queries."""

    @staticmethod
    def parse_datetime(date_str: str) -> datetime:
        """Parse an ISO datetime string."""
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

    @staticmethod
    def filter_before(query, date: str):
        """Filter entities created before a given date."""
        dt = TemporalFilterService.parse_datetime(date)
        return query.filter(Entity.created_at < dt)

    @staticmethod
    def filter_after(query, date: str):
        """Filter entities created after a given date."""
        dt = TemporalFilterService.parse_datetime(date)
        return query.filter(Entity.created_at > dt)

    @staticmethod
    def filter_between(query, date_from: str, date_to: str):
        """Filter entities created between two dates."""
        dt_from = TemporalFilterService.parse_datetime(date_from)
        dt_to = TemporalFilterService.parse_datetime(date_to)
        return query.filter(
            Entity.created_at >= dt_from,
            Entity.created_at <= dt_to,
        )

    @staticmethod
    def filter_first_seen(query, date: str, before: bool = False):
        """Filter entities by their first observation date."""
        dt = TemporalFilterService.parse_datetime(date)
        if before:
            return query.filter(Entity.first_observed_at < dt)
        return query.filter(Entity.first_observed_at > dt)

    @staticmethod
    def filter_last_seen(query, date: str, before: bool = False):
        """Filter entities by their last observation date."""
        dt = TemporalFilterService.parse_datetime(date)
        if before:
            return query.filter(Entity.last_observed_at < dt)
        return query.filter(Entity.last_observed_at > dt)

    @staticmethod
    def filter_observation_count(
        query,
        min_count: int | None = None,
        max_count: int | None = None,
    ):
        """Filter entities by observation count."""
        if min_count is not None:
            query = query.filter(Entity.observation_count >= min_count)
        if max_count is not None:
            query = query.filter(Entity.observation_count <= max_count)
        return query

    @staticmethod
    def filter_duration(
        query,
        min_days: int | None = None,
        max_days: int | None = None,
    ):
        """Filter entities by the duration between first and last observed."""
        from sqlalchemy import cast, Date

        if min_days is not None:
            query = query.filter(
                func.julianday(Entity.last_observed_at)
                - func.julianday(Entity.first_observed_at)
                >= min_days
            )
        if max_days is not None:
            query = query.filter(
                func.julianday(Entity.last_observed_at)
                - func.julianday(Entity.first_observed_at)
                <= max_days
            )
        return query

    @staticmethod
    def apply_temporal_filter(query, temporal: dict):
        """Apply a temporal filter clause to a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query on Entity model.
            temporal: Temporal filter dict from query builder.
            
        Returns:
            Filtered SQLAlchemy query.
        """
        operator = temporal.get("operator", "between")

        if operator == "before" and "date" in temporal:
            return TemporalFilterService.filter_before(query, temporal["date"])

        if operator == "after" and "date" in temporal:
            return TemporalFilterService.filter_after(query, temporal["date"])

        if operator == "between":
            date_from = temporal.get("date_from")
            date_to = temporal.get("date_to")
            if date_from and date_to:
                return TemporalFilterService.filter_between(query, date_from, date_to)

        if operator == "first_seen" and "date" in temporal:
            return TemporalFilterService.filter_first_seen(
                query, temporal["date"], temporal.get("before", False)
            )

        if operator == "last_seen" and "date" in temporal:
            return TemporalFilterService.filter_last_seen(
                query, temporal["date"], temporal.get("before", False)
            )

        if operator == "observation_count":
            return TemporalFilterService.filter_observation_count(
                query,
                temporal.get("min_observations"),
                temporal.get("max_observations"),
            )

        if operator == "duration":
            return TemporalFilterService.filter_duration(
                query,
                temporal.get("min_duration_days"),
                temporal.get("max_duration_days"),
            )

        return query
