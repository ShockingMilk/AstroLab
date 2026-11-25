"""Unit tests for Picamera2 live control handling."""

import unittest
from unittest.mock import MagicMock, patch

from astro_assist.camera.picamera_backend import PicameraBackend
from astro_assist.camera.manager import CameraManager
from astro_assist.common.enums import CameraState
from astro_assist.common.exceptions import CameraError


SETTINGS = {
    "sensor_mode": "4056:3040:12:P",
    "width": 1280,
    "height": 960,
    "framerate": 10,
    "rotation": 180,
}

CONTROLS = {
    "AeEnable": (False, True, True),
    "AwbEnable": (False, True, True),
    "ExposureTime": (1, 66666, 20000),
    "AnalogueGain": (1.0, 16.0, 1.0),
    "ColourGains": (
        (0.0, 0.0),
        (32.0, 32.0),
        None,
    ),
    "Brightness": (-1.0, 1.0, 0.0),
}

METADATA = {
    "AeEnable": True,
    "AwbEnable": True,
    "ExposureTime": 20000,
    "AnalogueGain": 1.0,
    "ColourGains": (1.0, 1.0),
    "Brightness": 0.0,
}


class PicameraBackendControlTests(unittest.TestCase):
    """Test control validation and application without camera hardware."""

    def setUp(self):
        self.backend = PicameraBackend(SETTINGS)

        self.camera = MagicMock()
        self.camera.camera_controls = CONTROLS
        self.camera.capture_metadata.return_value = METADATA.copy()

        self.backend._camera = self.camera
        self.backend.state = CameraState.STREAMING

    def test_camera_controls_returns_supported_ranges(self):
        self.assertEqual(self.backend.camera_controls, CONTROLS)

    def test_get_controls_reads_capture_metadata(self):
        values = self.backend.get_controls()

        self.assertEqual(values["ExposureTime"], 20000)
        self.assertEqual(values["ColourGains"], (1.0, 1.0))
        self.camera.capture_metadata.assert_called_once()

    def test_get_control_info_includes_range_default_and_current(self):
        info = self.backend.get_control_info("ExposureTime")

        self.assertEqual(
            info,
            {
                "name": "ExposureTime",
                "minimum": 1,
                "maximum": 66666,
                "default": 20000,
                "current": 20000,
            },
        )

    def test_unknown_control_info_is_rejected(self):
        with self.assertRaises(CameraError):
            self.backend.get_control_info("NotAControl")

    def test_manual_exposure_disables_auto_exposure(self):
        self.backend.set_controls({"ExposureTime": 30000})

        self.camera.set_controls.assert_called_once_with(
            {
                "ExposureTime": 30000,
                "AeEnable": False,
            }
        )

    def test_manual_gain_disables_auto_exposure(self):
        self.backend.set_controls({"AnalogueGain": 2.0})

        self.camera.set_controls.assert_called_once_with(
            {
                "AnalogueGain": 2.0,
                "AeEnable": False,
            }
        )

    def test_manual_white_balance_disables_auto_white_balance(self):
        self.backend.set_controls({"ColourGains": (2.0, 2.0)})

        self.camera.set_controls.assert_called_once_with(
            {
                "ColourGains": (2.0, 2.0),
                "AwbEnable": False,
            }
        )

    def test_explicit_auto_disable_is_preserved(self):
        self.backend.set_controls(
            {
                "AeEnable": False,
                "ExposureTime": 30000,
            }
        )

        self.camera.set_controls.assert_called_once_with(
            {
                "AeEnable": False,
                "ExposureTime": 30000,
            }
        )

    def test_conflicting_auto_mode_is_rejected(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls(
                {
                    "AeEnable": True,
                    "ExposureTime": 30000,
                }
            )

        self.camera.set_controls.assert_not_called()

    def test_unknown_control_is_rejected_before_apply(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls({"NotAControl": 1})

        self.camera.set_controls.assert_not_called()

    def test_out_of_range_scalar_is_rejected(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls({"ExposureTime": 70000})

        self.camera.set_controls.assert_not_called()

    def test_out_of_range_tuple_value_is_rejected(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls({"ColourGains": (2.0, 40.0)})

        self.camera.set_controls.assert_not_called()

    def test_tuple_control_requires_correct_length(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls({"ColourGains": (2.0,)})

        self.camera.set_controls.assert_not_called()

    def test_boolean_control_requires_boolean(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls({"AeEnable": 1})

        self.camera.set_controls.assert_not_called()

    def test_integer_control_rejects_float(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls({"ExposureTime": 1000.5})

        self.camera.set_controls.assert_not_called()

    def test_non_finite_value_is_rejected(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls({"Brightness": float("nan")})

        self.camera.set_controls.assert_not_called()

    def test_empty_controls_are_rejected(self):
        with self.assertRaises(CameraError):
            self.backend.set_controls({})

        self.camera.set_controls.assert_not_called()

    def test_controls_require_streaming(self):
        self.backend.state = CameraState.DISCONNECTED

        with self.assertRaises(CameraError):
            self.backend.get_controls()

        with self.assertRaises(CameraError):
            self.backend.set_controls({"Brightness": 0.5})

    def test_picamera_errors_are_wrapped(self):
        self.camera.set_controls.side_effect = RuntimeError("camera fault")

        with self.assertRaises(CameraError):
            self.backend.set_controls({"Brightness": 0.5})


class CameraManagerControlTests(unittest.TestCase):
    """Test the public manager interface."""

    @patch("astro_assist.camera.manager.PicameraBackend")
    def test_manager_exposes_control_api(self, backend_class):
        backend = backend_class.return_value
        backend.camera_controls = CONTROLS
        backend.get_controls.return_value = {"ExposureTime": 1000}
        backend.get_control_info.return_value = {
            "name": "ExposureTime",
            "current": 1000,
        }

        manager = CameraManager(SETTINGS)

        self.assertEqual(manager.camera_controls, CONTROLS)
        self.assertEqual(
            manager.get_controls(),
            {"ExposureTime": 1000},
        )
        self.assertEqual(
            manager.get_control_info("ExposureTime"),
            {
                "name": "ExposureTime",
                "current": 1000,
            },
        )

        manager.set_controls({"ExposureTime": 2000})

        backend.set_controls.assert_called_once_with(
            {"ExposureTime": 2000}
        )


if __name__ == "__main__":
    unittest.main()