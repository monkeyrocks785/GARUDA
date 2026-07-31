"""Pipeline Runner - Orchestrates pipeline execution."""

import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from pipeline_engine.database.models import Pipeline, PipelineHistory, PipelineLog, PipelineNode
from pipeline_engine.events.emitter import emit_event
from pipeline_engine.executor.node_executor import NodeExecutor

logger = logging.getLogger("garuda.pipeline.runner")


class PipelineRunner:
    """Executes a pipeline by running its nodes in dependency order."""

    def __init__(self, db: Session):
        self.db = db
        self.node_executor = NodeExecutor(db)

    def run(self, pipeline_id: str) -> dict:
        """Run a pipeline from start to finish."""
        pipeline = self.db.get(Pipeline, pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        if pipeline.status not in ("pending", "queued"):
            raise ValueError(f"Pipeline {pipeline_id} cannot be started (status: {pipeline.status})")

        # Mark pipeline as running
        pipeline.status = "running"
        pipeline.started_at = datetime.utcnow()
        self.db.commit()

        self._log("info", f"Pipeline '{pipeline.name}' started")
        emit_event("pipeline_started", {
            "pipeline_id": pipeline.id,
            "pipeline_name": pipeline.name,
        })

        # Record history
        history = PipelineHistory(
            pipeline_id=pipeline.id,
            action="started",
            details="Pipeline execution started",
        )
        self.db.add(history)
        self.db.commit()

        try:
            nodes = (
                self.db.query(PipelineNode)
                .filter(PipelineNode.pipeline_id == pipeline.id)
                .order_by(PipelineNode.sort_order)
                .all()
            )

            pipeline.total_nodes = len(nodes)
            self.db.commit()

            for node in nodes:
                # Check if pipeline was cancelled
                pipeline = self.db.get(Pipeline, pipeline_id)
                if pipeline.status == "cancelled":
                    self._log("info", "Pipeline cancelled during execution")
                    return {"success": False, "cancelled": True}

                # Check if pipeline was paused
                if pipeline.status == "paused":
                    self._log("info", "Pipeline paused during execution")
                    return {"success": False, "paused": True}

                # Check dependencies
                if not self._dependencies_met(node, nodes):
                    node.status = "skipped"
                    self.db.commit()
                    continue

                # Execute node
                try:
                    self.node_executor.execute(node)
                    pipeline.completed_nodes += 1
                except Exception:
                    pipeline.failed_nodes += 1

                # Update progress
                pipeline.progress = (
                    (pipeline.completed_nodes + pipeline.failed_nodes) / max(pipeline.total_nodes, 1)
                ) * 100
                self.db.commit()

            # Determine final status
            pipeline = self.db.get(Pipeline, pipeline_id)
            if pipeline.failed_nodes > 0 and pipeline.completed_nodes == 0:
                pipeline.status = "failed"
            elif pipeline.failed_nodes > 0:
                pipeline.status = "completed"  # partial success
            else:
                pipeline.status = "completed"

            pipeline.completed_at = datetime.utcnow()
            pipeline.execution_time_ms = int(
                (pipeline.completed_at - pipeline.started_at).total_seconds() * 1000
            ) if pipeline.started_at else 0
            pipeline.progress = 100.0
            self.db.commit()

            self._log("info", f"Pipeline '{pipeline.name}' completed ({pipeline.status})")
            emit_event("pipeline_completed", {
                "pipeline_id": pipeline.id,
                "pipeline_name": pipeline.name,
                "status": pipeline.status,
                "execution_time_ms": pipeline.execution_time_ms,
            })

            history = PipelineHistory(
                pipeline_id=pipeline.id,
                action="completed",
                details=f"Pipeline {pipeline.status}",
                execution_time_ms=pipeline.execution_time_ms,
            )
            self.db.add(history)
            self.db.commit()

            return {"success": True, "status": pipeline.status}

        except Exception as e:
            pipeline = self.db.get(Pipeline, pipeline_id)
            pipeline.status = "failed"
            pipeline.error_message = str(e)
            pipeline.completed_at = datetime.utcnow()
            self.db.commit()

            self._log("error", f"Pipeline '{pipeline.name}' failed: {e}")
            emit_event("pipeline_completed", {
                "pipeline_id": pipeline.id,
                "pipeline_name": pipeline.name,
                "status": "failed",
                "error": str(e),
            })

            return {"success": False, "error": str(e)}

    def pause(self, pipeline_id: str) -> bool:
        """Pause a running pipeline."""
        pipeline = self.db.get(Pipeline, pipeline_id)
        if not pipeline or pipeline.status != "running":
            return False

        pipeline.status = "paused"
        self.db.commit()

        self._log("info", f"Pipeline '{pipeline.name}' paused")
        emit_event("pipeline_paused", {"pipeline_id": pipeline.id})

        history = PipelineHistory(
            pipeline_id=pipeline.id,
            action="paused",
            details="Pipeline paused by user",
        )
        self.db.add(history)
        self.db.commit()

        return True

    def resume(self, pipeline_id: str) -> bool:
        """Resume a paused pipeline."""
        pipeline = self.db.get(Pipeline, pipeline_id)
        if not pipeline or pipeline.status != "paused":
            return False

        pipeline.status = "running"
        self.db.commit()

        self._log("info", f"Pipeline '{pipeline.name}' resumed")
        emit_event("pipeline_resumed", {"pipeline_id": pipeline.id})

        history = PipelineHistory(
            pipeline_id=pipeline.id,
            action="resumed",
            details="Pipeline resumed by user",
        )
        self.db.add(history)
        self.db.commit()

        return True

    def cancel(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline."""
        pipeline = self.db.get(Pipeline, pipeline_id)
        if not pipeline or pipeline.status not in ("running", "queued", "paused"):
            return False

        pipeline.status = "cancelled"
        pipeline.completed_at = datetime.utcnow()
        self.db.commit()

        self._log("info", f"Pipeline '{pipeline.name}' cancelled")
        emit_event("pipeline_cancelled", {"pipeline_id": pipeline.id})

        history = PipelineHistory(
            pipeline_id=pipeline.id,
            action="cancelled",
            details="Pipeline cancelled by user",
        )
        self.db.add(history)
        self.db.commit()

        return True

    def retry(self, pipeline_id: str) -> bool:
        """Retry a failed pipeline from the last checkpoint."""
        pipeline = self.db.get(Pipeline, pipeline_id)
        if not pipeline or pipeline.status not in ("failed", "cancelled"):
            return False

        # Reset failed nodes
        failed_nodes = (
            self.db.query(PipelineNode)
            .filter(
                PipelineNode.pipeline_id == pipeline_id,
                PipelineNode.status.in_(["failed", "cancelled"]),
            )
            .all()
        )
        for node in failed_nodes:
            node.status = "pending"
            node.retry_count = 0
            node.error_message = None

        pipeline.status = "pending"
        pipeline.failed_nodes = 0
        pipeline.error_message = None
        pipeline.progress = 0.0
        self.db.commit()

        self._log("info", f"Pipeline '{pipeline.name}' reset for retry")
        return True

    def _dependencies_met(self, node: PipelineNode, all_nodes: list[PipelineNode]) -> bool:
        """Check if all dependencies of a node are completed."""
        if not node.depends_on_json:
            return True

        dep_ids = json.loads(node.depends_on_json)
        if not dep_ids:
            return True

        node_map = {n.id: n for n in all_nodes}
        for dep_id in dep_ids:
            dep_node = node_map.get(dep_id)
            if not dep_node or dep_node.status != "completed":
                return False

        return True

    def _log(self, level: str, message: str):
        """Write a pipeline log."""
        log = PipelineLog(
            pipeline_id=getattr(self, '_pipeline_id', None),
            level=level,
            message=message,
        )
        self.db.add(log)
        self.db.commit()
