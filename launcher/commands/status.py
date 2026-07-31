"""GARUDA Launcher - System status command."""

import json
from pathlib import Path

from launcher.config import PathConfig, ServerConfig, AppInfo
from launcher.style import Style, ok, warn, fail, info, header, banner
from launcher.utils import (
    get_python_version,
    get_node_version,
    get_npm_version,
    get_frontend_version,
    is_port_in_use,
    get_storage_size,
    format_bytes,
)


def cmd_status() -> int:
    """Display system status."""
    print(banner(f"GARUDA Status v{AppInfo.VERSION}"))
    print(header("System Status"))
    print()

    # Version
    print(f"  {Style.BOLD}Application{Style.RESET}")
    print(f"    Name    : {AppInfo.NAME}")
    print(f"    Version : {AppInfo.VERSION}")
    print(f"    Build   : {AppInfo.BUILD}")
    print()

    # Backend status
    backend_running = is_port_in_use(ServerConfig.BACKEND_PORT)
    if backend_running:
        print(f"  {Style.BOLD}Backend{Style.RESET}")
        print(f"    Status  : {Style.GREEN}Running{Style.RESET} (port {ServerConfig.BACKEND_PORT})")
    else:
        print(f"  {Style.BOLD}Backend{Style.RESET}")
        print(f"    Status  : {Style.RED}Stopped{Style.RESET}")
    print()

    # Frontend status
    frontend_running = is_port_in_use(ServerConfig.FRONTEND_PORT)
    if frontend_running:
        print(f"  {Style.BOLD}Frontend{Style.RESET}")
        print(f"    Status  : {Style.GREEN}Running{Style.RESET} (port {ServerConfig.FRONTEND_PORT})")
    else:
        print(f"  {Style.BOLD}Frontend{Style.RESET}")
        print(f"    Status  : {Style.RED}Stopped{Style.RESET}")
    print()

    # Database
    print(f"  {Style.BOLD}Database{Style.RESET}")
    if PathConfig.DB_PATH.exists():
        size = PathConfig.DB_PATH.stat().st_size
        print(f"    File    : {Style.GREEN}Exists{Style.RESET} ({format_bytes(size)})")
    else:
        print(f"    File    : {Style.RED}Not Found{Style.RESET}")
    print()

    # Configuration
    print(f"  {Style.BOLD}Configuration{Style.RESET}")
    if PathConfig.ENV_FILE.exists():
        print(f"    .env    : {Style.GREEN}Loaded{Style.RESET}")
    else:
        print(f"    .env    : {Style.YELLOW}Not Found{Style.RESET}")
    print()

    # Storage
    print(f"  {Style.BOLD}Storage{Style.RESET}")
    sizes = get_storage_size()
    for name, size in sizes.items():
        if name != "total":
            print(f"    {name:12s}: {format_bytes(size)}")
    print(f"    {'-' * 25}")
    print(f"    {'Total':12s}: {format_bytes(sizes.get('total', 0))}")
    print()

    # Logs
    print(f"  {Style.BOLD}Logs{Style.RESET}")
    log_files = {
        "launcher": PathConfig.LAUNCHER_LOG,
        "startup": PathConfig.STARTUP_LOG,
        "shutdown": PathConfig.SHUTDOWN_LOG,
    }
    for name, path in log_files.items():
        if path.exists():
            size = path.stat().st_size
            print(f"    {name:12s}: {format_bytes(size)}")
        else:
            print(f"    {name:12s}: {Style.DIM}not created yet{Style.RESET}")
    print()

    return 0
