"""Load and validate Astro Assist configuration."""

import json
import re
from pathlib import Path
from typing import Any

from astro_assist.common.exceptions import ConfigurationError

_SENSOR_MODE_PATTERN = re.compile(
    r"^\d+:\d+:(8|10|12):P$"
)

class ConfigLoader:
    """Load application settings and provide structured access."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.settings: dict[str, Any] = {}

    def get(self, *keys: str, default: Any = None) -> Any:
        """Retrieve a nested configuration value."""
        value: Any = self.settings

        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return default
            value = value[key]

        return value

    def load(self) -> dict[str, Any]:
        """Load and validate the JSON configuration."""
        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                self.settings = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(f"Unable to load configuration: {exc}") from exc

        self.validate()
        return self.settings

    def validate(self) -> None:
        """Validate required sections and their values."""
        required_sections = (
            "application",
            "camera",
            "profiles",
            "ui",
            "controls",
        )

        for section in required_sections:
            if section not in self.settings:
                raise ConfigurationError(f"Missing configuration section: {section}")

        application = self.settings["application"]
        if not isinstance(application, dict):
            raise ConfigurationError("Application configuration must be an object.")

        camera = self.settings["camera"]
        if not isinstance(camera, dict):
            raise ConfigurationError("Camera configuration must be an object.")

        self._validate_dimensions(camera, "camera")
        self._validate_rotation(camera, "camera")

        profiles = self.settings["profiles"]
        if not isinstance(profiles, dict) or "0" not in profiles:
            raise ConfigurationError("A calibration profile with key '0' is required.")

        for profile_id, profile in profiles.items():
            if not isinstance(profile, dict):
                raise ConfigurationError(f"Profile '{profile_id}' must be an object.")

            if not profile.get("name"):
                raise ConfigurationError(f"Profile '{profile_id}' requires a name.")

            profile_camera = profile.get("camera")
            if not isinstance(profile_camera, dict):
                raise ConfigurationError(f"Profile '{profile_id}' requires camera settings.")

            self._validate_dimensions(profile_camera, f"profile '{profile_id}'")
            self._validate_rotation(profile_camera, f"profile '{profile_id}'")
            self._validate_sensor_mode(profile_camera, profile_id)

            if profile.get("enabled", True):
                framerate = profile_camera.get("framerate")
                if not isinstance(framerate, int) or isinstance(framerate, bool) or framerate <= 0:
                    raise ConfigurationError(f"Profile '{profile_id}' requires a positive integer framerate.")

    @staticmethod
    def _validate_dimensions(
        settings: dict[str, Any],
        label: str,
    ) -> None:
        """Validate positive, even YUV420 output dimensions."""
        for key in ("width", "height"):
            value = settings.get(key)

            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ConfigurationError(f"{label}: '{key}' must be a positive integer.")

            if value % 2:
                raise ConfigurationError(f"{label}: '{key}' must be even for YUV420 output.")

    @staticmethod
    def _validate_rotation(
        settings: dict[str, Any],
        label: str,
    ) -> None:
        """Validate supported rpicam rotation values."""
        rotation = settings.get("rotation", 0)

        if rotation not in (0, 180):
            raise ConfigurationError(f"{label}: rotation must be 0 or 180 degrees.")

    @staticmethod
    def _validate_sensor_mode(
        settings: dict[str, Any],
        profile_id: str,
    ) -> None:
        """Validate the rpicam sensor mode string."""
        sensor_mode = settings.get("sensor_mode")

        if not isinstance(sensor_mode, str) or not _SENSOR_MODE_PATTERN.fullmatch(sensor_mode):
            raise ConfigurationError(
                f"Profile '{profile_id}' has an invalid sensor_mode. "
                "Expected width:height:bit-depth:P, for example "
                "'2028:1520:12:P'."
            )