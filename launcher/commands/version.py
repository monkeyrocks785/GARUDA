"""GARUDA Launcher - Version information command."""

import sys

from launcher.config import PathConfig, AppInfo
from launcher.style import Style, header, banner
from launcher.utils import get_python_version, get_node_version, get_npm_version, get_frontend_version


def cmd_version() -> int:
    """Display version and build information."""
    print(banner(f"GARUDA Version Info"))
    print(header("Build Information"))
    print()

    print(f"  {Style.BOLD}Application{Style.RESET}")
    print(f"    Name    : {AppInfo.NAME}")
    print(f"    Version : {AppInfo.VERSION}")
    print(f"    Build   : {AppInfo.BUILD}")
    print()

    print(f"  {Style.BOLD}Runtime{Style.RESET}")
    print(f"    Python  : {get_python_version()}")
    node = get_node_version()
    npm = get_npm_version()
    print(f"    Node.js : {node or 'not installed'}")
    print(f"    npm     : {npm or 'not installed'}")
    print()

    print(f"  {Style.BOLD}Components{Style.RESET}")
    frontend_ver = get_frontend_version()
    print(f"    Frontend: {frontend_ver or 'unknown'}")

    # Backend version from pyproject.toml
    backend_toml = PathConfig.BACKEND_DIR / "pyproject.toml"
    if backend_toml.exists():
        try:
            content = backend_toml.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.strip().startswith("version"):
                    ver = line.split("=")[1].strip().strip('"').strip("'")
                    print(f"    Backend : {ver}")
                    break
        except Exception:
            print(f"    Backend : {AppInfo.VERSION}")
    else:
        print(f"    Backend : {AppInfo.VERSION}")

    # Database version
    if PathConfig.DB_PATH.exists():
        print(f"    Database: SQLite {PathConfig.DB_PATH.stat().st_size:,} bytes")
    else:
        print(f"    Database: not initialized")

    print()
    return 0
