"""GARUDA Launcher - Process management utilities."""

import json
import subprocess
import sys
import time
from pathlib import Path

from launcher.config import PathConfig


PROCESS_FILE = PathConfig.STORAGE_DIR / ".garuda_processes.json"


def read_process_state() -> dict:
    """Read stored process state."""
    if PROCESS_FILE.exists():
        try:
            return json.loads(PROCESS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def write_process_state(state: dict) -> None:
    """Write process state to disk."""
    PROCESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROCESS_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def register_process(name: str, pid: int) -> None:
    """Register a running process."""
    state = read_process_state()
    state[name] = {
        "pid": pid,
        "started_at": time.time(),
        "status": "running",
    }
    write_process_state(state)


def unregister_process(name: str) -> None:
    """Unregister a stopped process."""
    state = read_process_state()
    if name in state:
        state[name]["status"] = "stopped"
        state[name]["stopped_at"] = time.time()
    write_process_state(state)


def is_process_running(pid: int) -> bool:
    """Check if a process with given PID exists."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return False


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is available."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0
    except Exception:
        return True


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is in use."""
    return not is_port_available(port, host)


def kill_existing_processes() -> None:
    """Kill any existing GARUDA processes."""
    state = read_process_state()
    for name, info in state.items():
        pid = info.get("pid")
        if pid and info.get("status") == "running":
            if is_process_running(pid):
                try:
                    if sys.platform == "win32":
                        subprocess.run(
                            ["taskkill", "/F", "/PID", str(pid)],
                            capture_output=True,
                            timeout=5,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                    else:
                        import os
                        os.kill(pid, 15)
                except Exception:
                    pass
            unregister_process(name)


def get_running_processes() -> dict:
    """Get all running GARUDA processes."""
    state = read_process_state()
    running = {}
    for name, info in state.items():
        pid = info.get("pid")
        if pid and info.get("status") == "running":
            if is_process_running(pid):
                running[name] = info
            else:
                unregister_process(name)
    return running
