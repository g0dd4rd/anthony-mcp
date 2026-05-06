import Shell from 'gi://Shell';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

const SCREENSHOT_DIR = '/tmp/gnome-mcp';
let _counter = 0;

function _ensureDir() {
    GLib.mkdir_with_parents(SCREENSHOT_DIR, 0o700);
}

function _nextFilename() {
    _counter++;
    return GLib.build_filenamev([
        SCREENSHOT_DIR,
        `screenshot-${Date.now()}-${_counter}.png`,
    ]);
}

function _createStream(filepath) {
    const file = Gio.File.new_for_path(filepath);
    return file.replace(null, false, Gio.FileCreateFlags.PRIVATE, null);
}

export function screenshotFull(includeCursor, invocation) {
    _ensureDir();
    const filepath = _nextFilename();
    const stream = _createStream(filepath);
    const screenshot = new Shell.Screenshot();

    screenshot.screenshot(includeCursor, stream, (source, result) => {
        try {
            screenshot.screenshot_finish(result);
            stream.close(null);
            invocation.return_value(GLib.Variant.new('(s)', [filepath]));
        } catch (e) {
            stream.close(null);
            invocation.return_error_literal(
                Gio.DBusError, Gio.DBusError.FAILED,
                `ScreenshotFailed: ${e.message}`);
        }
    });
}

export function screenshotWindow(includeCursor, includeFrame, invocation, onComplete = null) {
    _ensureDir();
    const filepath = _nextFilename();
    const stream = _createStream(filepath);
    const screenshot = new Shell.Screenshot();

    screenshot.screenshot_window(includeFrame, includeCursor, stream, (source, result) => {
        try {
            screenshot.screenshot_window_finish(result);
            stream.close(null);
            if (onComplete) onComplete();
            invocation.return_value(GLib.Variant.new('(s)', [filepath]));
        } catch (e) {
            stream.close(null);
            if (onComplete) onComplete();
            invocation.return_error_literal(
                Gio.DBusError, Gio.DBusError.FAILED,
                `ScreenshotFailed: ${e.message}`);
        }
    });
}

export function screenshotArea(x, y, width, height, includeCursor, invocation) {
    _ensureDir();
    const filepath = _nextFilename();
    const stream = _createStream(filepath);
    const screenshot = new Shell.Screenshot();

    screenshot.screenshot_area(x, y, width, height, stream, (source, result) => {
        try {
            screenshot.screenshot_area_finish(result);
            stream.close(null);
            invocation.return_value(GLib.Variant.new('(s)', [filepath]));
        } catch (e) {
            stream.close(null);
            invocation.return_error_literal(
                Gio.DBusError, Gio.DBusError.FAILED,
                `ScreenshotFailed: ${e.message}`);
        }
    });
}

export function pickColor(x, y, invocation) {
    // Use XDG Desktop Portal for color picking (like Contrast app does)
    const portal = Gio.DBusProxy.new_for_bus_sync(
        Gio.BusType.SESSION,
        Gio.DBusProxyFlags.NONE,
        null,
        'org.freedesktop.portal.Desktop',
        '/org/freedesktop/portal/desktop',
        'org.freedesktop.portal.Screenshot',
        null
    );

    try {
        // Call PickColor on the portal
        // Parameters: (parent_window, options)
        const options = {};
        const result = portal.call_sync(
            'PickColor',
            new GLib.Variant('(sa{sv})', ['', options]),
            Gio.DBusCallFlags.NONE,
            -1,
            null
        );

        // Parse response: returns (response_code, results)
        // results contains 'color' key with (r, g, b) tuple
        const [response_code, results] = result.deep_unpack();

        if (response_code === 0) {
            const color = results['color'].deep_unpack();
            invocation.return_value(GLib.Variant.new('(ddd)', color));
        } else {
            invocation.return_error_literal(
                Gio.DBusError, Gio.DBusError.FAILED,
                'ColorPick cancelled or failed');
        }
    } catch (e) {
        invocation.return_error_literal(
            Gio.DBusError, Gio.DBusError.FAILED,
            `ColorPickFailed: ${e.message}`);
    }
}

export function cleanupScreenshots() {
    let count = 0;
    const dir = Gio.File.new_for_path(SCREENSHOT_DIR);
    if (!dir.query_exists(null))
        return count;

    const enumerator = dir.enumerate_children(
        'standard::name', Gio.FileQueryInfoFlags.NONE, null);
    let info;
    while ((info = enumerator.next_file(null)) !== null) {
        const child = dir.get_child(info.get_name());
        if (child.delete(null))
            count++;
    }
    return count;
}
