"""GARUDA Launcher - Environment diagnostics and system checks."""

import shutil
import sys

from launcher.config import PathConfig, PythonConfig, ServerConfig, AppInfo
from launcher.style import Style, ok, warn, fail, header, banner
from launcher.utils import (
    get_python_version,
    get_node_version,
    get_npm_version,
    check_backend_python,
    run_command,
    is_port_in_use,
    get_disk_usage,
)


class CheckResult:
    """Result of a single diagnostic check."""

    def __init__(self, name: str, status: str, message: str = ""):
        self.name = name
        self.status = status  # PASS, WARN, FAIL
        self.message = message

    def __str__(self) -> str:
        if self.status == "PASS":
            icon = f"{Style.GREEN}PASS{Style.RESET}"
        elif self.status == "WARN":
            icon = f"{Style.YELLOW}WARN{Style.RESET}"
        else:
            icon = f"{Style.RED}FAIL{Style.RESET}"
        suffix = f"  {Style.DIM}{self.message}{Style.RESET}" if self.message else ""
        return f"  [{icon}] {self.name}{suffix}"


def check_python_version() -> CheckResult:
    """Check Python version."""
    ver = sys.version_info[:2]
    required = PythonConfig.MIN_VERSION
    ver_str = get_python_version()
    if ver >= required:
        return CheckResult("Python Version", "PASS", f"{ver_str} (required: >={required[0]}.{required[1]})")
    return CheckResult("Python Version", "FAIL", f"{ver_str} (required: >={required[0]}.{required[1]})")


def check_venv() -> CheckResult:
    """Check if running inside a virtual environment."""
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if in_venv:
        return CheckResult("Virtual Environment", "PASS", f"active at {sys.prefix}")
    return CheckResult("Virtual Environment", "WARN", "not detected (using system Python)")


def check_backend_packages() -> CheckResult:
    """Check required Python packages."""
    missing = []
    for pkg in PythonConfig.REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if not missing:
        return CheckResult("Backend Packages", "PASS", f"{len(PythonConfig.REQUIRED_PACKAGES)} packages installed")
    return CheckResult("Backend Packages", "FAIL", f"missing: {', '.join(missing)}")


def check_node() -> CheckResult:
    """Check Node.js installation."""
    ver = get_node_version()
    if ver:
        return CheckResult("Node.js", "PASS", ver)
    return CheckResult("Node.js", "FAIL", "not found on PATH")


def check_npm() -> CheckResult:
    """Check npm installation."""
    ver = get_npm_version()
    if ver:
        return CheckResult("npm", "PASS", ver)
    return CheckResult("npm", "FAIL", "not found on PATH")


def check_frontend_deps() -> CheckResult:
    """Check frontend dependencies."""
    nm_dir = PathConfig.FRONTEND_DIR / "node_modules"
    pkg_json = PathConfig.FRONTEND_DIR / "package.json"
    if not pkg_json.exists():
        return CheckResult("Frontend Deps", "FAIL", "package.json not found")
    if nm_dir.exists():
        return CheckResult("Frontend Deps", "PASS", "node_modules present")
    return CheckResult("Frontend Deps", "FAIL", "run: npm install")


def check_sqlite() -> CheckResult:
    """Check SQLite availability."""
    try:
        import sqlite3
        ver = sqlite3.sqlite_version
        return CheckResult("SQLite", "PASS", f"v{ver}")
    except ImportError:
        return CheckResult("SQLite", "FAIL", "not available")


def check_database() -> CheckResult:
    """Check if database file exists."""
    if PathConfig.DB_PATH.exists():
        size = PathConfig.DB_PATH.stat().st_size
        return CheckResult("Database", "PASS", f"{size:,} bytes")
    return CheckResult("Database", "FAIL", "not found")


def check_alembic() -> CheckResult:
    """Check Alembic configuration."""
    if not PathConfig.ALEMBIC_INI.exists():
        return CheckResult("Alembic", "FAIL", "alembic.ini not found")
    if not check_backend_python():
        return CheckResult("Alembic", "FAIL", "backend Python not found")
    code, out = run_command(
        [str(PathConfig.BACKEND_PYTHON), "-m", "alembic", "current"],
        cwd=str(PathConfig.BACKEND_DIR),
        timeout=15,
    )
    if code == 0:
        rev = out.strip() or "none"
        return CheckResult("Alembic", "PASS", f"current revision: {rev}")
    return CheckResult("Alembic", "WARN", "could not determine revision")


