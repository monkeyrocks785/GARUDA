"""Map state service for persistence."""

import json

from loguru import logger
from sqlalchemy.orm import Session

from models.map_state import ProjectMapState


class MapStateService:
    """Service for map state persistence."""

    def __init__(self, db: Session):
        self.db = db

    def get_map_state(self, project_id: str) -> ProjectMapState:
        """Get or create map state for a project.

        Args:
            project_id: Project UUID.

        Returns:
            ProjectMapState instance.
        """
        state = (
            self.db.query(ProjectMapState)
            .filter(ProjectMapState.project_id == project_id)
            .first()
        )

        if not state:
            # Create default state
            state = ProjectMapState(project_id=project_id)
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)

            logger.info("Created default map state", project_id=project_id)

        return state

    def update_map_state(
        self,
        project_id: str,
        zoom: float | None = None,
        center_lat: float | None = None,
        center_lng: float | None = None,
        map_rotation: float | None = None,
        basemap: str | None = None,
        visible_layers: list[str] | None = None,
        selected_layer_id: str | None = None,
        sidebar_width: int | None = None,
        panel_visible: bool | None = None,
        active_tool: str | None = None,
    ) -> ProjectMapState:
        """Update map state.

        Args:
            project_id: Project UUID.
            **kwargs: Fields to update.

        Returns:
            Updated ProjectMapState instance.
        """
        state = self.get_map_state(project_id)

        if zoom is not None:
            state.zoom = zoom
        if center_lat is not None:
            state.center_lat = center_lat
        if center_lng is not None:
            state.center_lng = center_lng
        if map_rotation is not None:
            state.map_rotation = map_rotation
        if basemap is not None:
            state.basemap = basemap
        if visible_layers is not None:
            state.visible_layers = json.dumps(visible_layers)
        if selected_layer_id is not None:
            state.selected_layer_id = selected_layer_id
        if sidebar_width is not None:
            state.sidebar_width = sidebar_width
        if panel_visible is not None:
            state.panel_visible = panel_visible
        if active_tool is not None:
            state.active_tool = active_tool

        self.db.commit()
        self.db.refresh(state)

        return state

    def delete_map_state(self, project_id: str) -> None:
        """Delete map state for a project."""
        state = (
            self.db.query(ProjectMapState)
            .filter(ProjectMapState.project_id == project_id)
            .first()
        )

        if state:
            self.db.delete(state)
            self.db.commit()
            logger.info("Deleted map state", project_id=project_id)
