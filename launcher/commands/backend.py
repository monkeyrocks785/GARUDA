"""GARUDA Launcher - Backend-only command."""

import subprocess
import sys

from launcher.config import PathConfig, ServerConfig, AppInfo
from launcher.style import ok, fail, info, header, banner


def cmd_backend() -> int:
    """Run only the backend server."""
    print(banner(f"GARUDA Backend v{AppInfo.VERSION}"))
    print(header("Starting Backend"))

    if not PathConfig.BACKEND_PYTHON.exists():
        print(fail("Backend Python not found"))
        return 1

    print(info(f"Starting uvicorn on {ServerConfig.BACKEND_HOST}:{ServerConfig.BACKEND_PORT}"))
    print()

    try:
        cmd = [
            str(PathConfig.BACKEND_PYTHON),
            "-m", "uvicorn",
            "main:app",
            "--reload",
            "--host", ServerConfig.BACKEND_HOST,
            "--port", str(ServerConfig.BACKEND_PORT),
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(PathConfig.BACKEND_DIR),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        return proc.returncode
    except KeyboardInterrupt:
        print()
        print(info("Backend stopped"))
        return 0
    except Exception as e:
        print(fail(f"Failed to start backend: {e}"))
        return 1
