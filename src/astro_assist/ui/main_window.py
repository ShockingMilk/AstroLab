"""Main Astro Assist application window."""

import time
import tkinter as tk

from astro_assist.camera.manager import CameraManager
from astro_assist.ui.controls import ControlPanel
from astro_assist.ui.preview import CameraPreview
from astro_assist.ui.status_bar import StatusBar


class MainWindow:
    """Own the application window and coordinate UI updates."""

    def __init__(
        self,
        root: tk.Tk,
        camera: CameraManager,
        settings: dict,
    ) -> None:
        self.root = root
        self.camera = camera
        self.settings = settings

        self.running = True
        self.fullscreen = settings["application"].get("fullscreen", True)
        self.show_crosshair = settings["ui"].get("show_crosshair", True)

        self.last_frame_time = time.monotonic()
        self.fps = 0.0

        self._configure_window()
        self._create_layout()
        self._bind_keys()

        self.root.protocol("WM_DELETE_WINDOW", self.terminate)

    # ------------------------------------------------------------------
    # Initialization and layout
    # ------------------------------------------------------------------

    def _configure_window(self) -> None:
        """Configure the root window and request true fullscreen."""
        self.root.title(self.settings["application"].get("name", "Astro Assist"))

        self.root.configure(
            bg=self.settings["ui"].get("background", "#101010")
        )

        self.root.minsize(800, 480)

        # Tkinter requests fullscreen from the window manager.
        # Do not use overrideredirect as the default workaround.
        if self.fullscreen:
            self.root.attributes("-fullscreen", True)
        else:
            width, height = self.settings["application"].get(
                "fallback_resolution",
                [1024, 600],
            )
            self.root.geometry(f"{width}x{height}")

        # Allow the preview row to consume all available space.
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.root.update_idletasks()

    def _create_layout(self) -> None:
        """Create the header, preview, controls, and status regions."""
        background = self.settings["ui"].get("background", "#101010")

        self.header = tk.Label(
            self.root,
            text="ASTRO ASSIST  |  PROFILE: 0 - CALIBRATION",
            bg=background,
            fg="#FFFFFF",
            anchor="w",
            font=("Arial", 12, "bold"),
            padx=10,
            height=2,
        )
        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.preview = CameraPreview(
            parent=self.root,
            settings=self.settings["ui"],
        )
        self.preview.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=self.settings["ui"].get("preview_padding", 4),
        )

        self.controls = ControlPanel(
            parent=self.root,
            settings=self.settings["ui"],
            callbacks={
                "calibration": self._handle_calibration,
                "crosshair": self._handle_crosshair,
                "fullscreen": self._handle_fullscreen,
                "exit": self._handle_exit,
            },
        )
        self.controls.grid(
            row=2,
            column=0,
            sticky="ew",
        )

        self.status = StatusBar(
            parent=self.root,
            settings=self.settings["ui"],
        )
        self.status.grid(
            row=3,
            column=0,
            sticky="ew",
        )

    # ------------------------------------------------------------------
    # Keyboard controls
    # ------------------------------------------------------------------

    def _bind_keys(self) -> None:
        """Bind keyboard shortcuts to application actions."""
        self.root.bind("<Escape>", self._handle_exit)
        self.root.bind("q", self._handle_exit)
        self.root.bind("Q", self._handle_exit)

        self.root.bind("<F11>", self._handle_fullscreen)
        self.root.bind("c", self._handle_crosshair)
        self.root.bind("C", self._handle_crosshair)

        self.root.bind("0", self._handle_calibration)

    def _handle_calibration(self, event: tk.Event | None = None) -> None:
        """Select the initial calibration profile."""
        self.header.configure(
            text="ASTRO ASSIST  |  PROFILE: 0 - CALIBRATION"
        )
        self.status.update_status("Camera: Calibration profile selected")

    def _handle_crosshair(self, event: tk.Event | None = None) -> None:
        """Toggle the camera preview crosshair."""
        self.preview.toggle_crosshair()

    def _handle_exit(self, event: tk.Event | None = None) -> None:
        """Request application shutdown."""
        self.terminate()

    def _handle_fullscreen(self, event: tk.Event | None = None) -> None:
        """Toggle between fullscreen and windowed mode."""
        if not self.settings["application"].get(
            "allow_windowed_mode",
            True,
        ):
            return

        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

        if not self.fullscreen:
            width, height = self.settings["application"].get(
                "fallback_resolution",
                [1024, 600],
            )
            self.root.geometry(f"{width}x{height}")

    # ------------------------------------------------------------------
    # Display updates
    # ------------------------------------------------------------------

    def update_frame(self) -> None:
        """Fetch and display the newest camera frame."""
        if not self.running:
            return

        frame = self.camera.get_frame()

        if frame is not None:
            self.preview.display_frame(frame)

            current_time = time.monotonic()
            elapsed = current_time - self.last_frame_time

            if elapsed > 0:
                self.fps = 1.0 / elapsed

            self.last_frame_time = current_time

            self.status.update_status(
                f"Camera: {self.camera.state.value.upper()}  |  "
                f"Display: {self.root.winfo_width()}x"
                f"{self.root.winfo_height()}  |  "
                f"FPS: {self.fps:.1f}"
            )

        elif self.camera.state.value == "error":
            self.status.update_status("Camera: ERROR - check camera process")

        self.root.after(10, self.update_frame)

    # ------------------------------------------------------------------
    # Application lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the UI update loop and Tkinter event loop."""
        self.update_frame()
        self.root.mainloop()

    def terminate(self) -> None:
        """Stop UI updates and close the application."""
        if not self.running:
            return

        self.running = False

        try:
            self.camera.stop()
        finally:
            self.root.destroy()