"""Data Engine catalog - Search, filter, and organize datasets."""

import json
from typing import Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from data_engine.database.datasets import Dataset
from data_engine.database.tags import DatasetTag


def search_datasets(
    db: Session,
    project_id: str,
    query: str | None = None,
    dataset_type: str | None = None,
    extension: str | None = None,
    tags: list[str] | None = None,
    status: str | None = None,
    favorite_only: bool = False,
    archived_only: bool = False,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[Dataset], int]:
    """Search datasets with filters."""
    q = db.query(Dataset).filter(Dataset.project_id == project_id)

    # Text search
    if query:
        search = f"%{query}%"
        q = q.filter(
            or_(
                Dataset.name.ilike(search),
                Dataset.original_filename.ilike(search),
                Dataset.description.ilike(search),
            )
        )

    # Type filter
    if dataset_type:
        q = q.filter(Dataset.dataset_type == dataset_type)

    # Extension filter
    if extension:
        q = q.filter(Dataset.extension == extension)

    # Status filter
    if status:
        q = q.filter(Dataset.status == status)

    # Favorites
    if favorite_only:
        q = q.filter(Dataset.is_favorite == True)

    # Archived
    if archived_only:
        q = q.filter(Dataset.is_archived == True)
    else:
        q = q.filter(Dataset.is_archived == False)

    # Tag filter
    if tags:
        tag_subq = (
            db.query(DatasetTag.dataset_id)
            .filter(DatasetTag.tag.in_(tags))
            .subquery()
        )
        q = q.filter(Dataset.id.in_(tag_subq))

    # Count total
    total = q.count()

    # Sort
    sort_column = getattr(Dataset, sort_by, Dataset.created_at)
    if sort_order == "desc":
        q = q.order_by(desc(sort_column))
    else:
        q = q.order_by(sort_column)

    # Paginate
    datasets = q.offset(offset).limit(limit).all()

    return datasets, total


def get_dataset(db: Session, dataset_id: str) -> Dataset | None:
    """Get a single dataset by ID."""
    return db.query(Dataset).filter(Dataset.id == dataset_id).first()


def get_recent_datasets(db: Session, project_id: str, limit: int = 10) -> list[Dataset]:
    """Get recently imported datasets."""
    return (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id, Dataset.is_archived == False)
        .order_by(desc(Dataset.imported_at))
        .limit(limit)
        .all()
    )


def get_favorite_datasets(db: Session, project_id: str) -> list[Dataset]:
    """Get favorite datasets."""
    return (
        db.query(Dataset)
        .filter(
            Dataset.project_id == project_id,
            Dataset.is_favorite == True,
            Dataset.is_archived == False,
        )
        .order_by(desc(Dataset.modified_at))
        .all()
    )


def get_datasets_by_type(db: Session, project_id: str, dataset_type: str) -> list[Dataset]:
    """Get all datasets of a specific type."""
    return (
        db.query(Dataset)
        .filter(
            Dataset.project_id == project_id,
            Dataset.dataset_type == dataset_type,
            Dataset.is_archived == False,
        )
        .order_by(desc(Dataset.created_at))
        .all()
    )


def get_datasets_by_extension(db: Session, project_id: str, extension: str) -> list[Dataset]:
    """Get all datasets with a specific extension."""
    return (
        db.query(Dataset)
        .filter(
            Dataset.project_id == project_id,
            Dataset.extension == extension,
            Dataset.is_archived == False,
        )
        .order_by(desc(Dataset.created_at))
        .all()
    )


def get_dataset_stats(db: Session, project_id: str) -> dict:
    """Get dataset statistics for a project."""
    total = db.query(func.count(Dataset.id)).filter(
        Dataset.project_id == project_id,
        Dataset.is_archived == False,
    ).scalar() or 0

    by_type = dict(
        db.query(Dataset.dataset_type, func.count(Dataset.id))
        .filter(Dataset.project_id == project_id, Dataset.is_archived == False)
        .group_by(Dataset.dataset_type)
        .all()
    )

    by_extension = dict(
        db.query(Dataset.extension, func.count(Dataset.id))
        .filter(Dataset.project_id == project_id, Dataset.is_archived == False)
        .group_by(Dataset.extension)
        .all()
    )

    total_size = db.query(func.sum(Dataset.file_size)).filter(
        Dataset.project_id == project_id,
        Dataset.is_archived == False,
    ).scalar() or 0

    return {
        "total": total,
        "by_type": by_type,
        "by_extension": by_extension,
        "total_size_bytes": total_size,
    }


def add_tag(db: Session, dataset_id: str, tag: str) -> bool:
    """Add a tag to a dataset."""
    existing = (
        db.query(DatasetTag)
        .filter(DatasetTag.dataset_id == dataset_id, DatasetTag.tag == tag)
        .first()
    )
    if existing:
        return False

    tag_entry = DatasetTag(dataset_id=dataset_id, tag=tag)
    db.add(tag_entry)
    db.commit()
    return True


def remove_tag(db: Session, dataset_id: str, tag: str) -> bool:
    """Remove a tag from a dataset."""
    tag_entry = (
        db.query(DatasetTag)
        .filter(DatasetTag.dataset_id == dataset_id, DatasetTag.tag == tag)
        .first()
    )
    if tag_entry:
        db.delete(tag_entry)
        db.commit()
        return True
    return False


def get_dataset_tags(db: Session, dataset_id: str) -> list[str]:
    """Get all tags for a dataset."""
    tags = (
        db.query(DatasetTag.tag)
        .filter(DatasetTag.dataset_id == dataset_id)
        .all()
    )
    return [t[0] for t in tags]


def toggle_favorite(db: Session, dataset_id: str) -> bool:
    """Toggle favorite status of a dataset."""
    dataset = get_dataset(db, dataset_id)
    if dataset:
        dataset.is_favorite = not dataset.is_favorite
        db.commit()
        return dataset.is_favorite
    return False
