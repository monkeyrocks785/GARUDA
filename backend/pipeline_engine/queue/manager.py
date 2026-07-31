"""Queue Manager - Manages pipeline processing queue."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from pipeline_engine.database.models import Pipeline, PipelineQueue

logger = logging.getLogger("garuda.pipeline.queue")


class QueueManager:
    """Manages the processing queue for pipelines."""

    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, pipeline_id: str, priority: int = 0) -> PipelineQueue | None:
        """Add a pipeline to the queue."""
        pipeline = self.db.get(Pipeline, pipeline_id)
        if not pipeline:
            return None

        # Check if already in queue
        existing = (
            self.db.query(PipelineQueue)
            .filter(PipelineQueue.pipeline_id == pipeline_id)
            .first()
        )
        if existing:
            return existing

        # Get next position
        max_pos = self.db.query(PipelineQueue.position).filter(
            PipelineQueue.status.in_(["waiting", "running"])
        ).order_by(PipelineQueue.position.desc()).first()
        position = (max_pos[0] + 1) if max_pos else 1

        queue_entry = PipelineQueue(
            pipeline_id=pipeline_id,
            priority=priority,
            position=position,
            status="waiting",
        )
        self.db.add(queue_entry)

        pipeline.status = "queued"
        pipeline.priority = priority
        self.db.commit()

        logger.info(f"Pipeline {pipeline_id} enqueued at position {position}")
        return queue_entry

    def dequeue(self, pipeline_id: str) -> bool:
        """Remove a pipeline from the queue."""
        entry = (
            self.db.query(PipelineQueue)
            .filter(PipelineQueue.pipeline_id == pipeline_id)
            .first()
        )
        if not entry:
            return False

        pipeline = self.db.get(Pipeline, pipeline_id)
        if pipeline:
            pipeline.status = "pending"

        self.db.delete(entry)
        self.db.commit()
        return True

    def get_next(self) -> Pipeline | None:
        """Get the next pipeline to process (highest priority, oldest first)."""
        entry = (
            self.db.query(PipelineQueue)
            .filter(PipelineQueue.status == "waiting")
            .order_by(PipelineQueue.priority.desc(), PipelineQueue.position)
            .first()
        )
        if not entry:
            return None

        pipeline = self.db.get(Pipeline, entry.pipeline_id)
        if pipeline and pipeline.status == "queued":
            return pipeline

        return None

    def start_processing(self, pipeline_id: str, worker_id: str = "main") -> bool:
        """Mark a pipeline as currently processing."""
        entry = (
            self.db.query(PipelineQueue)
            .filter(PipelineQueue.pipeline_id == pipeline_id)
            .first()
        )
        if not entry:
            return False

        entry.status = "running"
        entry.worker_id = worker_id
        entry.started_at = datetime.utcnow()
        self.db.commit()

        pipeline = self.db.get(Pipeline, pipeline_id)
        if pipeline:
            pipeline.status = "running"
            self.db.commit()

        return True

    def complete_processing(self, pipeline_id: str, success: bool = True) -> bool:
        """Mark a pipeline as completed in queue."""
        entry = (
            self.db.query(PipelineQueue)
            .filter(PipelineQueue.pipeline_id == pipeline_id)
            .first()
        )
        if not entry:
            return False

        entry.status = "completed" if success else "failed"
        entry.completed_at = datetime.utcnow()
        self.db.commit()

        return True

    def pause(self, pipeline_id: str) -> bool:
        """Pause a queued pipeline."""
        entry = (
            self.db.query(PipelineQueue)
            .filter(PipelineQueue.pipeline_id == pipeline_id)
            .first()
        )
        if not entry:
            return False

        entry.status = "paused"
        self.db.commit()

        pipeline = self.db.get(Pipeline, pipeline_id)
        if pipeline:
            pipeline.status = "paused"
            self.db.commit()

        return True

    def resume(self, pipeline_id: str) -> bool:
        """Resume a paused pipeline."""
        entry = (
            self.db.query(PipelineQueue)
            .filter(PipelineQueue.pipeline_id == pipeline_id)
            .first()
        )
        if not entry:
            return False

        entry.status = "waiting"
        self.db.commit()

        pipeline = self.db.get(Pipeline, pipeline_id)
        if pipeline:
            pipeline.status = "queued"
            self.db.commit()

        return True

    def cancel(self, pipeline_id: str) -> bool:
        """Cancel a queued pipeline."""
        entry = (
            self.db.query(PipelineQueue)
            .filter(PipelineQueue.pipeline_id == pipeline_id)
            .first()
        )
        if not entry:
            return False

        entry.status = "cancelled"
        self.db.commit()

        pipeline = self.db.get(Pipeline, pipeline_id)
        if pipeline:
            pipeline.status = "cancelled"
            self.db.commit()

        return True

    def get_queue_status(self) -> dict:
        """Get queue statistics."""
        entries = self.db.query(PipelineQueue).all()
        return {
            "waiting": sum(1 for e in entries if e.status == "waiting"),
            "running": sum(1 for e in entries if e.status == "running"),
            "paused": sum(1 for e in entries if e.status == "paused"),
            "completed": sum(1 for e in entries if e.status == "completed"),
            "failed": sum(1 for e in entries if e.status == "failed"),
            "cancelled": sum(1 for e in entries if e.status == "cancelled"),
            "total": len(entries),
        }

    def get_all_entries(self, status: str | None = None) -> list:
        """Get all queue entries, optionally filtered by status."""
        q = self.db.query(PipelineQueue)
        if status:
            q = q.filter(PipelineQueue.status == status)
        return q.order_by(PipelineQueue.priority.desc(), PipelineQueue.position).all()
