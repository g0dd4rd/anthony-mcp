"""Key name mapping, base64 encoding, temp file cleanup.

Key translation follows dogtail's approach: explicit alias map for common
names, then GDK validation with case fallbacks so we don't need to enumerate
every possible key.
"""

import base64
import os
from pathlib import Path

import gi
gi.require_version('Gdk', '4.0')
from gi.repository import Gdk

# Friendly name -> Clutter/GDK key name.
# Modifiers and keys whose GDK name differs from the friendly name.
# Everything else is resolved via GDK validation in friendly_to_clutter_name().
_KEY_NAME_MAP = {
    # Modifiers
    "Ctrl": "Control_L",
    "ctrl": "Control_L",
    "Control": "Control_L",
    "control": "Control_L",
    "Shift": "Shift_L",
    "shift": "Shift_L",
    "Alt": "Alt_L",
    "alt": "Alt_L",
    "Super": "Super_L",
    "super": "Super_L",
    "Win": "Super_L",
    "win": "Super_L",
    "Meta": "Super_L",
    "meta": "Super_L",
    # Keys whose GDK name doesn't match the friendly name
    "Enter": "Return",
    "enter": "Return",
    "Esc": "Escape",
    "esc": "Escape",
    "Backspace": "BackSpace",
    "backspace": "BackSpace",
    "Del": "Delete",
    "del": "Delete",
    "Ins": "Insert",
    "ins": "Insert",
    "Space": "space",
    " ": "space",
    "PageUp": "Page_Up",
    "pageup": "Page_Up",
    "PageDown": "Page_Down",
    "pagedown": "Page_Down",
}

# Add F1-F12
for _i in range(1, 13):
    _KEY_NAME_MAP[f"F{_i}"] = f"F{_i}"


def _gdk_valid(name: str) -> bool:
    """Check if a key name is recognized by GDK."""
    return Gdk.keyval_from_name(name) not in (0, 0xffffff)


def friendly_to_clutter_name(key: str) -> str:
    """Translate a friendly key name to a GDK key name.

    Follows dogtail's resolution chain:
    1. Explicit alias map (modifiers, common renames)
    2. Single letter → lowercase (avoids implicit Shift)
    3. GDK validation: as-is → lowercase → Gdk.KEY_<name> attribute
    """
    if key in _KEY_NAME_MAP:
        return _KEY_NAME_MAP[key]
    if key.lower() in _KEY_NAME_MAP:
        return _KEY_NAME_MAP[key.lower()]
    # Single letters must be lowercase — uppercase keyvals (e.g. "H"=72)
    # implicitly include Shift, so "Ctrl+H" would become Ctrl+Shift+h.
    if len(key) == 1 and key.isalpha():
        return key.lower()
    if _gdk_valid(key):
        return key
    lower = key.lower()
    if _gdk_valid(lower):
        return lower
    # Capitalize for keys like "f4" → "F4", "ESCAPE" → "Escape"
    capitalized = key.capitalize()
    if _gdk_valid(capitalized):
        return capitalized
    # Last resort: try Gdk.KEY_<name> (handles things like "Dash", "Colon")
    if hasattr(Gdk, f"KEY_{key}"):
        return key
    return key


def friendly_to_keyval(key: str) -> int:
    """Translate a friendly key name to an X11 keyval."""
    gdk_name = friendly_to_clutter_name(key)
    kv = Gdk.keyval_from_name(gdk_name)
    if kv not in (0, 0xffffff):
        return kv
    if len(gdk_name) == 1:
        return Gdk.unicode_to_keyval(ord(gdk_name))
    raise ValueError(f"Unknown key: {key}")


def translate_combo(combo: str) -> str:
    """Translate a friendly combo like 'Ctrl+Alt+t' to 'Control_L+Alt_L+t'."""
    parts = combo.split("+")
    return "+".join(friendly_to_clutter_name(p.strip()) for p in parts)


def file_to_base64(filepath: str) -> str:
    """Read a file and return its base64-encoded content."""
    data = Path(filepath).read_bytes()
    return base64.b64encode(data).decode("ascii")


def cleanup_file(filepath: str) -> None:
    """Remove a temp file if it exists."""
    try:
        os.unlink(filepath)
    except OSError:
        pass
