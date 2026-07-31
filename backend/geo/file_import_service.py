"""File import service for KML, GeoJSON, and Shapefile."""

import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
from loguru import logger
from sqlalchemy.orm import Session

from config.settings import settings
from geo.geometry_service import GeometryService
from models.imported_file import ImportedFile
from models.layer import Layer
from repositories.imported_file_repository import ImportedFileRepository


class FileImportService:
    """Service for importing geospatial files."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = ImportedFileRepository(db)
        self.geometry_service = GeometryService()

    def import_geojson(
        self,
        project_id: str,
        file_content: str,
        filename: str,
    ) -> tuple[ImportedFile, Layer]:
        """Import a GeoJSON file.

        Args:
            project_id: Project UUID.
            file_content: GeoJSON file content.
            filename: Original filename.

        Returns:
            Tuple of (ImportedFile, Layer).

        Raises:
            ValueError: If file is invalid.
        """
        try:
            # Parse GeoJSON
            geojson = json.loads(file_content)

            # Handle FeatureCollection or single Feature
            if geojson.get("type") == "FeatureCollection":
                features = geojson.get("features", [])
            elif geojson.get("type") == "Feature":
                features = [geojson]
            else:
                raise ValueError("Invalid GeoJSON: must be Feature or FeatureCollection")

            if not features:
                raise ValueError("GeoJSON contains no features")

            # Validate geometries
            geometry_types = set()
            for feature in features:
                if "geometry" not in feature:
                    continue
                is_valid, geom_type, error = self.geometry_service.validate_geometry(
                    feature["geometry"]
                )
                if not is_valid:
                    raise ValueError(f"Invalid geometry in feature: {error}")
                geometry_types.add(geom_type)

            # Save file
            project_path = Path(settings.PROJECTS_DIR) / project_id / "vectors"
            project_path.mkdir(parents=True, exist_ok=True)

            file_id = str(__import__("uuid").uuid4())
            saved_filename = f"{file_id}.geojson"
            file_path = project_path / saved_filename

            with open(file_path, "w") as f:
                f.write(file_content)

            # Create imported file record
            imported_file = ImportedFile(
                id=file_id,
                project_id=project_id,
                filename=saved_filename,
                original_filename=filename,
                file_type="geojson",
                file_size=len(file_content.encode()),
                storage_path=str(file_path),
                geometry_type=", ".join(geometry_types) if geometry_types else None,
                feature_count=len(features),
                is_valid=True,
            )
            imported_file = self.repository.create(imported_file)

            # Create layer
            layer = Layer(
                project_id=project_id,
                name=Path(filename).stem,
                layer_type="vector",
                source_id=file_id,
                source_type="imported_file",
            )
            self.db.add(layer)
            self.db.commit()
            self.db.refresh(layer)

            # Update imported file with layer reference
            imported_file.layer_id = layer.id
            self.repository.update(imported_file)

            logger.info(
                "GeoJSON imported",
                file_id=file_id,
                filename=filename,
                feature_count=len(features),
                project_id=project_id,
            )

            return imported_file, layer

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to import GeoJSON: {str(e)}")

    def import_kml(
        self,
        project_id: str,
        file_content: str,
        filename: str,
    ) -> tuple[ImportedFile, Layer]:
        """Import a KML file.

        Args:
            project_id: Project UUID.
            file_content: KML file content.
            filename: Original filename.

        Returns:
            Tuple of (ImportedFile, Layer).

        Raises:
            ValueError: If file is invalid.
        """
        try:

            # Save KML temporarily
            with tempfile.NamedTemporaryFile(mode="w", suffix=".kml", delete=False) as f:
                f.write(file_content)
                temp_path = f.name

            try:
                # Read KML using fiona
                gdf = gpd.read_file(temp_path, driver="KML")

                if gdf.empty:
                    raise ValueError("KML file contains no features")

                # Save as GeoJSON for internal use
                project_path = Path(settings.PROJECTS_DIR) / project_id / "vectors"
                project_path.mkdir(parents=True, exist_ok=True)

                file_id = str(__import__("uuid").uuid4())
                saved_filename = f"{file_id}.geojson"
                file_path = project_path / saved_filename

                gdf.to_file(file_path, driver="GeoJSON")

                # Get geometry info
                geometry_types = set(gdf.geometry.geom_type.tolist())
                feature_count = len(gdf)

                # Create imported file record
                imported_file = ImportedFile(
                    id=file_id,
                    project_id=project_id,
                    filename=saved_filename,
                    original_filename=filename,
                    file_type="kml",
                    file_size=len(file_content.encode()),
                    storage_path=str(file_path),
                    geometry_type=", ".join(geometry_types),
                    feature_count=feature_count,
                    is_valid=True,
                )
                imported_file = self.repository.create(imported_file)

                # Create layer
                layer = Layer(
                    project_id=project_id,
                    name=Path(filename).stem,
                    layer_type="vector",
                    source_id=file_id,
                    source_type="imported_file",
                )
                self.db.add(layer)
                self.db.commit()
                self.db.refresh(layer)

                # Update imported file with layer reference
                imported_file.layer_id = layer.id
                self.repository.update(imported_file)

                logger.info(
                    "KML imported",
                    file_id=file_id,
                    filename=filename,
                    feature_count=feature_count,
                    project_id=project_id,
                )

                return imported_file, layer

            finally:
                os.unlink(temp_path)

        except Exception as e:
            raise ValueError(f"Failed to import KML: {str(e)}")

    def import_shapefile(
        self,
        project_id: str,
        zip_content: bytes,
        filename: str,
    ) -> tuple[ImportedFile, Layer]:
        """Import a Shapefile (ZIP containing .shp, .dbf, .shx, .prj).

        Args:
            project_id: Project UUID.
            zip_content: ZIP file content.
            filename: Original filename.

        Returns:
            Tuple of (ImportedFile, Layer).

        Raises:
            ValueError: If file is invalid.
        """
        try:

            # Extract ZIP to temporary directory
            temp_dir = tempfile.mkdtemp()
            try:
                zip_path = os.path.join(temp_dir, "shapefile.zip")
                with open(zip_path, "wb") as f:
                    f.write(zip_content)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Find .shp file
                shp_files = list(Path(temp_dir).glob("**/*.shp"))
                if not shp_files:
                    raise ValueError("No .shp file found in ZIP archive")

                shp_path = shp_files[0]

                # Read shapefile
                gdf = gpd.read_file(shp_path)

                if gdf.empty:
                    raise ValueError("Shapefile contains no features")

                # Save as GeoJSON for internal use
                project_path = Path(settings.PROJECTS_DIR) / project_id / "vectors"
                project_path.mkdir(parents=True, exist_ok=True)

                file_id = str(__import__("uuid").uuid4())
                saved_filename = f"{file_id}.geojson"
                file_path = project_path / saved_filename

                gdf.to_file(file_path, driver="GeoJSON")

                # Get geometry info
                geometry_types = set(gdf.geometry.geom_type.tolist())
                feature_count = len(gdf)

                # Create imported file record
                imported_file = ImportedFile(
                    id=file_id,
                    project_id=project_id,
                    filename=saved_filename,
                    original_filename=filename,
                    file_type="shapefile",
                    file_size=len(zip_content),
                    storage_path=str(file_path),
                    geometry_type=", ".join(geometry_types),
                    feature_count=feature_count,
                    is_valid=True,
                )
                imported_file = self.repository.create(imported_file)

                # Create layer
                layer = Layer(
                    project_id=project_id,
                    name=Path(filename).stem,
                    layer_type="vector",
                    source_id=file_id,
                    source_type="imported_file",
                )
                self.db.add(layer)
                self.db.commit()
                self.db.refresh(layer)

                # Update imported file with layer reference
                imported_file.layer_id = layer.id
                self.repository.update(imported_file)

                logger.info(
                    "Shapefile imported",
                    file_id=file_id,
                    filename=filename,
                    feature_count=feature_count,
                    project_id=project_id,
                )

                return imported_file, layer

            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        except Exception as e:
            raise ValueError(f"Failed to import Shapefile: {str(e)}")

    def get_imported_files(self, project_id: str) -> list[ImportedFile]:
        """Get all imported files for a project."""
        return self.repository.get_by_project(project_id)

    def delete_imported_file(self, file_id: str) -> None:
        """Delete an imported file."""
        imported_file = self.repository.get_by_id(file_id)
        if not imported_file:
            raise ValueError(f"Imported file not found: {file_id}")

        # Delete file from storage
        file_path = Path(imported_file.storage_path)
        if file_path.exists():
            os.unlink(file_path)

        # Delete associated layer
        if imported_file.layer_id:
            layer = self.db.query(Layer).filter(Layer.id == imported_file.layer_id).first()
            if layer:
                self.db.delete(layer)

        self.repository.delete(imported_file)

        logger.info("Imported file deleted", file_id=file_id, filename=imported_file.filename)
