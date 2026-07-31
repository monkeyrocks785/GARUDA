"""Data Engine validators - Validate datasets before import."""

from pathlib import Path
from typing import Optional

from data_engine.config import ALL_EXTENSIONS, RASTER_EXTENSIONS, VECTOR_EXTENSIONS
from data_engine.utils import compute_checksum, get_file_extension


class ValidationResult:
    """Result of a validation check."""

    def __init__(self):
        self.is_valid = True
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def validate_file_exists(file_path: Path) -> ValidationResult:
    """Validate that file exists and is accessible."""
    result = ValidationResult()
    if not file_path.exists():
        result.add_error(f"File not found: {file_path}")
    elif not file_path.is_file():
        result.add_error(f"Not a file: {file_path}")
    elif not file_path.stat().st_size > 0:
        result.add_error(f"File is empty: {file_path}")
    return result


def validate_extension(filename: str) -> ValidationResult:
    """Validate file extension is supported."""
    result = ValidationResult()
    ext = get_file_extension(filename)
    if ext not in ALL_EXTENSIONS:
        result.add_error(f"Unsupported extension: {ext}")
        result.add_warning(f"Supported extensions: {', '.join(sorted(ALL_EXTENSIONS)[:10])}...")
    return result


def validate_file_readable(file_path: Path) -> ValidationResult:
    """Validate file is readable."""
    result = ValidationResult()
    try:
        with open(file_path, "rb") as f:
            f.read(1024)
    except PermissionError:
        result.add_error(f"Permission denied: {file_path}")
    except Exception as e:
        result.add_error(f"Cannot read file: {e}")
    return result


def validate_checksum(file_path: Path, expected: str | None = None) -> ValidationResult:
    """Validate file checksum."""
    result = ValidationResult()
    try:
        actual = compute_checksum(file_path)
        if expected and actual != expected:
            result.add_error(f"Checksum mismatch: expected {expected}, got {actual}")
    except Exception as e:
        result.add_error(f"Checksum computation failed: {e}")
    return result


def validate_raster_metadata(file_path: Path) -> ValidationResult:
    """Validate raster file metadata."""
    result = ValidationResult()
    ext = get_file_extension(file_path)

    if ext in RASTER_EXTENSIONS:
        try:
            import rasterio
            with rasterio.open(str(file_path)) as src:
                if src.width <= 0 or src.height <= 0:
                    result.add_error("Invalid raster dimensions")
                if src.count <= 0:
                    result.add_error("Raster has no bands")
        except ImportError:
            result.add_warning("rasterio not installed, skipping raster validation")
        except Exception as e:
            result.add_error(f"Invalid raster file: {e}")

    return result


def validate_vector_geometry(file_path: Path) -> ValidationResult:
    """Validate vector file geometry."""
    result = ValidationResult()
    ext = get_file_extension(file_path)

    if ext in VECTOR_EXTENSIONS:
        try:
            import geopandas as gpd
            gdf = gpd.read_file(str(file_path))
            if len(gdf) == 0:
                result.add_warning("Vector file has no features")
        except ImportError:
            result.add_warning("geopandas not installed, skipping vector validation")
        except Exception as e:
            result.add_error(f"Invalid vector file: {e}")

    return result


def validate_dataset(file_path: Path) -> ValidationResult:
    """Run all validations on a dataset."""
    result = ValidationResult()

    # File existence
    file_result = validate_file_exists(file_path)
    if not file_result.is_valid:
        result.errors.extend(file_result.errors)
        return result

    # Extension
    ext_result = validate_extension(file_path.name)
    result.errors.extend(ext_result.errors)
    result.warnings.extend(ext_result.warnings)

    # Readability
    read_result = validate_file_readable(file_path)
    result.errors.extend(read_result.errors)

    # Type-specific validation
    ext = get_file_extension(file_path)
    if ext in RASTER_EXTENSIONS:
        raster_result = validate_raster_metadata(file_path)
        result.errors.extend(raster_result.errors)
        result.warnings.extend(raster_result.warnings)
    elif ext in VECTOR_EXTENSIONS:
        vector_result = validate_vector_geometry(file_path)
        result.errors.extend(vector_result.errors)
        result.warnings.extend(vector_result.warnings)

    result.is_valid = len(result.errors) == 0
    return result
