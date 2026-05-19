# Anthony MCP

Desktop automation for GNOME Wayland via MCP. Take screenshots, manage windows, and inject keyboard/mouse input from AI assistants like Claude Code.

```
Anthony  ──MCP──>  anthony-mcp (Python)  ──D-Bus──>  GNOME Shell Extension
```

## Credits

This project is a fork of [gnome-desktop-mcp](https://github.com/sbuysse/gnome-desktop-mcp) by sbuysse, which was inspired by [gnome-mcp-server](https://github.com/bilelmoussaoui/gnome-mcp-server) by Bilal Elmoussaoui.

## Why

GNOME Wayland blocks external processes from taking screenshots or injecting input. This extension runs **inside** the compositor, bypassing those restrictions, and exposes a D-Bus API. The MCP server bridges that API to any MCP-compatible client.

## Features

- **30+ MCP tools**: screenshots, window management, input injection, workspace control, volume, media, notifications, file/URL opening, search
- **Privacy indicator**: top bar icon shows connection status (red = active, grey = idle)
- **Consent dialog**: first-use confirmation before enabling automation
- **Access gating**: master kill switch to disable all automation instantly

## Requirements

- GNOME Shell 45-50 (Wayland)
- Python 3.12+

## Installation

### Quick install (development)

```bash
git clone https://github.com/g0dd4rd/anthony-mcp.git
cd anthony-mcp
./install.sh
```

Then log out and back in (required for Wayland), and enable:

```bash
gnome-extensions enable desktop-automation@anthonymcp.github.io
```

### MCP server only

```bash
pip install -e mcp-server
```

## Claude Code Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "desktop-automation": {
      "command": "anthony-mcp"
    }
  }
}
```

## Tools

### Screenshots

| Tool | Description |
|---|---|
| `screenshot` | Full screen capture |
| `screenshot_window` | Capture a specific window |
| `screenshot_area` | Capture a rectangular region |
| `pick_color` | Get pixel color at coordinates |
| `cleanup_screenshots` | Remove temp screenshot files |

### Windows

| Tool | Description |
|---|---|
| `list_windows` | List all open windows |
| `get_window` | Get detailed window properties |
| `focus_window` | Focus and raise a window |
| `move_resize_window` | Move and resize a window |
| `minimize_window` / `unminimize_window` | Minimize/restore |
| `maximize_window` / `unmaximize_window` | Maximize/restore |
| `close_window` | Close a window |
| `list_workspaces` | List all workspaces |
| `activate_workspace` | Switch workspace |

### Input

| Tool | Description |
|---|---|
| `key_press` | Press a single key ("Return", "F5", "a") |
| `key_combo` | Key combination ("Ctrl+Alt+t") |
| `type_text` | Type text character by character |
| `gnome_search` | Open GNOME search and activate top result |
| `mouse_move` | Move mouse to coordinates |
| `mouse_click` | Click at coordinates |
| `mouse_double_click` | Double-click |
| `mouse_down` / `mouse_up` | Press/release mouse button |
| `mouse_drag` | Drag from point A to point B |
| `mouse_scroll` | Scroll at coordinates |

### Audio & Media

| Tool | Description |
|---|---|
| `get_volume` / `set_volume` | Get/set system volume |
| `mute_volume` | Mute/unmute |
| `media_control` | Play, pause, next, previous, stop |
| `get_media_status` | Current track and player status |

### Files & Apps

| Tool | Description |
|---|---|
| `open_file` | Open files by path or search for them |
| `open_url` | Open URL in default browser |
| `search_files` | Search files via GNOME Tracker |
| `set_wallpaper` | Set desktop wallpaper |
| `quick_settings` | Toggle WiFi, Bluetooth, Dark Mode, etc. |

### Utility

| Tool | Description |
|---|---|
| `ping` | Check extension is alive |
| `get_enabled` / `set_enabled` | Check/toggle automation |
| `get_monitors` | List monitors with geometry |
| `send_notification` | Send desktop notification (immediate or delayed) |

## Privacy

- **Top bar indicator** shows when automation is active
- **Toggle switch** to disable all automation instantly
- **Activity log** tracks last 20 method calls (name + timestamp only, no data)
- **D-Bus access gating**: all methods blocked when disabled

## Architecture

The GNOME Shell extension (`desktop-automation@anthonymcp.github.io`) runs inside the Wayland compositor. It exports `io.github.anthonymcp.DesktopAutomation` on the session D-Bus with privileged access to:

- `Shell.Screenshot` — silent screenshots (no permission dialog)
- `Meta.Window` — window management
- `Clutter.VirtualInputDevice` — keyboard/mouse injection

The Python MCP server (`anthony-mcp`) translates MCP tool calls into D-Bus method calls via `dasbus`.

## Development

```bash
# Install in development mode
pip install -e mcp-server[dev]

# Run tests
python -m pytest tests/ -v

# Watch extension logs
journalctl /usr/bin/gnome-shell -f

# Test D-Bus directly
gdbus call --session --dest org.gnome.Shell \
  --object-path /io/github/anthonymcp/DesktopAutomation \
  --method io.github.anthonymcp.DesktopAutomation.Ping
```

## License

[GPL-3.0](LICENSE)
