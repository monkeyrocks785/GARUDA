"""Project service for business logic and storage management."""

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session

from config.settings import settings
from models.project import Project
from repositories.project_repository import ProjectRepository

# Project subdirectories to create on initialization
PROJECT_SUBDIRS = [
    "imagery",
    "vectors",
    "terrain",
    "downloads",
    "models",
    "reports",
    "exports",
    "logs",
    "cache",
    "temp",
    "config",
    "metadata",
    "analysis",
    "timeline",
]

# Invalid filesystem characters
INVALID_FS_CHARS = r'[<>:"/\\|?*\x00-\x1f]'


class ProjectService:
    """Service for project management operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProjectRepository(db)

    def validate_name(self, name: str, exclude_id: str | None = None) -> str:
        """Validate and sanitize project name.

        Args:
            name: The project name to validate.
            exclude_id: Optional project ID to exclude from duplicate check.

        Returns:
            Sanitized project name.

        Raises:
            ValueError: If name is invalid or already exists.
        """
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")

        sanitized = name.strip()

        # Remove invalid filesystem characters
        sanitized = re.sub(INVALID_FS_CHARS, "", sanitized)

        if not sanitized:
            raise ValueError("Project name contains only invalid characters")

        if len(sanitized) > 255:
            raise ValueError("Project name cannot exceed 255 characters")

        # Check for duplicates
        if self.repository.name_exists(sanitized, exclude_id=exclude_id):
            raise ValueError(f"A project named '{sanitized}' already exists")

        return sanitized

    def create_project(
        self,
        name: str,
        description: str | None = None,
        area_of_interest: str | None = None,
        coordinate_system: str | None = None,
        tags: list[str] | None = None,
    ) -> Project:
        """Create a new project with storage directories.

        Args:
            name: Project name.
            description: Optional project description.
            area_of_interest: Optional AOI description.
            coordinate_system: Optional EPSG code.
            tags: Optional list of tags.

        Returns:
            Created project instance.
        """
        validated_name = self.validate_name(name)

        # Create project UUID and storage path
        project_id = str(__import__("uuid").uuid4())
        storage_path = Path(settings.PROJECTS_DIR) / project_id

        # Create storage directories
        storage_path.mkdir(parents=True, exist_ok=True)
        for subdir in PROJECT_SUBDIRS:
            (storage_path / subdir).mkdir(exist_ok=True)

        # Create project
        project = Project(
            id=project_id,
            name=validated_name,
            description=description,
            status="created",
            current_stage="initialization",
            storage_path=str(storage_path),
            area_of_interest=area_of_interest,
            coordinate_system=coordinate_system,
            tags=json.dumps(tags) if tags else None,
        )

        project = self.repository.create(project)

        # Create metadata JSON file
        self._save_metadata_json(project)

        logger.info(
            "Project created",
            project_id=project.id,
            name=project.name,
        )

        return project

    def open_project(self, project_id: str) -> Project:
        """Open a project and update its last opened timestamp.

        Args:
            project_id: The project UUID.

        Returns:
            Updated project instance.

        Raises:
            ValueError: If project not found.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project.last_opened_at = datetime.now(UTC)
        project = self.repository.update(project)

        logger.info(
            "Project opened",
            project_id=project.id,
            name=project.name,
        )

        return project

    def delete_project(self, project_id: str, delete_files: bool = True) -> None:
        """Delete a project and optionally its storage files.

        Args:
            project_id: The project UUID.
            delete_files: If True, delete storage directory.

        Raises:
            ValueError: If project not found.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project_name = project.name
        storage_path = Path(project.storage_path)

        # Delete files if requested
        if delete_files and storage_path.exists():
            shutil.rmtree(storage_path)
            logger.info("Project storage deleted", path=str(storage_path))

        self.repository.delete(project)

        logger.info(
            "Project deleted",
            project_id=project_id,
            name=project_name,
        )

    def rename_project(self, project_id: str, new_name: str) -> Project:
        """Rename a project.

        Args:
            project_id: The project UUID.
            new_name: New project name.

        Returns:
            Updated project instance.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        validated_name = self.validate_name(new_name, exclude_id=project_id)
        project.name = validated_name
        project = self.repository.update(project)

        # Update metadata JSON
        self._save_metadata_json(project)

        logger.info(
            "Project renamed",
            project_id=project.id,
            new_name=project.name,
        )

        return project

    def archive_project(self, project_id: str) -> Project:
        """Archive a project.

        Args:
            project_id: The project UUID.

        Returns:
            Updated project instance.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project.archived = True
        project.status = "archived"
        project = self.repository.update(project)

        logger.info(
            "Project archived",
            project_id=project.id,
            name=project.name,
        )

        return project

    def unarchive_project(self, project_id: str) -> Project:
        """Unarchive a project.

        Args:
            project_id: The project UUID.

        Returns:
            Updated project instance.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project.archived = False
        project.status = "active"
        project = self.repository.update(project)

        logger.info(
            "Project unarchived",
            project_id=project.id,
            name=project.name,
        )

        return project

    def toggle_favorite(self, project_id: str) -> Project:
        """Toggle favorite status of a project.

        Args:
            project_id: The project UUID.

        Returns:
            Updated project instance.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project.favorite = not project.favorite
        project = self.repository.update(project)

        logger.info(
            "Project favorite toggled",
            project_id=project.id,
            favorite=project.favorite,
        )

        return project

    def duplicate_project(self, project_id: str, new_name: str | None = None) -> Project:
        """Duplicate a project with its storage.

        Args:
            project_id: The project UUID to duplicate.
            new_name: Optional name for the duplicate.

        Returns:
            New project instance.
        """
        source = self.repository.get_by_id(project_id)
        if not source:
            raise ValueError(f"Project not found: {project_id}")

        # Create new project
        duplicate_name = new_name or f"{source.name} (Copy)"
        duplicate = self.create_project(
            name=duplicate_name,
            description=source.description,
            area_of_interest=source.area_of_interest,
            coordinate_system=source.coordinate_system,
            tags=json.loads(source.tags) if source.tags else None,
        )

        # Copy storage contents
        source_path = Path(source.storage_path)
        dest_path = Path(duplicate.storage_path)

        if source_path.exists():
            for item in source_path.iterdir():
                if item.is_dir():
                    dest_item = dest_path / item.name
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest_path / item.name)

        logger.info(
            "Project duplicated",
            source_id=project_id,
            new_id=duplicate.id,
            new_name=duplicate.name,
        )

        return duplicate

    def update_metadata(
        self,
        project_id: str,
        **kwargs,
    ) -> Project:
        """Update project metadata fields.

        Args:
            project_id: The project UUID.
            **kwargs: Fields to update.

        Returns:
            Updated project instance.
        """
        project = self.repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        # Update allowed fields
        allowed_fields = {
            "name",
            "description",
            "status",
            "current_stage",
            "current_task",
            "progress",
            "area_of_interest",
            "coordinate_system",
            "tags",
            "notes",
            "favorite",
            "archived",
            "completed_steps",
            "pending_steps",
            "last_opened_file",
            "last_viewed_map_position",
            "selected_layers",
            "dashboard_layout",
            "user_notes",
            "is_processing",
            "last_job_id",
            "last_job_status",
            "last_opened_at",
        }

        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(project, key):
                setattr(project, key, value)

        project = self.repository.update(project)

        # Auto-save metadata JSON
        self._save_metadata_json(project)

        return project

    def update_work_state(
        self,
        project_id: str,
        current_stage: str | None = None,
        current_task: str | None = None,
        progress: float | None = None,
        completed_steps: list | None = None,
        pending_steps: list | None = None,
        last_opened_file: str | None = None,
        last_viewed_map_position: dict | None = None,
        selected_layers: list | None = None,
        dashboard_layout: dict | None = None,
        user_notes: str | None = None,
    ) -> Project:
        """Update project work state (auto-saved).

        Args:
            project_id: The project UUID.
            **kwargs: Work state fields to update.

        Returns:
            Updated project instance.
        """
        updates = {}
        if current_stage is not None:
            updates["current_stage"] = current_stage
        if current_task is not None:
            updates["current_task"] = current_task
        if progress is not None:
            updates["progress"] = progress
        if completed_steps is not None:
            updates["completed_steps"] = json.dumps(completed_steps)
        if pending_steps is not None:
            updates["pending_steps"] = json.dumps(pending_steps)
        if last_opened_file is not None:
            updates["last_opened_file"] = last_opened_file
        if last_viewed_map_position is not None:
            updates["last_viewed_map_position"] = json.dumps(last_viewed_map_position)
        if selected_layers is not None:
            updates["selected_layers"] = json.dumps(selected_layers)
        if dashboard_layout is not None:
            updates["dashboard_layout"] = json.dumps(dashboard_layout)
        if user_notes is not None:
            updates["user_notes"] = user_notes

        return self.update_metadata(project_id, **updates)

    def start_processing(self, project_id: str, job_id: str) -> Project:
        """Mark project as processing.

        Args:
            project_id: The project UUID.
            job_id: The job identifier.

        Returns:
            Updated project instance.
        """
        return self.update_metadata(
            project_id,
            is_processing=True,
            last_job_id=job_id,
            last_job_status="running",
            status="processing",
        )

    def complete_processing(self, project_id: str) -> Project:
        """Mark project processing as completed.

        Args:
            project_id: The project UUID.

        Returns:
            Updated project instance.
        """
        return self.update_metadata(
            project_id,
            is_processing=False,
            last_job_status="completed",
            status="active",
            progress=100.0,
        )

    def fail_processing(self, project_id: str) -> Project:
        """Mark project processing as failed.

        Args:
            project_id: The project UUID.

        Returns:
            Updated project instance.
        """
        return self.update_metadata(
            project_id,
            is_processing=False,
            last_job_status="failed",
            status="failed",
        )

    def recover_interrupted_projects(self) -> list[Project]:
        """Find and mark interrupted projects for recovery.

        Returns:
            List of projects that were interrupted.
        """
        interrupted = self.repository.get_processing()
        recovered = []

        for project in interrupted:
            project.is_processing = False
            project.last_job_status = "interrupted"
            project.status = "active"
            project = self.repository.update(project)
            recovered.append(project)

            logger.info(
                "Project recovered from interruption",
                project_id=project.id,
                name=project.name,
            )

        return recovered

    def get_project_stats(self) -> dict:
        """Get project statistics.

        Returns:
            Dictionary with project counts.
        """
        return {
            "total": self.repository.count(include_archived=False),
            "archived": self.repository.count(include_archived=True)
            - self.repository.count(include_archived=False),
            "favorites": len(self.repository.get_favorites(limit=1000)),
            "processing": len(self.repository.get_processing()),
        }

    def _save_metadata_json(self, project: Project) -> None:
        """Save project metadata to JSON file for portability.

        Args:
            project: The project instance.
        """
        metadata_path = Path(project.storage_path) / "metadata" / "project.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        metadata = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "current_stage": project.current_stage,
            "current_task": project.current_task,
            "progress": project.progress,
            "area_of_interest": project.area_of_interest,
            "coordinate_system": project.coordinate_system,
            "tags": json.loads(project.tags) if project.tags else [],
            "notes": project.notes,
            "favorite": project.favorite,
            "archived": project.archived,
            "project_version": project.project_version,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "last_opened_at": project.last_opened_at.isoformat() if project.last_opened_at else None,
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
