"""Data Engine watcher - Placeholder for future folder watching."""

from collections.abc import Callable
from pathlib import Path
from typing import Optional


class FolderWatcher:
    """Watch a folder for changes (placeholder for future implementation)."""

    def __init__(self, watch_path: Path, callback: Callable | None = None):
        self.watch_path = watch_path
        self.callback = callback
        self._running = False

    def start(self) -> None:
        """Start watching (placeholder)."""
        self._running = True
        # Future: Implement using watchdog or polling

    def stop(self) -> None:
        """Stop watching."""
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
