"""File search using GNOME localsearch (Tracker indexing)."""

import subprocess
import json
import os
from urllib.parse import unquote

_EXT_ALIASES = {
    '.jpg': '.jpeg',
    '.jpeg': '.jpg',
    '.htm': '.html',
    '.html': '.htm',
    '.tif': '.tiff',
    '.tiff': '.tif',
}


def search_files(query: str, file_type: str = "files", limit: int = 10) -> str:
    """Search for files using GNOME localsearch (Tracker).

    Uses the system's file index for instant results.

    Args:
        query: Search query (filename, keywords, content)
        file_type: Type of files to search for.
                   Options: files, folders, images, videos, documents, audio, music_albums, music_artists, software
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        JSON string with list of file paths

    Raises:
        Exception: If localsearch is not available or search fails
    """
    try:
        # Map file_type to localsearch flag
        type_flags = {
            "files": "--files",
            "folders": "--folders",
            "images": "--images",
            "videos": "--videos",
            "documents": "--documents",
            "audio": "--audio",
            "music_albums": "--music-albums",
            "music_artists": "--music-artists",
            "software": "--software"
        }

        type_flag = type_flags.get(file_type, "--files")

        # Clamp limit to reasonable range
        limit = max(1, min(limit, 50))

        # Run localsearch
        result = subprocess.run(
            ["localsearch", "search", type_flag, "--limit", str(limit), query],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse results - each line is a file:// URI
        lines = result.stdout.strip().split('\n')
        paths = []

        for line in lines:
            if line.startswith('file://'):
                # Remove file:// prefix and decode URL encoding
                path = unquote(line[7:])
                paths.append(path)

        if not paths:
            _, ext = os.path.splitext(query)
            alt_ext = _EXT_ALIASES.get(ext.lower())
            if alt_ext:
                alt_query = query[:len(query) - len(ext)] + alt_ext
                alt_result = subprocess.run(
                    ["localsearch", "search", type_flag, "--limit", str(limit), alt_query],
                    capture_output=True, text=True, check=True
                )
                for line in alt_result.stdout.strip().split('\n'):
                    if line.startswith('file://'):
                        paths.append(unquote(line[7:]))

        return json.dumps({
            "query": query,
            "file_type": file_type,
            "count": len(paths),
            "results": paths
        })

    except subprocess.CalledProcessError as e:
        raise Exception(f"Search failed: {e.stderr.decode()}")
    except FileNotFoundError:
        raise Exception("localsearch not found - GNOME file indexing not available")
    except Exception as e:
        raise Exception(f"Search error: {e}")
