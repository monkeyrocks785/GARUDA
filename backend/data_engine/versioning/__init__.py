"""Data Engine versioning - Track dataset versions."""

from sqlalchemy.orm import Session

from data_engine.database.datasets import Dataset
from data_engine.database.versions import DatasetVersion


def create_version(
    db: Session,
    dataset: Dataset,
    checksum: str,
    file_size: int,
    storage_path: str,
    internal_filename: str,
    change_description: str = "New version",
) -> DatasetVersion:
    """Create a new version entry for a dataset."""
    new_version = dataset.version + 1

    version = DatasetVersion(
        dataset_id=dataset.id,
        version_number=new_version,
        checksum=checksum,
        file_size=file_size,
        storage_path=storage_path,
        internal_filename=internal_filename,
        change_description=change_description,
    )
    db.add(version)

    # Update dataset version
    dataset.version = new_version
    dataset.checksum = checksum
    dataset.file_size = file_size
    dataset.storage_path = storage_path
    dataset.internal_filename = internal_filename

    db.commit()
    db.refresh(version)
    return version


def get_version_history(db: Session, dataset_id: str) -> list[DatasetVersion]:
    """Get version history for a dataset."""
    return (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
        .all()
    )


def get_latest_version(db: Session, dataset_id: str) -> DatasetVersion | None:
    """Get the latest version for a dataset."""
    return (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
        .first()
    )


def check_duplicate(db: Session, checksum: str, project_id: str) -> Dataset | None:
    """Check if a dataset with the same checksum exists in the project."""
    return (
        db.query(Dataset)
        .filter(
            Dataset.checksum == checksum,
            Dataset.project_id == project_id,
        )
        .first()
    )


def find_existing_by_name(db: Session, name: str, project_id: str) -> Dataset | None:
    """Find existing dataset with same name in project."""
    return (
        db.query(Dataset)
        .filter(
            Dataset.name == name,
            Dataset.project_id == project_id,
        )
        .first()
    )
