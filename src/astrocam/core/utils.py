from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


def switch(
    value: Any,
    cases: Mapping[Any, Any],
    default: Any = None,
    *args,
    **kwargs,
) -> Any:
    """
    Python equivalent of a simple switch/case.

    Callable cases are executed.
    Non-callable cases are returned directly.

    Example:

        switch(
            action,
            {
                "start": start_camera,
                "stop": stop_camera,
            },
            default=unknown_action,
        )
    """

    selected = cases.get(
        value,
        default,
    )

    if callable(selected):
        return selected(
            *args,
            **kwargs,
        )

    return selected


def clamp(
    value,
    minimum,
    maximum,
):
    return max(
        minimum,
        min(value, maximum),
    )


def expand_path(
    path: str | Path,
) -> Path:
    return Path(
        path
    ).expanduser().resolve()


def ensure_directory(
    path: str | Path,
) -> Path:
    directory = expand_path(path)

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def format_bytes(
    num_bytes: int,
    decimals: int = 1,
) -> str:

    if num_bytes < 0:
        return "0 B"

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
        "PB",
    ]

    value = float(num_bytes)

    for unit in units:
        if (
            value < 1024
            or unit == units[-1]
        ):
            if unit == "B":
                return f"{int(value)} {unit}"

            return (
                f"{value:.{decimals}f} "
                f"{unit}"
            )

        value /= 1024

    return f"{value:.{decimals}f} PB"


def safe_int(
    value,
    default=0,
):
    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def safe_float(
    value,
    default=0.0,
):
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def normalize_size(value):
    if value is None:
        return None

    if (
        isinstance(
            value,
            (list, tuple),
        )
        and len(value) == 2
    ):
        try:
            return (
                int(value[0]),
                int(value[1]),
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    return None


def run_command(
    command: Sequence[str],
    timeout: float = 5.0,
):
    try:
        return subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (
        OSError,
        subprocess.SubprocessError,
    ):
        return None


def disk_usage(
    path: str | Path,
):
    return shutil.disk_usage(
        expand_path(path)
    )


def filename_safe(
    value: str,
) -> str:

    allowed = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_-"
    )

    cleaned = "".join(
        char
        if char in allowed
        else "_"
        for char in str(value)
    )

    while "__" in cleaned:
        cleaned = cleaned.replace(
            "__",
            "_",
        )

    return (
        cleaned.strip("_")
        or "capture"
    )


def now_timestamp() -> str:
    return datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )


def split_lines(
    text: str,
    maximum_length: int,
):
    """
    Basic word-aware text wrapping.
    """

    words = str(text).split()

    if not words:
        return [""]

    lines = []
    current = ""

    for word in words:
        candidate = (
            word
            if not current
            else f"{current} {word}"
        )

        if len(candidate) <= maximum_length:
            current = candidate
        else:
            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


def estimate_image_size(
    width: int,
    height: int,
    channels: int = 3,
    compression_factor: float = 1.5,
) -> int:

    raw_size = (
        width
        * height
        * channels
    )

    return int(
        raw_size
        * compression_factor
    )


def estimate_video_size(
    width: int,
    height: int,
    fps: float,
    duration_seconds: float,
    bytes_per_pixel: float = 0.08,
    safety_factor: float = 1.5,
) -> int:

    bytes_per_second = (
        width
        * height
        * max(1.0, fps)
        * bytes_per_pixel
    )

    return int(
        bytes_per_second
        * max(
            1.0,
            duration_seconds,
        )
        * safety_factor
    )