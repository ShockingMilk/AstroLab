"""Application status display."""

import tkinter as tk

class StatusBar(tk.Frame):
    """Display camera, profile, and performance status."""

    def __init__(self, parent, settings: dict) -> None:
        super().__init__(
            parent,
            bg=settings.get("background", "#101010"),
            height=30,
        )

        self.pack_propagate(False)

        background = settings.get("background", "#101010")
        foreground = settings.get("foreground", "#FFFFFF")
        accent = settings.get("accent", "#36A3FF")

        self.profile_label = tk.Label(
            self,
            text="Profile: Calibration",
            anchor="w",
            bg=background,
            fg=accent,
            font=("Arial", 9, "bold"),
        )
        self.profile_label.pack(side="left", padx=(8, 12))

        self.status_label = tk.Label(
            self,
            text="Camera: Initializing",
            anchor="w",
            bg=background,
            fg=foreground,
            font=("Arial", 9),
        )
        self.status_label.pack(
            side="left",
            fill="both",
            expand=True,
            padx=4,
        )

    def update_status(self, message: str) -> None:
        """Update the camera and performance status."""
        self.status_label.configure(text=message)

    def update_profile(self, profile_name: str) -> None:
        """Update the active profile label."""
        self.profile_label.configure(text=f"Profile: {profile_name}")