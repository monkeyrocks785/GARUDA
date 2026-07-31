"""Mission Engine - Services."""

import json
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from mission_engine.database.models import (
    Mission,
    MissionActivity,
    MissionNote,
    MissionProject,
    MissionTag,
)

logger = logging.getLogger("garuda.mission.service")


class MissionService:
    """High-level service for mission operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_mission(
        self,
        name: str,
        code: str | None = None,
        description: str | None = None,
        classification: str | None = None,
        status: str = "planning",
        priority: str = "medium",
        created_by: str | None = None,
        mission_start: datetime | None = None,
        mission_end: datetime | None = None,
        area_of_interest: str | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
    ) -> Mission:
        """Create a new mission."""
        mission = Mission(
            name=name,
            code=code,
            description=description,
            classification=classification,
            status=status,
            priority=priority,
            created_by=created_by,
            mission_start=mission_start,
            mission_end=mission_end,
            area_of_interest=area_of_interest,
            tags=json.dumps(tags) if tags else None,
            notes=notes,
        )
        self.db.add(mission)
        self.db.flush()

        # Create storage directory
        storage_path = os.path.join("storage", "missions", mission.id)
        os.makedirs(os.path.join(storage_path, "projects"), exist_ok=True)
        os.makedirs(os.path.join(storage_path, "reports"), exist_ok=True)
        os.makedirs(os.path.join(storage_path, "evidence"), exist_ok=True)
        os.makedirs(os.path.join(storage_path, "logs"), exist_ok=True)
        os.makedirs(os.path.join(storage_path, "exports"), exist_ok=True)
        mission.storage_path = storage_path

        # Add tags
        if tags:
            for tag in tags:
                mission_tag = MissionTag(mission_id=mission.id, tag=tag)
                self.db.add(mission_tag)

        # Log activity
        activity = MissionActivity(
            mission_id=mission.id,
            action="created",
            details=f"Mission '{name}' created",
            performed_by=created_by,
        )
        self.db.add(activity)

        self.db.commit()
        self.db.refresh(mission)
        logger.info(f"Mission created: {mission.name} ({mission.id})")
        return mission

    def get_mission(self, mission_id: str) -> Mission | None:
        """Get a mission by ID."""
        return self.db.get(Mission, mission_id)

    def list_missions(
        self,
        status: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Mission], int]:
        """List missions with filters."""
        q = self.db.query(Mission).filter(Mission.archived == False)
        if status:
            q = q.filter(Mission.status == status)
        if priority:
            q = q.filter(Mission.priority == priority)
        if search:
            q = q.filter(
                Mission.name.ilike(f"%{search}%")
                | Mission.code.ilike(f"%{search}%")
                | Mission.description.ilike(f"%{search}%")
            )

        total = q.count()
        missions = q.order_by(Mission.created_at.desc()).offset(offset).limit(limit).all()
        return missions, total

    def update_mission(self, mission_id: str, **kwargs) -> Mission | None:
        """Update a mission."""
        mission = self.db.get(Mission, mission_id)
        if not mission:
            return None

        for key, value in kwargs.items():
            if hasattr(mission, key) and value is not None:
                setattr(mission, key, value)

        # Update tags
        if "tags" in kwargs and kwargs["tags"] is not None:
            self.db.query(MissionTag).filter(MissionTag.mission_id == mission_id).delete()
            for tag in kwargs["tags"]:
                mission_tag = MissionTag(mission_id=mission_id, tag=tag)
                self.db.add(mission_tag)

        # Log activity
        activity = MissionActivity(
            mission_id=mission_id,
            action="updated",
            details=f"Mission updated: {list(kwargs.keys())}",
        )
        self.db.add(activity)

        self.db.commit()
        self.db.refresh(mission)
        return mission

    def delete_mission(self, mission_id: str) -> bool:
        """Delete a mission."""
        mission = self.db.get(Mission, mission_id)
        if not mission:
            return False

        self.db.delete(mission)
        self.db.commit()
        return True

    def archive_mission(self, mission_id: str) -> Mission | None:
        """Archive a mission."""
        mission = self.db.get(Mission, mission_id)
        if not mission:
            return None

        mission.archived = True
        mission.status = "archived"

        activity = MissionActivity(
            mission_id=mission_id,
            action="archived",
            details="Mission archived",
        )
        self.db.add(activity)

        self.db.commit()
        self.db.refresh(mission)
        return mission

    def toggle_favorite(self, mission_id: str) -> Mission | None:
        """Toggle mission favorite status."""
        mission = self.db.get(Mission, mission_id)
        if not mission:
            return None

        mission.favorite = not mission.favorite
        self.db.commit()
        self.db.refresh(mission)
        return mission

    def add_project(self, mission_id: str, project_id: str, notes: str | None = None) -> MissionProject | None:
        """Add a project to a mission."""
        mission = self.db.get(Mission, mission_id)
        if not mission:
            return None

        # Check if already linked
        existing = (
            self.db.query(MissionProject)
            .filter(
                MissionProject.mission_id == mission_id,
                MissionProject.project_id == project_id,
            )
            .first()
        )
        if existing:
            return existing

        link = MissionProject(
            mission_id=mission_id,
            project_id=project_id,
            notes=notes,
        )
        self.db.add(link)

        # Update mission project count
        mission.project_count += 1

        # Log activity
        activity = MissionActivity(
            mission_id=mission_id,
            action="project_added",
            details=f"Project {project_id} linked to mission",
            entity_type="project",
            entity_id=project_id,
        )
        self.db.add(activity)

        self.db.commit()
        self.db.refresh(link)
        return link

    def remove_project(self, mission_id: str, project_id: str) -> bool:
        """Remove a project from a mission."""
        link = (
            self.db.query(MissionProject)
            .filter(
                MissionProject.mission_id == mission_id,
                MissionProject.project_id == project_id,
            )
            .first()
        )
        if not link:
            return False

        mission = self.db.get(Mission, mission_id)
        if mission and mission.project_count > 0:
            mission.project_count -= 1

        self.db.delete(link)

        activity = MissionActivity(
            mission_id=mission_id,
            action="project_removed",
            details=f"Project {project_id} unlinked from mission",
            entity_type="project",
            entity_id=project_id,
        )
        self.db.add(activity)

        self.db.commit()
        return True

    def get_mission_projects(self, mission_id: str) -> list[MissionProject]:
        """Get all projects linked to a mission."""
        return (
            self.db.query(MissionProject)
            .filter(MissionProject.mission_id == mission_id)
            .order_by(MissionProject.added_at.desc())
            .all()
        )

    def get_timeline(self, mission_id: str, limit: int = 50) -> list[MissionActivity]:
        """Get mission activity timeline."""
        return (
            self.db.query(MissionActivity)
            .filter(MissionActivity.mission_id == mission_id)
            .order_by(MissionActivity.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_notes(self, mission_id: str) -> list[MissionNote]:
        """Get all notes for a mission."""
        return (
            self.db.query(MissionNote)
            .filter(MissionNote.mission_id == mission_id)
            .order_by(MissionNote.created_at.desc())
            .all()
        )

    def add_note(
        self,
        mission_id: str,
        title: str | None = None,
        content: str | None = None,
        author: str | None = None,
    ) -> MissionNote | None:
        """Add a note to a mission."""
        mission = self.db.get(Mission, mission_id)
        if not mission:
            return None

        note = MissionNote(
            mission_id=mission_id,
            title=title,
            content=content,
            author=author,
        )
        self.db.add(note)

        activity = MissionActivity(
            mission_id=mission_id,
            action="note_added",
            details=f"Note '{title}' added" if title else "Note added",
            entity_type="note",
        )
        self.db.add(activity)

        self.db.commit()
        self.db.refresh(note)
        return note

    def get_tags(self, mission_id: str) -> list[MissionTag]:
        """Get all tags for a mission."""
        return (
            self.db.query(MissionTag)
            .filter(MissionTag.mission_id == mission_id)
            .all()
        )

    def get_mission_stats(self) -> dict:
        """Get mission statistics."""
        missions = self.db.query(Mission).filter(Mission.archived == False).all()
        return {
            "total": len(missions),
            "planning": sum(1 for m in missions if m.status == "planning"),
            "active": sum(1 for m in missions if m.status == "active"),
            "completed": sum(1 for m in missions if m.status == "completed"),
            "paused": sum(1 for m in missions if m.status == "paused"),
            "archived": sum(1 for m in missions if m.status == "archived"),
            "cancelled": sum(1 for m in missions if m.status == "cancelled"),
            "total_projects": sum(m.project_count for m in missions),
        }
