"""Index and search GNOME wallpapers by color and name."""

import os
import xml.etree.ElementTree as ET
from pathlib import Path


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_color_name(rgb: tuple[int, int, int]) -> str:
    """Convert RGB to basic color name using simple heuristic."""
    r, g, b = rgb

    # Grayscale detection
    if max(r, g, b) - min(r, g, b) < 30:
        if max(r, g, b) < 50:
            return "black"
        elif min(r, g, b) > 200:
            return "white"
        else:
            return "gray"

    # Color detection - find dominant channel
    max_channel = max(r, g, b)

    # Red dominant
    if r == max_channel and r > g + 30 and r > b + 30:
        if r > 180:
            return "red"
        else:
            return "dark-red"

    # Green dominant
    if g == max_channel and g > r + 30 and g > b + 30:
        if g > 180:
            return "green"
        else:
            return "dark-green"

    # Blue dominant
    if b == max_channel and b > r + 30 and b > g + 30:
        if b > 180:
            return "blue"
        else:
            return "dark-blue"

    # Yellow (red + green)
    if r > 150 and g > 150 and b < 100:
        return "yellow"

    # Orange (red > green > blue)
    if r > 200 and g > 100 and g < r and b < 100:
        return "orange"

    # Purple/Magenta (red + blue)
    if r > 100 and b > 100 and g < 100:
        return "purple"

    # Cyan (green + blue)
    if g > 100 and b > 100 and r < 100:
        return "cyan"

    # Default to gray if no clear color
    return "gray"


def index_wallpapers() -> list[dict[str, str]]:
    """Index all GNOME wallpapers from XML metadata.

    Returns:
        List of wallpaper dicts with keys: name, path, color, dark_color, xml_file
    """
    wallpapers = []
    xml_dir = Path("/usr/share/gnome-background-properties")

    if not xml_dir.exists():
        return wallpapers

    for xml_file in xml_dir.glob("*.xml"):
        try:
            tree = ET.parse(xml_file)  # noqa: S314
            root = tree.getroot()

            for wp in root.findall("wallpaper"):
                # Skip deleted wallpapers
                if wp.get("deleted") == "true":
                    continue

                name_elem = wp.find("name")
                filename_elem = wp.find("filename")
                pcolor_elem = wp.find("pcolor")

                if name_elem is None or filename_elem is None:
                    continue

                name = name_elem.text
                path = filename_elem.text

                # Skip if file doesn't exist
                if not os.path.exists(path):
                    continue

                # Extract color if available
                color_name = None
                if pcolor_elem is not None and pcolor_elem.text:
                    rgb = hex_to_rgb(pcolor_elem.text)
                    color_name = rgb_to_color_name(rgb)

                wallpapers.append(
                    {"name": name, "path": path, "color": color_name, "xml_file": xml_file.name}
                )

        except Exception:  # noqa: S112
            # Skip files that can't be parsed
            continue

    return wallpapers


def search_wallpaper_by_color(color_query: str) -> str | None:
    """Search for a wallpaper by color name.

    Args:
        color_query: Color keyword (red, blue, green, etc.)

    Returns:
        Path to matching wallpaper, or None if not found
    """
    wallpapers = index_wallpapers()

    if not wallpapers:
        return None

    # Normalize query
    color_query = color_query.lower().strip()

    # Try exact color match first
    matches = [wp for wp in wallpapers if wp["color"] == color_query]

    # Try partial match (e.g., "dark-blue" matches "blue")
    if not matches:
        matches = [wp for wp in wallpapers if wp["color"] and color_query in wp["color"]]

    # Try reverse partial match (e.g., "blue" matches "dark-blue")
    if not matches:
        matches = [wp for wp in wallpapers if wp["color"] and wp["color"] in color_query]

    if matches:
        # Return first match
        return matches[0]["path"]

    return None


def search_wallpaper_by_name(name_query: str) -> str | None:
    """Search for a wallpaper by name.

    Args:
        name_query: Name keyword (fedora, adwaita, default, etc.)

    Returns:
        Path to matching wallpaper, or None if not found
    """
    wallpapers = index_wallpapers()

    if not wallpapers:
        return None

    # Normalize query
    name_query = name_query.lower().strip()

    # Try case-insensitive name match
    for wp in wallpapers:
        if name_query in wp["name"].lower():
            return wp["path"]

    return None


def list_available_wallpapers() -> str:
    """List all available wallpapers with their colors.

    Returns:
        Human-readable list of wallpapers
    """
    wallpapers = index_wallpapers()

    if not wallpapers:
        return "No wallpapers found"

    result = f"Available wallpapers ({len(wallpapers)}):\n"

    # Group by color
    by_color = {}
    for wp in wallpapers:
        color = wp["color"] or "unknown"
        if color not in by_color:
            by_color[color] = []
        by_color[color].append(wp)

    for color in sorted(by_color.keys()):
        result += f"\n{color.upper()}:\n"
        for wp in by_color[color]:
            result += f"  - {wp['name']}\n"

    return result
