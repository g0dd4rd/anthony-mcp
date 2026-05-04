"""Quick Settings control for GNOME."""

import subprocess
import dbus


def toggle_wifi(enabled: bool) -> str:
    """Enable or disable WiFi using NetworkManager.

    Args:
        enabled: True to enable WiFi, False to disable

    Returns:
        Success message string

    Raises:
        Exception: If NetworkManager is not available or operation fails
    """
    try:
        bus = dbus.SystemBus()
        nm_obj = bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
        nm_props = dbus.Interface(nm_obj, 'org.freedesktop.DBus.Properties')

        nm_props.Set('org.freedesktop.NetworkManager', 'WirelessEnabled', enabled)

        return f"WiFi {'enabled' if enabled else 'disabled'}"
    except Exception as e:
        raise Exception(f"Failed to toggle WiFi: {e}")


def toggle_bluetooth(enabled: bool) -> str:
    """Enable or disable Bluetooth using bluez.

    Args:
        enabled: True to enable Bluetooth, False to disable

    Returns:
        Success message string

    Raises:
        Exception: If Bluetooth adapter not found or operation fails
    """
    try:
        bus = dbus.SystemBus()
        adapter_obj = bus.get_object('org.bluez', '/org/bluez/hci0')
        adapter_props = dbus.Interface(adapter_obj, 'org.freedesktop.DBus.Properties')

        adapter_props.Set('org.bluez.Adapter1', 'Powered', enabled)

        return f"Bluetooth {'enabled' if enabled else 'disabled'}"
    except Exception as e:
        raise Exception(f"Failed to toggle Bluetooth: {e}")


def toggle_night_light(enabled: bool) -> str:
    """Enable or disable Night Light using gsettings.

    Args:
        enabled: True to enable Night Light, False to disable

    Returns:
        Success message string

    Raises:
        Exception: If gsettings command fails
    """
    try:
        value = "true" if enabled else "false"
        subprocess.run(
            ["gsettings", "set", "org.gnome.settings-daemon.plugins.color",
             "night-light-enabled", value],
            check=True,
            capture_output=True
        )

        return f"Night Light {'enabled' if enabled else 'disabled'}"
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to toggle Night Light: {e.stderr.decode()}")


def toggle_dark_style(enabled: bool) -> str:
    """Enable or disable Dark Style using gsettings.

    Args:
        enabled: True to enable dark mode, False for light mode

    Returns:
        Success message string

    Raises:
        Exception: If gsettings command fails
    """
    try:
        value = "prefer-dark" if enabled else "prefer-light"
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.interface",
             "color-scheme", value],
            check=True,
            capture_output=True
        )

        return f"Dark style {'enabled' if enabled else 'disabled'}"
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to toggle dark style: {e.stderr.decode()}")


def toggle_do_not_disturb(enabled: bool) -> str:
    """Enable or disable Do Not Disturb using gsettings.

    Note: show-banners logic is inverted (false = DND enabled)

    Args:
        enabled: True to enable DND, False to disable

    Returns:
        Success message string

    Raises:
        Exception: If gsettings command fails
    """
    try:
        # Inverted: show-banners=false means DND is enabled
        value = "false" if enabled else "true"
        subprocess.run(
            ["gsettings", "set", "org.gnome.desktop.notifications",
             "show-banners", value],
            check=True,
            capture_output=True
        )

        return f"Do Not Disturb {'enabled' if enabled else 'disabled'}"
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to toggle Do Not Disturb: {e.stderr.decode()}")


def quick_settings(setting: str, enabled: bool) -> str:
    """Toggle GNOME quick settings.

    Args:
        setting: Which setting to toggle. Options: wifi, bluetooth, night_light,
                do_not_disturb, dark_style
        enabled: True to enable, False to disable

    Returns:
        Success message string

    Raises:
        Exception: If setting is unknown or operation fails
    """
    setting = setting.lower().replace("-", "_").replace(" ", "_")

    if setting == "wifi":
        return toggle_wifi(enabled)
    elif setting == "bluetooth":
        return toggle_bluetooth(enabled)
    elif setting == "night_light":
        return toggle_night_light(enabled)
    elif setting == "dark_style" or setting == "dark_mode":
        return toggle_dark_style(enabled)
    elif setting == "do_not_disturb" or setting == "dnd":
        return toggle_do_not_disturb(enabled)
    else:
        raise Exception(f"Unknown setting: {setting}. Supported: wifi, bluetooth, night_light, dark_style, do_not_disturb")
