from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from astrocam.core.enums import (
    StorageMode,
)
from astrocam.core.utils import (
    disk_usage,
    ensure_directory,
    expand_path,
    run_command,
    safe_int,
)


class StorageUnavailableError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class StorageDeviceInfo:

    device: str
    mount_point: str
    filesystem: str
    label: str
    model: str

    total_bytes: int
    free_bytes: int

    removable: bool
    transport: str
    external: bool

    @property
    def used_bytes(self):
        return max(
            0,
            self.total_bytes
            - self.free_bytes,
        )

    @property
    def free_gb(self):
        return (
            self.free_bytes
            / (1024 ** 3)
        )

    @property
    def total_gb(self):
        return (
            self.total_bytes
            / (1024 ** 3)
        )

    @property
    def display_name(self):
        return (
            self.label
            or self.model
            or self.mount_point
        )


@dataclass(frozen=True)
class StorageRecommendation:

    location: str
    reason: str
    free_bytes: int
    sufficient: bool


class StorageManager:

    def __init__(
        self,
        config,
    ):
        self.config = config

        self.devices = []
        self.active_device = None

        self.user_selection = "auto"

        self._last_refresh = 0.0

        self.refresh_interval = (
            float(
                self.config.get(
                    "refresh_interval",
                    2.0,
                )
            )
        )

    # ----------------------------------------------------------
    # Configuration
    # ----------------------------------------------------------

    def update_config(
        self,
        config,
    ):
        self.config = config

        self.refresh_interval = (
            float(
                self.config.get(
                    "refresh_interval",
                    2.0,
                )
            )
        )

        self.refresh(
            force=True
        )

    def set_selection(
        self,
        selection,
    ):
        self.user_selection = (
            str(selection)
            .lower()
        )

        self.refresh(
            force=True
        )

    # ----------------------------------------------------------
    # Discovery
    # ----------------------------------------------------------

    def refresh(
        self,
        force=False,
    ):

        now = time.monotonic()

        if (
            not force
            and self._last_refresh
            and (
                now
                - self._last_refresh
                < self.refresh_interval
            )
        ):
            return

        self.devices = (
            self._discover_devices()
        )

        self.active_device = (
            self._select_device_from_current_inventory()
        )

        self._last_refresh = now

    def _discover_devices(self):

        result = run_command(
            [
                "lsblk",
                "-J",
                "-o",
                (
                    "NAME,KNAME,TYPE,FSTYPE,"
                    "LABEL,MOUNTPOINTS,SIZE,RM,"
                    "TRAN,MODEL"
                ),
            ]
        )

        if (
            not result
            or result.returncode != 0
        ):
            return []

        try:
            data = json.loads(
                result.stdout
            )

        except json.JSONDecodeError:
            return []

        rows = []

        for device in data.get(
            "blockdevices",
            [],
        ):
            self._flatten(
                device,
                rows,
            )

        devices = []

        for row in rows:

            mount_points = row.get(
                "mountpoints",
                [],
            )

            if isinstance(
                mount_points,
                str,
            ):
                mount_points = [
                    mount_points
                ]

            mount_points = [
                point
                for point in mount_points
                if point
            ]

            if not mount_points:
                continue

            mount_point = (
                mount_points[0]
            )

            if self._is_system_mount(
                mount_point
            ):
                continue

            try:
                usage = disk_usage(
                    mount_point
                )

            except OSError:
                continue

            transport = str(
                row.get("tran") or ""
            ).lower()

            removable = bool(
                safe_int(
                    row.get("rm"),
                    0,
                )
            )

            external = (
                self._is_external(
                    transport,
                    removable,
                    mount_point,
                )
            )

            devices.append(
                StorageDeviceInfo(
                    device=(
                        "/dev/"
                        + str(
                            row.get(
                                "kname"
                            )
                            or row.get(
                                "name"
                            )
                        )
                    ),
                    mount_point=mount_point,
                    filesystem=str(
                        row.get(
                            "fstype"
                        )
                        or ""
                    ),
                    label=str(
                        row.get(
                            "label"
                        )
                        or ""
                    ),
                    model=str(
                        row.get(
                            "model"
                        )
                        or ""
                    ).strip(),
                    total_bytes=(
                        usage.total
                    ),
                    free_bytes=(
                        usage.free
                    ),
                    removable=(
                        removable
                    ),
                    transport=(
                        transport
                    ),
                    external=(
                        external
                    ),
                )
            )

        return devices

    def _flatten(
        self,
        row,
        output,
    ):
        output.append(row)

        for child in (
            row.get(
                "children",
                [],
            )
            or []
        ):
            self._flatten(
                child,
                output,
            )

    def _is_system_mount(
        self,
        mount_point,
    ):
        return os.path.normpath(
            mount_point
        ) in {
            "/",
            "/boot",
            "/boot/firmware",
        }

    def _is_external(
        self,
        transport,
        removable,
        mount_point,
    ):

        configured = [
            str(value).lower()
            for value in self.config.get(
                "external_transports",
                ["usb"],
            )
        ]

        if transport in configured:
            return True

        if removable:
            return True

        normalized = os.path.normpath(
            mount_point
        )

        return (
            normalized.startswith(
                "/media/"
            )
            or normalized.startswith(
                "/run/media/"
            )
            or normalized.startswith(
                "/mnt/"
            )
        )

    # ----------------------------------------------------------
    # Device selection
    # ----------------------------------------------------------

    def get_external_devices(self):

        self.refresh()

        return [
            device
            for device in self.devices
            if device.external
        ]

    def get_best_external(self):

        self.refresh()

        candidates = [
            device
            for device in self.devices
            if device.external
        ]

        if not candidates:
            return None

        preferred_label = (
            self.config.get(
                "preferred_label"
            )
        )

        preferred_mount = (
            self.config.get(
                "preferred_mount"
            )
        )

        def score(device):

            return (
                1
                if (
                    preferred_label
                    and device.label
                    == preferred_label
                )
                else 0,

                1
                if (
                    preferred_mount
                    and device.mount_point
                    == preferred_mount
                )
                else 0,

                1
                if device.transport
                == "usb"
                else 0,

                1
                if not device.removable
                else 0,

                device.free_bytes,
            )

        return max(
            candidates,
            key=score,
        )

    def get_internal_storage(self):

        self.refresh()

        candidates = [
            device
            for device in self.devices
            if not device.external
        ]

        if candidates:
            return max(
                candidates,
                key=lambda device:
                    device.free_bytes,
            )

        fallback = expand_path(
            self.config.get(
                "fallback_directory",
                "~/Pictures/Astronomy",
            )
        )

        try:
            usage = disk_usage(
                fallback
            )

        except OSError:
            return None

        return StorageDeviceInfo(
            device="local-filesystem",
            mount_point=str(
                fallback
            ),
            filesystem="",
            label="Internal",
            model="",
            total_bytes=usage.total,
            free_bytes=usage.free,
            removable=False,
            transport="",
            external=False,
        )

    def _select_device_from_current_inventory(
        self,
    ):

        if (
            self.user_selection
            == "external"
        ):

            candidates = [
                device
                for device in self.devices
                if device.external
            ]

            return (
                max(
                    candidates,
                    key=lambda d:
                        d.free_bytes,
                )
                if candidates
                else None
            )

        if (
            self.user_selection
            == "internal"
        ):

            candidates = [
                device
                for device in self.devices
                if not device.external
            ]

            if candidates:
                return max(
                    candidates,
                    key=lambda d:
                        d.free_bytes,
                )

            return None

        mode = StorageMode.from_value(
            self.config.get(
                "mode",
                "auto",
            )
        )

        if mode == StorageMode.EXTERNAL:

            candidates = [
                device
                for device in self.devices
                if device.external
            ]

            return (
                max(
                    candidates,
                    key=lambda d:
                        d.free_bytes,
                )
                if candidates
                else None
            )

        if mode == StorageMode.LOCAL:

            candidates = [
                device
                for device in self.devices
                if not device.external
            ]

            if candidates:
                return max(
                    candidates,
                    key=lambda d:
                        d.free_bytes,
                )

            return None

        external = [
            device
            for device in self.devices
            if device.external
        ]

        if (
            self.config.get(
                "prefer_external",
                True,
            )
            and external
        ):
            return max(
                external,
                key=lambda d:
                    d.free_bytes,
            )

        internal = [
            device
            for device in self.devices
            if not device.external
        ]

        if internal:
            return max(
                internal,
                key=lambda d:
                    d.free_bytes,
            )

        return None

    # ----------------------------------------------------------
    # Space safeguards
    # ----------------------------------------------------------

    def has_enough_space(
        self,
        device,
        required_bytes,
    ):

        if device is None:
            return False

        safety_mb = safe_int(
            self.config.get(
                "safety_margin_mb",
                256,
            ),
            256,
        )

        safety_bytes = (
            safety_mb
            * 1024
            * 1024
        )

        return (
            device.free_bytes
            >= (
                required_bytes
                + safety_bytes
            )
        )

    def recommend_storage(
        self,
        required_bytes,
    ):

        external = (
            self.get_best_external()
        )

        internal = (
            self.get_internal_storage()
        )

        external_ok = (
            external is not None
            and self.has_enough_space(
                external,
                required_bytes,
            )
        )

        internal_ok = (
            internal is not None
            and self.has_enough_space(
                internal,
                required_bytes,
            )
        )

        if (
            external_ok
            and internal_ok
        ):

            if (
                external.free_bytes
                >= internal.free_bytes
            ):
                return StorageRecommendation(
                    location="external",
                    reason=(
                        "External storage "
                        "has more free space."
                    ),
                    free_bytes=(
                        external.free_bytes
                    ),
                    sufficient=True,
                )

            return StorageRecommendation(
                location="internal",
                reason=(
                    "Internal storage "
                    "has more free space."
                ),
                free_bytes=(
                    internal.free_bytes
                ),
                sufficient=True,
            )

        if external_ok:
            return StorageRecommendation(
                location="external",
                reason=(
                    "External storage "
                    "has enough free space."
                ),
                free_bytes=(
                    external.free_bytes
                ),
                sufficient=True,
            )

        if internal_ok:
            return StorageRecommendation(
                location="internal",
                reason=(
                    "External storage does "
                    "not have enough space; "
                    "internal storage does."
                ),
                free_bytes=(
                    internal.free_bytes
                ),
                sufficient=True,
            )

        return StorageRecommendation(
            location="none",
            reason=(
                "No available storage "
                "location has enough "
                "free space."
            ),
            free_bytes=0,
            sufficient=False,
        )

    # ----------------------------------------------------------
    # Destination handling
    # ----------------------------------------------------------

    def get_directory(
        self,
        category,
    ):

        self.refresh(
            force=True
        )

        device = (
            self._select_device_from_current_inventory()
        )

        if device is None:

            if (
                self.user_selection
                == "internal"
            ):
                device = (
                    self.get_internal_storage()
                )

            if device is None:
                raise StorageUnavailableError(
                    "No suitable storage "
                    "location is available."
                )

        mode = StorageMode.from_value(
            self.config.get(
                "mode",
                "auto",
            )
        )

        if (
            mode
            == StorageMode.EXTERNAL
            and not device.external
        ):
            raise StorageUnavailableError(
                "External storage is "
                "required but unavailable."
            )

        if (
            self.user_selection
            == "external"
            and not device.external
        ):
            raise StorageUnavailableError(
                "External storage was "
                "selected but is unavailable."
            )

        if device.external:

            root = (
                Path(
                    device.mount_point
                )
                / self.config.get(
                    "directory_name",
                    "Astronomy",
                )
            )

        else:

            root = expand_path(
                self.config.get(
                    "fallback_directory",
                    "~/Pictures/Astronomy",
                )
            )

        directory_name = (
            self.config.get(
                f"{category}_directory",
                category.capitalize(),
            )
        )

        directory = ensure_directory(
            root / directory_name
        )

        self.active_device = device

        return directory

    # ----------------------------------------------------------
    # Runtime status
    # ----------------------------------------------------------

    def is_path_available(
        self,
        path,
    ):

        self.refresh()

        target = Path(path)

        for device in self.devices:

            mount = Path(
                device.mount_point
            )

            try:
                target.relative_to(
                    mount
                )

                return True

            except ValueError:
                continue

        return False

    def status_text(self):

        self.refresh()

        device = self.active_device

        if device is None:
            return "STOR: NONE"

        location = (
            "EXT"
            if device.external
            else "INT"
        )

        threshold = float(
            self.config.get(
                "low_space_threshold_gb",
                5,
            )
        )

        warning = (
            " !LOW"
            if device.free_gb
            < threshold
            else ""
        )

        return (
            f"STOR: {location} "
            f"{device.free_gb:.1f}G"
            f"{warning}"
        )