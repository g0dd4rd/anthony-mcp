# ANTHONY-MCP.md — Project Map for AI Agents

> **Audience:** LLMs and AI coding agents.
> Read this file first to understand the codebase before making changes.
> It describes the project structure, data flow, design patterns, and key conventions.

## What This Project Is

Anthony-MCP is a GNOME desktop automation toolkit with two components: a GNOME Shell extension (JavaScript) that provides low-level desktop control, and an MCP server (Python) that exposes those capabilities as tools via the Model Context Protocol. Together, they let AI agents and voice assistants control the GNOME desktop — manage windows, inject keyboard/mouse input, take screenshots, control audio, change system settings, and more.

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│              MCP Client                      │
│  (anthony orchestrator, Claude Code, etc.)   │
└───────────────────┬──────────────────────────┘
                    │ MCP protocol (stdio)
                    ▼
┌──────────────────────────────────────────────┐
│           MCP Server (Python)                │
│         mcp-server/src/anthony_mcp/          │
│                                              │
│  server.py ─── 40+ @mcp.tool() functions     │
│       │                                      │
│       ├── dbus_client.py (D-Bus proxy)       │
│       ├── volume_control.py (pactl)          │
│       ├── media_control.py (MPRIS D-Bus)     │
│       ├── quick_settings.py (gsettings/dbus) │
│       ├── system_control.py (upower/systemctl)│
│       ├── open_file.py (xdg-open)            │
│       ├── open_url.py (xdg-open)             │
│       ├── search_files.py (localsearch)      │
│       ├── wallpaper.py (gsettings)           │
│       └── utils.py (key mapping, base64)     │
└───────────────────┬──────────────────────────┘
                    │ D-Bus IPC (session bus)
                    ▼
