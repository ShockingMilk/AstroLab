from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from astrocam.core.enums import (
    CameraModeSelection,
    CameraPurpose,
)
from astrocam.core.utils import normalize_size


@dataclass(frozen=True)
class SensorMode:
    size: tuple[int, int]
    bit_depth: int
    fps: float
    crop_limits: tuple[int, ...] | None = None
    exposure_limits: tuple[int, ...] | None = None
    format: str | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ):
        size = normalize_size(
            data.get("size")
        )

        if not size:
            raise ValueError(
                "Sensor mode has no valid size."
            )

        crop_limits = data.get(
            "crop_limits"
        )

        if crop_limits:
            crop_limits = tuple(
                int(value)
                for value in crop_limits
            )

        exposure_limits = data.get(
            "exposure_limits"
        )

        if exposure_limits:
            exposure_limits = tuple(
                int(value)
                for value in exposure_limits
            )

        return cls(
            size=size,
            bit_depth=int(
                data.get(
                    "bit_depth",
                    0,
                )
            ),
            fps=float(
                data.get(
                    "fps",
                    0,
                )
            ),
            crop_limits=crop_limits,
            exposure_limits=exposure_limits,
            format=data.get(
                "format"
            ),
        )


class CameraModeSelector:

    def select(
        self,
        modes: list[SensorMode],
        purpose: CameraPurpose,
        selection: CameraModeSelection,
        explicit_size=None,
        explicit_bit_depth=None,
    ) -> SensorMode:

        if not modes:
            raise ValueError(
                "No camera sensor modes available."
            )

        if (
            selection
            == CameraModeSelection.EXPLICIT
        ):
            return self._select_explicit(
                modes,
                explicit_size,
                explicit_bit_depth,
            )

        return self._select_auto(
            modes,
            purpose,
        )

    def _select_explicit(
        self,
        modes,
        size,
        bit_depth,
    ):

        normalized_size = (
            normalize_size(size)
        )

        candidates = modes

        if normalized_size:
            candidates = [
                mode
                for mode in candidates
                if mode.size
                == normalized_size
            ]

        if bit_depth is not None:
            candidates = [
                mode
                for mode in candidates
                if mode.bit_depth
                == int(bit_depth)
            ]

        if not candidates:
            raise ValueError(
                "Requested sensor mode "
                "is not available."
            )

        return max(
            candidates,
            key=lambda mode: mode.fps,
        )

    def _select_auto(
        self,
        modes,
        purpose,
    ):

        if purpose in (
            CameraPurpose.CALIBRATION,
            CameraPurpose.GENERAL,
        ):
            return max(
                modes,
                key=lambda mode: (
                    mode.bit_depth,
                    mode.size[0]
                    * mode.size[1],
                ),
            )

        if purpose == CameraPurpose.MOON:
            candidates = [
                mode
                for mode in modes
                if mode.fps >= 20
            ]

            if not candidates:
                candidates = modes

            twelve_bit = [
                mode
                for mode in candidates
                if mode.bit_depth == 12
            ]

            if twelve_bit:
                candidates = twelve_bit

            return max(
                candidates,
                key=lambda mode: (
                    mode.size[0]
                    * mode.size[1],
                    mode.fps,
                ),
            )

        if purpose == CameraPurpose.PLANETARY:
            candidates = [
                mode
                for mode in modes
                if mode.fps >= 60
            ]

            if not candidates:
                candidates = modes

            ten_bit = [
                mode
                for mode in candidates
                if mode.bit_depth == 10
            ]

            if ten_bit:
                candidates = ten_bit

            return max(
                candidates,
                key=lambda mode: mode.fps,
            )

        if purpose == CameraPurpose.BRIGHT_PLANET:
            candidates = [
                mode
                for mode in modes
                if mode.fps >= 30
            ]

            if not candidates:
                candidates = modes

            ten_bit = [
                mode
                for mode in candidates
                if mode.bit_depth == 10
            ]

            if ten_bit:
                candidates = ten_bit

            return max(
                candidates,
                key=lambda mode: (
                    mode.fps,
                    mode.size[0]
                    * mode.size[1],
                ),
            )

        if purpose in (
            CameraPurpose.BRIGHT_STAR,
            CameraPurpose.STAR_FIELD,
        ):
            twelve_bit = [
                mode
                for mode in modes
                if mode.bit_depth == 12
            ]

            candidates = (
                twelve_bit
                if twelve_bit
                else modes
            )

            return max(
                candidates,
                key=lambda mode: (
                    mode.size[0]
                    * mode.size[1],
                    mode.bit_depth,
                ),
            )

        return max(
            modes,
            key=lambda mode: (
                mode.size[0]
                * mode.size[1],
                mode.bit_depth,
            ),
        )