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

        self.status_label = tk.Label(
            self,
            text="Camera: Initializing",
            anchor="w",
            bg=settings.get("background", "#101010"),
            fg=settings.get("foreground", "#FFFFFF"),
            font=("Arial", 10),
        )
        self.status_label.pack(fill="both", expand=True, padx=8)

    # ------------------------------------------------------------------
    # Status updates
    # ------------------------------------------------------------------

    def update_status(self, message: str) -> None:
        """Update the displayed status."""
        self.status_label.configure(text=message)