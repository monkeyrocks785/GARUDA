"""Event Bus - Pipeline event system."""

import logging
from collections.abc import Callable

logger = logging.getLogger("garuda.pipeline.events")

# Global event handlers
_handlers: dict[str, list[Callable]] = {}


def on(event_type: str, handler: Callable):
    """Register an event handler."""
    if event_type not in _handlers:
        _handlers[event_type] = []
    _handlers[event_type].append(handler)


def off(event_type: str, handler: Callable | None = None):
    """Unregister an event handler."""
    if event_type not in _handlers:
        return
    if handler:
        _handlers[event_type] = [h for h in _handlers[event_type] if h != handler]
    else:
        _handlers[event_type] = []


def emit_event(event_type: str, data: dict):
    """Emit an event to all registered handlers."""
    logger.debug(f"Event: {event_type} - {data}")
    handlers = _handlers.get(event_type, [])
    for handler in handlers:
        try:
            handler(event_type, data)
        except Exception as e:
            logger.error(f"Event handler error: {e}")


def clear_handlers():
    """Clear all event handlers."""
    _handlers.clear()
