"""GARUDA Launcher - Cleanup commands."""

import shutil

from launcher.config import PathConfig, AppInfo
from launcher.style import Style, ok, info, header, banner


def cmd_clean() -> int:
    """Delete temporary files and cache only."""
    print(banner(f"GARUDA Clean v{AppInfo.VERSION}"))
    print(header("Cleaning Temporary Files"))
    print()

    cleaned = 0

    for name, path in [("cache", PathConfig.CACHE_DIR), ("temp", PathConfig.TEMP_DIR)]:
        if path.exists():
            count = sum(1 for _ in path.rglob("*") if _.is_file())
            shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=True)
            print(ok(f"Cleaned {name}/ ({count} files)"))
            cleaned += count

    # Clean __pycache__ directories
    pycache_count = 0
    for pycache in PathConfig.PROJECT_ROOT.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache, ignore_errors=True)
            pycache_count += 1
    if pycache_count:
        print(ok(f"Cleaned {pycache_count} __pycache__ directories"))

    # Clean .pytest_cache
    pytest_count = 0
    for pytest_cache in PathConfig.PROJECT_ROOT.rglob(".pytest_cache"):
        if pytest_cache.is_dir():
            shutil.rmtree(pytest_cache, ignore_errors=True)
            pytest_count += 1
    if pytest_count:
        print(ok(f"Cleaned {pytest_count} .pytest_cache directories"))

    print()
    if cleaned or pycache_count or pytest_count:
        print(ok(f"Cleanup complete"))
    else:
        print(info("Nothing to clean"))
    print()
    return 0


def cmd_reset_cache() -> int:
    """Clear cache without touching projects."""
    print(banner(f"GARUDA Reset Cache v{AppInfo.VERSION}"))
    print(header("Resetting Cache"))
    print()

    cleaned = 0

    if PathConfig.CACHE_DIR.exists():
        count = sum(1 for _ in PathConfig.CACHE_DIR.rglob("*") if _.is_file())
        shutil.rmtree(PathConfig.CACHE_DIR)
        PathConfig.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print(ok(f"Cache cleared ({count} files)"))
        cleaned += count

    for pycache in PathConfig.PROJECT_ROOT.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache, ignore_errors=True)
            cleaned += 1

    print()
    print(ok("Cache reset complete"))
    print()
    return 0
