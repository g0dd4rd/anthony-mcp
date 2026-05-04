"""MCP server for GNOME desktop automation."""

import json
import time
import threading
import re
import subprocess
from mcp.server.fastmcp import FastMCP
from gnome_desktop_mcp.dbus_client import (
    DbusClient, AutomationDisabledError, ExtensionNotFoundError,
    WindowNotFoundError, ScreenshotFailedError, InputFailedError,
)
from gnome_desktop_mcp.utils import friendly_to_keyval, translate_combo, file_to_base64, cleanup_file

mcp = FastMCP(
    "gnome-desktop-automation",
    instructions="GNOME desktop automation: screenshots, window management, input injection",
)

_client: DbusClient | None = None


def _get_client() -> DbusClient:
    global _client
    if _client is None:
        _client = DbusClient()
    return _client


def _handle_error(e: Exception) -> str:
    if isinstance(e, AutomationDisabledError):
        return f"Error: {e}"
    if isinstance(e, ExtensionNotFoundError):
        return f"Error: {e}"
    if isinstance(e, WindowNotFoundError):
        return f"Error: {e}"
    if isinstance(e, ScreenshotFailedError):
        return f"Error: {e}"
    if isinstance(e, InputFailedError):
        return f"Error: {e}"
    return f"Error: {e}"


# --- Screenshot Tools ---

@mcp.tool()
def screenshot(include_cursor: bool = False, format: str = "path") -> str:
    """Take a full screenshot of the entire screen.

    Args:
        include_cursor: Whether to include the mouse cursor.
        format: "path" returns filepath, "base64" returns base64-encoded PNG.
    """
    try:
        client = _get_client()
        filepath = client.screenshot(include_cursor)
        if format == "base64":
            data = file_to_base64(filepath)
            cleanup_file(filepath)
            return data
        return filepath
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def screenshot_window(window_id: int, include_frame: bool = True,
                      include_cursor: bool = False,
                      format: str = "path") -> str:
    """Take a screenshot of a specific window.

    Args:
        window_id: The window's stable ID (from list_windows).
        include_frame: Whether to include window decorations.
        include_cursor: Whether to include the mouse cursor.
        format: "path" returns filepath, "base64" returns base64-encoded PNG.
    """
    try:
        client = _get_client()
        filepath = client.screenshot_window(window_id, include_frame, include_cursor)
        if format == "base64":
            data = file_to_base64(filepath)
            cleanup_file(filepath)
            return data
        return filepath
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def screenshot_area(x: int, y: int, width: int, height: int,
                    include_cursor: bool = False,
                    format: str = "path") -> str:
    """Take a screenshot of a rectangular screen region.

    Args:
        x: Left edge in pixels.
        y: Top edge in pixels.
        width: Width in pixels.
        height: Height in pixels.
        include_cursor: Whether to include the mouse cursor.
        format: "path" returns filepath, "base64" returns base64-encoded PNG.
    """
    try:
        client = _get_client()
        filepath = client.screenshot_area(x, y, width, height, include_cursor)
        if format == "base64":
            data = file_to_base64(filepath)
            cleanup_file(filepath)
            return data
        return filepath
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def pick_color(x: int, y: int) -> str:
    """Get the pixel color at screen coordinates.

    Args:
        x: X coordinate in pixels.
        y: Y coordinate in pixels.

    Returns:
        JSON with r, g, b values (0.0-1.0).
    """
    try:
        client = _get_client()
        r, g, b = client.pick_color(x, y)
        return json.dumps({"r": r, "g": g, "b": b})
    except Exception as e:
        return _handle_error(e)


# --- Window Tools ---

