"""Media playback control via MPRIS D-Bus interface."""

import dbus


def find_mpris_players():
    """Find all available MPRIS media players on D-Bus.

    Returns:
        list: List of player bus names (e.g., ['org.mpris.MediaPlayer2.rhythmbox'])
    """
    try:
        bus = dbus.SessionBus()
        dbus_obj = bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
        dbus_iface = dbus.Interface(dbus_obj, "org.freedesktop.DBus")

        # Get all bus names
        names = dbus_iface.ListNames()

        # Filter for MPRIS players
        players = [name for name in names if name.startswith("org.mpris.MediaPlayer2.")]

        return players
    except Exception as e:
        raise Exception(f"Failed to find media players: {e}") from e


def media_control(action: str, player: str = "") -> str:
    """Control media playback via MPRIS.

    Args:
        action: Media control action - play, pause, play_pause, stop, next, previous
        player: Optional specific player name (e.g., 'spotify', 'rhythmbox').
                If empty, uses the first available player.

    Returns:
        Success message string.

    Raises:
        Exception: If no players found, invalid action, or operation fails.
    """
    try:
        # Find available players
        players = find_mpris_players()

        if not players:
            raise Exception("No media players found")

        # Select target player
        if player:
            # Find player matching the requested name
            target_player = None
            player_lower = player.lower()
            for p in players:
                if player_lower in p.lower():
                    target_player = p
                    break

            if not target_player:
                available = ", ".join(p.split(".")[-1] for p in players)
                raise Exception(f"Player '{player}' not found. Available: {available}")
        else:
            # Use first available player
            target_player = players[0]

        # Connect to the MPRIS player
        bus = dbus.SessionBus()
        player_obj = bus.get_object(target_player, "/org/mpris/MediaPlayer2")
        player_iface = dbus.Interface(player_obj, "org.mpris.MediaPlayer2.Player")

        # Execute the requested action
        player_name = target_player.split(".")[-1]

        if action == "play":
            player_iface.Play()
            return f"Started playback on {player_name}"
        elif action == "pause":
            player_iface.Pause()
            return f"Paused playback on {player_name}"
        elif action == "play_pause":
            player_iface.PlayPause()
            return f"Toggled playback on {player_name}"
        elif action == "stop":
            player_iface.Stop()
            return f"Stopped playback on {player_name}"
        elif action == "next":
            player_iface.Next()
            return f"Skipped to next track on {player_name}"
        elif action == "previous":
            player_iface.Previous()
            return f"Skipped to previous track on {player_name}"
        else:
            raise Exception(
                f"Unknown action: {action}. Valid actions:"
                " play, pause, play_pause, stop, next, previous"
            )

    except Exception as e:
        raise Exception(f"Media control failed: {e}") from e


def get_media_status(player: str = "") -> dict:
    """Get current media player status.

    Args:
        player: Optional specific player name. If empty, uses first available.

    Returns:
        dict with status, player name, metadata (title, artist, album)
    """
    try:
        # Find available players
        players = find_mpris_players()

        if not players:
            return {"error": "No media players found"}

        # Select target player
        if player:
            target_player = None
            player_lower = player.lower()
            for p in players:
                if player_lower in p.lower():
                    target_player = p
                    break

            if not target_player:
                return {"error": f"Player '{player}' not found"}
        else:
            target_player = players[0]

        # Connect to the player
        bus = dbus.SessionBus()
        player_obj = bus.get_object(target_player, "/org/mpris/MediaPlayer2")

        # Get properties interface
        props_iface = dbus.Interface(player_obj, "org.freedesktop.DBus.Properties")

        # Get playback status
        status = props_iface.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus")

        # Get metadata
        metadata = props_iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")

        player_name = target_player.split(".")[-1]

        # Extract useful metadata
        title = metadata.get("xesam:title", "Unknown")
        artist = (
            metadata.get("xesam:artist", ["Unknown"])[0]
            if "xesam:artist" in metadata
            else "Unknown"
        )
        album = metadata.get("xesam:album", "Unknown")

        return {
            "player": player_name,
            "status": str(status),  # Playing, Paused, or Stopped
            "title": str(title),
            "artist": str(artist),
            "album": str(album),
        }

    except Exception as e:
        return {"error": f"Failed to get media status: {e}"}
