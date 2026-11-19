"""Tests for Astro Assist profile configuration."""

import json
import tempfile
import unittest

from pathlib import Path

from astro_assist.common.exceptions import ConfigurationError
from astro_assist.config.loader import ConfigLoader


def valid_settings() -> dict:
    """Return a minimal valid application configuration."""
    return {
        "application": {
            "name": "Astro Assist",
            "fullscreen": True,
            "allow_windowed_mode": True,
            "fallback_resolution": [1024, 600],
        },
        "camera": {
            "width": 1280,
            "height": 960,
            "framerate": 30,
            "rotation": 180,
        },
        "profiles": {
            "0": {
                "name": "Calibration",
                "enabled": True,
                "camera": {
                    "sensor_mode": "4056:3040:12:P",
                    "width": 1280,
                    "height": 960,
                    "framerate": 10,
                    "rotation": 180,
                },
            },
            "1": {
                "name": "Moon",
                "enabled": True,
                "camera": {
                    "sensor_mode": "2028:1520:12:P",
                    "width": 1280,
                    "height": 960,
                    "framerate": 30,
                    "rotation": 180,
                },
            },
        },
        "ui": {},
        "controls": {},
    }


class ConfigLoaderTests(unittest.TestCase):
    """Test configuration loading and validation."""

    def load_settings(self, settings: dict) -> ConfigLoader:
        """Write settings to a temporary file and load them."""
        temporary_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            encoding="utf-8",
            delete=False,
        )

        try:
            json.dump(settings, temporary_file)
            temporary_file.close()

            loader = ConfigLoader(Path(temporary_file.name))
            loader.load()
            return loader
        finally:
            Path(temporary_file.name).unlink(missing_ok=True)

    def test_valid_profiles_load(self) -> None:
        loader = self.load_settings(valid_settings())

        self.assertIn("0", loader.settings["profiles"])
        self.assertIn("1", loader.settings["profiles"])

    def test_calibration_profile_is_required(self) -> None:
        settings = valid_settings()
        del settings["profiles"]["0"]

        with self.assertRaises(ConfigurationError):
            self.load_settings(settings)

    def test_invalid_sensor_mode_is_rejected(self) -> None:
        settings = valid_settings()
        settings["profiles"]["1"]["camera"]["sensor_mode"] = (
            "2028x1520"
        )

        with self.assertRaises(ConfigurationError):
            self.load_settings(settings)

    def test_unsupported_rotation_is_rejected(self) -> None:
        settings = valid_settings()
        settings["profiles"]["1"]["camera"]["rotation"] = 90

        with self.assertRaises(ConfigurationError):
            self.load_settings(settings)

    def test_odd_output_dimensions_are_rejected(self) -> None:
        settings = valid_settings()
        settings["profiles"]["1"]["camera"]["width"] = 1279

        with self.assertRaises(ConfigurationError):
            self.load_settings(settings)

    def test_non_positive_framerate_is_rejected(self) -> None:
        settings = valid_settings()
        settings["profiles"]["1"]["camera"]["framerate"] = 0

        with self.assertRaises(ConfigurationError):
            self.load_settings(settings)


if __name__ == "__main__":
    unittest.main()