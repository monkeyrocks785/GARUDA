"""Pipeline Services - High-level service layer."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from pipeline_engine.database.models import Pipeline, PipelineHistory, PipelineLog, PipelineNode
from pipeline_engine.pipeline.runner import PipelineRunner
from pipeline_engine.queue.manager import QueueManager

logger = logging.getLogger("garuda.pipeline.service")


class PipelineService:
    """High-level service for pipeline operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_pipeline(
        self,
        name: str,
        project_id: str | None = None,
        description: str | None = None,
        owner: str | None = None,
        nodes_config: list[dict] | None = None,
    ) -> Pipeline:
        """Create a new pipeline with nodes."""
        pipeline = Pipeline(
            project_id=project_id,
            name=name,
            description=description,
            owner=owner,
            status="pending",
        )
        self.db.add(pipeline)
        self.db.flush()

        if nodes_config:
            for i, node_cfg in enumerate(nodes_config):
                node = PipelineNode(
                    pipeline_id=pipeline.id,
                    name=node_cfg.get("name", f"Node {i + 1}"),
                    description=node_cfg.get("description"),
                    node_type=node_cfg.get("node_type", "custom"),
                    inputs_json=json.dumps(node_cfg.get("inputs", {})),
                    parameters_json=json.dumps(node_cfg.get("parameters", {})),
                    depends_on_json=json.dumps(node_cfg.get("depends_on", [])),
                    sort_order=i,
                    max_retries=node_cfg.get("max_retries", 3),
                )
                self.db.add(node)

        self.db.commit()
        self.db.refresh(pipeline)
        if nodes_config:
            pipeline.total_nodes = len(nodes_config)
            self.db.commit()
            self.db.refresh(pipeline)
        logger.info(f"Pipeline created: {pipeline.name} ({pipeline.id})")
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> Pipeline | None:
        """Get a pipeline by ID."""
        return self.db.get(Pipeline, pipeline_id)

    def list_pipelines(
        self,
        project_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Pipeline], int]:
        """List pipelines with filters."""
        q = self.db.query(Pipeline)
        if project_id:
            q = q.filter(Pipeline.project_id == project_id)
        if status:
            q = q.filter(Pipeline.status == status)

        total = q.count()
        pipelines = q.order_by(Pipeline.created_at.desc()).offset(offset).limit(limit).all()
        return pipelines, total

    def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline."""
        pipeline = self.db.get(Pipeline, pipeline_id)
        if not pipeline:
            return False

        self.db.delete(pipeline)
        self.db.commit()
        return True

    def start_pipeline(self, pipeline_id: str) -> dict:
        """Start a pipeline execution."""
        runner = PipelineRunner(self.db)
        return runner.run(pipeline_id)

    def pause_pipeline(self, pipeline_id: str) -> bool:
        """Pause a running pipeline."""
        runner = PipelineRunner(self.db)
        return runner.pause(pipeline_id)

    def resume_pipeline(self, pipeline_id: str) -> bool:
        """Resume a paused pipeline."""
        runner = PipelineRunner(self.db)
        return runner.resume(pipeline_id)

    def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a pipeline."""
        runner = PipelineRunner(self.db)
        return runner.cancel(pipeline_id)

    def retry_pipeline(self, pipeline_id: str) -> bool:
        """Retry a failed pipeline."""
        runner = PipelineRunner(self.db)
        return runner.retry(pipeline_id)

    def enqueue_pipeline(self, pipeline_id: str, priority: int = 0):
        """Add pipeline to queue."""
        queue_mgr = QueueManager(self.db)
        return queue_mgr.enqueue(pipeline_id, priority)

    def dequeue_pipeline(self, pipeline_id: str) -> bool:
        """Remove pipeline from queue."""
        queue_mgr = QueueManager(self.db)
        return queue_mgr.dequeue(pipeline_id)

    def get_pipeline_nodes(self, pipeline_id: str) -> list[PipelineNode]:
        """Get nodes for a pipeline."""
        return (
            self.db.query(PipelineNode)
            .filter(PipelineNode.pipeline_id == pipeline_id)
            .order_by(PipelineNode.sort_order)
            .all()
        )

    def get_pipeline_history(self, pipeline_id: str, limit: int = 50) -> list[PipelineHistory]:
        """Get pipeline execution history."""
        return (
            self.db.query(PipelineHistory)
            .filter(PipelineHistory.pipeline_id == pipeline_id)
            .order_by(PipelineHistory.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_pipeline_logs(
        self,
        pipeline_id: str,
        node_id: str | None = None,
        level: str | None = None,
        limit: int = 100,
    ) -> list[PipelineLog]:
        """Get pipeline logs."""
        q = self.db.query(PipelineLog).filter(PipelineLog.pipeline_id == pipeline_id)
        if node_id:
            q = q.filter(PipelineLog.node_id == node_id)
        if level:
            q = q.filter(PipelineLog.level == level)
        return q.order_by(PipelineLog.timestamp.desc()).limit(limit).all()

    def get_queue_status(self) -> dict:
        """Get queue statistics."""
        queue_mgr = QueueManager(self.db)
        return queue_mgr.get_queue_status()

    def get_all_queued(self) -> list:
        """Get all queued pipelines."""
        queue_mgr = QueueManager(self.db)
        return queue_mgr.get_all_entries()

    def get_pipeline_stats(self, project_id: str | None = None) -> dict:
        """Get pipeline statistics."""
        q = self.db.query(Pipeline)
        if project_id:
            q = q.filter(Pipeline.project_id == project_id)

        pipelines = q.all()
        return {
            "total": len(pipelines),
            "pending": sum(1 for p in pipelines if p.status == "pending"),
            "queued": sum(1 for p in pipelines if p.status == "queued"),
            "running": sum(1 for p in pipelines if p.status == "running"),
            "completed": sum(1 for p in pipelines if p.status == "completed"),
            "failed": sum(1 for p in pipelines if p.status == "failed"),
            "cancelled": sum(1 for p in pipelines if p.status == "cancelled"),
            "paused": sum(1 for p in pipelines if p.status == "paused"),
        }

    def get_available_node_types(self) -> list[dict]:
        """Get all available node types."""
        from pipeline_engine.nodes import NODE_REGISTRY
        return [
            {"type": t, "name": cls.__name__, "description": cls.__doc__ or ""}
            for t, cls in NODE_REGISTRY.items()
        ]
