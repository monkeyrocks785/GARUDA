"""GARUDA Launcher - ANSI color utilities for terminal output."""

import sys


def supports_color() -> bool:
    """Check if the terminal supports color."""
    if sys.platform == "win32":
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


COLORS_ENABLED = supports_color()


class Style:
    """ANSI style constants."""

    RESET = "\033[0m" if COLORS_ENABLED else ""
    BOLD = "\033[1m" if COLORS_ENABLED else ""
    DIM = "\033[2m" if COLORS_ENABLED else ""
    ITALIC = "\033[3m" if COLORS_ENABLED else ""
    UNDERLINE = "\033[4m" if COLORS_ENABLED else ""

    RED = "\033[91m" if COLORS_ENABLED else ""
    GREEN = "\033[92m" if COLORS_ENABLED else ""
    YELLOW = "\033[93m" if COLORS_ENABLED else ""
    BLUE = "\033[94m" if COLORS_ENABLED else ""
    MAGENTA = "\033[95m" if COLORS_ENABLED else ""
    CYAN = "\033[96m" if COLORS_ENABLED else ""
    WHITE = "\033[97m" if COLORS_ENABLED else ""


def banner(text: str, width: int = 60) -> str:
    """Create a centered banner."""
    return f"{Style.CYAN}{Style.BOLD}{'=' * width}{Style.RESET}\n" \
           f"{Style.CYAN}{Style.BOLD}  {text}{Style.RESET}\n" \
           f"{Style.CYAN}{Style.BOLD}{'=' * width}{Style.RESET}"


def header(text: str) -> str:
    """Create a section header."""
    return f"\n{Style.BLUE}{Style.BOLD}[{text}]{Style.RESET}\n{Style.DIM}{'-' * 50}{Style.RESET}"


def ok(msg: str) -> str:
    """Create a success message."""
    return f"  {Style.GREEN}[OK]{Style.RESET} {msg}"


def warn(msg: str) -> str:
    """Create a warning message."""
    return f"  {Style.YELLOW}[WARN]{Style.RESET} {msg}"


def fail(msg: str) -> str:
    """Create an error message."""
    return f"  {Style.RED}[FAIL]{Style.RESET} {msg}"


def info(msg: str) -> str:
    """Create an info message."""
    return f"  {Style.DIM}...{Style.RESET} {msg}"


def step(msg: str) -> str:
    """Create a step indicator."""
    return f"  {Style.CYAN}[>]{Style.RESET} {msg}"
