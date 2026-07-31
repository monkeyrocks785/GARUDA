"""Node Executor - Executes individual pipeline nodes."""

import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from pipeline_engine.database.models import PipelineHistory, PipelineLog, PipelineNode
from pipeline_engine.events.emitter import emit_event
from pipeline_engine.nodes import create_node

logger = logging.getLogger("garuda.pipeline.executor")


class NodeExecutor:
    """Executes a single pipeline node with retry logic."""

    def __init__(self, db: Session):
        self.db = db

    def execute(self, node: PipelineNode) -> dict:
        """Execute a node. Returns outputs dict."""
        node.started_at = datetime.utcnow()
        node.status = "running"
        self.db.commit()

        self._log("info", f"Node '{node.name}' started ({node.node_type})")
        emit_event("node_started", {
            "pipeline_id": node.pipeline_id,
            "node_id": node.id,
            "node_name": node.name,
            "node_type": node.node_type,
        })

        try:
            node_instance = create_node(node, self.db)
            outputs = node_instance.run()

            node.status = "completed"
            node.completed_at = datetime.utcnow()
            node.execution_time_ms = node_instance.get_elapsed_ms()
            node.outputs_json = json.dumps(outputs)
            node.result_json = json.dumps({"success": True})
            self.db.commit()

            self._log("info", f"Node '{node.name}' completed in {node.execution_time_ms}ms")
            emit_event("node_finished", {
                "pipeline_id": node.pipeline_id,
                "node_id": node.id,
                "node_name": node.name,
                "outputs": outputs,
                "execution_time_ms": node.execution_time_ms,
            })

            # Record history
            history = PipelineHistory(
                pipeline_id=node.pipeline_id,
                node_id=node.id,
                action="completed",
                details=f"Node completed in {node.execution_time_ms}ms",
                execution_time_ms=node.execution_time_ms,
            )
            self.db.add(history)
            self.db.commit()

            return outputs

        except Exception as e:
            node.retry_count += 1
            node.error_message = str(e)

            if node.retry_count < node.max_retries:
                node.status = "pending"
                self._log("warning", f"Node '{node.name}' failed (retry {node.retry_count}/{node.max_retries}): {e}")
                emit_event("node_failed", {
                    "pipeline_id": node.pipeline_id,
                    "node_id": node.id,
                    "node_name": node.name,
                    "error": str(e),
                    "retry": True,
                    "retry_count": node.retry_count,
                })

                history = PipelineHistory(
                    pipeline_id=node.pipeline_id,
                    node_id=node.id,
                    action="retried",
                    details=f"Retry {node.retry_count}/{node.max_retries}: {e}",
                )
                self.db.add(history)
                self.db.commit()
            else:
                node.status = "failed"
                node.completed_at = datetime.utcnow()
                node.execution_time_ms = int(
                    (node.completed_at - node.started_at).total_seconds() * 1000
                ) if node.started_at else 0
                self._log("error", f"Node '{node.name}' failed permanently: {e}")
                emit_event("node_failed", {
                    "pipeline_id": node.pipeline_id,
                    "node_id": node.id,
                    "node_name": node.name,
                    "error": str(e),
                    "retry": False,
                })

                history = PipelineHistory(
                    pipeline_id=node.pipeline_id,
                    node_id=node.id,
                    action="failed",
                    details=str(e),
                    execution_time_ms=node.execution_time_ms,
                )
                self.db.add(history)
                self.db.commit()

            self.db.commit()
            raise

    def _log(self, level: str, message: str, node_id: str | None = None):
        """Write a log entry."""
        log = PipelineLog(
            pipeline_id=self.node.pipeline_id if hasattr(self, 'node') else None,
            node_id=node_id,
            level=level,
            message=message,
        )
        self.db.add(log)
        self.db.commit()
