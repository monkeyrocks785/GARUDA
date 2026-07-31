"""GARUDA Launcher - Process stop command."""

from launcher.config import AppInfo
from launcher.style import ok, info, fail, header, banner
from launcher.process import kill_existing_processes, get_running_processes


def cmd_stop() -> int:
    """Gracefully terminate running GARUDA processes."""
    print(banner(f"GARUDA Stop v{AppInfo.VERSION}"))
    print(header("Stopping Processes"))
    print()

    running = get_running_processes()
    if not running:
        print(info("No GARUDA processes running"))
        print()
        return 0

    print(info(f"Found {len(running)} running process(es):"))
    for name, info_dict in running.items():
        pid = info_dict.get("pid", "?")
        print(f"    - {name} (PID: {pid})")
    print()

    print(info("Terminating processes..."))
    kill_existing_processes()
    print(ok("All processes stopped"))

    print()
    return 0
