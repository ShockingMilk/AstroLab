"""Picamera2 camera backend and frame capture."""

import numpy as np
import queue
import re
import threading

from typing import Any, Optional


from astro_assist.common.enums import CameraState
from astro_assist.common.exceptions import CameraError


_SENSOR_MODE_PATTERN = re.compile(r"^(\d+):(\d+):(8|10|12):P$")


class PicameraBackend:
    """Manage Picamera2 configuration, streaming, and frame delivery."""

    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = settings.copy()

        self.state = CameraState.DISCONNECTED
        self.width = 0
        self.height = 0
        self.framerate = 0
        self.rotation = 0
        self.sensor_mode = ""

        self._camera: Any = None
        self._frame_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=1)
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._first_frame_event = threading.Event()
        self._error_message: Optional[str] = None

        self._apply_settings(self.settings)

    def _apply_settings(self, settings: dict[str, Any]) -> None:
        """Apply the selected profile settings."""
        self.settings = settings.copy()

        self.width = int(settings["width"])
        self.height = int(settings["height"])
        self.framerate = int(settings["framerate"])
        self.rotation = int(settings.get("rotation", 0))
        self.sensor_mode = str(settings["sensor_mode"])

        if self.rotation not in (0, 180):
            raise CameraError("Only 0 and 180 degree rotation are supported.")

        if self.framerate <= 0:
            raise CameraError("Camera framerate must be positive.")

        if self.width <= 0 or self.height <= 0:
            raise CameraError("Camera output dimensions must be positive.")

    @staticmethod
    def parse_sensor_mode(sensor_mode: str) -> tuple[int, int, int]:
        """Convert the legacy sensor-mode notation into Picamera2 values."""
        match = _SENSOR_MODE_PATTERN.fullmatch(sensor_mode)

        if match is None:
            raise CameraError("Invalid sensor mode. Expected width:height:bit-depth:P.")

        width, height, bit_depth = map(int, match.groups())
        return width, height, bit_depth

    @property
    def error_message(self) -> Optional[str]:
        """Return the latest camera capture error."""
        return self._error_message

    @property
    def camera_controls(self) -> dict[str, Any]:
        """Return the controls supported by the active camera."""
        if self._camera is None:
            return {}

        return self._camera.camera_controls

    def start(self) -> None:
        """Configure and start the camera capture thread."""
        if self.state == CameraState.STREAMING:
            return

        self.state = CameraState.STARTING
        self._error_message = None
        self._stop_event.clear()
        self._first_frame_event.clear()
        self._clear_frame_queue()

        try:
            # Import lazily so desktop unit tests can import Astro Assist
            # without requiring Raspberry Pi camera libraries.
            from libcamera import Transform
            from picamera2 import Picamera2

            self._camera = Picamera2()

            sensor_width, sensor_height, bit_depth = self.parse_sensor_mode(self.sensor_mode)

            frame_duration = round(1_000_000 / self.framerate)

            transform = Transform(
                hflip=self.rotation == 180,
                vflip=self.rotation == 180,
            )

            configuration = self._camera.create_video_configuration(
                main={
                    "size": (self.width, self.height),
                    "format": "BGR888",
                },
                sensor={
                    "output_size": (sensor_width, sensor_height),
                    "bit_depth": bit_depth,
                },
                transform=transform,
                controls={
                    "FrameDurationLimits": (
                        frame_duration,
                        frame_duration,
                    ),
                },
                buffer_count=4,
                queue=False,
                display=None,
                encode=None,
            )

            self._camera.configure(configuration)
            self._camera.start()

            self._capture_thread = threading.Thread(
                target=self._capture_frames,
                name="AstroAssistPicameraCapture",
                daemon=True,
            )
            self._capture_thread.start()

            timeout = float(self.settings.get("startup_timeout", 10))

            if not self._first_frame_event.wait(timeout):
                raise CameraError(self._error_message or "Timed out waiting for the first camera frame.")

            if self._error_message:
                raise CameraError(self._error_message)

            self.state = CameraState.STREAMING

        except Exception as exc:
            self.state = CameraState.ERROR
            self._release_camera()

            if isinstance(exc, CameraError):
                raise

            raise CameraError(f"Unable to initialize Picamera2: {exc}") from exc

    def _capture_frames(self) -> None:
        """Capture frames continuously and retain only the newest frame."""
        try:
            while not self._stop_event.is_set():
                frame = self._camera.capture_array("main")

                if frame is None:
                    continue

                # Picamera2's BGR888 stream already matches the UI's
                # expected OpenCV BGR channel order.
                frame = np.ascontiguousarray(frame)

                if self._frame_queue.full():
                    try:
                        self._frame_queue.get_nowait()
                    except queue.Empty:
                        pass

                try:
                    self._frame_queue.put_nowait(frame)
                except queue.Full:
                    pass

                self._first_frame_event.set()

        except Exception as exc:
            if not self._stop_event.is_set():
                self._error_message = str(exc)
                self.state = CameraState.ERROR

        finally:
            self._first_frame_event.set()

    def get_frame(self) -> Optional[np.ndarray]:
        """Return the newest available frame as a BGR NumPy array."""
        try:
            return self._frame_queue.get_nowait()
        except queue.Empty:
            return None

    def set_controls(self, controls: dict[str, Any]) -> None:
        """Apply runtime camera controls."""
        if self._camera is None or self.state != CameraState.STREAMING:
            raise CameraError("Camera must be streaming to change controls.")

        supported = self.camera_controls

        for name in controls:
            if name not in supported:
                raise CameraError(f"Camera does not support the '{name}' control.")

        try:
            self._camera.set_controls(controls)
        except Exception as exc:
            raise CameraError(f"Unable to apply camera controls: {exc}") from exc

    def stop(self) -> None:
        """Stop capture and release camera resources."""
        if self.state == CameraState.DISCONNECTED:
            return

        self.state = CameraState.STOPPING
        self._stop_event.set()
        self._release_camera()
        self._clear_frame_queue()

        self.state = CameraState.DISCONNECTED

    def _release_camera(self) -> None:
        """Stop and close the Picamera2 instance."""
        camera = self._camera
        self._camera = None

        if camera is not None:
            try:
                camera.stop()
            except Exception:
                pass

            try:
                camera.close()
            except Exception:
                pass

        if self._capture_thread is not None:
            self._capture_thread.join(timeout=3)
            self._capture_thread = None

    def _clear_frame_queue(self) -> None:
        """Discard frames from a previous camera session."""
        while True:
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break
