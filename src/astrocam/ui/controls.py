"""Application command controls."""

import tkinter as tk
from collections.abc import Callable


class ControlPanel(tk.Frame):
    """Display clickable application commands."""

    def __init__(
        self,
        parent,
        settings: dict,
        callbacks: dict[str, Callable[[], None]],
    ) -> None:
        super().__init__(
            parent,
            bg=settings.get("background", "#101010"),
            height=64,
        )

        self.pack_propagate(False)

        foreground = settings.get("foreground", "#FFFFFF")
        accent = settings.get("accent", "#36A3FF")

        commands = (
            ("0  Calibration", "calibration"),
            ("C  Crosshair", "crosshair"),
            ("F11  Fullscreen", "fullscreen"),
            ("Q  Exit", "exit"),
        )

        for label, action in commands:
            self._create_button(
                text=label,
                command=callbacks[action],
                foreground=foreground,
                accent=accent,
            )

    # ------------------------------------------------------------------
    # Control creation
    # ------------------------------------------------------------------

    def _create_button(
        self,
        text: str,
        command: Callable[[], None],
        foreground: str,
        accent: str,
    ) -> None:
        """Create a consistently styled command button."""
        button = tk.Button(
            self,
            text=text,
            command=command,
            bg="#202020",
            fg=foreground,
            activebackground=accent,
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Arial", 10),
            padx=12,
        )

        button.pack(side="left", padx=5, pady=8, fill="y")