"""Load and validate Astro Assist configuration."""

import json
from pathlib import Path
from typing import Any

from astro_assist.common.exceptions import ConfigurationError


class ConfigLoader:
    """Load application settings and provide structured access."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.settings: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Configuration access
    # ------------------------------------------------------------------

    def get(self, *keys: str, default: Any = None) -> Any:
        """Retrieve a nested configuration value."""
        value: Any = self.settings

        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default
            value = value[key]

        return value

    def load(self) -> dict[str, Any]:
        """Load configuration from the JSON file."""
        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                self.settings = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(
                f"Unable to load configuration: {exc}"
            ) from exc

        self.validate()
        return self.settings

    def validate(self) -> None:
        """Validate required configuration sections and values."""
        required_sections = (
            "application",
            "camera",
            "profiles",
            "ui",
            "controls",
        )

        for section in required_sections:
            if section not in self.settings:
                raise ConfigurationError(
                    f"Missing configuration section: {section}"
                )

        camera = self.settings["camera"]

        for key in ("width", "height", "framerate"):
            if not isinstance(camera.get(key), int) or camera[key] <= 0:
                raise ConfigurationError(
                    f"Camera setting '{key}' must be a positive integer."
                )

        if camera.get("rotation", 0) not in (0, 90, 180, 270):
            raise ConfigurationError(
                "Camera rotation must be 0, 90, 180, or 270 degrees."
            )

        if "0" not in self.settings["profiles"]:
            raise ConfigurationError(
                "Calibration profile '0' is required."
            )