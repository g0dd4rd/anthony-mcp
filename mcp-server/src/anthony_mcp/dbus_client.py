"""D-Bus client for the GNOME Desktop Automation extension."""

import json

from anthony_mcp.exceptions import (
    AutomationDisabledError,
    ExtensionNotFoundError,
    InputFailedError,
    ScreenshotFailedError,
    WindowNotFoundError,
)

IFACE = "io.github.anthonymcp.DesktopAutomation"
BUS_NAME = "org.gnome.Shell"
OBJECT_PATH = "/io/github/anthonymcp/DesktopAutomation"


def _translate_error(e: Exception) -> Exception:
    """Translate a D-Bus error to a typed exception."""
    msg = str(e)
    if "Disabled" in msg:
        return AutomationDisabledError(
            "Automation disabled by user. Enable from top bar indicator."
        )
    if "WindowNotFound" in msg:
        return WindowNotFoundError(msg)
    if "ScreenshotFailed" in msg:
        return ScreenshotFailedError(msg)
    if "InputFailed" in msg:
        return InputFailedError(msg)
    return e


class DbusClient:
    """Proxy to the Desktop Automation D-Bus interface."""

    TIMEOUT_MS = 5000  # 5 second timeout

    def __init__(self):
        # Imported lazily so that `tools/list` works in environments without
        # PyGObject / GNOME libraries (e.g. Glama's inspection sandbox).
        try:
            from dasbus.connection import SessionMessageBus

            bus = SessionMessageBus()
            self._proxy = bus.get_proxy(BUS_NAME, OBJECT_PATH)
        except Exception as e:
            raise ExtensionNotFoundError(
                "GNOME Shell extension not installed or not enabled. "
                "Install desktop-automation@anthonymcp.github.io and restart GNOME Shell."
            ) from e

    def _call(self, method: str, *args):
        from dasbus.error import DBusError

        try:
            return getattr(self._proxy, method)(*args, timeout=self.TIMEOUT_MS)
        except DBusError as e:
            raise _translate_error(e) from e
        except TimeoutError as e:
            raise ExtensionNotFoundError(
                "Extension not responding -- GNOME Shell may be busy"
            ) from e

    # --- Utility ---

    def ping(self) -> bool:
        return self._call("Ping")

    def get_enabled(self) -> bool:
        return self._call("GetEnabled")

    def set_enabled(self, enabled: bool) -> bool:
        return self._call("SetEnabled", enabled)

    def get_monitors(self) -> list[dict]:
        return json.loads(self._call("GetMonitors"))

    def cleanup_screenshots(self) -> int:
        return self._call("CleanupScreenshots")

    # --- Notifications ---

    def send_notification(self, summary: str, body: str = "") -> bool:
        return self._call("SendNotification", summary, body)

    # --- Volume ---

    def get_volume(self) -> dict:
        """Get current volume level and mute status.

        Returns:
            dict with 'volume' (0-100) and 'muted' (bool)
        """
        json_str = self._call("GetVolume")
        return json.loads(json_str)

    def set_volume(self, volume: int, relative: bool = False) -> str:
        """Set system volume.

        Args:
            volume: Volume level (0-100 for absolute, -100 to 100 for relative)
            relative: If True, volume is relative change

        Returns:
            Success message
        """
        return self._call("SetVolume", volume, relative)

    def mute_volume(self, mute: bool = True) -> str:
        """Mute or unmute system volume.

        Args:
            mute: True to mute, False to unmute

        Returns:
            Success message
        """
        return self._call("MuteVolume", mute)

    # --- Screenshots ---

    def screenshot(self, include_cursor: bool = False) -> str:
        return self._call("Screenshot", include_cursor)

    def screenshot_window(
        self, window_id: str, include_frame: bool = True, include_cursor: bool = False
    ) -> str:
        return self._call("ScreenshotWindow", int(window_id), include_frame, include_cursor)

    def screenshot_area(
        self, x: int, y: int, width: int, height: int, include_cursor: bool = False
    ) -> str:
        return self._call("ScreenshotArea", x, y, width, height, include_cursor)

    def pick_color(self, x: int, y: int) -> tuple[float, float, float]:
        return self._call("PickColor", x, y)

    # --- Windows ---

    def list_windows(self) -> list[dict]:
        return json.loads(self._call("ListWindows"))

    def get_window(self, window_id: str) -> dict:
        return json.loads(self._call("GetWindow", int(window_id)))

    def focus_window(self, window_id: str) -> bool:
        return self._call("FocusWindow", int(window_id))

    def move_resize_window(self, window_id: str, x: int, y: int, width: int, height: int) -> bool:
        return self._call("MoveResizeWindow", int(window_id), x, y, width, height)

    def minimize_window(self, window_id: str) -> bool:
        return self._call("MinimizeWindow", int(window_id))

    def unminimize_window(self, window_id: str) -> bool:
        return self._call("UnminimizeWindow", int(window_id))

    def maximize_window(self, window_id: str) -> bool:
        return self._call("MaximizeWindow", int(window_id))

    def unmaximize_window(self, window_id: str) -> bool:
        return self._call("UnmaximizeWindow", int(window_id))

    def close_window(self, window_id: str) -> bool:
        return self._call("CloseWindow", int(window_id))

    def list_workspaces(self) -> list[dict]:
        return json.loads(self._call("ListWorkspaces"))

    def activate_workspace(self, index: int) -> bool:
        return self._call("ActivateWorkspace", index)

    def move_window_to_workspace(self, window_id: str, workspace_index: int) -> bool:
        return self._call("MoveWindowToWorkspace", int(window_id), workspace_index)

    # --- Input ---

    def key_press(self, key: str) -> bool:
        from anthony_mcp.utils import friendly_to_keyval

        keyval = friendly_to_keyval(key)
        return self._call("KeyPress", keyval)

    def key_combo(self, combo: str) -> bool:
        from anthony_mcp.utils import translate_combo

        translated = translate_combo(combo)
        return self._call("KeyCombo", translated)

    def type_text(self, text: str) -> bool:
        return self._call("TypeText", text)

    def mouse_move(self, x: int, y: int) -> bool:
        return self._call("MouseMove", x, y)

    def mouse_click(self, x: int, y: int, button: int = 1) -> bool:
        return self._call("MouseClick", x, y, button)

    def mouse_double_click(self, x: int, y: int, button: int = 1) -> bool:
        return self._call("MouseDoubleClick", x, y, button)

    def mouse_down(self, x: int, y: int, button: int = 1) -> bool:
        return self._call("MouseDown", x, y, button)

    def mouse_up(self, x: int, y: int, button: int = 1) -> bool:
        return self._call("MouseUp", x, y, button)

    def mouse_drag(self, x1: int, y1: int, x2: int, y2: int, button: int = 1) -> bool:
        return self._call("MouseDrag", x1, y1, x2, y2, button)

    def mouse_scroll(self, x: int, y: int, dx: float, dy: float) -> bool:
        return self._call("MouseScroll", x, y, dx, dy)
