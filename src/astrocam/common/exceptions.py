"""Application-specific exceptions."""


class AstroAssistError(Exception):
    """Base exception for Astro Assist."""


class CameraError(AstroAssistError):
    """Raised when camera initialization or capture fails."""


class ConfigurationError(AstroAssistError):
    """Raised when application configuration is invalid."""


class DeviceError(AstroAssistError):
    """Raised when a required device cannot be found."""