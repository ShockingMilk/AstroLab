from __future__ import annotations

import cv2

from astrocam.core.utils import (
    normalize_size,
)


class DisplayController:

    def __init__(
        self,
        displays,
        config,
    ):
        self.displays = displays
        self.config = config

        self.active_display = (
            self._select_display()
        )

    def _select_display(self):

        configured_name = (
            self.config.get(
                "name"
            )
        )

        if configured_name:
            for display in self.displays:
                if display.name == configured_name:
                    return display

        primary = [
            display
            for display in self.displays
            if display.primary
        ]

        if primary:
            return primary[0]

        if self.displays:
            return self.displays[0]

        return None

    @property
    def resolution(self):
        configured = (
            self.config.get(
                "resolution",
                "auto",
            )
        )

        if configured == "auto":
            if self.active_display:
                return (
                    self.active_display.width,
                    self.active_display.height,
                )

            fallback = normalize_size(
                self.config.get(
                    "fallback_resolution",
                    [1024, 600],
                )
            )

            return fallback or (
                1024,
                600,
            )

        normalized = normalize_size(
            configured
        )

        if normalized:
            return normalized

        return (
            1024,
            600,
        )

    def resize_frame(
        self,
        frame,
    ):
        width, height = (
            self.resolution
        )

        return cv2.resize(
            frame,
            (width, height),
            interpolation=cv2.INTER_AREA,
        )