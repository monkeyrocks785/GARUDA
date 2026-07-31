"""Temporal Engine - Services."""

import json
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from temporal_engine.database.models import (
    ComparisonSession,
    Timeline,
    TimelineBookmark,
    TimelineEntry,
    TimelineLog,
)

logger = logging.getLogger("garuda.temporal.service")


class TemporalService:
    """High-level service for temporal analysis operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_timeline(
        self,
        name: str,
        project_id: str | None = None,
        description: str | None = None,
        group_by: str = "date",
        sort_order: str = "asc",
        tags: list[str] | None = None,
        notes: str | None = None,
    ) -> Timeline:
        """Create a new timeline."""
        timeline = Timeline(
            name=name,
            project_id=project_id,
            description=description,
            group_by=group_by,
            sort_order=sort_order,
            tags=json.dumps(tags) if tags else None,
            notes=notes,
        )
        self.db.add(timeline)
        self.db.flush()

        storage_path = os.path.join("storage", "timelines", timeline.id)
        os.makedirs(os.path.join(storage_path, "comparisons"), exist_ok=True)
        os.makedirs(os.path.join(storage_path, "bookmarks"), exist_ok=True)
        timeline.storage_path = storage_path

        log = TimelineLog(
            timeline_id=timeline.id,
            action="created",
            details=f"Timeline '{name}' created",
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(timeline)
        logger.info(f"Timeline created: {timeline.name} ({timeline.id})")
        return timeline

    def get_timeline(self, timeline_id: str) -> Timeline | None:
        """Get a timeline by ID."""
        return self.db.get(Timeline, timeline_id)

    def list_timelines(
        self,
        project_id: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Timeline], int]:
        """List timelines with filters."""
        q = self.db.query(Timeline).filter(Timeline.archived == False)
        if project_id:
            q = q.filter(Timeline.project_id == project_id)
        if search:
            q = q.filter(
                Timeline.name.ilike(f"%{search}%")
                | Timeline.description.ilike(f"%{search}%")
            )

        total = q.count()
        timelines = q.order_by(Timeline.created_at.desc()).offset(offset).limit(limit).all()
        return timelines, total

    def update_timeline(self, timeline_id: str, **kwargs) -> Timeline | None:
        """Update a timeline."""
        timeline = self.db.get(Timeline, timeline_id)
        if not timeline:
            return None

        for key, value in kwargs.items():
            if hasattr(timeline, key) and value is not None:
                setattr(timeline, key, value)

        if "tags" in kwargs and kwargs["tags"] is not None:
            timeline.tags = json.dumps(kwargs["tags"])

        log = TimelineLog(
            timeline_id=timeline_id,
            action="updated",
            details=f"Timeline updated: {list(kwargs.keys())}",
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(timeline)
        return timeline

    def delete_timeline(self, timeline_id: str) -> bool:
        """Delete a timeline."""
        timeline = self.db.get(Timeline, timeline_id)
        if not timeline:
            return False
        self.db.delete(timeline)
        self.db.commit()
        return True

    def duplicate_timeline(self, timeline_id: str, new_name: str | None = None) -> Timeline | None:
        """Duplicate a timeline with all entries."""
        original = self.db.get(Timeline, timeline_id)
        if not original:
            return None

        new_timeline = self.create_timeline(
            name=new_name or f"{original.name} (Copy)",
            project_id=original.project_id,
            description=original.description,
            group_by=original.group_by,
            sort_order=original.sort_order,
            notes=original.notes,
        )

        # Copy entries
        entries = (
            self.db.query(TimelineEntry)
            .filter(TimelineEntry.timeline_id == timeline_id)
            .order_by(TimelineEntry.sort_order)
            .all()
        )
        for entry in entries:
            new_entry = TimelineEntry(
                timeline_id=new_timeline.id,
                dataset_id=entry.dataset_id,
                acquisition_date=entry.acquisition_date,
                acquisition_time=entry.acquisition_time,
                sensor_name=entry.sensor_name,
                source=entry.source,
                resolution=entry.resolution,
                mission_id=entry.mission_id,
                aoi_id=entry.aoi_id,
                dataset_type=entry.dataset_type,
                sort_order=entry.sort_order,
                visibility=entry.visibility,
                opacity=entry.opacity,
                notes=entry.notes,
            )
            self.db.add(new_entry)

        new_timeline.entry_count = len(entries)
        self.db.commit()
        self.db.refresh(new_timeline)
        return new_timeline

    def toggle_favorite(self, timeline_id: str) -> Timeline | None:
        """Toggle timeline favorite status."""
        timeline = self.db.get(Timeline, timeline_id)
        if not timeline:
            return None
        timeline.favorite = not timeline.favorite
        self.db.commit()
        self.db.refresh(timeline)
        return timeline

    def add_entry(
        self,
        timeline_id: str,
        dataset_id: str,
        acquisition_date: datetime | None = None,
        acquisition_time: str | None = None,
        sensor_name: str | None = None,
        source: str | None = None,
        resolution: str | None = None,
        mission_id: str | None = None,
        aoi_id: str | None = None,
        dataset_type: str | None = None,
        notes: str | None = None,
    ) -> TimelineEntry | None:
        """Add a dataset to a timeline."""
        timeline = self.db.get(Timeline, timeline_id)
        if not timeline:
            return None

        # Get next sort order
        max_order = self.db.query(TimelineEntry.sort_order).filter(
            TimelineEntry.timeline_id == timeline_id
        ).order_by(desc(TimelineEntry.sort_order)).first()
        sort_order = (max_order[0] + 1) if max_order else 0

        entry = TimelineEntry(
            timeline_id=timeline_id,
            dataset_id=dataset_id,
            acquisition_date=acquisition_date,
            acquisition_time=acquisition_time,
            sensor_name=sensor_name,
            source=source,
            resolution=resolution,
            mission_id=mission_id,
            aoi_id=aoi_id,
            dataset_type=dataset_type,
            sort_order=sort_order,
            notes=notes,
        )
        self.db.add(entry)

        timeline.entry_count += 1

        log = TimelineLog(
            timeline_id=timeline_id,
            action="dataset_added",
            details=f"Dataset {dataset_id} added to timeline",
            entity_type="dataset",
            entity_id=dataset_id,
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(entry)
        return entry

    def remove_entry(self, timeline_id: str, entry_id: str) -> bool:
        """Remove a dataset from a timeline."""
        entry = self.db.get(TimelineEntry, entry_id)
        if not entry or entry.timeline_id != timeline_id:
            return False

        timeline = self.db.get(Timeline, timeline_id)
        if timeline and timeline.entry_count > 0:
            timeline.entry_count -= 1

        self.db.delete(entry)

        log = TimelineLog(
            timeline_id=timeline_id,
            action="dataset_removed",
            details=f"Entry {entry_id} removed from timeline",
            entity_type="entry",
            entity_id=entry_id,
        )
        self.db.add(log)

        self.db.commit()
        return True

    def get_entries(
        self,
        timeline_id: str,
        sensor: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[TimelineEntry]:
        """Get all entries for a timeline, sorted chronologically."""
        q = self.db.query(TimelineEntry).filter(TimelineEntry.timeline_id == timeline_id)
        if sensor:
            q = q.filter(TimelineEntry.sensor_name == sensor)
        if date_from:
            q = q.filter(TimelineEntry.acquisition_date >= date_from)
        if date_to:
            q = q.filter(TimelineEntry.acquisition_date <= date_to)

        timeline = self.db.get(Timeline, timeline_id)
        if timeline and timeline.sort_order == "desc":
            return q.order_by(desc(TimelineEntry.acquisition_date), TimelineEntry.sort_order).all()
        return q.order_by(asc(TimelineEntry.acquisition_date), TimelineEntry.sort_order).all()

    def update_entry(self, entry_id: str, **kwargs) -> TimelineEntry | None:
        """Update a timeline entry."""
        entry = self.db.get(TimelineEntry, entry_id)
        if not entry:
            return None
        for key, value in kwargs.items():
            if hasattr(entry, key) and value is not None:
                setattr(entry, key, value)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def reorder_entries(self, timeline_id: str, entry_ids: list[str]) -> bool:
        """Reorder entries in a timeline."""
        for i, entry_id in enumerate(entry_ids):
            entry = self.db.get(TimelineEntry, entry_id)
            if entry and entry.timeline_id == timeline_id:
                entry.sort_order = i
        self.db.commit()
        return True

    def create_comparison(
        self,
        timeline_id: str,
        name: str | None = None,
        mode: str = "side_by_side",
        left_entry_id: str | None = None,
        right_entry_id: str | None = None,
    ) -> ComparisonSession | None:
        """Create a comparison session."""
        timeline = self.db.get(Timeline, timeline_id)
        if not timeline:
            return None

        session = ComparisonSession(
            timeline_id=timeline_id,
            name=name,
            mode=mode,
            left_entry_id=left_entry_id,
            right_entry_id=right_entry_id,
        )
        self.db.add(session)

        log = TimelineLog(
            timeline_id=timeline_id,
            action="comparison_started",
            details=f"Comparison session created ({mode})",
            entity_type="comparison",
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(session)
        return session

    def get_comparison(self, session_id: str) -> ComparisonSession | None:
        """Get a comparison session."""
        return self.db.get(ComparisonSession, session_id)

    def update_comparison(self, session_id: str, **kwargs) -> ComparisonSession | None:
        """Update a comparison session."""
        session = self.db.get(ComparisonSession, session_id)
        if not session:
            return None
        for key, value in kwargs.items():
            if hasattr(session, key) and value is not None:
                setattr(session, key, value)
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_bookmark(
        self,
        timeline_id: str,
        label: str,
        entry_id: str | None = None,
        bookmark_date: datetime | None = None,
        color: str | None = None,
        notes: str | None = None,
    ) -> TimelineBookmark | None:
        """Add a bookmark to a timeline."""
        timeline = self.db.get(Timeline, timeline_id)
        if not timeline:
            return None

        bookmark = TimelineBookmark(
            timeline_id=timeline_id,
            entry_id=entry_id,
            label=label,
            bookmark_date=bookmark_date,
            color=color,
            notes=notes,
        )
        self.db.add(bookmark)

        log = TimelineLog(
            timeline_id=timeline_id,
            action="bookmark_added",
            details=f"Bookmark '{label}' added",
            entity_type="bookmark",
        )
        self.db.add(log)

        self.db.commit()
        self.db.refresh(bookmark)
        return bookmark

    def get_bookmarks(self, timeline_id: str) -> list[TimelineBookmark]:
        """Get all bookmarks for a timeline."""
        return (
            self.db.query(TimelineBookmark)
            .filter(TimelineBookmark.timeline_id == timeline_id)
            .order_by(TimelineBookmark.created_at.desc())
            .all()
        )

    def delete_bookmark(self, bookmark_id: str) -> bool:
        """Delete a bookmark."""
        bookmark = self.db.get(TimelineBookmark, bookmark_id)
        if not bookmark:
            return False
        self.db.delete(bookmark)
        self.db.commit()
        return True

    def get_logs(self, timeline_id: str, limit: int = 50) -> list[TimelineLog]:
        """Get timeline activity logs."""
        return (
            self.db.query(TimelineLog)
            .filter(TimelineLog.timeline_id == timeline_id)
            .order_by(TimelineLog.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_sensors(self, timeline_id: str) -> list[str]:
        """Get distinct sensor names in a timeline."""
        results = (
            self.db.query(TimelineEntry.sensor_name)
            .filter(
                TimelineEntry.timeline_id == timeline_id,
                TimelineEntry.sensor_name.isnot(None),
            )
            .distinct()
            .all()
        )
        return [r[0] for r in results if r[0]]

    def get_stats(self, timeline_id: str | None = None) -> dict:
        """Get timeline statistics."""
        q = self.db.query(Timeline).filter(Timeline.archived == False)
        if timeline_id:
            q = q.filter(Timeline.id == timeline_id)
        timelines = q.all()

        total_entries = sum(t.entry_count for t in timelines)
        return {
            "total_timelines": len(timelines),
            "total_entries": total_entries,
        }
