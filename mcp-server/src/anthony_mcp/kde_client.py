"""KDE/KWin desktop automation client using D-Bus and KWin scripting."""

import json
import os
import subprocess
import tempfile
import threading
import time

from anthony_mcp.exceptions import (
    ExtensionNotFoundError,
    InputFailedError,
    ScreenshotFailedError,
    WindowNotFoundError,
)

# Friendly key name -> Linux evdev keycode (linux/input-event-codes.h)
_EVDEV_KEYMAP = {
    "Escape": 1,
    "Esc": 1,
    "1": 2,
    "2": 3,
    "3": 4,
    "4": 5,
    "5": 6,
    "6": 7,
    "7": 8,
    "8": 9,
    "9": 10,
    "0": 11,
    "Minus": 12,
    "-": 12,
    "Equal": 13,
    "=": 13,
    "BackSpace": 14,
    "Backspace": 14,
    "Tab": 15,
    "q": 16,
    "w": 17,
    "e": 18,
    "r": 19,
    "t": 20,
    "y": 21,
    "u": 22,
    "i": 23,
    "o": 24,
    "p": 25,
    "BracketLeft": 26,
    "[": 26,
    "BracketRight": 27,
    "]": 27,
    "Return": 28,
    "Enter": 28,
    "Control_L": 29,
    "Ctrl": 29,
    "Control": 29,
    "a": 30,
    "s": 31,
    "d": 32,
    "f": 33,
    "g": 34,
    "h": 35,
    "j": 36,
    "k": 37,
    "l": 38,
    "Semicolon": 39,
    ";": 39,
    "Apostrophe": 40,
    "'": 40,
    "Grave": 41,
    "`": 41,
    "Shift_L": 42,
    "Shift": 42,
    "BackSlash": 43,
    "\\": 43,
    "z": 44,
    "x": 45,
    "c": 46,
    "v": 47,
    "b": 48,
    "n": 49,
    "m": 50,
    "Comma": 51,
    ",": 51,
    "Period": 52,
    ".": 52,
    "Slash": 53,
    "/": 53,
    "Shift_R": 54,
    "Alt_L": 56,
    "Alt": 56,
    "space": 57,
    "Space": 57,
    " ": 57,
    "Caps_Lock": 58,
    "F1": 59,
    "F2": 60,
    "F3": 61,
    "F4": 62,
    "F5": 63,
    "F6": 64,
    "F7": 65,
    "F8": 66,
    "F9": 67,
    "F10": 68,
    "F11": 87,
    "F12": 88,
    "Num_Lock": 69,
    "Scroll_Lock": 70,
    "Home": 102,
    "Up": 103,
    "Page_Up": 104,
    "PageUp": 104,
    "Left": 105,
    "Right": 106,
    "End": 107,
    "Down": 108,
    "Page_Down": 109,
    "PageDown": 109,
    "Insert": 110,
    "Delete": 111,
    "Del": 111,
    "Super_L": 125,
    "Super": 125,
    "Win": 125,
    "Meta": 125,
    "Super_R": 126,
    "Menu": 127,
    "Print": 99,
    "PrintScreen": 99,
    "Pause": 119,
    "Break": 119,
}

# Add uppercase letters mapping to same codes as lowercase
for _ch in "abcdefghijklmnopqrstuvwxyz":
    _EVDEV_KEYMAP[_ch.upper()] = _EVDEV_KEYMAP[_ch]


def _friendly_to_evdev(key: str) -> int:
    if key in _EVDEV_KEYMAP:
        return _EVDEV_KEYMAP[key]
    lower = key.lower()
    if lower in _EVDEV_KEYMAP:
        return _EVDEV_KEYMAP[lower]
    if len(key) == 1 and key.isalpha():
        return _EVDEV_KEYMAP.get(key.lower(), 0)
    raise InputFailedError(f"Unknown key: {key}")


# ydotool mouse button mapping (X11 button -> ydotool hex)
_YDOTOOL_BUTTONS = {1: "0x00", 2: "0x02", 3: "0x01"}


