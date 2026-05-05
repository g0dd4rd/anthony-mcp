"""Set desktop wallpaper."""

import subprocess
import os
from pathlib import Path


def set_wallpaper(image_path: str) -> str:
    """Set the desktop wallpaper.

    Sets wallpaper for both light and dark modes.

    Args:
        image_path: Path to image file
                   Full path: '/home/user/Pictures/sunset.jpg'
                   Tilde path: '~/Pictures/nature.png'
                   Relative: 'Pictures/photo.jpg' (expands from home)

    Returns:
        Success message string

    Raises:
        Exception: If file not found or invalid format
    """
    try:
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
        valid_extensions = {'.jpg', '.jpeg', '.png', '.svg', '.bmp', '.gif', '.webp', '.jxl'}
        if path.suffix.lower() not in valid_extensions:
            raise Exception(f"Unsupported image format: {path.suffix}. Supported: JPG, JPEG, PNG, SVG, BMP, GIF, WEBP, JXL")

        # Convert to file:// URI
        image_uri = f"file://{path}"

        # Set wallpaper for both light and dark mode
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", image_uri],
            check=True,
            capture_output=True,
            text=True
        )

        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", image_uri],
            check=True,
            capture_output=True,
            text=True
        )

        return f"Wallpaper set to: {path.name}"

    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to set wallpaper: {e.stderr}")
    except Exception as e:
        raise Exception(f"Failed to set wallpaper: {e}")
