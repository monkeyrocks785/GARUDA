"""Data Engine indexer - Index datasets for fast search."""

from sqlalchemy.orm import Session

from data_engine.catalog import get_dataset_stats
from data_engine.database.datasets import Dataset


def index_dataset(db: Session, dataset_id: str) -> dict:
    """Index a single dataset for search."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return {"error": "Dataset not found"}

    # Update status to indexed
    dataset.status = "indexed"
    db.commit()

    return {
        "id": dataset.id,
        "name": dataset.name,
        "type": dataset.dataset_type,
        "extension": dataset.extension,
        "status": "indexed",
    }


def index_project_datasets(db: Session, project_id: str) -> dict:
    """Index all datasets in a project."""
    datasets = db.query(Dataset).filter(
        Dataset.project_id == project_id,
        Dataset.status != "indexed",
    ).all()

    indexed = 0
    for dataset in datasets:
        dataset.status = "indexed"
        indexed += 1

    db.commit()

    stats = get_dataset_stats(db, project_id)
    return {
        "indexed": indexed,
        "total": stats["total"],
    }
