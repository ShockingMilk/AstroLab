"""Tests for configuration loading and validation."""

import json
import tempfile
import unittest
from pathlib import Path

from astro_assist.common.exceptions import ConfigurationError
from astro_assist.config.loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    """Test configuration loading."""

    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_directory.name) / "settings.json"

        self.valid_settings = {
            "application": {},
            "camera": {
                "width": 1280,
                "height": 720,
                "framerate": 30,
                "rotation": 180,
            },
            "profiles": {
                "0": {
                    "name": "Calibration",
                }
            },
            "ui": {},
            "controls": {},
        }

    # ------------------------------------------------------------------
    # Test setup and cleanup
    # ------------------------------------------------------------------

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    # ------------------------------------------------------------------
    # Configuration tests
    # ------------------------------------------------------------------

    def test_load_valid_configuration(self) -> None:
        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(self.valid_settings, file)

        loader = ConfigLoader(config_path=self.config_path)
        settings = loader.load()

        self.assertEqual(settings["camera"]["width"], 1280)

    def test_missing_calibration_profile(self) -> None:
        self.valid_settings["profiles"] = {}

        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(self.valid_settings, file)

        loader = ConfigLoader(config_path=self.config_path)

        with self.assertRaises(ConfigurationError):
            loader.load()

    def test_invalid_rotation(self) -> None:
        self.valid_settings["camera"]["rotation"] = 45

        with self.config_path.open("w", encoding="utf-8") as file:
            json.dump(self.valid_settings, file)

        loader = ConfigLoader(config_path=self.config_path)

        with self.assertRaises(ConfigurationError):
            loader.load()


if __name__ == "__main__":
    unittest.main()