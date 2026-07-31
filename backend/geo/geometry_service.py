"""Geometry service for spatial operations."""


import pyproj
from shapely.geometry import mapping, shape
from shapely.ops import transform
from shapely.validation import make_valid


class GeometryService:
    """Service for geometry operations and validation."""

    @staticmethod
    def validate_geometry(geometry_geojson: dict) -> tuple[bool, str | None, str | None]:
        """Validate a GeoJSON geometry.

        Args:
            geometry_geojson: GeoJSON geometry dictionary.

        Returns:
            Tuple of (is_valid, geometry_type, error_message).
        """
        try:
            geom = shape(geometry_geojson)
            if geom.is_valid:
                return True, geom.geom_type, None
            else:
                # Try to fix invalid geometry
                fixed = make_valid(geom)
                if fixed.is_valid:
                    return True, fixed.geom_type, None
                return False, None, "Invalid geometry that cannot be auto-repaired"
        except Exception as e:
            return False, None, f"Invalid GeoJSON: {str(e)}"

    @staticmethod
    def calculate_area(geometry_geojson: dict, units: str = "meters") -> float:
        """Calculate area of a geometry.

        Args:
            geometry_geojson: GeoJSON geometry dictionary.
            units: Output units ('meters' or 'degrees').

        Returns:
            Area in specified units.
        """
        geom = shape(geometry_geojson)

        if units == "meters":
            # Project to equal area projection (UTM)
            project = pyproj.Transformer.from_crs(
                "EPSG:4326", "EPSG:3857", always_xy=True
            ).transform
            geom_projected = transform(project, geom)
            return geom_projected.area
        else:
            return geom.area

    @staticmethod
    def calculate_bbox(geometry_geojson: dict) -> list[float]:
        """Calculate bounding box of a geometry.

        Args:
            geometry_geojson: GeoJSON geometry dictionary.

        Returns:
            Bounding box as [min_lng, min_lat, max_lng, max_lat].
        """
        geom = shape(geometry_geojson)
        bounds = geom.bounds  # (minx, miny, maxx, maxy)
        return [bounds[0], bounds[1], bounds[2], bounds[3]]

    @staticmethod
    def transform_geometry(
        geometry_geojson: dict,
        from_crs: str = "EPSG:4326",
        to_crs: str = "EPSG:4326",
    ) -> dict:
        """Transform geometry between coordinate systems.

        Args:
            geometry_geojson: GeoJSON geometry dictionary.
            from_crs: Source CRS.
            to_crs: Target CRS.

        Returns:
            Transformed GeoJSON geometry.
        """
        if from_crs == to_crs:
            return geometry_geojson

        geom = shape(geometry_geojson)
        project = pyproj.Transformer.from_crs(
            from_crs, to_crs, always_xy=True
        ).transform
        transformed = transform(project, geom)
        return mapping(transformed)

    @staticmethod
    def simplify_geometry(geometry_geojson: dict, tolerance: float = 0.0001) -> dict:
        """Simplify geometry to reduce vertex count.

        Args:
            geometry_geojson: GeoJSON geometry dictionary.
            tolerance: Simplification tolerance.

        Returns:
            Simplified GeoJSON geometry.
        """
        geom = shape(geometry_geojson)
        simplified = geom.simplify(tolerance, preserve_topology=True)
        return mapping(simplified)

    @staticmethod
    def get_geometry_center(geometry_geojson: dict) -> tuple[float, float]:
        """Get the centroid of a geometry.

        Args:
            geometry_geojson: GeoJSON geometry dictionary.

        Returns:
            Tuple of (latitude, longitude).
        """
        geom = shape(geometry_geojson)
        centroid = geom.centroid
        return centroid.y, centroid.x
