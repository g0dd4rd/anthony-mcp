"""Set desktop wallpaper."""

import os
import subprocess
from pathlib import Path

from . import wallpaper_index


def _is_kde():
    return "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper()


def set_wallpaper(image_path: str) -> str:
    """Set the desktop wallpaper.

    Sets wallpaper for both light and dark modes.

    Args:
        image_path: Path to image file OR color name OR wallpaper name
                   Path: '/home/user/Pictures/sunset.jpg', '~/Pictures/nature.png'
                   Color: 'red', 'blue', 'green', 'orange', 'purple'
                   Name: 'fedora', 'adwaita', 'default'

    Returns:
        Success message string

    Raises:
        Exception: If file not found or invalid format
    """
    try:
        # Check if input is a color or name search query
        if _is_search_query(image_path):
            resolved_path = _search_wallpaper(image_path)
            if resolved_path:
                return _set_wallpaper_from_path(resolved_path)
            else:
                # Fallback: try as file path anyway
                pass

        # Try as file path
        return _set_wallpaper_from_path(image_path)

    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to set wallpaper: {e.stderr}") from e
    except Exception as e:
        raise Exception(f"Failed to set wallpaper: {e}") from e


def _is_search_query(query: str) -> bool:
    """Check if input looks like a color/name search rather than a file path.

    Args:
        query: User input

    Returns:
        True if looks like search query (color or name), False if looks like path
    """
    query_lower = query.lower().strip()

    # Common color keywords
    colors = {
        "red",
        "blue",
        "green",
        "yellow",
        "orange",
        "purple",
        "pink",
        "cyan",
        "black",
        "white",
        "gray",
        "grey",
        "dark",
        "light",
    }

    # Common wallpaper names
    names = {"fedora", "adwaita", "default", "gnome", "abstract", "nature"}

    # If it's a single word and matches color/name, it's a search
    if " " not in query_lower and not query.startswith(("/", "~", ".")):
        if query_lower in colors or query_lower in names:
            return True

        # Multi-word color (e.g., "dark blue")
        for word in query_lower.split():
            if word in colors:
                return True

    return False


def _search_wallpaper(query: str) -> str:
    """Search for wallpaper by color or name.

    Args:
        query: Color name or wallpaper name

    Returns:
        Path to wallpaper, or None if not found
    """
    query = query.lower().strip()

    # Try color search first
    result = wallpaper_index.search_wallpaper_by_color(query)
    if result:
        return result

    # Try name search
    result = wallpaper_index.search_wallpaper_by_name(query)
    if result:
        return result

    return None


def _set_wallpaper_from_path(image_path: str) -> str:
    """Set wallpaper from a validated file path.

    Args:
        image_path: Path to image file (can be relative, ~, or absolute)

    Returns:
        Success message

    Raises:
        Exception: If file not found or invalid
    """
    # Expand and validate path
    expanded_path = os.path.expanduser(image_path)

    # If still relative, make it relative to home
    if not os.path.isabs(expanded_path):
        expanded_path = os.path.join(os.path.expanduser("~"), expanded_path)

    # Canonicalize path
    path = Path(expanded_path).resolve()

    # Validate file exists
    if not path.exists():
        raise Exception(f"Image file not found: {image_path}")

    # Validate it's a file
    if not path.is_file():
        raise Exception(f"Path is not a file: {image_path}")

    # Validate file extension
    valid_extensions = {".jpg", ".jpeg", ".png", ".svg", ".bmp", ".gif", ".webp", ".jxl"}
    if path.suffix.lower() not in valid_extensions:
        raise Exception(
            f"Unsupported image format: {path.suffix}."
            " Supported: JPG, JPEG, PNG, SVG, BMP, GIF, WEBP, JXL"
        )

    if _is_kde():
        subprocess.run(
            ["plasma-apply-wallpaperimage", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        image_uri = f"file://{path}"
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", image_uri],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", image_uri],
            check=True,
            capture_output=True,
            text=True,
        )

    return f"Wallpaper set to: {path.name}"
