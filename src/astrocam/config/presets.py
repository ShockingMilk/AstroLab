from __future__ import annotations

import json
from pathlib import Path

from astrocam.core.enums import (
    CameraModeSelection,
    CameraPurpose,
    CommandAction,
    StorageMode,
)


class PresetManager:

    def __init__(
        self,
        path,
    ):
        self.path = Path(path)

        self.data = {}

        self.load()

    def load(self):

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            self.data = json.load(file)

        self.validate()

    def reload(self):
        self.load()

    def validate(self):

        if "profiles" not in self.data:
            raise ValueError(
                "Configuration requires "
                "'profiles'."
            )

        if "commands" not in self.data:
            raise ValueError(
                "Configuration requires "
                "'commands'."
            )

        storage = self.data.get(
            "storage",
            {},
        )

        StorageMode.from_value(
            storage.get(
                "mode",
                "auto",
            )
        )

        for key, profile in (
            self.data["profiles"].items()
        ):

            camera = profile.get(
                "camera",
                {},
            )

            CameraPurpose.from_value(
                camera.get(
                    "purpose",
                    "general",
                )
            )

            CameraModeSelection.from_value(
                camera.get(
                    "mode",
                    "auto",
                )
            )

        for command in (
            self.data["commands"].values()
        ):
            CommandAction.from_value(
                command["action"]
            )

    @property
    def camera(self):
        return self.data.get(
            "camera",
            {},
        )

    @property
    def display(self):
        return self.data.get(
            "display",
            {},
        )

    @property
    def storage(self):
        return self.data.get(
            "storage",
            {},
        )

    @property
    def profiles(self):
        return self.data.get(
            "profiles",
            {},
        )

    @property
    def commands(self):
        return self.data.get(
            "commands",
            {},
        )

    def get_profile(
        self,
        number,
    ):
        return self.profiles.get(
            str(number)
        )

    def get_profile_name(
        self,
        number,
    ):
        profile = self.get_profile(
            number
        )

        if not profile:
            return "Unknown"

        return profile.get(
            "name",
            "Unnamed",
        )

    def get_command_items(self):

        result = []

        for key, command in (
            self.commands.items()
        ):
            result.append(
                (
                    key,
                    command.get(
                        "name",
                        key,
                    ),
                    CommandAction.from_value(
                        command["action"]
                    ),
                    command.get(
                        "options",
                        {},
                    ),
                )
            )

        return result