class _KWinBridge:
    """D-Bus service that receives results from KWin scripts."""

    def __init__(self, bus):
        import dbus.service

        self._result = None
        self._event = threading.Event()
        bridge_ref = self

        class BridgeObj(dbus.service.Object):
            @dbus.service.method(
                "io.github.anthonymcp.KWinBridge",
                in_signature="s",
                out_signature="",
            )
            def ReceiveResult(self, data):
                bridge_ref._result = str(data)
                bridge_ref._event.set()

        self._obj = BridgeObj(bus, "/Bridge")

    def reset(self):
        self._result = None
        self._event.clear()

    def wait(self, timeout: float = 5.0) -> str:
        if not self._event.wait(timeout):
            raise ExtensionNotFoundError("KWin script timed out — no result received")
        return self._result


class KdeClient:
    """Desktop automation client for KDE Plasma using KWin scripting + D-Bus."""

    SCRIPT_TIMEOUT = 5

    def __init__(self):
        uid = os.getuid()
        runtime_dir = f"/run/user/{uid}"
        defaults = {
            "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_dir}/bus",
            "XDG_RUNTIME_DIR": runtime_dir,
            "WAYLAND_DISPLAY": "wayland-0",
            "YDOTOOL_SOCKET": "/tmp/.ydotool_socket",
        }
        for key, value in defaults.items():
            if key not in os.environ:
                os.environ[key] = value

        import dbus
        import dbus.service
        from dbus.mainloop.glib import DBusGMainLoop
        from gi.repository import GLib

        DBusGMainLoop(set_as_default=True)
        self._bus = dbus.SessionBus()
        self._bus_name = dbus.service.BusName("io.github.anthonymcp.KWinBridge", self._bus)
        self._bridge = _KWinBridge(self._bus)
        self._screenshot_dir = tempfile.mkdtemp(prefix="anthony-kde-screenshots-")
        self._script_lock = threading.Lock()

        self._loop = GLib.MainLoop()
        self._loop_thread = threading.Thread(target=self._loop.run, daemon=True)
        self._loop_thread.start()

    def _run_kwin_script(self, js_code: str) -> str:
        with self._script_lock:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".js", delete=False, prefix="kwin-"
            ) as f:
                f.write(js_code)
                script_path = f.name

            try:
                # Unload any stale script left from a previous crash
                subprocess.run(
                    [
                        "gdbus",
                        "call",
                        "--session",
                        "--dest",
                        "org.kde.KWin",
                        "--object-path",
                        "/Scripting",
                        "--method",
                        "org.kde.kwin.Scripting.unloadScript",
                        "anthony-mcp-temp",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )

                result = subprocess.run(
                    [
                        "gdbus",
                        "call",
                        "--session",
                        "--dest",
                        "org.kde.KWin",
                        "--object-path",
                        "/Scripting",
                        "--method",
                        "org.kde.kwin.Scripting.loadScript",
                        script_path,
                        "anthony-mcp-temp",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode != 0:
                    raise ExtensionNotFoundError(f"Failed to load KWin script: {result.stderr}")

                script_id = result.stdout.strip().strip("(),").split()[-1].rstrip(",")

                self._bridge.reset()

                subprocess.run(
                    [
                        "gdbus",
                        "call",
                        "--session",
                        "--dest",
                        "org.kde.KWin",
                        "--object-path",
                        f"/Scripting/Script{script_id}",
                        "--method",
                        "org.kde.kwin.Script.run",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                data = self._bridge.wait(timeout=self.SCRIPT_TIMEOUT)

                subprocess.run(
                    [
                        "gdbus",
                        "call",
                        "--session",
                        "--dest",
                        "org.kde.KWin",
                        "--object-path",
                        f"/Scripting/Script{script_id}",
                        "--method",
                        "org.kde.kwin.Script.stop",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                subprocess.run(
                    [
                        "gdbus",
                        "call",
                        "--session",
                        "--dest",
                        "org.kde.KWin",
                        "--object-path",
                        "/Scripting",
                        "--method",
                        "org.kde.kwin.Scripting.unloadScript",
                        "anthony-mcp-temp",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                return data
            finally:
                os.unlink(script_path)

    def _window_action(self, window_id: str, action_js: str) -> str:
        js = f'''
        var clients = workspace.stackingOrder;
        var found = false;
        for (var i = 0; i < clients.length; i++) {{
            if (String(clients[i].internalId) === "{window_id}") {{
                var client = clients[i];
                {action_js}
                found = true;
                break;
            }}
        }}
        callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                 "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                 found ? "OK" : "ERROR:WindowNotFound");
        '''
        data = self._run_kwin_script(js)
        if data == "ERROR:WindowNotFound":
            raise WindowNotFoundError(f"Window not found: {window_id}")
        return data

    # --- Utility ---

    def ping(self) -> bool:
        result = subprocess.run(
            [
                "gdbus",
                "introspect",
                "--session",
                "--dest",
                "org.kde.KWin",
                "--object-path",
                "/Scripting",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0

    def get_enabled(self) -> bool:
        return True

    def set_enabled(self, enabled: bool) -> bool:
        return True

    def get_monitors(self) -> list[dict]:
        js = """
        var screens = workspace.screens;
        var result = [];
        for (var i = 0; i < screens.length; i++) {
            var s = screens[i];
            var geo = s.geometry;
            result.push({
                index: i,
                name: s.name,
                x: geo.x, y: geo.y,
                width: geo.width, height: geo.height,
                scale: s.devicePixelRatio || 1.0,
                primary: (i === 0)
            });
        }
        callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                 "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                 JSON.stringify(result));
        """
        data = self._run_kwin_script(js)
        return json.loads(data)

    def cleanup_screenshots(self) -> int:
        count = 0
        if os.path.isdir(self._screenshot_dir):
            for f in os.listdir(self._screenshot_dir):
                os.unlink(os.path.join(self._screenshot_dir, f))
                count += 1
        return count

    # --- Notifications ---

    def send_notification(self, summary: str, body: str = "") -> bool:
        subprocess.run(
            ["notify-send", summary, body],
            check=True,
            capture_output=True,
            timeout=5,
        )
        return True

    # --- Screenshots ---

    def screenshot(self, include_cursor: bool = False) -> str:
        filepath = os.path.join(self._screenshot_dir, f"screenshot-{time.time_ns()}.png")
        args = ["spectacle", "-b", "-n", "-f", "-o", filepath]
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or not os.path.exists(filepath):
            raise ScreenshotFailedError(f"Screenshot failed: {result.stderr}")
        return filepath

    def screenshot_window(
        self, window_id: str, include_frame: bool = True, include_cursor: bool = False
    ) -> str:
        self.focus_window(window_id)
        time.sleep(0.3)
        filepath = os.path.join(self._screenshot_dir, f"window-{time.time_ns()}.png")
        args = ["spectacle", "-b", "-n", "-a", "-o", filepath]
        if not include_frame:
            args.append("--no-decoration")
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        if result.returncode != 0 or not os.path.exists(filepath):
            raise ScreenshotFailedError(f"Window screenshot failed: {result.stderr}")
        return filepath

    def screenshot_area(
        self, x: int, y: int, width: int, height: int, include_cursor: bool = False
    ) -> str:
        full_path = os.path.join(self._screenshot_dir, f"full-temp-{time.time_ns()}.png")
        subprocess.run(
            ["spectacle", "-b", "-n", "-f", "-o", full_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if not os.path.exists(full_path):
            raise ScreenshotFailedError("Full screenshot for area crop failed")
        filepath = os.path.join(self._screenshot_dir, f"area-{time.time_ns()}.png")
        try:
            crop = subprocess.run(
                [
                    "convert",
                    full_path,
                    "-crop",
                    f"{width}x{height}+{x}+{y}",
                    "+repage",
                    filepath,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            os.unlink(full_path)
            if crop.returncode != 0 or not os.path.exists(filepath):
                raise ScreenshotFailedError(f"Crop failed: {crop.stderr}")
        except FileNotFoundError as e:
            os.unlink(full_path)
            raise ScreenshotFailedError(
                "ImageMagick 'convert' not found — install with: sudo dnf install ImageMagick"
            ) from e
        return filepath

    def pick_color(self, x: int, y: int) -> tuple[float, float, float]:
        # TODO: use KWin ColorPicker D-Bus for accuracy
        return (0.0, 0.0, 0.0)

    # --- Windows ---

    def list_windows(self) -> list[dict]:
        js = """
        var clients = workspace.stackingOrder;
        var result = [];
        for (var i = 0; i < clients.length; i++) {
            var c = clients[i];
            if (!c.normalWindow) continue;
            var geo = c.frameGeometry;
            var desktops = c.desktops;
            var wsIndex = -1;
            if (desktops.length > 0) {
                wsIndex = desktops[0].x11DesktopNumber - 1;
            }
            result.push({
                id: String(c.internalId),
                title: c.caption,
                wmClass: c.resourceClass,
                x: geo.x, y: geo.y,
                width: geo.width, height: geo.height,
                minimized: c.minimized,
                maximized: (c.maximizeMode === 3),
                focused: (c === workspace.activeWindow),
                workspace: wsIndex,
                pid: c.pid
            });
        }
        callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                 "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                 JSON.stringify(result));
        """
        data = self._run_kwin_script(js)
        return json.loads(data)

    def get_window(self, window_id: str) -> dict:
        js = f'''
        var clients = workspace.stackingOrder;
        var found = null;
        for (var i = 0; i < clients.length; i++) {{
            if (String(clients[i].internalId) === "{window_id}") {{
                found = clients[i];
                break;
            }}
        }}
        if (!found) {{
            callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                     "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                     "ERROR:WindowNotFound");
        }} else {{
            var geo = found.frameGeometry;
            var desktops = found.desktops;
            var wsIndex = -1;
            if (desktops.length > 0) wsIndex = desktops[0].x11DesktopNumber - 1;
            var result = {{
                id: String(found.internalId),
                title: found.caption,
                wmClass: found.resourceClass,
                x: geo.x, y: geo.y,
                width: geo.width, height: geo.height,
                minimized: found.minimized,
                maximized: (found.maximizeMode === 3),
                focused: (found === workspace.activeWindow),
                workspace: wsIndex,
                pid: found.pid
            }};
            callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                     "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                     JSON.stringify(result));
        }}
        '''
        data = self._run_kwin_script(js)
        if data == "ERROR:WindowNotFound":
            raise WindowNotFoundError(f"Window not found: {window_id}")
        return json.loads(data)

    def focus_window(self, window_id: str) -> bool:
        self._window_action(window_id, "workspace.activeWindow = client;")
        return True

    def close_window(self, window_id: str) -> bool:
        self._window_action(window_id, "client.closeWindow();")
        return True

    def minimize_window(self, window_id: str) -> bool:
        self._window_action(window_id, "client.minimized = true;")
        return True

    def unminimize_window(self, window_id: str) -> bool:
        self._window_action(window_id, "client.minimized = false;")
        return True

    def maximize_window(self, window_id: str) -> bool:
        self._window_action(window_id, "client.setMaximize(true, true);")
        return True

    def unmaximize_window(self, window_id: str) -> bool:
        self._window_action(window_id, "client.setMaximize(false, false);")
        return True

    def move_resize_window(self, window_id: str, x: int, y: int, width: int, height: int) -> bool:
        action = f"""
                client.setMaximize(false, false);
                client.frameGeometry = Qt.rect({x}, {y}, {width}, {height});
        """
        self._window_action(window_id, action)
        return True

    # --- Workspaces ---

    def list_workspaces(self) -> list[dict]:
        js = """
        var desktops = workspace.desktops;
        var current = workspace.currentDesktop;
        var result = [];
        for (var i = 0; i < desktops.length; i++) {
            var d = desktops[i];
            result.push({
                index: d.x11DesktopNumber - 1,
                name: d.name,
                active: (d === current)
            });
        }
        callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                 "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                 JSON.stringify(result));
        """
        data = self._run_kwin_script(js)
        return json.loads(data)

    def activate_workspace(self, index: int) -> bool:
        js = f"""
        var desktops = workspace.desktops;
        var target = null;
        for (var i = 0; i < desktops.length; i++) {{
            if (desktops[i].x11DesktopNumber - 1 === {index}) {{
                target = desktops[i];
                break;
            }}
        }}
        if (target) {{
            workspace.currentDesktop = target;
            callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                     "io.github.anthonymcp.KWinBridge", "ReceiveResult", "OK");
        }} else {{
            callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                     "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                     "ERROR:InvalidWorkspace");
        }}
        """
        data = self._run_kwin_script(js)
        if data.startswith("ERROR:"):
            raise ValueError(f"Invalid workspace index: {index}")
        return True

    def move_window_to_workspace(self, window_id: str, workspace_index: int) -> bool:
        js = f'''
        var clients = workspace.stackingOrder;
        var desktops = workspace.desktops;
        var targetDesktop = null;
        for (var i = 0; i < desktops.length; i++) {{
            if (desktops[i].x11DesktopNumber - 1 === {workspace_index}) {{
                targetDesktop = desktops[i];
                break;
            }}
        }}
        if (!targetDesktop) {{
            callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                     "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                     "ERROR:InvalidWorkspace");
        }} else {{
            var found = false;
            for (var i = 0; i < clients.length; i++) {{
                if (String(clients[i].internalId) === "{window_id}") {{
                    clients[i].desktops = [targetDesktop];
                    found = true;
                    break;
                }}
            }}
            callDBus("io.github.anthonymcp.KWinBridge", "/Bridge",
                     "io.github.anthonymcp.KWinBridge", "ReceiveResult",
                     found ? "OK" : "ERROR:WindowNotFound");
        }}
        '''
        data = self._run_kwin_script(js)
        if data == "ERROR:WindowNotFound":
            raise WindowNotFoundError(f"Window not found: {window_id}")
        if data == "ERROR:InvalidWorkspace":
            raise ValueError(f"Invalid workspace index: {workspace_index}")
        return True

    # --- Input (ydotool) ---

    def key_press(self, key: str) -> bool:
        keycode = _friendly_to_evdev(key)
        result = subprocess.run(
            ["ydotool", "key", f"{keycode}:1", f"{keycode}:0"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise InputFailedError(f"key_press failed: {result.stderr}")
        return True

    def key_combo(self, combo: str) -> bool:
        parts = combo.split("+")
        codes = [_friendly_to_evdev(p.strip()) for p in parts]
        key_args = [f"{c}:1" for c in codes] + [f"{c}:0" for c in reversed(codes)]
        result = subprocess.run(
            ["ydotool", "key"] + key_args,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise InputFailedError(f"key_combo failed: {result.stderr}")
        return True

    def type_text(self, text: str) -> bool:
        result = subprocess.run(
            ["ydotool", "type", "--", text],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise InputFailedError(f"type_text failed: {result.stderr}")
        return True

    def mouse_move(self, x: int, y: int) -> bool:
        result = subprocess.run(
            ["ydotool", "mousemove", "--absolute", "-x", str(x), "-y", str(y)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise InputFailedError(f"mouse_move failed: {result.stderr}")
        return True

    def mouse_click(self, x: int, y: int, button: int = 1) -> bool:
        self.mouse_move(x, y)
        btn = _YDOTOOL_BUTTONS.get(button, "0x00")
        result = subprocess.run(
            ["ydotool", "click", btn],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            raise InputFailedError(f"mouse_click failed: {result.stderr}")
        return True

    def mouse_double_click(self, x: int, y: int, button: int = 1) -> bool:
        self.mouse_move(x, y)
        btn = _YDOTOOL_BUTTONS.get(button, "0x00")
        subprocess.run(
            ["ydotool", "click", btn],
            capture_output=True,
            text=True,
            timeout=5,
        )
        time.sleep(0.05)
        subprocess.run(
            ["ydotool", "click", btn],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return True

    def mouse_down(self, x: int, y: int, button: int = 1) -> bool:
        self.mouse_move(x, y)
        keycode = {1: 272, 2: 274, 3: 273}.get(button, 272)
        subprocess.run(
            ["ydotool", "key", f"{keycode}:1"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return True

    def mouse_up(self, x: int, y: int, button: int = 1) -> bool:
        self.mouse_move(x, y)
        keycode = {1: 272, 2: 274, 3: 273}.get(button, 272)
        subprocess.run(
            ["ydotool", "key", f"{keycode}:0"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return True

    def mouse_drag(self, x1: int, y1: int, x2: int, y2: int, button: int = 1) -> bool:
        self.mouse_down(x1, y1, button)
        time.sleep(0.1)
        self.mouse_move(x2, y2)
        time.sleep(0.1)
        self.mouse_up(x2, y2, button)
        return True

    def mouse_scroll(self, x: int, y: int, dx: float, dy: float) -> bool:
        self.mouse_move(x, y)
        # Simulate scroll via ydotool key events (wheel up=REL_WHEEL)
        # ydotool mousemove doesn't support scroll directly in all versions
        # Use key-based approach: Up=KEY_SCROLLUP, Down=KEY_SCROLLDOWN
        if dy != 0:
            steps = abs(int(dy))
            direction = "4" if dy > 0 else "5"  # 4=scroll down, 5=scroll up
            for _ in range(max(1, steps)):
                subprocess.run(
                    ["ydotool", "click", f"0x0{direction}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
        return True
