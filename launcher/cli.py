"""GARUDA Launcher - CLI command dispatcher."""

import sys

from launcher.config import AppInfo
from launcher.style import Style, banner, header


COMMANDS = {
    "dev": ("launcher.commands.dev", "cmd_dev"),
    "prod": ("launcher.commands.prod", "cmd_prod"),
    "doctor": ("launcher.commands.doctor", "cmd_doctor"),
    "backend": ("launcher.commands.backend", "cmd_backend"),
    "frontend": ("launcher.commands.frontend", "cmd_frontend"),
    "migrate": ("launcher.commands.migration", "cmd_migrate"),
    "makemigration": ("launcher.commands.migration", "cmd_makemigration"),
    "clean": ("launcher.commands.cleanup", "cmd_clean"),
    "reset-cache": ("launcher.commands.cleanup", "cmd_reset_cache"),
    "logs": ("launcher.commands.logs", "cmd_logs"),
    "version": ("launcher.commands.version", "cmd_version"),
    "status": ("launcher.commands.status", "cmd_status"),
    "stop": ("launcher.commands.stop", "cmd_stop"),
}


def show_help() -> None:
    """Display usage information."""
    print(banner(f"GARUDA Command Center v{AppInfo.VERSION}"))
    print()
    print(f"  {Style.BOLD}Usage:{Style.RESET}")
    print(f"    python main.py [command]")
    print()
    print(f"  {Style.BOLD}Commands:{Style.RESET}")
    print(f"    {Style.CYAN}dev{Style.RESET}           Start GARUDA in development mode")
    print(f"    {Style.CYAN}prod{Style.RESET}          Start GARUDA in production mode")
    print(f"    {Style.CYAN}doctor{Style.RESET}        Run system diagnostics")
    print(f"    {Style.CYAN}backend{Style.RESET}       Run only the backend")
    print(f"    {Style.CYAN}frontend{Style.RESET}      Run only the frontend")
    print(f"    {Style.CYAN}migrate{Style.RESET}       Run Alembic migrations")
    print(f"    {Style.CYAN}makemigration{Style.RESET} Create a new migration")
    print(f"    {Style.CYAN}clean{Style.RESET}         Clean temp files and cache")
    print(f"    {Style.CYAN}reset-cache{Style.RESET}   Clear cache only")
    print(f"    {Style.CYAN}logs{Style.RESET}          Show recent logs")
    print(f"    {Style.CYAN}version{Style.RESET}       Show version info")
    print(f"    {Style.CYAN}status{Style.RESET}        Show system status")
    print(f"    {Style.CYAN}stop{Style.RESET}          Stop running processes")
    print(f"    {Style.CYAN}help{Style.RESET}          Show this help")
    print()
    print(f"  {Style.DIM}Running without a command starts development mode.{Style.RESET}")
    print()


def dispatch() -> int:
    """Parse arguments and dispatch to the appropriate command."""
    args = sys.argv[1:]

    if not args or args[0] in ("dev", "--dev", "-d"):
        from launcher.commands.dev import cmd_dev
        return cmd_dev()

    if args[0] in ("help", "--help", "-h"):
        show_help()
        return 0

    cmd = args[0]
    if cmd in ("--version", "-v"):
        from launcher.commands.version import cmd_version
        return cmd_version()

    if cmd not in COMMANDS:
        print(f"{Style.RED}Unknown command: {cmd}{Style.RESET}")
        print(f"Run {Style.CYAN}python main.py help{Style.RESET} for usage.")
        return 1

    module_path, func_name = COMMANDS[cmd]
    try:
        import importlib
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        return func()
    except Exception as e:
        print(f"{Style.RED}Error executing {cmd}: {e}{Style.RESET}")
        return 1
