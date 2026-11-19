"""Tests for camera command construction."""

import unittest

from astro_assist.camera.manager import CameraManager


class CameraCommandTests(unittest.TestCase):
    """Test rpicam-vid command construction."""

    def setUp(self) -> None:
        self.settings = {
            "executable": "rpicam-vid",
            "sensor_mode": "2028:1520:12:P",
            "width": 1280,
            "height": 960,
            "framerate": 30,
            "rotation": 180,
            "timeout": 0,
            "pixel_format": "yuv420",
            "nopreview": True,
        }

        self.camera = CameraManager(self.settings)

    def test_command_includes_sensor_mode(self) -> None:
        command = self.camera.build_command()

        mode_index = command.index("--mode")
        self.assertEqual(
            command[mode_index + 1],
            "2028:1520:12:P",
        )

    def test_command_uses_preview_dimensions(self) -> None:
        command = self.camera.build_command()

        width_index = command.index("--width")
        height_index = command.index("--height")

        self.assertEqual(command[width_index + 1], "1280")
        self.assertEqual(command[height_index + 1], "960")

    def test_command_uses_yuv420_output(self) -> None:
        command = self.camera.build_command()

        codec_index = command.index("--codec")
        self.assertEqual(
            command[codec_index + 1],
            "yuv420",
        )

    def test_frame_size_uses_output_dimensions(self) -> None:
        self.assertEqual(
            self.camera.frame_size,
            1280 * 960 * 3 // 2,
        )

    def test_command_includes_rotation_and_framerate(self) -> None:
        command = self.camera.build_command()

        self.assertEqual(
            command[command.index("--rotation") + 1],
            "180",
        )
        self.assertEqual(
            command[command.index("--framerate") + 1],
            "30",
        )


if __name__ == "__main__":
    unittest.main()