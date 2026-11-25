"""Tests for main window command and live-controls behavior."""

import unittest

from unittest.mock import MagicMock, patch

from astro_assist.common.exceptions import CameraError
from astro_assist.ui.main_window import MainWindow


class MainWindowTests(unittest.TestCase):
    """Test main window behavior without starting Tkinter."""

    def setUp(self) -> None:
        self.window = MainWindow.__new__(MainWindow)

        self.window.root = MagicMock()
        self.window.camera = MagicMock()
        self.window.running = True
        self.window.fullscreen = True
        self.window.live_controls_open = False

        self.window.live_controls = MagicMock()
        self.window.controls = MagicMock()
        self.window.preview = MagicMock()
        self.window.status = MagicMock()
        self.window.header = MagicMock()

        self.window.current_profile = "0"
        self.window.profiles = {
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
        }

        self.window.settings = {
            "application": {
                "allow_windowed_mode": True,
                "fallback_resolution": [1024, 600],
            },
            "camera": {
                "width": 1280,
                "height": 960,
                "rotation": 180,
            },
            "profiles": self.window.profiles,
            "ui": {},
        }

    def test_live_controls_open(self) -> None:
        self.window._handle_live_controls()

        self.window.live_controls.grid.assert_called_once()
        self.window.live_controls.grid_remove.assert_not_called()
        self.assertTrue(self.window.live_controls_open)
        self.window.controls.set_live_controls_open.assert_called_once_with(
            True
        )

    def test_live_controls_close(self) -> None:
        self.window.live_controls_open = True

        self.window._handle_live_controls()

        self.window.live_controls.grid_remove.assert_called_once()
        self.window.live_controls.grid.assert_not_called()
        self.assertFalse(self.window.live_controls_open)
        self.window.controls.set_live_controls_open.assert_called_once_with(
            False
        )

    def test_crosshair_toggle_is_forwarded_to_preview(self) -> None:
        self.window._handle_crosshair()

        self.window.preview.toggle_crosshair.assert_called_once()

    def test_display_mode_switches_out_of_fullscreen(self) -> None:
        self.window._handle_display_mode()

        self.assertFalse(self.window.fullscreen)
        self.window.root.attributes.assert_called_once_with(
            "-fullscreen",
            False,
        )
        self.window.root.geometry.assert_called_once_with("1024x600")

    def test_display_mode_switches_into_fullscreen(self) -> None:
        self.window.fullscreen = False

        self.window._handle_display_mode()

        self.assertTrue(self.window.fullscreen)
        self.window.root.attributes.assert_called_once_with(
            "-fullscreen",
            True,
        )

    def test_profile_switch_reconfigures_camera(self) -> None:
        self.window._update_profile_display = MagicMock()

        self.window._handle_profile("1")

        self.window.camera.reconfigure.assert_called_once_with(
            {
                "width": 1280,
                "height": 960,
                "rotation": 180,
                "sensor_mode": "2028:1520:12:P",
                "framerate": 30,
            }
        )

        self.assertEqual(self.window.current_profile, "1")
        self.window._update_profile_display.assert_called_once()

    def test_current_profile_is_not_restarted(self) -> None:
        self.window._handle_profile("0")

        self.window.camera.reconfigure.assert_not_called()

    def test_disabled_profile_is_not_selected(self) -> None:
        self.window.profiles["1"]["enabled"] = False

        self.window._handle_profile("1")

        self.window.camera.reconfigure.assert_not_called()
        self.assertEqual(self.window.current_profile, "0")

    def test_profile_failure_keeps_current_profile(self) -> None:
        self.window.camera.reconfigure.side_effect = CameraError(
            "Unable to start profile."
        )
        self.window.camera.state.value = "streaming"

        self.window._handle_profile("1")

        self.assertEqual(self.window.current_profile, "0")
        self.window.status.update_status.assert_any_call(
            "Camera: Previous profile restored"
        )

    def test_terminate_stops_camera_and_destroys_window(self) -> None:
        self.window.terminate()

        self.assertFalse(self.window.running)
        self.window.camera.stop.assert_called_once()
        self.window.root.destroy.assert_called_once()

    def test_terminate_does_not_run_twice(self) -> None:
        self.window.running = False

        self.window.terminate()

        self.window.camera.stop.assert_not_called()
        self.window.root.destroy.assert_not_called()


if __name__ == "__main__":
    unittest.main()