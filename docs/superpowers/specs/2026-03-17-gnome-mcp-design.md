# Gnome-MCP Design Spec

**Date:** 2026-03-17
**Status:** Approved
**Author:** sbuysse + Claude

## Problem

No MCP server exists for GNOME Wayland desktop automation. The closest equivalent (kwin-mcp) requires KDE. GNOME's strict Wayland security model blocks external processes from taking silent screenshots or injecting input. A GNOME Shell extension running inside the compositor can bypass these restrictions and expose capabilities via D-Bus.

## Solution

Two independently installable components:

1. **GNOME Shell Extension** (`desktop-automation@sbuysse.github.io`) — runs inside the compositor, exposes a D-Bus interface for screenshots, window management, and input injection
2. **Python MCP Server** (`gnome-desktop-mcp`) — translates MCP tool calls into D-Bus calls, distributed via PyPI

```
Claude Code  ──stdio/MCP──▶  gnome-desktop-mcp (Python)  ──D-Bus──▶  desktop-automation@sbuysse.github.io
                              (pip package)                            (GNOME Shell extension)
```

## Distribution

| Component | Channel |
|---|---|
| Extension | extensions.gnome.org + GitHub |
| MCP Server | PyPI (`gnome-desktop-mcp`) + GitHub |
| License | GPL-3.0 |

## Repository Structure

```
Gnome-MCP/
├── extension/
│   └── desktop-automation@sbuysse.github.io/
│       ├── metadata.json
│       ├── extension.js          # enable/disable, D-Bus export
│       ├── dbus.js               # D-Bus service implementation
│       ├── screenshot.js         # Shell.Screenshot wrappers
│       ├── windows.js            # Meta.Window management
│       ├── input.js              # Clutter.VirtualInputDevice
│       ├── indicator.js          # Top bar status indicator
│       └── stylesheet.css        # Indicator styling
├── mcp-server/
│   ├── pyproject.toml
│   └── src/
│       └── gnome_desktop_mcp/
│           ├── __init__.py
│           ├── server.py         # MCP server entry point
│           ├── dbus_client.py    # D-Bus proxy calls
│           ├── tools/
│           │   ├── screenshot.py
│           │   ├── windows.py
│           │   └── input.py
│           └── utils.py          # base64, temp file cleanup, key name mapping
├── tests/
│   ├── test_dbus_client.py
│   ├── test_tools.py
│   └── test_key_mapping.py
├── docs/
├── LICENSE
├── README.md
└── install.sh                    # Convenience: installs both
```

## D-Bus Interface Contract

**Interface:** `org.gnome.Shell.Extensions.DesktopAutomation`
**Object path:** `/org/gnome/Shell/Extensions/DesktopAutomation`
**Bus:** Session bus (exported on `org.gnome.Shell`)

All methods use the `MethodNameAsync(params, invocation)` pattern for async D-Bus responses.

### Screenshot Methods

| Method | In | Out | Notes |
|---|---|---|---|
| `Screenshot(includeCursor: b)` | bool | `s` (filepath) | Full screen to /tmp |
| `ScreenshotWindow(windowId: u, includeFrame: b, includeCursor: b)` | uint32, bool, bool | `s` (filepath) | Focuses window first |
| `ScreenshotArea(x: i, y: i, w: i, h: i, includeCursor: b)` | 4x int + bool | `s` (filepath) | Region capture |
| `PickColor(x: i, y: i)` | 2x int | `(ddd)` (r,g,b) | Pixel color at coordinates |

### Window Methods

| Method | In | Out | Notes |
|---|---|---|---|
| `ListWindows()` | -- | `s` (JSON array) | All windows with id, title, wmClass, rect, state |
| `GetWindow(windowId: u)` | uint32 | `s` (JSON) | Full properties for one window |
| `FocusWindow(windowId: u)` | uint32 | `b` | Activate + raise |
| `MoveResizeWindow(windowId: u, x: i, y: i, w: i, h: i)` | uint32 + 4x int | `b` | Unmaximizes first if needed |
| `MinimizeWindow(windowId: u)` | uint32 | `b` | |
| `UnminimizeWindow(windowId: u)` | uint32 | `b` | |
| `MaximizeWindow(windowId: u)` | uint32 | `b` | |
| `UnmaximizeWindow(windowId: u)` | uint32 | `b` | |
| `CloseWindow(windowId: u)` | uint32 | `b` | `delete()` with timestamp |

### Input Methods

| Method | In | Out | Notes |
|---|---|---|---|
| `KeyPress(keyval: u)` | uint32 | `b` | Single key press+release |
| `KeyCombo(combo: s)` | string | `b` | e.g. `"Control_L+Alt_L+t"` |
| `TypeText(text: s)` | string | `b` | Character by character via unichar |
| `MouseMove(x: i, y: i)` | 2x int | `b` | Absolute position |
| `MouseClick(x: i, y: i, button: u)` | 2x int + uint32 | `b` | 1=left, 2=middle, 3=right |
| `MouseDoubleClick(x: i, y: i, button: u)` | 2x int + uint32 | `b` | |
| `MouseScroll(x: i, y: i, dx: d, dy: d)` | 2x int + 2x double | `b` | Smooth scroll |

### Utility Methods

| Method | In | Out | Notes |
|---|---|---|---|
| `GetMonitors()` | -- | `s` (JSON array) | Index, geometry, scale, primary |
| `SetEnabled(enabled: b)` | bool | `b` | Toggle automation on/off |
| `GetEnabled()` | -- | `b` | Current state |
| `Ping()` | -- | `b` | Health check |

