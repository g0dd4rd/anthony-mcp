import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

export async function sendNotification(summary, body) {
    try {
        // Use notify-send command for reliable notifications
        // This works consistently across GNOME versions
        const args = ['notify-send'];

        // Add summary
        args.push(summary);

        // Add body if provided
        if (body && body.length > 0) {
            args.push(body);
        }

        // Spawn the process
        const proc = Gio.Subprocess.new(
            args,
            Gio.SubprocessFlags.NONE
        );

        // Wait for completion asynchronously (non-blocking)
        await proc.wait_check_async(null);
        return true;
    } catch (e) {
        console.error(`sendNotification failed: ${e.message}`);
        return false;
    }
}
