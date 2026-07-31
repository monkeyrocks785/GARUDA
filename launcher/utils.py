"""GARUDA Launcher - Utility functions."""

import subprocess
import sys
from pathlib import Path

from launcher.config import PathConfig, PythonConfig


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 60,
    capture: bool = True,
) -> tuple[int, str]:
    """Run a command and return (returncode, combined output)."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=capture,
            text=True,
            timeout=timeout,
            creationflags=flags,
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except FileNotFoundError:
        return -1, "executable not found"
    except subprocess.TimeoutExpired:
        return -2, "command timed out"
    except Exception as e:
        return -3, str(e)


def get_python_version() -> str:
    """Get the current Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_node_version() -> str | None:
    """Get Node.js version if available."""
    code, out = run_command(["node", "--version"], timeout=10)
    return out.strip() if code == 0 else None


def get_npm_version() -> str | None:
    """Get npm version if available."""
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    code, out = run_command([npm_cmd, "--version"], timeout=10)
    return out.strip() if code == 0 else None


def get_frontend_version() -> str | None:
    """Get frontend version from package.json."""
    pkg_json = PathConfig.FRONTEND_DIR / "package.json"
    if pkg_json.exists():
        try:
            import json
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            return data.get("version", "unknown")
        except Exception:
            pass
    return None


def check_backend_python() -> bool:
    """Check if backend venv Python exists and is valid."""
    return PathConfig.BACKEND_PYTHON.exists()


def ensure_directories() -> None:
    """Create all required storage directories."""
    for subdir in ["cache", "exports", "logs", "models", "projects", "temp"]:
        d = PathConfig.STORAGE_DIR / subdir
        d.mkdir(parents=True, exist_ok=True)


def get_disk_usage(path: Path | None = None) -> dict:
    """Get disk usage statistics."""
    import shutil
    target = path or PathConfig.STORAGE_DIR
    try:
        usage = shutil.disk_usage(str(target))
        return {
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "percent_used": round((usage.used / usage.total) * 100, 1),
        }
    except Exception:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent_used": 0}


def get_storage_size() -> dict:
    """Get storage directory sizes."""
    sizes = {}
    for name in ["cache", "exports", "logs", "models", "projects", "temp", "garuda.db"]:
        path = PathConfig.STORAGE_DIR / name
        if path.exists():
            if path.is_file():
                sizes[name] = path.stat().st_size
            else:
                total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
                sizes[name] = total
        else:
            sizes[name] = 0
    sizes["total"] = sum(sizes.values())
    return sizes


def format_bytes(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is in use."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is available."""
    return not is_port_in_use(port, host)