def check_config() -> CheckResult:
    """Check configuration files."""
    if PathConfig.ENV_FILE.exists():
        return CheckResult("Config", "PASS", ".env present")
    if PathConfig.ENV_EXAMPLE.exists():
        return CheckResult("Config", "WARN", ".env missing (example exists)")
    return CheckResult("Config", "WARN", "no configuration files found")


def check_storage_dirs() -> CheckResult:
    """Check storage directories."""
    missing = []
    for subdir in ["cache", "exports", "logs", "models", "projects", "temp"]:
        d = PathConfig.STORAGE_DIR / subdir
        if not d.exists():
            missing.append(subdir)
    if not missing:
        return CheckResult("Storage Dirs", "PASS", "all directories present")
    return CheckResult("Storage Dirs", "WARN", f"missing: {', '.join(missing)}")


def check_writable() -> CheckResult:
    """Check write permissions."""
    test_file = PathConfig.STORAGE_DIR / ".write_test"
    try:
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        return CheckResult("Permissions", "PASS", "storage is writable")
    except Exception as e:
        return CheckResult("Permissions", "FAIL", str(e))


def check_disk_space() -> CheckResult:
    """Check available disk space."""
    usage = get_disk_usage()
    free = usage.get("free_gb", 0)
    if free > 10:
        return CheckResult("Disk Space", "PASS", f"{free} GB free")
    elif free > 1:
        return CheckResult("Disk Space", "WARN", f"{free} GB free (low)")
    return CheckResult("Disk Space", "FAIL", f"{free} GB free (critical)")


def check_backend_port() -> CheckResult:
    """Check if backend port is available."""
    port = ServerConfig.BACKEND_PORT
    if is_port_in_use(port):
        return CheckResult("Backend Port", "WARN", f"port {port} already in use")
    return CheckResult("Backend Port", "PASS", f"port {port} available")


def check_frontend_port() -> CheckResult:
    """Check if frontend port is available."""
    port = ServerConfig.FRONTEND_PORT
    if is_port_in_use(port):
        return CheckResult("Frontend Port", "WARN", f"port {port} already in use")
    return CheckResult("Frontend Port", "PASS", f"port {port} available")


def check_log_dir() -> CheckResult:
    """Check log directory."""
    if PathConfig.LOG_DIR.exists():
        return CheckResult("Log Dir", "PASS", str(PathConfig.LOG_DIR))
    return CheckResult("Log Dir", "WARN", "will be created on startup")


def check_project_dir() -> CheckResult:
    """Check project directory."""
    if PathConfig.PROJECTS_DIR.exists():
        count = len(list(PathConfig.PROJECTS_DIR.iterdir()))
        return CheckResult("Projects Dir", "PASS", f"{count} projects")
    return CheckResult("Projects Dir", "WARN", "will be created on startup")


def check_gpu() -> CheckResult:
    """Check for GPU (placeholder)."""
    try:
        code, out = run_command(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], timeout=5)
        if code == 0 and out.strip():
            return CheckResult("GPU", "PASS", out.strip())
    except Exception:
        pass
    return CheckResult("GPU", "WARN", "no GPU detected (placeholder)")


def run_all_checks() -> list[CheckResult]:
    """Run all diagnostic checks."""
    checks = [
        check_python_version(),
        check_venv(),
        check_backend_packages(),
        check_node(),
        check_npm(),
        check_frontend_deps(),
        check_sqlite(),
        check_database(),
        check_alembic(),
        check_config(),
        check_storage_dirs(),
        check_writable(),
        check_disk_space(),
        check_backend_port(),
        check_frontend_port(),
        check_log_dir(),
        check_project_dir(),
        check_gpu(),
    ]
    return checks


def print_results(checks: list[CheckResult]) -> None:
    """Print check results as a formatted table."""
    passed = sum(1 for c in checks if c.status == "PASS")
    warned = sum(1 for c in checks if c.status == "WARN")
    failed = sum(1 for c in checks if c.status == "FAIL")

    for c in checks:
        print(c)

    print(f"\n  {Style.DIM}Results: {passed} passed, {warned} warnings, {failed} failed{Style.RESET}")

    if failed == 0:
        print(f"  {Style.GREEN}{Style.BOLD}System is ready!{Style.RESET}")
    else:
        print(f"  {Style.RED}{Style.BOLD}Fix {failed} error(s) before running GARUDA{Style.RESET}")


def cmd_doctor() -> int:
    """Run the doctor command."""
    print(banner(f"GARUDA Doctor v{AppInfo.VERSION}"))
    print(header("System Diagnostics"))
    print()

    checks = run_all_checks()
    print_results(checks)

    return 0 if all(c.status != "FAIL" for c in checks) else 1