## Privacy & Visibility

### Top Bar Indicator

- Persistent status icon in the GNOME top bar when extension is enabled
- **Red dot** when an MCP client is actively connected (D-Bus calls in last 5s)
- **Grey** when idle (extension enabled but no active client)
- Click opens dropdown menu:
  - Connection status (connected/idle)
  - **Toggle: "Allow automation"** -- master kill switch
  - Last activity timestamp
  - "Disconnect" button (rejects all D-Bus calls until re-enabled)

### D-Bus Access Gating

- Every D-Bus method checks `_automationEnabled` flag before executing
- When disabled: all methods return `org.gnome.Shell.Extensions.DesktopAutomation.Error.Disabled`
- `Ping()`, `GetEnabled()`, and `SetEnabled()` always work regardless of the flag

### Activity Logging

- Extension tracks last N method calls (method name + timestamp only, no payload data)
- Visible in dropdown menu
- No screenshots or input data stored

### First-Connection Signal

- Indicator flashes briefly when first D-Bus call arrives after enabling

## MCP Server Tools

Default `format` is `"path"`. Set to `"base64"` for inline image data.

### Screenshot Tools

| Tool | Parameters | Returns |
|---|---|---|
| `screenshot` | `include_cursor?: bool, format?: "path"\|"base64"` | filepath or base64 PNG |
| `screenshot_window` | `window_id: int, include_frame?: bool, format?: ...` | filepath or base64 PNG |
| `screenshot_area` | `x, y, width, height: int, format?: ...` | filepath or base64 PNG |
| `pick_color` | `x, y: int` | `{r, g, b}` floats |

### Window Tools

| Tool | Parameters | Returns |
|---|---|---|
| `list_windows` | -- | JSON array of window objects |
| `get_window` | `window_id: int` | JSON window properties |
| `focus_window` | `window_id: int` | bool |
| `move_resize_window` | `window_id, x, y, width, height: int` | bool |
| `minimize_window` | `window_id: int` | bool |
| `unminimize_window` | `window_id: int` | bool |
| `maximize_window` | `window_id: int` | bool |
| `close_window` | `window_id: int` | bool |

### Input Tools

| Tool | Parameters | Returns |
|---|---|---|
| `key_press` | `key: str` (name like "Return", "a", "F5") | bool |
| `key_combo` | `keys: str` (e.g. "Ctrl+Alt+t") | bool |
| `type_text` | `text: str` | bool |
| `mouse_move` | `x, y: int` | bool |
| `mouse_click` | `x, y: int, button?: 1\|2\|3` | bool |
| `mouse_double_click` | `x, y: int, button?: 1\|2\|3` | bool |
| `mouse_scroll` | `x, y: int, dx, dy: float` | bool |

### Utility Tools

| Tool | Parameters | Returns |
|---|---|---|
| `get_monitors` | -- | JSON array of monitor info |
| `ping` | -- | bool |

### Ergonomic Differences from Raw D-Bus

- `key_press` accepts key **names** ("Return", "Ctrl") — MCP server translates to keyvals
- `key_combo` accepts friendly format "Ctrl+Alt+t" — translated to "Control_L+Alt_L+t"
- `format` defaults to `"path"` for lightweight responses
- All tools return structured errors with actionable messages

## Error Handling

### D-Bus Errors (Extension)

| Error Name | When |
|---|---|
| `...Error.Disabled` | Automation toggle is off |
| `...Error.WindowNotFound` | Invalid window_id |
| `...Error.ScreenshotFailed` | File I/O or compositor error |
| `...Error.InputFailed` | Virtual device creation fails |

### MCP Server Error Translation

| D-Bus condition | MCP error message |
|---|---|
| Connection refused | "GNOME Shell extension not installed or not enabled" |
| Timeout (5s) | "Extension not responding -- GNOME Shell may be busy" |
| Disabled error | "Automation disabled by user. Enable from top bar indicator." |
| Window not found | "Window ID {id} not found. Use list_windows to see available windows." |

### Edge Cases

- `screenshot_window` on minimized window: unminimize, screenshot, re-minimize
- `move_resize_window` on maximized window: unmaximize first, then move/resize
- `type_text` with Unicode: use `notify_key_unichar` per character
- Temp screenshot files: MCP server cleans up after base64 encoding; path mode caller is responsible
- Rapid screenshots: unique filenames via timestamp + counter

## Tech Stack

| Component | Technology |
|---|---|
| Extension | GJS ESM (GNOME 45+ style), targeting GNOME 45-49 |
| D-Bus binding (ext) | `Gio.DBusExportedObject.wrapJSObject` |
| Indicator | `St.Icon` + `PanelMenu.Button` |
| MCP server | Python 3.12+, `mcp` SDK (FastMCP), `dasbus` for D-Bus |
| Packaging | `pyproject.toml` with `[project.scripts]` entry point |
| Testing | pytest (MCP server), manual gdbus (extension) |

## Testing Strategy

### Extension

- Manual testing via `gdbus call` commands against the D-Bus interface
- Logs via `journalctl /usr/bin/gnome-shell -f`
- No automated tests (standard for GNOME extensions)

### MCP Server

- Unit tests with mocked D-Bus proxy (pytest)
- Integration tests requiring running extension
- Key name to keyval translation table tested exhaustively

## GNOME Review Compliance

- No subprocess spawning from extension
- Clean enable/disable lifecycle (all state created in enable, destroyed in disable)
- No bundled binaries
- D-Bus interface follows established patterns (Window Calls, Focused Window D-Bus)
- Privacy indicator follows GNOME HIG for status area items
