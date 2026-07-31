"""Vector feature service - serves simplified, projected GeoJSON for display."""

from __future__ import annotations

import json

import geopandas as gpd
from loguru import logger
from sqlalchemy.orm import Session

from assets.database.assets import Asset
from geo.secure_paths import is_allowed_location
from models.aoi import AOI
from models.imported_file import ImportedFile
from models.layer import Layer


class LayerFeaturesService:
    """Resolve a layer's source data into a browser-friendly FeatureCollection."""

    def __init__(self, db: Session):
        self.db = db

    def _is_allowed_path(self, raw_path: str) -> bool:
        """Reject paths that escape the configured GARUDA data locations."""
        return is_allowed_location(raw_path)

    def _resolve_source_path(self, layer: Layer) -> str | None:
        """Return the on-disk path backing a layer, or ``None`` for AOI layers."""
        source_type = layer.source_type or ""

        if source_type == "aoi" or layer.layer_type == "aoi":
            return None

        if source_type == "imported_file" and layer.source_id:
            imported = (
                self.db.query(ImportedFile)
                .filter(ImportedFile.id == layer.source_id)
                .first()
            )
            if not imported or not imported.storage_path:
                raise ValueError("Layer source file not found")
            if not self._is_allowed_path(imported.storage_path):
                raise ValueError("Layer source path is outside allowed locations")
            return imported.storage_path

        if source_type == "asset" and layer.source_id:
            asset = (
                self.db.query(Asset)
                .filter(Asset.id == layer.source_id, Asset.is_archived == False)  # noqa: E712
                .first()
            )
            if not asset or not asset.storage_path:
                raise ValueError("Layer source asset not found")
            if not self._is_allowed_path(asset.storage_path):
                raise ValueError("Layer source path is outside allowed locations")
            return asset.storage_path

        if layer.source_id:
            raise ValueError(f"Unsupported layer source type: {source_type}")
        raise ValueError("Layer has no source data")

    def _aoi_feature_collection(self, layer: Layer) -> dict:
        aoi = self.db.query(AOI).filter(AOI.id == layer.source_id).first()
        if not aoi:
            raise ValueError("AOI not found for layer")
        geometry = json.loads(aoi.geometry)
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": aoi.id,
                        "name": aoi.name,
                        "geometry_type": aoi.geometry_type,
                        "area_m2": aoi.area_m2,
                        "fill_color": aoi.fill_color,
                    },
                }
            ],
            "crs": layer.crs or "EPSG:4326",
        }

    def get_feature_collection(
        self,
        layer: Layer,
        max_features: int = 2000,
        simplify: bool = True,
        tolerance: float | None = None,
    ) -> dict:
        """Return a FeatureCollection for a vector layer.

        Reprojects to EPSG:4326, optionally simplifies geometries, and caps the
        number of features so the browser can render without freezing.
        """
        path = self._resolve_source_path(layer)
        if path is None:
            return self._aoi_feature_collection(layer)

        try:
            gdf = gpd.read_file(path)
        except Exception as e:
            raise ValueError(f"Failed to read vector source: {e}") from e

        if gdf.empty:
            return {"type": "FeatureCollection", "features": [], "crs": "EPSG:4326"}

        # Project to WGS84 for display.
        if gdf.crs is not None and str(gdf.crs).upper() != "EPSG:4326":
            try:
                gdf = gdf.to_crs("EPSG:4326")
            except Exception as e:
                raise ValueError(f"Failed to reproject layer: {e}") from e

        # Simplify to keep the browser responsive on dense vectors.
        if simplify and tolerance is None:
            if gdf.crs is None:
                tolerance = 0.0001
            else:
                total_bounds = gdf.total_bounds
                extent = max(
                    total_bounds[2] - total_bounds[0],
                    total_bounds[3] - total_bounds[1],
                    1e-9,
                )
                tolerance = extent / 2000.0

        if simplify and tolerance:
            try:
                gdf.geometry = gdf.geometry.simplify(
                    tolerance, preserve_topology=True
                )
            except Exception:
                logger.warning("Layer simplification failed", layer_id=layer.id)

        returned_count = len(gdf)
        if returned_count > max_features:
            step = max(1, returned_count // max_features)
            gdf = gdf.iloc[::step]

        try:
            collection = gdf.__geo_interface__
        except Exception as e:
            raise ValueError(f"Failed to serialize features: {e}") from e

        collection["crs"] = "EPSG:4326"
        collection["simplified"] = bool(simplify and tolerance)
        collection["returned_count"] = len(collection["features"])
        return collection
