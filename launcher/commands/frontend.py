"""GARUDA Launcher - Frontend-only command."""

import subprocess
import sys

from launcher.config import PathConfig, AppInfo
from launcher.style import ok, fail, info, header, banner


def cmd_frontend() -> int:
    """Run only the frontend dev server."""
    print(banner(f"GARUDA Frontend v{AppInfo.VERSION}"))
    print(header("Starting Frontend"))

    pkg_json = PathConfig.FRONTEND_DIR / "package.json"
    if not pkg_json.exists():
        print(fail("package.json not found"))
        return 1

    nm_dir = PathConfig.FRONTEND_DIR / "node_modules"
    if not nm_dir.exists():
        print(info("Installing dependencies..."))
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        subprocess.run([npm, "install"], cwd=str(PathConfig.FRONTEND_DIR))

    print(info("Starting Vite dev server..."))
    print()

    try:
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        cmd = [npm, "run", "dev"]
        proc = subprocess.run(
            cmd,
            cwd=str(PathConfig.FRONTEND_DIR),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        return proc.returncode
    except KeyboardInterrupt:
        print()
        print(info("Frontend stopped"))
        return 0
    except Exception as e:
        print(fail(f"Failed to start frontend: {e}"))
        return 1
