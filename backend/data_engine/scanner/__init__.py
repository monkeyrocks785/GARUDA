"""Data Engine scanner - Scan folders for datasets."""

from pathlib import Path

from data_engine.config import ALL_EXTENSIONS


def scan_folder(folder_path: Path, recursive: bool = True) -> list[dict]:
    """Scan a folder for supported dataset files."""
    if not folder_path.exists() or not folder_path.is_dir():
        return []

    results = []
    pattern = "**/*" if recursive else "*"

    for file_path in folder_path.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in ALL_EXTENSIONS:
            stat = file_path.stat()
            results.append({
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix.lower(),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })

    return results


def scan_for_duplicates(folder_path: Path) -> list[list[dict]]:
    """Scan folder and group files by checksum."""
    import hashlib

    files_by_hash: dict[str, list[dict]] = {}

    for file_path in folder_path.rglob("*"):
        if file_path.is_file():
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            checksum = h.hexdigest()

            if checksum not in files_by_hash:
                files_by_hash[checksum] = []
            files_by_hash[checksum].append({
                "path": str(file_path),
                "name": file_path.name,
                "size": file_path.stat().st_size,
            })

    return [files for files in files_by_hash.values() if len(files) > 1]
