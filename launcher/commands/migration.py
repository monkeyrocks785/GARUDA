"""GARUDA Launcher - Migration commands."""

import sys

from launcher.config import PathConfig, AppInfo
from launcher.style import Style, ok, fail, info, header, banner
from launcher.utils import run_command


def cmd_migrate() -> int:
    """Run Alembic migrations."""
    print(banner(f"GARUDA Migrate v{AppInfo.VERSION}"))
    print(header("Running Migrations"))
    print()

    if not PathConfig.ALEMBIC_INI.exists():
        print(fail("alembic.ini not found"))
        return 1

    if not PathConfig.BACKEND_PYTHON.exists():
        print(fail("Backend Python not found"))
        return 1

    print(info("Applying Alembic migrations..."))
    code, out = run_command(
        [str(PathConfig.BACKEND_PYTHON), "-m", "alembic", "-c", str(PathConfig.ALEMBIC_INI), "upgrade", "head"],
        cwd=str(PathConfig.BACKEND_DIR),
        timeout=60,
    )

    if code == 0:
        print(ok("Migrations applied successfully"))
        if out.strip():
            for line in out.strip().splitlines():
                print(f"    {line}")
    else:
        print(fail(f"Migration failed"))
        if out.strip():
            for line in out.strip().splitlines():
                print(f"    {line}")
        return 1

    print()
    return 0


def cmd_makemigration() -> int:
    """Create a new Alembic migration."""
    print(banner(f"GARUDA Make Migration v{AppInfo.VERSION}"))
    print(header("Creating Migration"))
    print()

    if len(sys.argv) < 3:
        print(fail("Usage: python main.py makemigration <message>"))
        return 1

    message = sys.argv[2]

    if not PathConfig.ALEMBIC_INI.exists():
        print(fail("alembic.ini not found"))
        return 1

    if not PathConfig.BACKEND_PYTHON.exists():
        print(fail("Backend Python not found"))
        return 1

    print(info(f"Creating migration: {message}"))
    code, out = run_command(
        [str(PathConfig.BACKEND_PYTHON), "-m", "alembic", "-c", str(PathConfig.ALEMBIC_INI), "revision", "--autogenerate", "-m", message],
        cwd=str(PathConfig.BACKEND_DIR),
        timeout=60,
    )

    if code == 0:
        print(ok(f"Migration created: {message}"))
        if out.strip():
            for line in out.strip().splitlines():
                print(f"    {line}")
    else:
        print(fail("Failed to create migration"))
        if out.strip():
            for line in out.strip().splitlines():
                print(f"    {line}")
        return 1

    print()
    return 0
