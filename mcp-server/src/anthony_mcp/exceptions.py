"""Shared exception types for desktop automation backends."""


class AutomationDisabledError(Exception):
    """Raised when automation is disabled by user."""

    pass


class ExtensionNotFoundError(Exception):
    """Raised when the desktop backend is not available."""

    pass


class WindowNotFoundError(Exception):
    """Raised when a window ID is invalid."""

    pass


class ScreenshotFailedError(Exception):
    """Raised when a screenshot operation fails."""

    pass


class InputFailedError(Exception):
    """Raised when an input injection fails."""

    pass
