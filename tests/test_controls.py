"""Tests for live camera adjustment controls."""

import unittest

from unittest.mock import MagicMock

from astro_assist.common.exceptions import CameraError
from astro_assist.ui.controls import LiveControlsPanel


class LiveControlsPanelTests(unittest.TestCase):
    """Test live control behavior without creating a Tk window."""

    def setUp(self) -> None:
        self.panel = LiveControlsPanel.__new__(LiveControlsPanel)

        self.panel.camera = MagicMock()
        self.panel.on_status = MagicMock()

        self.panel.supported = {
            "ExposureTime": (1, 66666, 20000),
            "AnalogueGain": (1.0, 16.0, 1.0),
            "ColourGains": (0.0, 32.0, None),
            "Brightness": (-1.0, 1.0, 0.0),
        }

        self.panel._value_labels = {
            "ExposureTime": MagicMock(),
            "AnalogueGain": MagicMock(),
            "ColourGains:0": MagicMock(),
            "ColourGains:1": MagicMock(),
            "Brightness": MagicMock(),
        }

        self.panel._scales = {}
        self.panel._auto_variables = {}
        self.panel._dependent_controls = {
            "AeEnable": [],
            "AwbEnable": [],
        }

        self.panel._colour_gain_values = [1.0, 1.0]

    def test_integer_slider_value_is_converted_to_integer(self) -> None:
        self.panel._on_scalar_change(
            "ExposureTime",
            "30000.0",
            self.panel._exposure_value,
        )

        self.panel.camera.set_controls.assert_called_once_with(
            {"ExposureTime": 30000}
        )

    def test_float_slider_value_is_preserved(self) -> None:
        self.panel._on_scalar_change(
            "AnalogueGain",
            "2.5",
            self.panel._decimal_value,
        )

        self.panel.camera.set_controls.assert_called_once_with(
            {"AnalogueGain": 2.5}
        )

    def test_scalar_change_updates_visible_value(self) -> None:
        self.panel._on_scalar_change(
            "Brightness",
            "0.5",
            self.panel._decimal_value,
        )

        self.panel._value_labels["Brightness"].configure.assert_called_once_with(
            text="0.50"
        )

    def test_red_gain_preserves_blue_gain(self) -> None:
        self.panel._on_colour_gain_change(0, "2.5")

        self.panel.camera.set_controls.assert_called_once_with(
            {"ColourGains": (2.5, 1.0)}
        )

    def test_blue_gain_preserves_red_gain(self) -> None:
        self.panel._colour_gain_values = [2.0, 1.0]

        self.panel._on_colour_gain_change(1, "3.5")

        self.panel.camera.set_controls.assert_called_once_with(
            {"ColourGains": (2.0, 3.5)}
        )

    def test_colour_gain_updates_visible_value(self) -> None:
        self.panel._on_colour_gain_change(0, "2.5")

        self.panel._value_labels["ColourGains:0"].configure.assert_called_once_with(
            text="2.50"
        )

    def test_toggle_auto_applies_boolean_value(self) -> None:
        variable = MagicMock()
        variable.get.return_value = False

        self.panel._auto_variables = {"AeEnable": variable}
        self.panel._apply_auto_states = MagicMock()

        self.panel._toggle_auto("AeEnable")

        self.panel.camera.set_controls.assert_called_once_with(
            {"AeEnable": False}
        )
        self.panel._apply_auto_states.assert_called_once()

    def test_manual_controls_disabled_when_auto_is_enabled(self) -> None:
        auto_variable = MagicMock()
        auto_variable.get.return_value = True

        manual_control = MagicMock()

        self.panel._auto_variables = {"AeEnable": auto_variable}
        self.panel._dependent_controls = {
            "AeEnable": [manual_control],
            "AwbEnable": [],
        }

        self.panel._apply_auto_states()

        manual_control.configure.assert_called_once_with(
            state="disabled"
        )

    def test_manual_controls_enabled_when_auto_is_disabled(self) -> None:
        auto_variable = MagicMock()
        auto_variable.get.return_value = False

        manual_control = MagicMock()

        self.panel._auto_variables = {"AeEnable": auto_variable}
        self.panel._dependent_controls = {
            "AeEnable": [manual_control],
            "AwbEnable": [],
        }

        self.panel._apply_auto_states()

        manual_control.configure.assert_called_once_with(
            state="normal"
        )

    def test_successful_adjustment_updates_status(self) -> None:
        self.panel._apply_controls({"Brightness": 0.5})

        self.panel.camera.set_controls.assert_called_once_with(
            {"Brightness": 0.5}
        )
        self.panel.on_status.assert_called_once_with(
            "Camera adjustments updated"
        )

    def test_camera_error_is_reported_without_crashing(self) -> None:
        self.panel.camera.set_controls.side_effect = CameraError(
            "Camera is not streaming."
        )

        self.panel._apply_controls({"Brightness": 0.5})

        self.panel.on_status.assert_called_once_with(
            "Adjustment failed: Camera is not streaming."
        )


if __name__ == "__main__":
    unittest.main()