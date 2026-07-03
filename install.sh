#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect desktop environment (works from graphical session and SSH)
DESKTOP="${XDG_CURRENT_DESKTOP:-}"
DESKTOP_UPPER="${DESKTOP^^}"

if [[ "$DESKTOP_UPPER" == *"KDE"* ]]; then
    DE="kde"
elif [[ "$DESKTOP_UPPER" == *"GNOME"* ]]; then
    DE="gnome"
elif pgrep -x plasmashell &>/dev/null; then
    DE="kde"
elif pgrep -x gnome-shell &>/dev/null; then
    DE="gnome"
else
    echo "Warning: Could not detect desktop environment, assuming GNOME"
    DE="gnome"
fi

echo "=== Installing Desktop Automation (detected: $DE) ==="

# ── Ensure pip is available ──────────────────────────────────────────
if ! python3 -m pip --version &>/dev/null; then
    echo "pip not found, bootstrapping..."
    python3 -m ensurepip --user
fi

# ── GNOME: install extension ─────────────────────────────────────────
if [ "$DE" = "gnome" ]; then
    EXTENSION_UUID="desktop-automation@anthonymcp.github.io"
    EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"

    echo ""
    echo "=== Installing GNOME Shell Extension ==="

    mkdir -p "$(dirname "$EXTENSION_DIR")"

    if [ -L "$EXTENSION_DIR" ]; then
        rm "$EXTENSION_DIR"
    elif [ -d "$EXTENSION_DIR" ]; then
        echo "Warning: $EXTENSION_DIR exists and is not a symlink. Remove it first."
        exit 1
    fi

    ln -s "$SCRIPT_DIR/extension/$EXTENSION_UUID" "$EXTENSION_DIR"
    echo "Extension symlinked to $EXTENSION_DIR"

    echo "Compiling GSettings schemas..."
    glib-compile-schemas "$SCRIPT_DIR/extension/$EXTENSION_UUID/schemas/"
fi

# ── KDE: install system dependencies ─────────────────────────────────
if [ "$DE" = "kde" ]; then
    echo ""
    echo "=== Installing KDE Dependencies ==="

    KDE_PACKAGES=()

    if ! command -v ydotool &>/dev/null; then
        KDE_PACKAGES+=("ydotool")
    fi

    if ! command -v convert &>/dev/null; then
        KDE_PACKAGES+=("ImageMagick")
    fi

    if [ ${#KDE_PACKAGES[@]} -gt 0 ]; then
        echo "Installing: ${KDE_PACKAGES[*]}"
        sudo dnf install -y "${KDE_PACKAGES[@]}"
    else
        echo "All KDE dependencies already installed"
    fi

    # Configure system ydotool service with user-accessible socket.
    # ydotoold needs /dev/uinput (root-only), so it runs as root via the
    # system service.  We override socket ownership so the current user
    # can connect without opening /dev/uinput to unprivileged processes.
    YDOTOOL_OVERRIDE="/etc/systemd/system/ydotool.service.d/socket-access.conf"
    CURRENT_GID="$(id -g)"
    if [ ! -f "$YDOTOOL_OVERRIDE" ]; then
        echo "Creating ydotool socket-access override..."
        sudo mkdir -p "$(dirname "$YDOTOOL_OVERRIDE")"
        sudo tee "$YDOTOOL_OVERRIDE" >/dev/null <<EOF
[Service]
ExecStart=
ExecStart=/usr/bin/ydotoold --socket-path=/tmp/.ydotool_socket --socket-perm=0660 --socket-own=0:${CURRENT_GID}
EOF
        sudo systemctl daemon-reload
    fi

    # Remove leftover user service if present (from earlier installs)
    YDOTOOL_USER_SERVICE="$HOME/.config/systemd/user/ydotoold.service"
    if [ -f "$YDOTOOL_USER_SERVICE" ]; then
        echo "Removing old ydotoold user service..."
        systemctl --user disable --now ydotoold 2>/dev/null || true
        rm -f "$YDOTOOL_USER_SERVICE"
        systemctl --user daemon-reload
    fi

    # Enable the system service
    if ! systemctl is-active --quiet ydotool 2>/dev/null; then
        echo "Enabling ydotool system service..."
        sudo systemctl enable --now ydotool
    fi
fi

# ── Install MCP server ───────────────────────────────────────────────
echo ""
echo "=== Installing MCP Server ==="
python3 -m pip install -e "$SCRIPT_DIR/mcp-server"

# ── Done ─────────────────────────────────────────────────────────────
echo ""
echo "=== Done ==="

if [ "$DE" = "gnome" ]; then
    EXTENSION_UUID="desktop-automation@anthonymcp.github.io"
    echo "1. Restart GNOME Shell (log out/in on Wayland)"
    echo "2. Enable the extension: gnome-extensions enable $EXTENSION_UUID"
    echo "3. Add to Claude Code config:"
    echo '   "desktop-automation": {'
    echo '     "command": "anthony-mcp"'
    echo '   }'
else
    echo "1. Add to Claude Code config:"
    echo '   "desktop-automation": {'
    echo '     "command": "anthony-mcp"'
    echo '   }'
    echo ""
    echo "No shell restart needed on KDE — KWin D-Bus is always available."
fi
