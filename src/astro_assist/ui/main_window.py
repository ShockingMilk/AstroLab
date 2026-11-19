"""Main Astro Assist application window."""

import time
import tkinter as tk

from typing import Any

from astro_assist.camera.manager import CameraManager
from astro_assist.common.exceptions import CameraError
from astro_assist.ui.controls import ControlPanel
from astro_assist.ui.preview import CameraPreview
from astro_assist.ui.status_bar import StatusBar

class MainWindow:
    """Own the application window and coordinate UI updates."""

    def __init__(
        self,
        root: tk.Tk,
        camera: CameraManager,
        settings: dict[str, Any],
    ) -> None:
        self.root = root
        self.camera = camera
        self.settings = settings

        self.running = True
        self.fullscreen = bool(settings["application"].get("fullscreen", True))
        self.profiles = settings["profiles"]
        self.current_profile = "0"

        self.last_frame_time = time.monotonic()
        self.fps = 0.0

        self._configure_window()
        self._create_layout()
        self._bind_keys()

        self._update_profile_display()
        self.root.protocol("WM_DELETE_WINDOW", self.terminate)

    def _configure_window(self) -> None:
        """Configure the root window and initial display mode."""
        application = self.settings["application"]
        ui = self.settings["ui"]

        self.root.title(
            application.get("name", "Astro Assist")
        )
        self.root.configure(
            bg=ui.get("background", "#101010")
        )
        self.root.minsize(800, 480)

        if self.fullscreen:
            self.root.attributes("-fullscreen", True)
        else:
            width, height = application.get(
                "fallback_resolution",
                [1024, 600],
            )
            self.root.geometry(f"{width}x{height}")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.update_idletasks()

    def _create_layout(self) -> None:
        """Create the header, preview, controls, and status regions."""
        ui = self.settings["ui"]
        application = self.settings["application"]
        background = ui.get("background", "#101010")

        self.header = tk.Label(
            self.root,
            text="ASTRO ASSIST",
            bg=background,
            fg=ui.get("foreground", "#FFFFFF"),
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
            settings=ui,
        )
        self.preview.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=ui.get("preview_padding", 4),
        )

        callbacks = {
            "crosshair": self._handle_crosshair,
            "display_mode": self._handle_display_mode,
            "exit": self._handle_exit,
        }

        for profile_id in self.profiles:
            callbacks[f"profile:{profile_id}"] = (
                lambda selected_id=profile_id:
                self._handle_profile(selected_id)
            )

        self.controls = ControlPanel(
            parent=self.root,
            settings=ui,
            profiles=self.profiles,
            callbacks=callbacks,
            allow_windowed_mode=application.get(
                "allow_windowed_mode",
                True,
            ),
        )
        self.controls.grid(
            row=2,
            column=0,
            sticky="ew",
        )

        self.status = StatusBar(
            parent=self.root,
            settings=ui,
        )
        self.status.grid(
            row=3,
            column=0,
            sticky="ew",
        )

    def _bind_keys(self) -> None:
        """Bind keyboard shortcuts to application actions."""
        controls = self.settings.get("controls", {})

        for key in controls.get("exit", ["Escape", "q"]):
            if key.lower() == "escape":
                self.root.bind("<Escape>", self._handle_exit)
            else:
                self.root.bind(key.lower(), self._handle_exit)
                self.root.bind(key.upper(), self._handle_exit)

        for key in controls.get("toggle_crosshair", ["c"]):
            self.root.bind(key.lower(), self._handle_crosshair)
            self.root.bind(key.upper(), self._handle_crosshair)

        for profile_id in controls.get(
            "profiles",
            list(self.profiles.keys()),
        ):
            if profile_id not in self.profiles:
                continue

            self.root.bind(
                profile_id,
                lambda event, selected_id=profile_id:
                self._handle_profile(selected_id),
            )

    def _update_profile_display(self) -> None:
        """Refresh profile information in the header and status bar."""
        profile = self.profiles[self.current_profile]
        profile_name = profile.get("name", self.current_profile)

        self.header.configure(text=f"ASTRO ASSIST  |  PROFILE: {self.current_profile} - {profile_name.upper()}")
        self.status.update_profile(profile_name)

    def _handle_profile(self, profile_id: str) -> None:
        """Select a profile and restart the camera with its settings."""
        if not self.running or profile_id not in self.profiles:
            return

        profile = self.profiles[profile_id]

        if not profile.get("enabled", True):
            return

        if profile_id == self.current_profile:
            return

        profile_name = profile.get("name", profile_id)
        self.status.update_status(f"Camera: Switching to {profile_name}...")
        self.root.update_idletasks()

        camera_settings = self.settings["camera"].copy()
        camera_settings.update(profile["camera"])

        try:
            self.camera.reconfigure(camera_settings)
        except CameraError as exc:
            self.status.update_status(str(exc))

            if self.camera.state.value == "streaming":
                self.status.update_status("Camera: Previous profile restored")
            return

        self.current_profile = profile_id
        self.last_frame_time = time.monotonic()
        self.fps = 0.0

        self._update_profile_display()
        self.status.update_status(f"Camera: STREAMING  |  Sensor: {self.camera.sensor_mode}")

    def _handle_crosshair(
        self,
        event: tk.Event | None = None,
    ) -> None:
        """Toggle the camera preview crosshair."""
        self.preview.toggle_crosshair()

    def _handle_exit(
        self,
        event: tk.Event | None = None,
    ) -> None:
        """Request application shutdown."""
        self.terminate()

    def _handle_display_mode(
        self,
        event: tk.Event | None = None,
    ) -> None:
        """Toggle fullscreen when windowed mode is permitted."""
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

    def update_frame(self) -> None:
        """Fetch and display the newest camera frame."""
        if not self.running:
            return

        try:
            frame = self.camera.get_frame()

            if frame is not None:
                self.preview.display_frame(frame)

                current_time = time.monotonic()
                elapsed = current_time - self.last_frame_time

                if elapsed > 0:
                    self.fps = 1.0 / elapsed

                self.last_frame_time = current_time

                status_parts = [
                    f"Camera: {self.camera.state.value.upper()}",
                    (
                        f"Display: {self.root.winfo_width()}x"
                        f"{self.root.winfo_height()}"
                    ),
                ]

                if self.settings["ui"].get("show_fps", True):
                    status_parts.append(f"Preview: {self.fps:.1f} FPS")

                self.status.update_status("  |  ".join(status_parts))

            elif self.camera.state.value == "error":
                self.status.update_status("Camera: ERROR - check camera process")

        except CameraError as exc:
            self.status.update_status(f"Camera: ERROR - {exc}")

        if self.running:
            self.root.after(10, self.update_frame)

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
            try:
                self.root.destroy()
            except tk.TclError:
                pass