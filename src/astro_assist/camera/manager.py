"""High-level camera management and frame conversion."""

import subprocess
from typing import Optional

import cv2
import numpy as np

from astro_assist.camera.process import CameraProcess
from astro_assist.common.enums import CameraState
from astro_assist.common.exceptions import CameraError


class CameraManager:
    """Manage camera settings, process state, and image frames."""

    def __init__(self, settings: dict) -> None:
        self.settings = settings
        self.state = CameraState.DISCONNECTED

        self.width = int(settings["width"])
        self.height = int(settings["height"])
        self.framerate = int(settings["framerate"])
        self.rotation = int(settings.get("rotation", 0))

        self.process: Optional[CameraProcess] = None

    # ------------------------------------------------------------------
    # Camera information
    # ------------------------------------------------------------------

    @property
    def frame_size(self) -> int:
        """Return the number of bytes in one YUV420 frame."""
        return self.width * self.height * 3 // 2

    def build_command(self) -> list[str]:
        """Build the rpicam-vid command."""
        command = [
            self.settings.get("executable", "rpicam-vid"),
            "--nopreview",
            "--timeout",
            str(self.settings.get("timeout", 0)),
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
        ]

        return command

    # ------------------------------------------------------------------
    # Camera lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the camera stream."""
        if self.state == CameraState.STREAMING:
            return

        try:
            subprocess.run(
                [self.settings.get("executable", "rpicam-vid"), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )

            self.state = CameraState.STARTING

            self.process = CameraProcess(
                command=self.build_command(),
                frame_size=self.frame_size,
            )
            self.process.start()

            self.state = CameraState.STREAMING

        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            self.state = CameraState.ERROR
            raise CameraError(f"Unable to start camera: {exc}") from exc

    def stop(self) -> None:
        """Stop camera capture and release process resources."""
        self.state = CameraState.STOPPING

        if self.process is not None:
            self.process.stop()
            self.process = None

        self.state = CameraState.DISCONNECTED

    # ------------------------------------------------------------------
    # Frame capture
    # ------------------------------------------------------------------

    def get_frame(self) -> Optional[np.ndarray]:
        """Return the newest camera frame as a BGR image."""
        if self.process is None:
            return None

        raw_frame = self.process.get_frame()

        if raw_frame is None:
            if self.process.error_message:
                self.state = CameraState.ERROR
            return None

        try:
            yuv_frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape(
                (self.height * 3 // 2, self.width)
            )

            return cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)

        except (ValueError, cv2.error) as exc:
            self.state = CameraState.ERROR
            raise CameraError(f"Unable to decode camera frame: {exc}") from exc