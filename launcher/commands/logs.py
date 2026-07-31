"""GARUDA Launcher - Logs command."""

from pathlib import Path

from launcher.config import PathConfig, AppInfo
from launcher.style import Style, ok, info, fail, header, banner


def cmd_logs() -> int:
    """Show recent backend logs."""
    print(banner(f"GARUDA Logs v{AppInfo.VERSION}"))
    print(header("Recent Backend Logs"))
    print()

    log_files = [
        ("Launcher", PathConfig.LAUNCHER_LOG),
        ("Startup", PathConfig.STARTUP_LOG),
        ("Shutdown", PathConfig.SHUTDOWN_LOG),
        ("Backend", PathConfig.LOG_DIR / "backend.log"),
        ("Errors", PathConfig.LOG_DIR / "errors.log"),
    ]

    found_any = False
    for name, path in log_files:
        if path.exists() and path.stat().st_size > 0:
            found_any = True
            print(f"  {Style.BOLD}{name}{Style.RESET} ({path.name})")
            try:
                lines = path.read_text(encoding="utf-8").strip().splitlines()
                recent = lines[-20:] if len(lines) > 20 else lines
                for line in recent:
                    print(f"    {line}")
            except Exception as e:
                print(f"    {Style.RED}Error reading: {e}{Style.RESET}")
            print()

    if not found_any:
        print(info("No log files found"))
        print()

    return 0
