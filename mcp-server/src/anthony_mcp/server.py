"""MCP server for desktop automation (GNOME and KDE)."""

import json
import os
import re
import threading
import time

from mcp.server.fastmcp import FastMCP

from anthony_mcp.exceptions import (
    AutomationDisabledError,
    ExtensionNotFoundError,
    InputFailedError,
    ScreenshotFailedError,
    WindowNotFoundError,
)
from anthony_mcp.utils import cleanup_file, file_to_base64

mcp = FastMCP(
    "desktop-automation",
    instructions="Desktop automation: screenshots, window management, input injection",
)

_client = None


def _get_client():
    global _client
    if _client is None:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
        if "KDE" in desktop:
            from anthony_mcp.kde_client import KdeClient

            _client = KdeClient()
        else:
            from anthony_mcp.dbus_client import DbusClient

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
def screenshot_window(
    window_id: str, include_frame: bool = True, include_cursor: bool = False, format: str = "path"
) -> str:
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
def screenshot_area(
    x: int, y: int, width: int, height: int, include_cursor: bool = False, format: str = "path"
) -> str:
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
def get_window(window_id: str) -> str:
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
def focus_window(window_id: str) -> str:
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
def move_resize_window(window_id: str, x: int, y: int, width: int, height: int) -> str:
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
def minimize_window(window_id: str) -> str:
    """Minimize a window."""
    try:
        client = _get_client()
        client.minimize_window(window_id)
        return "Window minimized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def unminimize_window(window_id: str) -> str:
    """Unminimize (restore) a window."""
    try:
        client = _get_client()
        client.unminimize_window(window_id)
        return "Window unminimized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def maximize_window(window_id: str) -> str:
    """Maximize a window."""
    try:
        client = _get_client()
        client.maximize_window(window_id)
        return "Window maximized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def unmaximize_window(window_id: str) -> str:
    """Unmaximize a window."""
    try:
        client = _get_client()
        client.unmaximize_window(window_id)
        return "Window unmaximized"
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def close_window(window_id: str) -> str:
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


@mcp.tool()
def move_window_to_workspace(window_id: str, workspace_index: int) -> str:
    """Move a window to a different workspace by index (0-based)."""
    try:
        client = _get_client()
        client.move_window_to_workspace(window_id, workspace_index)
        return f"Moved window to workspace {workspace_index}"
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
        client.key_press(key)
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
        client.key_combo(keys)
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
def gnome_search(query: str) -> str:
    """Use desktop search to find and open apps, files, or settings.

    Opens the desktop search overlay (GNOME Activities / KDE KRunner),
    types the query, and presses Enter to activate the top result.

    Args:
        query: Just the app name, file name, or domain name. Search handles fuzzy matching.

    Examples:
        - Launch apps: "firefox", "text editor", "calculator"
        - Open files: "screenshot.png", "document.pdf"
        - Open settings: "wifi", "bluetooth"
        - Web navigation: "amazon.com", "github.com"
        - Calculator: "2+2", "15% of 200"
    """
    try:
        client = _get_client()

        client.key_combo("Super")
        time.sleep(0.3)

        client.type_text(query)
        time.sleep(0.2)

        client.key_press("Return")

        return f"Desktop search: '{query}'"
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
def move_window_to_monitor(window_id: str, monitor: str) -> str:
    """Move a window to a target monitor.

    Args:
        window_id: The window's stable ID.
        monitor: Target monitor — "1", "2" (1-based, primary=1), or "other".
    """
    try:
        client = _get_client()
        monitors = client.get_monitors()
        if len(monitors) < 2:
            return "Only one monitor connected"

        sorted_mons = sorted(monitors, key=lambda m: (not m.get("primary", False), m["index"]))

        window = client.get_window(window_id)
        current_idx = window.get("monitor", 0)

        if monitor == "other":
            dest = next((m for m in monitors if m["index"] != current_idx), None)
        else:
            user_idx = int(monitor) - 1
            if 0 <= user_idx < len(sorted_mons):
                dest = sorted_mons[user_idx]
            else:
                return f"Monitor {monitor} not found"

        if not dest:
            return f"Monitor {monitor} not found"

        win_w = window.get("width", 800)
        win_h = window.get("height", 600)
        dest_x = dest["x"] + (dest["width"] - win_w) // 2
        dest_y = dest["y"] + (dest["height"] - win_h) // 2

        client.move_resize_window(window_id, dest_x, dest_y, win_w, win_h)
        return f"Window moved to monitor {monitor}"
    except Exception as e:
        return _handle_error(e)


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
        hours_match = re.search(r"(\d+)\s*(?:hour|hr|hours|hrs)", delay_lower)
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600

        # Match minutes
        minutes_match = re.search(r"(\d+)\s*(?:minute|min|minutes|mins)", delay_lower)
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60

        # Match seconds
        seconds_match = re.search(r"(\d+)\s*(?:second|sec|seconds|secs)", delay_lower)
        if seconds_match:
            total_seconds += int(seconds_match.group(1))

        if total_seconds == 0:
            return (
                f"Error: Could not parse delay '{delay}'."
                " Use format like '5 minutes', '1 hour', '30 seconds'"
            )

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
            h_s = "s" if hours > 1 else ""
            m_s = "s" if minutes > 1 else ""
            if minutes > 0:
                delay_text = f"{hours} hour{h_s} and {minutes} minute{m_s}"
            else:
                delay_text = f"{hours} hour{h_s}"
        elif total_seconds >= 60:
            minutes = total_seconds // 60
            remaining = total_seconds % 60
            m_s = "s" if minutes > 1 else ""
            s_s = "s" if remaining > 1 else ""
            if remaining > 0:
                delay_text = f"{minutes} minute{m_s} and {remaining} second{s_s}"
            else:
                delay_text = f"{minutes} minute{m_s}"
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


