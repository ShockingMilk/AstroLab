"""Basic hardware and display discovery."""

import shutil
from dataclasses import dataclass


@dataclass
class DisplayInfo:
    """Information about the active application display."""

    width: int
    height: int


@dataclass
class DeviceInfo:
    """Basic discovered hardware information."""

    camera_executable: str | None
    display: DisplayInfo


class DeviceManager:
    """Discover the devices required by the application."""

    def __init__(self, root) -> None:
        self.root = root

    # ------------------------------------------------------------------
    # Device discovery
    # ------------------------------------------------------------------

    def detect(self) -> DeviceInfo:
        """Detect the camera command and active display."""
        self.root.update_idletasks()

        executable = shutil.which("rpicam-vid")

        return DeviceInfo(
            camera_executable=executable,
            display=self.detect_display(),
        )

    def detect_display(self) -> DisplayInfo:
        """Read the display dimensions from Tkinter."""
        self.root.update_idletasks()

        return DisplayInfo(
            width=self.root.winfo_screenwidth(),
            height=self.root.winfo_screenheight(),
        )