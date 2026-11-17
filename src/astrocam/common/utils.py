"""Reusable application utilities."""

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, TypeVar


T = TypeVar("T")


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Constrain a value to the supplied range."""
    return max(minimum, min(value, maximum))


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_bytes(value: int) -> str:
    """Format a byte count into a human-readable string."""
    size = float(value)

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} TB"


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON file into a dictionary."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_command(
    command: list[str],
    timeout: float = 5.0,
) -> subprocess.CompletedProcess[str]:
    """Run a system command and capture its output."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def sanitize_filename(value: str) -> str:
    """Remove characters unsuitable for filenames."""
    value = re.sub(r"[^\w\- ]", "", value)
    return re.sub(r"\s+", "_", value).strip("_")


def switch(
    value: T,
    cases: Mapping[T, Callable[[T], Any] | Any],
    default: Callable[[T], Any] | Any = None,
) -> Any:
    """
    Provide a reusable Python switch/case equivalent.

    Callable cases receive the selected value. Literal cases are
    returned directly.
    """
    selected = cases.get(value, default)

    if callable(selected):
        return selected(value)

    return selected


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write a dictionary to a formatted JSON file."""
    ensure_directory(path.parent)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)