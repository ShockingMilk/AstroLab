"""Application command controls."""

import tkinter as tk
from collections.abc import Callable
from typing import Any

class ControlPanel(tk.Frame):
    """Display profile selection and application commands."""

    def __init__(
        self,
        parent: tk.Misc,
        settings: dict,
        profiles: dict[str, dict[str, Any]],
        callbacks: dict[str, Callable[[], None]],
        allow_windowed_mode: bool = True,
    ) -> None:
        super().__init__(
            parent,
            bg=settings.get("background", "#101010"),
            height=settings.get("controls_height", 76),
        )

        self.pack_propagate(False)

        foreground = settings.get("foreground", "#FFFFFF")
        accent = settings.get("accent", "#36A3FF")
        background = settings.get("background", "#101010")

        profile_row = tk.Frame(self, bg=background)
        profile_row.pack(
            side="top",
            fill="both",
            expand=True,
            padx=4,
            pady=(3, 0),
        )

        action_row = tk.Frame(self, bg=background)
        action_row.pack(
            side="bottom",
            fill="both",
            expand=True,
            padx=4,
            pady=(0, 3),
        )

        for profile_id, profile in profiles.items():
            if not profile.get("enabled", True):
                continue

            name = profile.get("name", profile_id)
            label = f"{profile_id}  {name}"

            self._create_button(
                parent=profile_row,
                text=label,
                command=callbacks[f"profile:{profile_id}"],
                foreground=foreground,
                accent=accent,
                expand=True,
            )

        self._create_button(
            parent=action_row,
            text="Crosshair",
            command=callbacks["crosshair"],
            foreground=foreground,
            accent=accent,
        )

        if allow_windowed_mode:
            self._create_button(
                parent=action_row,
                text="Display Mode",
                command=callbacks["display_mode"],
                foreground=foreground,
                accent=accent,
            )

        self._create_button(
            parent=action_row,
            text="Exit",
            command=callbacks["exit"],
            foreground=foreground,
            accent=accent,
        )

    @staticmethod
    def _create_button(
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        foreground: str,
        accent: str,
        expand: bool = False,
    ) -> None:
        """Create a consistently styled command button."""
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg="#202020",
            fg=foreground,
            activebackground=accent,
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Arial", 9),
            padx=8,
            pady=2,
            takefocus=True,
        )

        button.pack(
            side="left",
            padx=3,
            pady=2,
            fill="both",
            expand=expand,
        )