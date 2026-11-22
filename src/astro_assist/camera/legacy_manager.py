"""High-level camera management and frame conversion."""

import cv2
import numpy as np
import subprocess

from typing import Optional

from astro_assist.camera.process import CameraProcess
from astro_assist.common.enums import CameraState
from astro_assist.common.exceptions import CameraError

class CameraManager:
    """Manage camera settings, process state, and image frames."""

    def __init__(self, settings: dict) -> None:
        self.settings = settings.copy()
        self.state = CameraState.DISCONNECTED

        self.width = 0
        self.height = 0
        self.framerate = 0
        self.rotation = 0
        self.sensor_mode = ""

        self.process: Optional[CameraProcess] = None
        self._pending_frame: Optional[bytes] = None

        self._apply_settings(self.settings)

    @property
    def frame_size(self) -> int:
        """Return the byte count of one YUV420 frame."""
        return self.width * self.height * 3 // 2

    def _apply_settings(self, settings: dict) -> None:
        """Apply dimensions and camera options from settings."""
        self.settings = settings.copy()

        self.width = int(settings["width"])
        self.height = int(settings["height"])
        self.framerate = int(settings["framerate"])
        self.rotation = int(settings.get("rotation", 0))
        self.sensor_mode = settings.get("sensor_mode", "")

    def build_command(self) -> list[str]:
        """Build the rpicam-vid command."""
        command = [
            self.settings.get("executable", "rpicam-vid"),
            "--nopreview",
            "--timeout",
            str(self.settings.get("timeout", 0)),
        ]

        if self.sensor_mode:
            command.extend(["--mode", self.sensor_mode])

        command.extend([
            "--codec",
            self.settings.get("pixel_format", "yuv420"),
            "--width",
            str(self.width),
            "--height",
            str(self.height),
            "--framerate",
            str(self.framerate),
            "--rotation",
            str(self.rotation),
            "--output",
            "-",
        ])

        return command

    def start(self) -> None:
        """Start the camera and confirm that a complete frame arrives."""
        if self.state == CameraState.STREAMING:
            return

        self.state = CameraState.STARTING
        self._pending_frame = None

        try:
            executable = self.settings.get("executable", "rpicam-vid")

            subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )

            self.process = CameraProcess(
                command=self.build_command(),
                frame_size=self.frame_size,
            )
            self.process.start()

            startup_timeout = float(self.settings.get("startup_timeout", 10))
            first_frame = self.process.wait_for_frame(timeout=startup_timeout)

            if first_frame is None:
                error = (
                    self.process.error_message
                    or "Timed out waiting for the first camera frame."
                )
                raise CameraError(error)

            self._pending_frame = first_frame
            self.state = CameraState.STREAMING

        except (
            OSError,
            subprocess.SubprocessError,
            RuntimeError,
            ValueError,
            CameraError,
        ) as exc:
            self.state = CameraState.ERROR

            if self.process is not None:
                self.process.stop()
                self.process = None

            raise CameraError(f"Unable to start camera: {exc}") from exc

    def stop(self) -> None:
        """Stop capture and release process resources."""
        self.state = CameraState.STOPPING

        if self.process is not None:
            self.process.stop()
            self.process = None

        self._pending_frame = None
        self.state = CameraState.DISCONNECTED

    def reconfigure(self, new_settings: dict) -> None:
        """Restart the camera using new settings.

        If the new settings fail, attempt to restore the previous
        configuration and stream.
        """
        previous_settings = self.settings.copy()

        self.stop()
        self._apply_settings(new_settings)

        try:
            self.start()
        except CameraError as original_error:
            self.stop()
            self._apply_settings(previous_settings)

            try:
                self.start()
            except CameraError as rollback_error:
                self.state = CameraState.ERROR
                raise CameraError(
                    "The requested profile failed, and the previous "
                    "camera configuration could not be restored. "
                    f"Original error: {original_error}. "
                    f"Recovery error: {rollback_error}"
                ) from rollback_error

            raise CameraError(
                "The requested profile could not be started. "
                "The previous profile has been restored. "
                f"Details: {original_error}"
            ) from original_error

    def get_frame(self) -> Optional[np.ndarray]:
        """Return the newest camera frame as a BGR image."""
        if self._pending_frame is not None:
            raw_frame = self._pending_frame
            self._pending_frame = None
        elif self.process is not None:
            raw_frame = self.process.get_frame()
        else:
            return None

        if raw_frame is None:
            if self.process is not None and self.process.error_message:
                self.state = CameraState.ERROR
            return None

        try:
            yuv_frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((self.height * 3 // 2, self.width))

            return cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)

        except (ValueError, cv2.error) as exc:
            self.state = CameraState.ERROR
            raise CameraError(f"Unable to decode camera frame: {exc}") from exc