@mcp.tool()
def media_control(action: str, player: str = "") -> str:
    """Control media playback (play, pause, skip, etc.) via MPRIS.

    Args:
        action: Media control action to perform.
                Valid actions: play, pause, play_pause, stop, next, previous
        player: Specific player to control (optional).
                Examples: 'spotify', 'rhythmbox', 'vlc'
                If empty, uses the first available player.

    Returns:
        Success or error message.
    """
    try:
        from . import media_control as mc

        message = mc.media_control(action, player)
        return message
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def get_media_status(player: str = "") -> str:
    """Get current media player status and track information.

    Args:
        player: Specific player to query (optional).
                If empty, uses the first available player.

    Returns:
        JSON string with player name, playback status, and track metadata.
    """
    try:
        from . import media_control as mc

        status = mc.get_media_status(player)
        return json.dumps(status)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def quick_settings(setting: str, enabled: bool) -> str:
    """Toggle desktop quick settings (WiFi, Bluetooth, Dark Mode, Night Light, Do Not Disturb).

    Args:
        setting: Which setting to toggle.
                Options: wifi, bluetooth, night_light, dark_style, do_not_disturb
        enabled: True to enable, False to disable

    Returns:
        Success or error message.
    """
    try:
        from . import quick_settings as qs

        message = qs.quick_settings(setting, enabled)
        return message
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def open_file(path: str, search_location: str = "") -> str:
    """Smart file opener - opens files by path or searches for them.

    Args:
        path: File path or filename to open.
              Full path: '/home/user/document.pdf', '~/Downloads/image.png'
              Filename: 'screenshot.png', 'report.pdf'
        search_location: Optional folder to search in (Pictures, Documents, Downloads, etc.)

    Returns:
        Success or error message.
    """
    try:
        from . import open_file as of

        message = of.open_file(path, search_location)
        return message
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def open_url(url: str) -> str:
    """Open a URL in the default web browser.

    Args:
        url: URL to open. Automatically adds https:// if needed.
             Examples: 'google.com', 'https://github.com', 'example.com/page'

    Returns:
        Success or error message.
    """
    try:
        from . import open_url as ou

        message = ou.open_url(url)
        return message
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def search_files(query: str, file_type: str = "files", limit: int = 10) -> str:
    """Search for files using GNOME file indexing (localsearch/Tracker).

    Args:
        query: Search query - filename, keywords, or content to search for.
        file_type: Type of files to search.
                   Options: files, folders, images, videos, documents,
                   audio, music_albums, music_artists, software
                   Default: files
        limit: Maximum number of results (1-50, default: 10)

    Returns:
        JSON string with search results containing file paths.
    """
    try:
        from . import search_files as sf

        result = sf.search_files(query, file_type, limit)
        return result
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def set_wallpaper(image_path: str) -> str:
    """Set the desktop wallpaper/background image.

    Sets wallpaper for both light and dark mode.

    Args:
        image_path: Path to image file.
                   Full path: '/home/user/Pictures/sunset.jpg'
                   Tilde path: '~/Pictures/nature.png'
                   Relative: 'Pictures/photo.jpg' (expands from home directory)
                   Supported formats: JPG, JPEG, PNG, SVG, BMP, GIF, WEBP, JXL

    Returns:
        Success message with wallpaper filename.
    """
    try:
        from . import wallpaper

        result = wallpaper.set_wallpaper(image_path)
        return result
    except Exception as e:
        return _handle_error(e)


# ── System control ──────────────────────────────────────────────────


@mcp.tool()
def get_battery_status() -> str:
    """Get battery percentage, state, and time remaining.

    Returns:
        Status string with battery level, charge state, and remaining time.
    """
    try:
        from . import system_control

        return system_control.get_battery_status()
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def set_brightness(target: str = "screen", level: str = "50%") -> str:
    """Set screen or keyboard backlight brightness.

    Args:
        target: "screen" for display brightness, "keyboard" for keyboard backlight.
        level: Brightness level. Examples: "50%", "up", "down", "max", "min".

    Returns:
        Success message with resulting brightness.
    """
    try:
        from . import system_control

        return system_control.set_brightness(target, level)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def get_power_profile() -> str:
    """Get the current power profile (performance, balanced, or power-saver).

    Returns:
        Status message with current profile name.
    """
    try:
        from . import system_control

        return system_control.get_power_profile()
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def set_power_profile(profile: str) -> str:
    """Set power profile.

    Args:
        profile: Power profile to set. Options: performance, balanced, power-saver.

    Returns:
        Success message.
    """
    try:
        from . import system_control

        return system_control.set_power_profile(profile)
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def lock_screen() -> str:
    """Lock the screen.

    Returns:
        Success message.
    """
    try:
        from . import system_control

        return system_control.lock_screen()
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
def power_action(action: str) -> str:
    """Execute a power action.

    Args:
        action: Power action to perform. Options: suspend, restart, shutdown, logout.

    Returns:
        Confirmation message.
    """
    try:
        from . import system_control

        return system_control.power_action(action)
    except Exception as e:
        return _handle_error(e)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
