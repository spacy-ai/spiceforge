from __future__ import annotations

from pathlib import Path


def validate_filename(filename: str) -> str:
    if not filename:
        raise ValueError("Filename must not be empty")
    if "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename: must not contain path separators")
    if ".." in filename:
        raise ValueError("Invalid filename: must not contain '..'")
    return filename


def safe_path(base_dir: Path, user_input: str) -> Path:
    resolved = (base_dir / user_input).resolve()
    if not resolved.is_relative_to(base_dir.resolve()):
        raise ValueError("Path traversal attempt blocked")
    return resolved
