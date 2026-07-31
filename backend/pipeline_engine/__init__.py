"""Pipeline Engine - Core package."""

from pipeline_engine.events.emitter import clear_handlers, emit_event, off, on
from pipeline_engine.executor.node_executor import NodeExecutor
from pipeline_engine.pipeline.runner import PipelineRunner
from pipeline_engine.queue.manager import QueueManager

EventBus = type("EventBus", (), {"on": staticmethod(on), "off": staticmethod(off), "emit": staticmethod(emit_event), "clear": staticmethod(clear_handlers)})

__all__ = ["PipelineRunner", "NodeExecutor", "QueueManager", "EventBus"]
