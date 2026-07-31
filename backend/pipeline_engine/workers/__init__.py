"""Worker - Executes pipelines from the queue."""

import logging
import threading
import time
from typing import Optional

from sqlalchemy.orm import Session

from pipeline_engine.database.models import Pipeline
from pipeline_engine.pipeline.runner import PipelineRunner
from pipeline_engine.queue.manager import QueueManager

logger = logging.getLogger("garuda.pipeline.worker")


class PipelineWorker:
    """Worker that processes pipelines from the queue."""

    def __init__(self, db_factory, worker_id: str = "main"):
        self.db_factory = db_factory
        self.worker_id = worker_id
        self._running = False
        self._thread: threading.Thread | None = None
        self._poll_interval = 2.0  # seconds

    def start(self):
        """Start the worker."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"Worker {self.worker_id} started")

    def stop(self):
        """Stop the worker."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info(f"Worker {self.worker_id} stopped")

    def _run_loop(self):
        """Main worker loop."""
        while self._running:
            try:
                db = self.db_factory()
                queue_mgr = QueueManager(db)
                pipeline = queue_mgr.get_next()

                if pipeline:
                    queue_mgr.start_processing(pipeline.id, self.worker_id)
                    runner = PipelineRunner(db)
                    result = runner.run(pipeline.id)
                    queue_mgr.complete_processing(pipeline.id, result.get("success", False))
                else:
                    time.sleep(self._poll_interval)

                db.close()
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                time.sleep(self._poll_interval)

    @property
    def is_running(self) -> bool:
        return self._running


class WorkerPool:
    """Manages multiple pipeline workers."""

    def __init__(self, db_factory, num_workers: int = 1):
        self.db_factory = db_factory
        self.workers: list[PipelineWorker] = []
        for i in range(num_workers):
            worker = PipelineWorker(db_factory, worker_id=f"worker-{i}")
            self.workers.append(worker)

    def start(self):
        """Start all workers."""
        for worker in self.workers:
            worker.start()

    def stop(self):
        """Stop all workers."""
        for worker in self.workers:
            worker.stop()

    @property
    def active_count(self) -> int:
        return sum(1 for w in self.workers if w.is_running)
