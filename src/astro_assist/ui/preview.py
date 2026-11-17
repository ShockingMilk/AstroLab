"""Resizable camera preview widget."""

import tkinter as tk

import cv2
import numpy as np
from PIL import Image, ImageTk


class CameraPreview(tk.Frame):
    """Display camera frames while preserving their aspect ratio."""

    def __init__(self, parent, settings: dict) -> None:
        super().__init__(
            parent,
            bg=settings.get("background", "#000000"),
        )

        self.settings = settings
        self.show_crosshair = settings.get("show_crosshair", True)
        self.image_reference = None

        self.preview_label = tk.Label(
            self,
            bg="#000000",
            borderwidth=0,
            highlightthickness=0,
        )
        self.preview_label.pack(fill="both", expand=True)

        self.preview_label.bind("<Configure>", self._on_resize)

        self.latest_frame: np.ndarray | None = None
        self.pending_resize = False

    # ------------------------------------------------------------------
    # Image display
    # ------------------------------------------------------------------

    def display_frame(self, frame: np.ndarray) -> None:
        """Display the latest clean camera frame."""
        self.latest_frame = frame.copy()
        self._render_frame()

    def _render_frame(self) -> None:
        """Resize and render the current frame."""
        if self.latest_frame is None:
            return

        width = self.preview_label.winfo_width()
        height = self.preview_label.winfo_height()

        if width <= 1 or height <= 1:
            return

        frame = self.latest_frame.copy()

        if self.show_crosshair:
            self._draw_crosshair(frame)

        frame_height, frame_width = frame.shape[:2]
        scale = min(width / frame_width, height / frame_height)

        target_width = max(1, int(frame_width * scale))
        target_height = max(1, int(frame_height * scale))

        resized = cv2.resize(
            frame,
            (target_width, target_height),
            interpolation=cv2.INTER_AREA,
        )

        rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)

        self.image_reference = ImageTk.PhotoImage(image=image)
        self.preview_label.configure(image=self.image_reference)

    # ------------------------------------------------------------------
    # Preview controls
    # ------------------------------------------------------------------

    def _draw_crosshair(self, frame: np.ndarray) -> None:
        """Draw a centered crosshair on the display copy."""
        height, width = frame.shape[:2]

        center_x = width // 2
        center_y = height // 2

        color = (0, 255, 0)
        thickness = 1
        length = min(width, height) // 25

        cv2.line(
            frame,
            (center_x - length, center_y),
            (center_x + length, center_y),
            color,
            thickness,
        )
        cv2.line(
            frame,
            (center_x, center_y - length),
            (center_x, center_y + length),
            color,
            thickness,
        )

    def _on_resize(self, event: tk.Event) -> None:
        """Schedule a redraw when the preview area changes size."""
        if self.pending_resize:
            return

        self.pending_resize = True

        self.after_idle(self._finish_resize)

    def _finish_resize(self) -> None:
        """Finish the pending preview redraw."""
        self.pending_resize = False
        self._render_frame()

    def toggle_crosshair(self) -> None:
        """Enable or disable the preview crosshair."""
        self.show_crosshair = not self.show_crosshair
        self._render_frame()