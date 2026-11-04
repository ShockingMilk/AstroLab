from __future__ import annotations

import os
from dataclasses import dataclass, field

from picamera2 import Picamera2

from astrocam.camera.modes import (
    SensorMode,
)
from astrocam.core.enums import (
    CameraTransport,
)
from astrocam.core.utils import (
    run_command,
)


@dataclass
class CameraDeviceInfo:
    index: int
    model: str
    camera_id: str
    location: str
    rotation: int
    camera_type: CameraTransport
    sensor_modes: list[SensorMode] = field(
        default_factory=list
    )


@dataclass
class DisplayDeviceInfo:
    name: str
    description: str
    width: int
    height: int
    refresh_rate: float
    source: str
    primary: bool = False


@dataclass
class TouchDeviceInfo:
    name: str
    event_device: str
    detected: bool


@dataclass
class DeviceInventory:
    cameras: list[
        CameraDeviceInfo
    ] = field(default_factory=list)

    displays: list[
        DisplayDeviceInfo
    ] = field(default_factory=list)

    touchscreens: list[
        TouchDeviceInfo
    ] = field(default_factory=list)


class DeviceManager:

    def __init__(
        self,
        camera_config=None,
    ):
        self.camera_config = (
            camera_config
            or {}
        )

    def detect(self):
        inventory = DeviceInventory()

        inventory.cameras = (
            self._discover_cameras()
        )

        inventory.displays = (
            self._discover_displays()
        )

        inventory.touchscreens = (
            self._discover_touchscreens()
        )

        return inventory

    # --------------------------------------------------------------
    # Cameras
    # --------------------------------------------------------------

    def _discover_cameras(self):
        cameras = []

        camera_info = (
            Picamera2.global_camera_info()
        )

        for index, info in enumerate(
            camera_info
        ):
            try:
                picam2 = Picamera2(
                    index
                )

                modes = [
                    SensorMode.from_dict(
                        mode
                    )
                    for mode
                    in picam2.sensor_modes
                ]

                picam2.close()

            except Exception:
                modes = []

            model = str(
                info.get(
                    "Model",
                    "Unknown",
                )
            )

            camera_id = str(
                info.get(
                    "Id",
                    "",
                )
            )

            location = str(
                info.get(
                    "Location",
                    "",
                )
            )

            rotation = int(
                info.get(
                    "Rotation",
                    0,
                )
            )

            camera_type = (
                self._classify_camera(
                    camera_id,
                    model,
                )
            )

            cameras.append(
                CameraDeviceInfo(
                    index=index,
                    model=model,
                    camera_id=camera_id,
                    location=location,
                    rotation=rotation,
                    camera_type=camera_type,
                    sensor_modes=modes,
                )
            )

        return cameras

    def _classify_camera(
        self,
        camera_id,
        model,
    ):

        combined = (
            f"{camera_id} {model}"
        ).lower()

        if "usb" in combined:
            return CameraTransport.USB

        if (
            "csi" in combined
            or "unicam" in combined
        ):
            return CameraTransport.CSI2

        # Picamera2 CSI cameras are the
        # normal native-camera path.
        return CameraTransport.CSI2

    def select_camera(
        self,
        inventory,
    ):

        cameras = inventory.cameras

        if not cameras:
            raise RuntimeError(
                "No compatible camera was detected."
            )

        configured_index = (
            self.camera_config.get(
                "index",
                "auto",
            )
        )

        configured_id = (
            self.camera_config.get(
                "id"
            )
        )

        configured_model = (
            self.camera_config.get(
                "model"
            )
        )

        if (
            configured_index != "auto"
            and configured_index is not None
        ):
            index = int(
                configured_index
            )

            for camera in cameras:
                if camera.index == index:
                    return camera

        if configured_id:
            for camera in cameras:
                if camera.camera_id == configured_id:
                    return camera

        if configured_model:
            for camera in cameras:
                if camera.model == configured_model:
                    return camera

        csi_cameras = [
            camera
            for camera in cameras
            if camera.camera_type
            == CameraTransport.CSI2
        ]

        return (
            csi_cameras[0]
            if csi_cameras
            else cameras[0]
        )

    # --------------------------------------------------------------
    # Displays
    # --------------------------------------------------------------

    def _discover_displays(self):
        displays = []

        displays.extend(
            self._discover_wayland_displays()
        )

        if not displays:
            displays.extend(
                self._discover_xrandr_displays()
            )

        if not displays:
            displays.extend(
                self._discover_drm_display()
            )

        return displays

    def _discover_wayland_displays(self):
        displays = []

        result = run_command(
            [
                "wlr-randr",
                "--json",
            ]
        )

        if not result or result.returncode != 0:
            return displays

        try:
            import json

            data = json.loads(
                result.stdout
            )

        except Exception:
            return displays

        for output in data:
            name = output.get(
                "name",
                "display",
            )

            modes = output.get(
                "modes",
                [],
            )

            preferred = None

            for mode in modes:
                if mode.get(
                    "current",
                    False,
                ):
                    preferred = mode
                    break

            if preferred is None:
                for mode in modes:
                    if mode.get(
                        "preferred",
                        False,
                    ):
                        preferred = mode
                        break

            if preferred is None and modes:
                preferred = modes[0]

            if preferred is None:
                continue

            displays.append(
                DisplayDeviceInfo(
                    name=name,
                    description=name,
                    width=int(
                        preferred["width"]
                    ),
                    height=int(
                        preferred["height"]
                    ),
                    refresh_rate=float(
                        preferred.get(
                            "refresh",
                            60,
                        )
                    ),
                    source="wayland",
                    primary=bool(
                        output.get(
                            "focused",
                            False,
                        )
                    ),
                )
            )

        return displays

    def _discover_xrandr_displays(self):
        displays = []

        result = run_command(
            [
                "xrandr",
                "--query",
            ]
        )

        if not result or result.returncode != 0:
            return displays

        for line in result.stdout.splitlines():
            if (
                " connected"
                not in line
            ):
                continue

            parts = line.split()

            if len(parts) < 3:
                continue

            name = parts[0]

            resolution = None

            for part in parts:
                if "x" in part:
                    candidate = part.split("+")[0]

                    try:
                        width, height = (
                            candidate.split("x")
                        )

                        resolution = (
                            int(width),
                            int(height),
                        )

                        break

                    except ValueError:
                        continue

            if not resolution:
                continue

            displays.append(
                DisplayDeviceInfo(
                    name=name,
                    description=name,
                    width=resolution[0],
                    height=resolution[1],
                    refresh_rate=60.0,
                    source="xrandr",
                    primary=(
                        "primary"
                        in line
                    ),
                )
            )

        return displays

    def _discover_drm_display(self):
        displays = []

        drm_path = "/sys/class/drm"

        if not os.path.exists(
            drm_path
        ):
            return displays

        for entry in os.listdir(
            drm_path
        ):
            status_path = os.path.join(
                drm_path,
                entry,
                "status",
            )

            mode_path = os.path.join(
                drm_path,
                entry,
                "modes",
            )

            if not os.path.exists(
                status_path
            ):
                continue

            try:
                status = open(
                    status_path,
                    "r",
                    encoding="utf-8",
                ).read().strip()

            except OSError:
                continue

            if status != "connected":
                continue

            try:
                mode = open(
                    mode_path,
                    "r",
                    encoding="utf-8",
                ).readline().strip()

                width, height = (
                    mode.split("x")
                )

                displays.append(
                    DisplayDeviceInfo(
                        name=entry,
                        description=entry,
                        width=int(width),
                        height=int(height),
                        refresh_rate=60.0,
                        source="drm",
                    )
                )

            except (
                OSError,
                ValueError,
            ):
                continue

        return displays

    # --------------------------------------------------------------
    # Touch
    # --------------------------------------------------------------

    def _discover_touchscreens(self):
        devices = []

        try:
            content = open(
                "/proc/bus/input/devices",
                "r",
                encoding="utf-8",
            ).read()

        except OSError:
            return devices

        blocks = content.split(
            "\n\n"
        )

        for block in blocks:
            lower = block.lower()

            if (
                "touchscreen" not in lower
                and "touch screen"
                not in lower
            ):
                continue

            name = "Unknown Touchscreen"

            for line in block.splitlines():
                if line.startswith(
                    "N: Name="
                ):
                    name = (
                        line.split(
                            "=", 1
                        )[1]
                        .strip('"')
                    )

            devices.append(
                TouchDeviceInfo(
                    name=name,
                    event_device="unknown",
                    detected=True,
                )
            )

        return devices

    # --------------------------------------------------------------

    @staticmethod
    def print_summary(
        inventory,
    ):

        print("\n=== Cameras ===")

        for camera in inventory.cameras:
            print(
                f"[{camera.index}] "
                f"{camera.model} "
                f"({camera.camera_type.value})"
            )

        print("\n=== Displays ===")

        for display in inventory.displays:
            print(
                f"{display.name}: "
                f"{display.width}x"
                f"{display.height}"
            )

        print("\n=== Touchscreens ===")

        for touchscreen in inventory.touchscreens:
            print(
                touchscreen.name
            )