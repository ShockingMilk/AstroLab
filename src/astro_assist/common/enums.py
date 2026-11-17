"""Centralized application enums."""

from enum import Enum


class AppState(Enum):
    """Application lifecycle states."""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class CameraState(Enum):
    """Camera process states."""

    DISCONNECTED = "disconnected"
    STARTING = "starting"
    STREAMING = "streaming"
    STOPPING = "stopping"
    ERROR = "error"


class ProfileType(Enum):
    """Initial observing profile categories."""

    CALIBRATION = "calibration"
    PLANETARY = "planetary"
    LUNAR = "lunar"
    STELLAR = "stellar"
    DEEP_SKY = "deep_sky"


class UIAction(Enum):
    """Actions available to the application UI."""

    EXIT = "exit"
    TOGGLE_FULLSCREEN = "toggle_fullscreen"
    TOGGLE_CROSSHAIR = "toggle_crosshair"
    SELECT_CALIBRATION = "select_calibration"