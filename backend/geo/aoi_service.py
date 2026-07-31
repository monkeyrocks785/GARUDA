"""AOI service for managing Areas of Interest."""

import json

from loguru import logger
from sqlalchemy.orm import Session

from geo.geometry_service import GeometryService
from models.aoi import AOI
from repositories.aoi_repository import AOIRepository


class AOIService:
    """Service for AOI operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = AOIRepository(db)
        self.geometry_service = GeometryService()

    def create_aoi(
        self,
        project_id: str,
        name: str,
        geometry: dict,
        description: str | None = None,
        fill_color: str = "#3388ff",
        fill_opacity: float = 0.2,
        stroke_color: str = "#3388ff",
        stroke_width: float = 2.0,
        source: str = "manual",
        source_file: str | None = None,
    ) -> AOI:
        """Create a new AOI.

        Args:
            project_id: Project UUID.
            name: AOI name.
            geometry: GeoJSON geometry.
            description: Optional description.
            fill_color: Fill color hex.
            fill_opacity: Fill opacity.
            stroke_color: Stroke color hex.
            stroke_width: Stroke width.
            source: Source type (manual, kml, geojson, shapefile).
            source_file: Source filename.

        Returns:
            Created AOI instance.

        Raises:
            ValueError: If geometry is invalid.
        """
        # Validate geometry
        is_valid, geom_type, error = self.geometry_service.validate_geometry(geometry)
        if not is_valid:
            raise ValueError(f"Invalid geometry: {error}")

        # Calculate properties
        bbox = self.geometry_service.calculate_bbox(geometry)
        area_m2 = self.geometry_service.calculate_area(geometry, units="meters")

        aoi = AOI(
            project_id=project_id,
            name=name,
            description=description,
            geometry=json.dumps(geometry),
            geometry_type=geom_type,
            bbox=json.dumps(bbox),
            area_m2=area_m2,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            source=source,
            source_file=source_file,
        )

        aoi = self.repository.create(aoi)

        logger.info(
            "AOI created",
            aoi_id=aoi.id,
            name=aoi.name,
            project_id=project_id,
            geometry_type=geom_type,
        )

        return aoi

    def get_aoi(self, aoi_id: str) -> AOI | None:
        """Get an AOI by ID."""
        return self.repository.get_by_id(aoi_id)

    def get_project_aois(self, project_id: str) -> list[AOI]:
        """Get all AOIs for a project."""
        return self.repository.get_by_project(project_id)

    def update_aoi(
        self,
        aoi_id: str,
        name: str | None = None,
        description: str | None = None,
        geometry: dict | None = None,
        fill_color: str | None = None,
        fill_opacity: float | None = None,
        stroke_color: str | None = None,
        stroke_width: float | None = None,
    ) -> AOI:
        """Update an AOI.

        Args:
            aoi_id: AOI UUID.
            **kwargs: Fields to update.

        Returns:
            Updated AOI instance.

        Raises:
            ValueError: If AOI not found or geometry invalid.
        """
        aoi = self.repository.get_by_id(aoi_id)
        if not aoi:
            raise ValueError(f"AOI not found: {aoi_id}")

        if name is not None:
            aoi.name = name
        if description is not None:
            aoi.description = description
        if geometry is not None:
            is_valid, geom_type, error = self.geometry_service.validate_geometry(geometry)
            if not is_valid:
                raise ValueError(f"Invalid geometry: {error}")
            aoi.geometry = json.dumps(geometry)
            aoi.geometry_type = geom_type
            aoi.bbox = json.dumps(self.geometry_service.calculate_bbox(geometry))
            aoi.area_m2 = self.geometry_service.calculate_area(geometry)
        if fill_color is not None:
            aoi.fill_color = fill_color
        if fill_opacity is not None:
            aoi.fill_opacity = fill_opacity
        if stroke_color is not None:
            aoi.stroke_color = stroke_color
        if stroke_width is not None:
            aoi.stroke_width = stroke_width

        aoi = self.repository.update(aoi)

        logger.info("AOI updated", aoi_id=aoi.id, name=aoi.name)

        return aoi

    def delete_aoi(self, aoi_id: str) -> None:
        """Delete an AOI.

        Args:
            aoi_id: AOI UUID.

        Raises:
            ValueError: If AOI not found.
        """
        aoi = self.repository.get_by_id(aoi_id)
        if not aoi:
            raise ValueError(f"AOI not found: {aoi_id}")

        logger.info("AOI deleted", aoi_id=aoi_id, name=aoi.name)

        self.repository.delete(aoi)

    def get_aoi_geometry(self, aoi_id: str) -> dict | None:
        """Get AOI geometry as GeoJSON."""
        aoi = self.repository.get_by_id(aoi_id)
        if not aoi:
            return None
        return json.loads(aoi.geometry)

    def calculate_distance(self, geom1: dict, geom2: dict) -> float:
        """Calculate distance between two geometries in meters."""
        from shapely.geometry import shape

        g1 = shape(geom1)
        g2 = shape(geom2)

        # Project to appropriate CRS for distance calculation
        import pyproj
        from shapely.ops import transform

        project = pyproj.Transformer.from_crs(
            "EPSG:4326", "EPSG:3857", always_xy=True
        ).transform

        g1_projected = transform(project, g1)
        g2_projected = transform(project, g2)

        return g1_projected.distance(g2_projected)
