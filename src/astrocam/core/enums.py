from enum import Enum


class ConfigEnum(str, Enum):
    """Base enum with convenient configuration parsing."""

    @classmethod
    def from_value(cls, value, default=None):
        if value is None:
            if default is not None:
                return default

            raise ValueError(
                f"{cls.__name__} requires a value."
            )

        if isinstance(value, cls):
            return value

        normalized = str(value).strip().lower()

        for member in cls:
            if member.value == normalized:
                return member

        valid = ", ".join(
            member.value
            for member in cls
        )

        raise ValueError(
            f"Invalid {cls.__name__} value "
            f"'{value}'. Expected one of: {valid}"
        )


class CameraPurpose(ConfigEnum):
    GENERAL = "general"
    CALIBRATION = "calibration"
    MOON = "moon"
    PLANETARY = "planetary"
    BRIGHT_PLANET = "bright_planet"
    BRIGHT_STAR = "bright_star"
    STAR_FIELD = "star_field"


class CameraModeSelection(ConfigEnum):
    AUTO = "auto"
    EXPLICIT = "explicit"


class StreamResolutionMode(ConfigEnum):
    SENSOR = "sensor"
    DEFAULT = "default"


class CommandAction(ConfigEnum):
    SCREENSHOT = "screenshot"
    CLEAN_VIEW = "clean_view"
    HISTOGRAM = "histogram"
    FOCUS_ASSIST = "focus_assist"
    EXPOSURE_MODE = "exposure_mode"
    RECORD_VIDEO = "record_video"
    STORAGE_LOCATION = "storage_location"
    RELOAD = "reload"
    EXIT = "exit"


class AdjustmentMode(ConfigEnum):
    EXPOSURE = "exposure"
    GAIN = "gain"


class CameraTransport(ConfigEnum):
    CSI2 = "csi2"
    USB = "usb"
    UNKNOWN = "unknown"


class StorageMode(ConfigEnum):
    AUTO = "auto"
    EXTERNAL = "external"
    LOCAL = "local"


class StorageSelection(ConfigEnum):
    AUTO = "auto"
    EXTERNAL = "external"
    INTERNAL = "internal"


class PopupType(ConfigEnum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CONFIRM = "confirm"
    SELECTION = "selection"