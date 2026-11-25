"""High-level camera manager."""

import numpy as np

from typing import Any, Optional

from astro_assist.camera.picamera_backend import PicameraBackend
from astro_assist.common.enums import CameraState
from astro_assist.common.exceptions import CameraError


class CameraManager:
    """Provide a stable interface between the UI and camera backend."""

    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = settings.copy()
        self.backend = PicameraBackend(settings)
        self.state = CameraState.DISCONNECTED

    @property
    def width(self) -> int:
        return self.backend.width

    @property
    def height(self) -> int:
        return self.backend.height

    @property
    def framerate(self) -> int:
        return self.backend.framerate

    @property
    def rotation(self) -> int:
        return self.backend.rotation

    @property
    def sensor_mode(self) -> str:
        return self.backend.sensor_mode

    @property
    def camera_controls(self) -> dict[str, Any]:
        """Return controls supported by the active camera."""
        return self.backend.camera_controls

    def get_control_info(self, name: str) -> dict[str, Any]:
        """Return range, default, and current value for one control."""
        return self.backend.get_control_info(name)

    def get_controls(self) -> dict[str, Any]:
        """Return current values reported by camera metadata."""
        return self.backend.get_controls()

    def start(self) -> None:
        """Start the configured camera backend."""
        try:
            self.backend.start()
            self.state = self.backend.state
        except CameraError:
            self.state = self.backend.state
            raise

    def stop(self) -> None:
        """Stop the camera backend."""
        self.backend.stop()
        self.state = self.backend.state

    def get_frame(self) -> Optional[np.ndarray]:
        """Return the newest BGR camera frame."""
        frame = self.backend.get_frame()
        self.state = self.backend.state
        return frame

    def set_controls(self, controls: dict[str, Any]) -> None:
        """Validate and apply runtime camera controls."""
        self.backend.set_controls(controls)

    def reconfigure(self, new_settings: dict[str, Any]) -> None:
        """Switch profiles, restoring the previous profile on failure."""
        previous_settings = self.settings.copy()

        self.stop()

        try:
            self.backend = PicameraBackend(new_settings)
            self.backend.start()
            self.settings = new_settings.copy()
            self.state = self.backend.state
        except CameraError as original_error:
            self.backend.stop()
            self.backend = PicameraBackend(previous_settings)

            try:
                self.backend.start()
                self.state = self.backend.state
            except CameraError as rollback_error:
                self.state = CameraState.ERROR

                raise CameraError(
                    "The requested profile failed, and the previous camera configuration could not be restored. "
                    f"Original error: {original_error}. Recovery error: {rollback_error}"
                ) from rollback_error

            raise CameraError(
                "The requested profile could not be started. The previous profile has been restored. "
                f"Details: {original_error}"
            ) from original_error