┌──────────────────────────────────────────────┐
│       GNOME Shell Extension (JavaScript)     │
│  extension/desktop-automation@anthonymcp.*/   │
│                                              │
│  extension.js ─── lifecycle (enable/disable) │
│       │                                      │
│       ├── dbus.js (D-Bus interface + service)│
│       ├── windows.js (window management)     │
│       ├── input.js (keyboard/mouse via Clutter)│
│       ├── screenshot.js (Shell.Screenshot)   │
│       ├── volume.js (Gvc mixer control)      │
│       ├── notifications.js (notify-send)     │
│       ├── indicator.js (panel status icon)   │
│       └── consent.js (first-run dialog)      │
└──────────────────────────────────────────────┘
```

## Data Flow

1. **MCP client** sends a tool call (e.g., `focus_window`) over stdio
2. **server.py** receives it via FastMCP, validates args, calls the appropriate handler
3. **Two paths depending on tool type:**
   - **Extension tools** (windows, input, screenshots): `server.py` → `dbus_client.py` → D-Bus → GNOME Shell extension JS
   - **System tools** (volume, media, settings, files): `server.py` → Python module using subprocess/dbus directly (pactl, gsettings, MPRIS, xdg-open, localsearch, etc.)
4. **Result** flows back through the same chain as a string response

## Module Map

### MCP Server — `mcp-server/src/anthony_mcp/`

| File | Purpose |
|---|---|
| `server.py` | FastMCP server entry point. Defines all 40+ `@mcp.tool()` functions. Routes to dbus_client or feature modules. Entry point: `anthony-mcp` CLI command |
| `dbus_client.py` | D-Bus proxy to the GNOME Shell extension. `DbusClient` class wraps all extension methods. Custom exceptions: `AutomationDisabledError`, `ExtensionNotFoundError`, `WindowNotFoundError`, `ScreenshotFailedError`, `InputFailedError` |
| `utils.py` | Key name translation (`friendly_to_keyval`, `translate_combo`), base64 encoding, temp file cleanup. Key mapping follows GDK conventions with alias table for common names |
| `volume_control.py` | Volume get/set/mute via `pactl` (PipeWire-compatible) |
| `media_control.py` | Media playback control (play/pause/next/previous/stop) via MPRIS D-Bus interface. Auto-discovers running players |
| `quick_settings.py` | Toggles for WiFi (NetworkManager D-Bus), Bluetooth (bluez D-Bus), Night Light, Dark Mode, Do Not Disturb (all via gsettings) |
| `system_control.py` | Battery status (upower), brightness (brightnessctl), power profile (power-profiles-daemon D-Bus), lock screen (loginctl), power actions (systemctl) |
| `open_file.py` | Smart file opener — resolves paths or searches via localsearch, then opens with xdg-open |
| `open_url.py` | URL opener via xdg-open with auto https:// prefix |
| `search_files.py` | File search using GNOME localsearch/Tracker indexing. Supports type filters (images, documents, etc.) and extension aliases |
| `wallpaper.py` | Wallpaper setter via gsettings. Supports file paths, color names, and wallpaper name search |
| `wallpaper_index.py` | Indexes system wallpapers by color/name for search |

### GNOME Shell Extension — `extension/desktop-automation@anthonymcp.github.io/`

| File | Purpose |
|---|---|
| `extension.js` | Extension lifecycle (enable/disable). Exports D-Bus service, creates panel indicator, shows first-run consent dialog |
| `dbus.js` | D-Bus interface XML definition + `DbusService` class implementing all methods. Central routing — every D-Bus call checks `_checkEnabled()` gate, logs activity, then dispatches to the appropriate module |
| `windows.js` | Window management: `findWindow` (by stable sequence ID), `listWindows`, `getWindow`, `listWorkspaces`, `activateWorkspace`. Uses Meta API |
| `input.js` | Input injection via Clutter virtual devices. `keyPress`, `keyCombo`, `typeText` (keyboard), `mouseMove`, `mouseClick`, `mouseDoubleClick`, `mouseDown`, `mouseUp`, `mouseDrag`, `mouseScroll` (pointer) |
| `screenshot.js` | Screenshots via `Shell.Screenshot`: full screen, window, area, color picker. Saves to `~/Pictures/Screenshots/`. `cleanupScreenshots` moves files to trash |
| `volume.js` | Volume control via Gvc (GNOME Volume Control) native API. Get/set volume, mute/unmute |
| `notifications.js` | Desktop notifications via `notify-send` subprocess |
| `indicator.js` | Panel status icon with enable/disable toggle, activity log (last 5 calls), idle/active/flash states |
| `consent.js` | First-run modal dialog warning about automation capabilities |
| `metadata.json` | Extension metadata (UUID, GNOME Shell version compatibility) |
| `stylesheet.css` | Indicator icon styling (idle, active, flash states) |
| `schemas/*.xml` | GSettings schema for `consent-acknowledged` boolean |

### Tests — `tests/`

| File | Purpose |
|---|---|
| `conftest.py` | Pytest fixtures |
| `test_dbus_client.py` | Tests for D-Bus client |
| `test_key_mapping.py` | Tests for key name translation (utils.py) |

## Key Design Patterns

### Two-Layer Architecture
The extension handles only what requires GNOME Shell internals (windows, input, screenshots, volume via Gvc). Everything else (media via MPRIS, settings via gsettings, files via localsearch, power via systemctl) is handled directly in Python, avoiding unnecessary D-Bus round-trips.

### D-Bus Interface
The extension exposes a single D-Bus interface (`io.github.anthonymcp.DesktopAutomation`) on the session bus at `/io/github/anthonymcp/DesktopAutomation`. All methods are async (`*Async`) and use GLib.Variant for typed returns. The interface XML in `dbus.js` is the contract.

### Consent Gate
Every D-Bus method (except Ping, GetEnabled, SetEnabled) checks `_checkEnabled()` before executing. The user must explicitly enable automation via the panel indicator toggle. First-run shows a consent dialog.

### Key Translation
Key names go through a three-step resolution: explicit alias map → single-letter lowercase → GDK validation with case fallbacks. This handles "Ctrl" → "Control_L", "Enter" → "Return", "a" stays lowercase (to avoid implicit Shift), etc.

### Error Typing
D-Bus errors are translated to typed Python exceptions (`AutomationDisabledError`, `WindowNotFoundError`, etc.) in `dbus_client.py`, allowing callers to handle specific failure modes.

## MCP Tools Reference (40+ tools)

**Screenshots:** `screenshot`, `screenshot_window`, `screenshot_area`, `pick_color`, `cleanup_screenshots`
**Windows:** `list_windows`, `get_window`, `focus_window`, `move_resize_window`, `minimize_window`, `unminimize_window`, `maximize_window`, `unmaximize_window`, `close_window`
**Workspaces:** `list_workspaces`, `activate_workspace`
**Input:** `key_press`, `key_combo`, `type_text`, `gnome_search`, `mouse_move`, `mouse_click`, `mouse_double_click`, `mouse_down`, `mouse_up`, `mouse_drag`, `mouse_scroll`
**Audio:** `get_volume`, `set_volume`, `mute_volume`, `media_control`, `get_media_status`
**Settings:** `quick_settings` (WiFi, Bluetooth, Night Light, Dark Mode, DND)
**Files:** `open_file`, `open_url`, `search_files`, `set_wallpaper`
**System:** `get_battery_status`, `set_brightness`, `get_power_profile`, `set_power_profile`, `lock_screen`, `power_action`
**Utility:** `ping`, `get_enabled`, `set_enabled`, `get_monitors`, `send_notification`

## Installation

```bash
./install.sh
# 1. Symlinks extension to ~/.local/share/gnome-shell/extensions/
# 2. Compiles GSettings schemas
# 3. pip install -e mcp-server/
# Then: restart GNOME Shell, enable extension, run anthony-mcp
```

## Companion Repo

**anthony** — Voice-driven desktop orchestrator that uses anthony-mcp as its backend. Adds voice I/O (Whisper + Piper), LLM-based intent parsing, RAG tool retrieval, and pattern-matching shortcuts.
