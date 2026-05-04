"""Open files and URLs with default applications."""

import subprocess
import os


def open_file(path: str) -> str:
    """Open a file or URL with the default application.

    Uses xdg-open which handles:
    - Local files (PDFs, images, documents, etc.) - opens with default app based on MIME type
    - URLs (http://, https://, etc.) - opens in default browser
    - Any URI scheme

    Args:
        path: File path or URL to open
              Examples: '/home/user/document.pdf', 'https://example.com', '~/Downloads/image.png'

    Returns:
        Success message string

    Raises:
        Exception: If file doesn't exist (for local files) or xdg-open fails
    """
    try:
        # Expand ~ to home directory for local paths
        expanded_path = path
        if not path.startswith(('http://', 'https://', 'file://')):
            expanded_path = os.path.expanduser(path)

            # Check if file exists for local paths
            if not os.path.exists(expanded_path):
                raise Exception(f"File not found: {expanded_path}")

        # Use xdg-open to open with default application
        # Detach from parent process so it doesn't block
        subprocess.Popen(
            ["xdg-open", expanded_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )

        # Determine what type of thing was opened
        if path.startswith(('http://', 'https://')):
            return f"Opened URL: {path}"
        else:
            filename = os.path.basename(expanded_path)
            return f"Opened file: {filename}"

    except Exception as e:
        raise Exception(f"Failed to open '{path}': {e}")
