"""Open URLs in the default browser."""

import subprocess


def open_url(url: str) -> str:
    """Open a URL in the default web browser.

    Automatically adds https:// if no protocol specified.

    Args:
        url: URL to open
             Examples: 'https://google.com', 'google.com', 'github.com/user/repo'

    Returns:
        Success message string

    Raises:
        Exception: If opening the URL fails
    """
    try:
        # Normalize URL - add https:// if no protocol
        normalized_url = url
        if not url.startswith(('http://', 'https://', 'file://', 'ftp://')):
            normalized_url = f"https://{url}"

        # Open with xdg-open (opens in default browser)
        subprocess.Popen(
            ["xdg-open", normalized_url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )

        return f"Opened URL: {normalized_url}"

    except Exception as e:
        raise Exception(f"Failed to open URL '{url}': {e}")
