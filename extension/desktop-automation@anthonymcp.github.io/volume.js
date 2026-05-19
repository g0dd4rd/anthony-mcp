// volume.js - Volume control using GNOME Shell's native APIs
import Gvc from 'gi://Gvc';

let _mixerControl = null;

function getMixerControl() {
    if (!_mixerControl) {
        _mixerControl = new Gvc.MixerControl({ name: 'GNOME Desktop MCP' });
        _mixerControl.open();
    }
    return _mixerControl;
}

function getDefaultSink() {
    const mixer = getMixerControl();
    const defaultSinkId = mixer.get_default_sink();
    if (!defaultSinkId) {
        throw new Error('No default audio sink found');
    }
    return mixer.lookup_stream_id(defaultSinkId);
}

/**
 * Get current volume level and mute status
 * @returns {Object} { volume: 0-100, muted: boolean }
 */
export function getVolume() {
    try {
        const sink = getDefaultSink();

        // Get volume (0.0 to 1.0, can go above 1.0 for amplified)
        const volumeFloat = sink.volume / sink.get_base_volume();
        const volumePercent = Math.round(volumeFloat * 100);

        // Get mute status
        const isMuted = sink.is_muted;

        return {
            volume: volumePercent,
            muted: isMuted
        };
    } catch (e) {
        throw new Error(`Failed to get volume: ${e.message}`);
    }
}

/**
 * Set volume level
 * @param {number} volume - Volume level (0-100 for absolute, -100 to 100 for relative)
 * @param {boolean} relative - If true, volume is relative change; if false, absolute level
 * @returns {string} Success message
 */
export function setVolume(volume, relative = false) {
    try {
        const sink = getDefaultSink();
        const baseVolume = sink.get_base_volume();

        let newVolume;

        if (relative) {
            // Relative volume change
            const currentVolume = sink.volume / baseVolume;
            const change = volume / 100.0;
            newVolume = Math.max(0, Math.min(1.5, currentVolume + change)); // Cap at 150%
        } else {
            // Absolute volume level (0-100)
            if (volume < 0 || volume > 100) {
                throw new Error('Volume must be between 0 and 100');
            }
            newVolume = volume / 100.0;
        }

        // Set the new volume
        sink.volume = Math.round(newVolume * baseVolume);
        sink.push_volume();

        const finalPercent = Math.round(newVolume * 100);

        if (relative) {
            if (volume >= 0) {
                return `Volume increased by ${volume}%`;
            } else {
                return `Volume decreased by ${Math.abs(volume)}%`;
            }
        } else {
            return `Volume set to ${finalPercent}%`;
        }
    } catch (e) {
        throw new Error(`Failed to set volume: ${e.message}`);
    }
}

/**
 * Mute or unmute volume
 * @param {boolean} mute - True to mute, false to unmute
 * @returns {string} Success message
 */
export function muteVolume(mute) {
    try {
        const sink = getDefaultSink();
        sink.change_is_muted(mute);

        return mute ? 'Muted' : 'Unmuted';
    } catch (e) {
        throw new Error(`Failed to ${mute ? 'mute' : 'unmute'}: ${e.message}`);
    }
}

export function cleanup() {
    if (_mixerControl) {
        _mixerControl.close();
        _mixerControl = null;
    }
}
