"""Astro Assist application entry point."""

import tkinter as tk

from pathlib import Path
from tkinter import messagebox

from astro_assist.camera.manager import CameraManager
from astro_assist.common.exceptions import AstroAssistError
from astro_assist.config.loader import ConfigLoader
from astro_assist.devices.device_manager import DeviceManager
from astro_assist.ui.main_window import MainWindow


class Application:
    """Initialize and run Astro Assist."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.config_path = project_root / "config" / "settings.json"

        self.config = ConfigLoader(config_path=self.config_path)
        self.root: tk.Tk | None = None
        self.camera: CameraManager | None = None
        self.window: MainWindow | None = None

    def initialize(self) -> None:
        """Load settings, detect the display, and start the camera."""
        settings = self.config.load()
        self.root = tk.Tk()

        DeviceManager(root=self.root).detect_display()

        calibration = settings["profiles"]["0"]

        if not calibration.get("enabled", True):
            raise AstroAssistError("The required Calibration profile is disabled.")

        camera_settings = settings["camera"].copy()
        camera_settings.update(calibration["camera"])

        self.camera = CameraManager(settings=camera_settings)
        self.camera.start()

        self.window = MainWindow(
            root=self.root,
            camera=self.camera,
            settings=settings,
        )

    def run(self) -> None:
        """Initialize and run the application."""
        try:
            self.initialize()

            if self.window is not None:
                self.window.run()

        except Exception as exc:
            if self.camera is not None:
                self.camera.stop()

            if self.root is not None:
                try:
                    messagebox.showerror(
                        "Astro Assist",
                        str(exc),
                        parent=self.root,
                    )
                except tk.TclError:
                    pass

                try:
                    self.root.destroy()
                except tk.TclError:
                    pass

            raise

    def terminate(self) -> None:
        """Stop all application resources."""
        if self.camera is not None:
            self.camera.stop()

        if self.root is not None:
            try:
                self.root.destroy()
            except tk.TclError:
                pass