@mcp.tool()
def list_windows() -> str:
    """List all open windows with their properties.

    Returns JSON array with id, title, wmClass, position, size, state, workspace.
    """
    try:
        client = _get_client()
        return json.dumps(client.list_windows(), indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def get_window(window_id: int) -> str:
    """Get detailed properties of a specific window.

    Args:
        window_id: The window's stable ID (from list_windows).
    """
    try:
        client = _get_client()
        return json.dumps(client.get_window(window_id), indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def focus_window(window_id: int) -> str:
    """Focus and raise a window.

    Args:
        window_id: The window's stable ID (from list_windows).
    """
    try:
        client = _get_client()
        client.focus_window(window_id)
        return "Window focused"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def move_resize_window(window_id: int, x: int, y: int,
                       width: int, height: int) -> str:
    """Move and resize a window. Unmaximizes first if needed.

    Args:
        window_id: The window's stable ID.
        x: New X position.
        y: New Y position.
        width: New width.
        height: New height.
    """
    try:
        client = _get_client()
        client.move_resize_window(window_id, x, y, width, height)
        return "Window moved and resized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def minimize_window(window_id: int) -> str:
    """Minimize a window."""
    try:
        client = _get_client()
        client.minimize_window(window_id)
        return "Window minimized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def unminimize_window(window_id: int) -> str:
    """Unminimize (restore) a window."""
    try:
        client = _get_client()
        client.unminimize_window(window_id)
        return "Window unminimized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def maximize_window(window_id: int) -> str:
    """Maximize a window."""
    try:
        client = _get_client()
        client.maximize_window(window_id)
        return "Window maximized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def unmaximize_window(window_id: int) -> str:
    """Unmaximize a window."""
    try:
        client = _get_client()
        client.unmaximize_window(window_id)
        return "Window unmaximized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def close_window(window_id: int) -> str:
    """Close a window."""
    try:
        client = _get_client()
        client.close_window(window_id)
        return "Window closed"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def list_workspaces() -> str:
    """List all workspaces with their properties."""
    try:
        client = _get_client()
        return json.dumps(client.list_workspaces(), indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def activate_workspace(index: int) -> str:
    """Switch to a workspace by index (0-based)."""
    try:
        client = _get_client()
        client.activate_workspace(index)
        return f"Switched to workspace {index}"
    except Exception as e:
        return _handle_error(e)


# --- Input Tools ---

@mcp.tool()
def key_press(key: str) -> str:
    """Press and release a single key.

    Args:
        key: Key name like "Return", "a", "F5", "Ctrl", "Escape".
    """
    try:
        client = _get_client()
        keyval = friendly_to_keyval(key)
        client.key_press(keyval)
        return f"Key pressed: {key}"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def key_combo(keys: str) -> str:
    """Press a key combination.

    Args:
        keys: Combo like "Ctrl+Alt+t", "Shift+F5", "Super+l".
    """
    try:
        client = _get_client()
        combo = translate_combo(keys)
        client.key_combo(combo)
        return f"Key combo pressed: {keys}"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def type_text(text: str) -> str:
    """Type text character by character.

    Args:
        text: Text to type.
    """
    try:
        client = _get_client()
        client.type_text(text)
        return f"Typed {len(text)} characters"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def mouse_move(x: int, y: int) -> str:
    """Move the mouse to absolute screen coordinates."""
    try:
        client = _get_client()
        client.mouse_move(x, y)
        return f"Mouse moved to ({x}, {y})"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def mouse_click(x: int, y: int, button: int = 1) -> str:
    """Click at screen coordinates. button: 1=left, 2=middle, 3=right."""
    try:
        client = _get_client()
        client.mouse_click(x, y, button)
        return f"Clicked at ({x}, {y}) button {button}"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def mouse_double_click(x: int, y: int, button: int = 1) -> str:
    """Double-click at screen coordinates."""
    try:
        client = _get_client()
        client.mouse_double_click(x, y, button)
        return f"Double-clicked at ({x}, {y}) button {button}"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def mouse_down(x: int, y: int, button: int = 1) -> str:
    """Press mouse button down without releasing."""
    try:
        client = _get_client()
        client.mouse_down(x, y, button)
        return f"Mouse down at ({x}, {y}) button {button}"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def mouse_up(x: int, y: int, button: int = 1) -> str:
    """Release mouse button."""
    try:
        client = _get_client()
        client.mouse_up(x, y, button)
        return f"Mouse up at ({x}, {y}) button {button}"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def mouse_drag(x1: int, y1: int, x2: int, y2: int, button: int = 1) -> str:
    """Drag from one position to another."""
    try:
        client = _get_client()
        client.mouse_drag(x1, y1, x2, y2, button)
        return f"Dragged from ({x1}, {y1}) to ({x2}, {y2})"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def mouse_scroll(x: int, y: int, dx: float, dy: float) -> str:
    """Scroll at screen coordinates. dy negative=up, positive=down."""
    try:
        client = _get_client()
        client.mouse_scroll(x, y, dx, dy)
        return f"Scrolled at ({x}, {y}) by ({dx}, {dy})"
    except Exception as e:
        return _handle_error(e)


# --- Utility Tools ---

@mcp.tool()
def get_monitors() -> str:
    """List all monitors with their geometry and scale."""
    try:
        client = _get_client()
        return json.dumps(client.get_monitors(), indent=2)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def ping() -> str:
    """Check if the extension is running and responding."""
    try:
        client = _get_client()
        client.ping()
        return "Extension is alive"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def get_enabled() -> str:
    """Check if automation is enabled."""
    try:
        client = _get_client()
        enabled = client.get_enabled()
        return f"Automation is {'enabled' if enabled else 'disabled'}"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def set_enabled(enabled: bool) -> str:
    """Enable or disable automation."""
    try:
        client = _get_client()
        client.set_enabled(enabled)
        return f"Automation {'enabled' if enabled else 'disabled'}"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def cleanup_screenshots() -> str:
    """Remove all temporary screenshot files."""
    try:
        client = _get_client()
        count = client.cleanup_screenshots()
        return f"Removed {count} screenshot files"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def send_notification(summary: str, body: str = "", delay: str = "") -> str:
    """Send a desktop notification immediately or after a delay.

    Args:
        summary: Notification title/headline (required).
        body: Notification message body (optional).
        delay: Time delay before sending (optional).
               Examples: "5 minutes", "1 hour", "30 seconds", "2 hours 30 minutes"
               If empty, sends immediately.

    Returns:
        Success or error message.
    """
    try:
        client = _get_client()

        # If no delay, send immediately
        if not delay or delay.strip() == "":
            success = client.send_notification(summary, body)
            if success:
                return f"Notification sent: {summary}"
            return "Notification failed"

        # Parse delay and schedule notification
        delay_lower = delay.lower().strip()
        total_seconds = 0

        # Match hours
        hours_match = re.search(r'(\d+)\s*(?:hour|hr|hours|hrs)', delay_lower)
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600

        # Match minutes
        minutes_match = re.search(r'(\d+)\s*(?:minute|min|minutes|mins)', delay_lower)
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60

        # Match seconds
        seconds_match = re.search(r'(\d+)\s*(?:second|sec|seconds|secs)', delay_lower)
        if seconds_match:
            total_seconds += int(seconds_match.group(1))

        if total_seconds == 0:
            return f"Error: Could not parse delay '{delay}'. Use format like '5 minutes', '1 hour', '30 seconds'"

        # Start background thread to send notification after delay
        def send_delayed():
            time.sleep(total_seconds)
            client.send_notification(summary, body)

        timer_thread = threading.Thread(target=send_delayed, daemon=True)
        timer_thread.start()

        # Format delay for confirmation message
        if total_seconds >= 3600:
            hours = total_seconds // 3600
            remaining = total_seconds % 3600
            minutes = remaining // 60
            if minutes > 0:
                delay_text = f"{hours} hour{'s' if hours > 1 else ''} and {minutes} minute{'s' if minutes > 1 else ''}"
            else:
                delay_text = f"{hours} hour{'s' if hours > 1 else ''}"
        elif total_seconds >= 60:
            minutes = total_seconds // 60
            remaining = total_seconds % 60
            if remaining > 0:
                delay_text = f"{minutes} minute{'s' if minutes > 1 else ''} and {remaining} second{'s' if remaining > 1 else ''}"
            else:
                delay_text = f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            delay_text = f"{total_seconds} second{'s' if total_seconds > 1 else ''}"

        return f"Scheduled notification in {delay_text}: {summary}"

    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def get_volume() -> str:
    """Get current system volume level and mute status.

    Returns:
        JSON string with volume level (0-100) and mute status.
    """
    try:
        from . import volume_control
        volume_info = volume_control.get_volume()
        return json.dumps(volume_info)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def set_volume(volume: int, relative: bool = False) -> str:
    """Set system volume level.

    Args:
        volume: Volume level (0-100 for absolute, -100 to 100 for relative).
        relative: If True, volume is a relative change (+/- from current).
                 If False, volume is an absolute level (0-100).

    Returns:
        Success or error message.
    """
    try:
        from . import volume_control
        message = volume_control.set_volume(volume, relative)
        return message
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def mute_volume(mute: bool = True) -> str:
    """Mute or unmute system volume.

    Args:
        mute: True to mute, False to unmute.

    Returns:
        Success or error message.
    """
    try:
        from . import volume_control
        message = volume_control.mute_volume(mute)
        return message
    except Exception as e:
        return _handle_error(e)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
