#!/bin/bash
set -euo pipefail

EXTENSION_UUID="desktop-automation@anthonymcp.github.io"
EXTENSION_DIR="$HOME/.local/share/gnome-shell/extensions/$EXTENSION_UUID"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing Desktop Automation Extension ==="

# Ensure extensions directory exists
mkdir -p "$(dirname "$EXTENSION_DIR")"

# Symlink extension
if [ -L "$EXTENSION_DIR" ]; then
    rm "$EXTENSION_DIR"
elif [ -d "$EXTENSION_DIR" ]; then
    echo "Warning: $EXTENSION_DIR exists and is not a symlink. Remove it first."
    exit 1
fi

ln -s "$SCRIPT_DIR/extension/$EXTENSION_UUID" "$EXTENSION_DIR"
echo "Extension symlinked to $EXTENSION_DIR"

# Compile GSettings schemas
echo "Compiling GSettings schemas..."
glib-compile-schemas "$SCRIPT_DIR/extension/$EXTENSION_UUID/schemas/"

# Install MCP server
echo ""
echo "=== Installing MCP Server ==="
pip install -e "$SCRIPT_DIR/mcp-server"

echo ""
echo "=== Done ==="
echo "1. Restart GNOME Shell (log out/in on Wayland)"
echo "2. Enable the extension: gnome-extensions enable $EXTENSION_UUID"
echo "3. Add to Claude Code config:"
echo '   "desktop-automation": {'
echo '     "command": "anthony-mcp"'
echo '   }'
