"""Volume control using pactl (works with PipeWire)."""

import subprocess
import json
import re


def get_volume() -> dict:
    """Get current volume level and mute status.

    Returns:
        dict with 'volume' (0-100) and 'muted' (bool)
    """
    try:
        # Get default sink info
        result = subprocess.run(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse volume from output like: "Volume: front-left: 65536 / 100% / 0.00 dB"
        volume_match = re.search(r'(\d+)%', result.stdout)
        if not volume_match:
            raise ValueError("Could not parse volume from pactl output")

        volume = int(volume_match.group(1))

        # Get mute status
        result = subprocess.run(
            ["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse mute status from output like: "Mute: no"
        muted = "yes" in result.stdout.lower()

        return {
            "volume": volume,
            "muted": muted
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get volume: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to get volume: {str(e)}")


def set_volume(volume: int, relative: bool = False) -> str:
    """Set system volume.

    Args:
        volume: Volume level (0-100 for absolute, -100 to 100 for relative)
        relative: If True, volume is relative change

    Returns:
        Success message
    """
    try:
        if relative:
            # Relative volume change
            if volume > 0:
                cmd = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"+{volume}%"]
                message = f"Volume increased by {volume}%"
            elif volume < 0:
                cmd = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"]
                message = f"Volume decreased by {abs(volume)}%"
            else:
                return "No volume change"
        else:
            # Absolute volume level
            if volume < 0 or volume > 100:
                raise ValueError("Volume must be between 0 and 100")

            cmd = ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"]
            message = f"Volume set to {volume}%"

        subprocess.run(cmd, check=True, capture_output=True)
        return message

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to set volume: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to set volume: {str(e)}")


def mute_volume(mute: bool = True) -> str:
    """Mute or unmute volume.

    Args:
        mute: True to mute, False to unmute

    Returns:
        Success message
    """
    try:
        value = "1" if mute else "0"
        subprocess.run(
            ["pactl", "set-sink-mute", "@DEFAULT_SINK@", value],
            check=True,
            capture_output=True
        )

        return "Muted" if mute else "Unmuted"

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to mute/unmute: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to mute/unmute: {str(e)}")
