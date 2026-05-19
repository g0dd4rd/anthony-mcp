"""System control: battery, brightness, power profile, lock screen, power actions."""

import re
import subprocess


def get_battery_status() -> str:
    """Get battery percentage, state, and time remaining.

    Returns:
        Formatted status string.

    Raises:
        RuntimeError: If upower is unavailable or output cannot be parsed.
    """
    try:
        result = subprocess.run(
            ["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"],
            capture_output=True, text=True, check=True
        )
        info = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("percentage:"):
                info["percentage"] = line.split(":")[-1].strip()
            elif line.startswith("state:"):
                info["state"] = line.split(":")[-1].strip()
            elif line.startswith("time to empty:"):
                info["remaining"] = line.split(":")[-1].strip()
            elif line.startswith("time to full:"):
                info["remaining"] = line.split(":")[-1].strip()

        pct = info.get("percentage", "unknown")
        state = info.get("state", "unknown")
        remaining = info.get("remaining")

        msg = f"Battery is at {pct}, {state}"
        if remaining:
            msg += f", {remaining} remaining"
        return msg + "."
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to read battery status: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to read battery status: {e}")


def set_brightness(target: str, level: str) -> str:
    """Set screen or keyboard backlight brightness.

    Args:
        target: "screen" or "keyboard".
        level: Brightness level — "up", "down", "max", "min", "off", or a
               percentage like "50%".

    Returns:
        Success message with resulting brightness.

    Raises:
        RuntimeError: If brightnessctl is missing or the command fails.
    """
    try:
        if target == "keyboard":
            device_flag = ["--device", "tpacpi::kbd_backlight"]
        else:
            device_flag = []

        if level in ("up", "increase"):
            cmd = ["brightnessctl", *device_flag, "set", "+10%"]
        elif level in ("down", "decrease"):
            cmd = ["brightnessctl", *device_flag, "set", "10%-"]
        elif level.endswith("%"):
            cmd = ["brightnessctl", *device_flag, "set", level]
        elif level == "max":
            cmd = ["brightnessctl", *device_flag, "set", "100%"]
        elif level in ("min", "off") and target == "keyboard":
            cmd = ["brightnessctl", *device_flag, "set", "0"]
        elif level == "min":
            cmd = ["brightnessctl", *device_flag, "set", "5%"]
        else:
            cmd = ["brightnessctl", *device_flag, "set", level]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if "Current brightness" in line:
                pct_match = re.search(r'\((\d+%)\)', line)
                if pct_match:
                    label = "Keyboard backlight" if target == "keyboard" else "Brightness"
                    return f"{label} set to {pct_match.group(1)}."
                return line.strip()
        label = "Keyboard backlight" if target == "keyboard" else "Brightness"
        return f"{label} set to {level}."
    except FileNotFoundError:
        raise RuntimeError("brightnessctl is not installed.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to set brightness: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to set brightness: {e}")


def get_power_profile() -> str:
    """Get the current power profile.

    Returns:
        Status message with current profile name.

    Raises:
        RuntimeError: If the power profiles D-Bus service is unavailable.
    """
    try:
        result = subprocess.run(
            ["gdbus", "call", "--system",
             "--dest", "net.hadess.PowerProfiles",
             "--object-path", "/net/hadess/PowerProfiles",
             "--method", "org.freedesktop.DBus.Properties.Get",
             "net.hadess.PowerProfiles", "ActiveProfile"],
            capture_output=True, text=True, check=True
        )
        profile = result.stdout.strip().strip("(<'>),")
        return f"Power mode is {profile}."
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to read power profile: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to read power profile: {e}")


def set_power_profile(profile: str) -> str:
    """Set power profile.

    Args:
        profile: Target profile — "performance", "balanced", or "power-saver".
                 Aliases like "power saver" and "powersaver" are accepted.

    Returns:
        Success message.

    Raises:
        ValueError: If the profile name is not recognized.
        RuntimeError: If the D-Bus call fails.
    """
    profile_map = {
        "performance": "performance",
        "balanced": "balanced",
        "power saver": "power-saver",
        "power-saver": "power-saver",
        "powersaver": "power-saver",
    }
    profile_name = profile_map.get(profile.lower())
    if not profile_name:
        raise ValueError(
            f"Unknown profile: {profile}. Options: performance, balanced, power-saver."
        )
    try:
        subprocess.run(
            ["gdbus", "call", "--system",
             "--dest", "net.hadess.PowerProfiles",
             "--object-path", "/net/hadess/PowerProfiles",
             "--method", "org.freedesktop.DBus.Properties.Set",
             "net.hadess.PowerProfiles", "ActiveProfile",
             f"<'{profile_name}'>"],
            capture_output=True, text=True, check=True
        )
        return f"Power mode set to {profile_name}."
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to set power profile: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to set power profile: {e}")


def lock_screen() -> str:
    """Lock the screen.

    Returns:
        Success message.

    Raises:
        RuntimeError: If the lock command fails.
    """
    try:
        subprocess.run(["loginctl", "lock-session"], check=True)
        return "Screen locked."
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to lock screen: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to lock screen: {e}")


def power_action(action: str) -> str:
    """Execute a power action.

    Args:
        action: One of "suspend", "restart", "shutdown", "logout".

    Returns:
        Confirmation message.

    Raises:
        ValueError: If the action is not recognized.
        RuntimeError: If the command fails.
    """
    commands = {
        "suspend": (["systemctl", "suspend"], "Suspending."),
        "restart": (["systemctl", "reboot"], "Restarting."),
        "shutdown": (["systemctl", "poweroff"], "Shutting down."),
        "logout": (["gnome-session-quit", "--logout", "--no-prompt"], "Logging out."),
    }
    entry = commands.get(action)
    if not entry:
        raise ValueError(
            f"Unknown power action: {action}. Options: suspend, restart, shutdown, logout."
        )
    cmd, message = entry
    subprocess.run(cmd, check=False)
    return message
