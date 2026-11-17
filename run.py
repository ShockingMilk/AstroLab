#!/usr/bin/env python3
"""Launch Astro Assist."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_DIRECTORY = PROJECT_ROOT / "src"

sys.path.insert(0, str(SOURCE_DIRECTORY))

from astro_assist.app.application import Application


def main() -> None:
    """Start the application."""
    application = Application(project_root=PROJECT_ROOT)
    application.run()


if __name__ == "__main__":
    main()