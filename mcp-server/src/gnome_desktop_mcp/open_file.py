"""Open files with default applications."""

import subprocess
import os
import json
from . import search_files as sf


def open_file(path: str, search_location: str = "") -> str:
    """Smart file opener - opens files by full path or searches for them first.

    If given a full path, opens directly.
    If given just a filename, searches for it and opens the first match.

    Args:
        path: File path or filename to open
              Full path: '/home/user/document.pdf', '~/Downloads/image.png'
              Filename: 'screenshot.png', 'report.pdf'
        search_location: Optional folder to search in (Pictures, Documents, Downloads, etc.)
                        If empty, searches everywhere.

    Returns:
        Success message string

    Raises:
        Exception: If file not found or open fails
    """
    try:
        # Check if it's a full path (starts with / or ~)
        if path.startswith('/') or path.startswith('~'):
            # Full path - open directly
            expanded_path = os.path.expanduser(path)

            if not os.path.exists(expanded_path):
                raise Exception(f"File not found: {expanded_path}")

            # Open with xdg-open
            subprocess.Popen(
                ["xdg-open", expanded_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )

            filename = os.path.basename(expanded_path)
            return f"Opened: {filename}"

        else:
            # Just a filename - search for it first
            # Build search query
            search_query = path

            # If search_location specified, search in that folder
            # Map common folder names to actual paths
            folder_map = {
                "pictures": "~/Pictures",
                "documents": "~/Documents",
                "downloads": "~/Downloads",
                "music": "~/Music",
                "videos": "~/Videos",
                "desktop": "~/Desktop"
            }

            search_filter = None
            if search_location:
                location_lower = search_location.lower()
                if location_lower in folder_map:
                    search_filter = os.path.expanduser(folder_map[location_lower])

            # Search for the file
            search_result = sf.search_files(search_query, "files", limit=10)
            results = json.loads(search_result)

            if results["count"] == 0:
                raise Exception(f"No files found matching '{path}'")

            # Filter by search_location if specified
            if search_filter:
                filtered = [r for r in results["results"] if r.startswith(search_filter)]
                if not filtered:
                    raise Exception(f"No files found matching '{path}' in {search_location}")
                file_path = filtered[0]
            else:
                file_path = results["results"][0]

            # Open the found file
            subprocess.Popen(
                ["xdg-open", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True
            )

            filename = os.path.basename(file_path)
            return f"Opened: {filename} (found at {file_path})"

    except Exception as e:
        raise Exception(f"Failed to open '{path}': {e}")
