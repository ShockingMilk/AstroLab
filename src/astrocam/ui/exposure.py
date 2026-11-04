from __future__ import annotations

from astrocam.core.enums import (
    AdjustmentMode,
)
from astrocam.core.utils import (
    clamp,
)


class ExposureController:

    def __init__(
        self,
        camera,
    ):
        self.camera = camera

        self.mode = (
            AdjustmentMode.EXPOSURE
        )

        self.exposure_time = 1000
        self.gain = 1.0

    def set_mode(
        self,
        mode,
    ):
        self.mode = (
            AdjustmentMode.from_value(
                mode
            )
        )

    def adjust(
        self,
        direction,
    ):

        if (
            self.mode
            == AdjustmentMode.EXPOSURE
        ):

            self.exposure_time = int(
                clamp(
                    self.exposure_time
                    + (
                        direction
                        * 100
                    ),
                    100,
                    1000000,
                )
            )

            self.camera.set_controls(
                {
                    "AeEnable": False,
                    "ExposureTime":
                        self.exposure_time,
                }
            )

        else:

            self.gain = clamp(
                self.gain
                + (
                    direction
                    * 0.25
                ),
                1.0,
                16.0,
            )

            self.camera.set_controls(
                {
                    "AeEnable": False,
                    "AnalogueGain":
                        self.gain,
                }
            )