from __future__ import annotations

import cv2

from picamera2 import Picamera2

from astrocam.camera.modes import (
    CameraModeSelector,
    SensorMode,
)
from astrocam.core.enums import (
    CameraModeSelection,
    CameraPurpose,
)


class CameraController:

    def __init__(
        self,
        device_info,
        config,
    ):
        self.device_info = device_info
        self.config = config

        self.picam2 = Picamera2(
            device_info.index
        )

        self.mode_selector = (
            CameraModeSelector()
        )

        self.sensor_modes = [
            SensorMode.from_dict(mode)
            for mode
            in self.picam2.sensor_modes
        ]

        self.active_sensor_mode = None
        self.active_stream_size = None

        self.picam2_started = False

    def start(self):
        if not self.picam2_started:
            self.picam2.start()
            self.picam2_started = True

    def stop(self):
        if self.picam2_started:
            self.picam2.stop()
            self.picam2_started = False

    def close(self):
        self.stop()
        self.picam2.close()

    def set_camera_mode(
        self,
        camera_config,
    ):

        purpose = CameraPurpose.from_value(
            camera_config.get(
                "purpose",
                "general",
            )
        )

        selection = (
            CameraModeSelection.from_value(
                camera_config.get(
                    "mode",
                    "auto",
                )
            )
        )

        sensor_mode = (
            self.mode_selector.select(
                self.sensor_modes,
                purpose,
                selection,
                camera_config.get(
                    "sensor_size"
                ),
                camera_config.get(
                    "bit_depth"
                ),
            )
        )

        stream_resolution = (
            camera_config.get(
                "stream_resolution",
                "default",
            )
        )

        if stream_resolution == "sensor":
            stream_size = (
                sensor_mode.size
            )

        elif isinstance(
            stream_resolution,
            list,
        ):
            stream_size = tuple(
                int(value)
                for value in stream_resolution
            )

        else:
            stream_size = (
                self.config.get(
                    "stream_resolution",
                    [800, 480],
                )
            )

            stream_size = tuple(
                stream_size
            )

        self.stop()

        configuration = (
            self.picam2
            .create_preview_configuration(
                main={
                    "size": stream_size,
                    "format": "RGB888",
                },
                sensor={
                    "output_size":
                        sensor_mode.size,
                    "bit_depth":
                        sensor_mode.bit_depth,
                },
                buffer_count=4,
            )
        )

        self.picam2.configure(
            configuration
        )

        self.active_sensor_mode = (
            sensor_mode
        )

        self.active_stream_size = (
            stream_size
        )

        self.start()

    def set_controls(
        self,
        controls,
    ):
        if not controls:
            return

        self.picam2.set_controls(
            controls
        )

    def capture_frame(self):
        frame = self.picam2.capture_array(
            "main"
        )

        return cv2.cvtColor(
            frame,
            cv2.COLOR_RGB2BGR,
        )

    def capture_metadata(self):
        return self.picam2.capture_metadata()

    def get_sensor_mode_text(self):
        if not self.active_sensor_mode:
            return "MODE: --"

        mode = self.active_sensor_mode

        return (
            f"{mode.size[0]}x{mode.size[1]} "
            f"{mode.bit_depth}bit "
            f"{mode.fps:.1f}fps"
        )