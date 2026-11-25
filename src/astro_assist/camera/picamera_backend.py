"""Picamera2 camera backend and frame capture."""

import math
import numbers
import queue
import re
import threading
import numpy as np

from typing import Any, Optional

from astro_assist.common.enums import CameraState
from astro_assist.common.exceptions import CameraError


_SENSOR_MODE_PATTERN = re.compile(r"^(\d+):(\d+):(8|10|12):P$")

# Manual controls require their associated automatic mode to be disabled.
_MANUAL_AUTO_PAIRS = {
    "ExposureTime": ("AeEnable", False),
    "AnalogueGain": ("AeEnable", False),
    "ColourGains": ("AwbEnable", False),
}


class PicameraBackend:
    """Manage Picamera2 configuration, streaming, controls, and frame delivery."""

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

        # Protect camera control and metadata operations from one another.
        self._camera_lock = threading.RLock()

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
        """Convert legacy sensor-mode notation into Picamera2 values."""
        match = _SENSOR_MODE_PATTERN.fullmatch(sensor_mode)

        if match is None:
            raise CameraError("Invalid sensor mode. Expected width:height:bit-depth:P.")

        return tuple(map(int, match.groups()))

    @property
    def error_message(self) -> Optional[str]:
        """Return the latest camera capture error."""
        return self._error_message

    @property
    def camera_controls(self) -> dict[str, Any]:
        """Return supported controls and their (minimum, maximum, default) values."""
        with self._camera_lock:
            if self._camera is None:
                return {}

            return dict(self._camera.camera_controls)

    def _require_streaming(self) -> None:
        """Ensure a live camera is available for metadata/control operations."""
        if self._camera is None or self.state != CameraState.STREAMING:
            raise CameraError("Camera must be streaming to access or change controls.")

    def get_controls(self) -> dict[str, Any]:
        """Return current values reported by Picamera2 capture metadata."""
        self._require_streaming()

        try:
            with self._camera_lock:
                metadata = self._camera.capture_metadata()
                supported = self.camera_controls

            # Not every supported control is necessarily present in every
            # metadata packet. Return only values actually reported.
            return {name: metadata[name] for name in supported if name in metadata}

        except Exception as exc:
            raise CameraError(f"Unable to read camera control values: {exc}") from exc

    def get_control_info(self, name: str) -> dict[str, Any]:
        """Return supported range/default and latest value for one control."""
        supported = self.camera_controls

        if name not in supported:
            raise CameraError(f"Camera does not support the '{name}' control.")

        limits = supported[name]

        if not isinstance(limits, (tuple, list)) or len(limits) != 3:
            raise CameraError(f"The '{name}' control does not expose a supported range.")

        minimum, maximum, default = limits
        current = self.get_controls().get(name)

        return {
            "name": name,
            "minimum": minimum,
            "maximum": maximum,
            "default": default,
            "current": current,
        }

    @staticmethod
    def _validate_control_value(
        name: str,
        value: Any,
        limits: Any,
    ) -> None:
        """Validate scalar and tuple control values against camera ranges."""
        if not isinstance(limits, (tuple, list)) or len(limits) != 3:
            raise CameraError(
                f"The '{name}' control does not expose a supported range."
            )

        minimum, maximum, _default = limits

        # Boolean controls, such as AeEnable and AwbEnable.
        if isinstance(minimum, bool) and isinstance(maximum, bool):
            if not isinstance(value, bool):
                raise CameraError(
                    f"The '{name}' control requires a boolean value."
                )
            return

        # ColourGains is a two-value control with shared scalar limits.
        if name == "ColourGains":
            if not isinstance(value, (tuple, list)) or len(value) != 2:
                raise CameraError(
                    "ColourGains requires two values: red and blue."
                )

            for channel, item in zip(("red", "blue"), value):
                if (
                    isinstance(item, bool)
                    or not isinstance(item, numbers.Real)
                    or not math.isfinite(item)
                ):
                    raise CameraError(
                        f"The {channel} ColourGains value must be finite and numeric."
                    )

                if item < minimum or item > maximum:
                    raise CameraError(
                        f"The {channel} ColourGains value {item} is outside "
                        f"the supported range ({minimum} to {maximum})."
                    )
            return

        # Tuple controls with separate limits, such as ScalerCrop.
        if isinstance(minimum, (tuple, list)) and isinstance(
            maximum, (tuple, list)
        ):
            if not isinstance(value, (tuple, list)):
                raise CameraError(
                    f"The '{name}' control requires a tuple/list value."
                )

            if len(value) != len(minimum) or len(value) != len(maximum):
                raise CameraError(
                    f"The '{name}' control requires {len(minimum)} values."
                )

            for index, item in enumerate(value):
                low = minimum[index]
                high = maximum[index]

                if (
                    isinstance(item, bool)
                    or not isinstance(item, numbers.Real)
                    or not math.isfinite(item)
                ):
                    raise CameraError(
                        f"Value {index + 1} for '{name}' must be finite and numeric."
                    )

                if item < low or item > high:
                    raise CameraError(
                        f"Value {item} for '{name}' is outside "
                        f"the supported range ({low} to {high})."
                    )
            return

        # Scalar numeric controls.
        if (
            isinstance(value, bool)
            or not isinstance(value, numbers.Real)
            or not math.isfinite(value)
        ):
            raise CameraError(
                f"The '{name}' control requires a finite numeric value."
            )

        if value < minimum or value > maximum:
            raise CameraError(
                f"The '{name}' value {value} is outside "
                f"the supported range ({minimum} to {maximum})."
            )

        # Picamera2 integer controls must not receive floating-point values.
        if (
            isinstance(minimum, numbers.Integral)
            and isinstance(maximum, numbers.Integral)
            and not isinstance(value, numbers.Integral)
        ):
            raise CameraError(
                f"The '{name}' control requires an integer value."
            )

    def set_controls(self, controls: dict[str, Any]) -> None:
        """Validate and apply runtime controls without restarting the camera."""
        self._require_streaming()

        if not isinstance(controls, dict) or not controls:
            raise CameraError("Provide at least one camera control to change.")

        supported = self.camera_controls
        requested = dict(controls)

        # Validate every requested control before sending anything to camera.
        for name, value in requested.items():
            if name not in supported:
                raise CameraError(f"Camera does not support the '{name}' control.")

            self._validate_control_value(name, value, supported[name])

        # If a manual value is requested, disable the corresponding automatic
        # mode in the same Picamera2 control update.
        for manual_name, (auto_name, disabled_value) in (
            _MANUAL_AUTO_PAIRS.items()
        ):
            if manual_name not in requested:
                continue

            if auto_name in requested and requested[auto_name] != disabled_value:
                raise CameraError(f"'{manual_name}' requires '{auto_name}' to be disabled.")

            if auto_name in supported:
                requested.setdefault(auto_name, disabled_value)

        try:
            with self._camera_lock:
                self._camera.set_controls(requested)

        except Exception as exc:
            raise CameraError(f"Unable to apply camera controls: {exc}") from exc

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
            # Import lazily so desktop unit tests do not require Raspberry Pi
            # camera libraries just to import the application.
            from libcamera import Transform
            from picamera2 import Picamera2

            self._camera = Picamera2()

            sensor_width, sensor_height, bit_depth = self.parse_sensor_mode(
                self.sensor_mode
            )

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

                # Picamera2's BGR888 stream matches the UI's expected
                # OpenCV BGR channel order.
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

    def stop(self) -> None:
        """Stop capture, wait for its thread, then close camera resources."""
        if (
            self.state == CameraState.DISCONNECTED
            and self._camera is None
        ):
            return

        self.state = CameraState.STOPPING
        self._stop_event.set()
        self._release_camera()
        self._clear_frame_queue()

        if self.state != CameraState.ERROR:
            self.state = CameraState.DISCONNECTED

    def _release_camera(self) -> None:
        """Stop the camera, join capture, and close its resources."""
        camera = self._camera
        thread = self._capture_thread

        if camera is not None:
            try:
                camera.stop()
            except Exception:
                pass

        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=5)

            if thread.is_alive():
                self._error_message = "Camera capture thread did not stop within 5 seconds."
                self.state = CameraState.ERROR
                return

        if camera is not None:
            try:
                camera.close()
            except Exception:
                pass

        self._camera = None
        self._capture_thread = None

    def _clear_frame_queue(self) -> None:
        """Discard frames from a previous camera session."""
        while True:
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break