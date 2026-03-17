import Clutter from 'gi://Clutter';
import St from 'gi://St';
import * as ModalDialog from 'resource:///org/gnome/shell/ui/modalDialog.js';

export function showConsentDialog(onAccept, onCancel) {
    const dialog = new ModalDialog.ModalDialog({ destroyOnClose: true });

    const content = new St.BoxLayout({ vertical: true, style: 'spacing: 12px;' });

    content.add_child(new St.Label({
        text: 'Desktop Automation',
        style: 'font-weight: bold; font-size: 1.2em;',
    }));

    content.add_child(new St.Label({
        text: 'This extension allows external programs to take screenshots, '
            + 'control windows, and inject keyboard/mouse input via D-Bus.\n\n'
            + 'Enable only if you trust the connecting application.',
        style: 'max-width: 400px;',
    }));

    dialog.contentLayout.add_child(content);

    dialog.addButton({
        label: 'Cancel',
        action: () => {
            dialog.close();
            if (onCancel) onCancel();
        },
        key: Clutter.KEY_Escape,
    });

    dialog.addButton({
        label: 'Enable',
        action: () => {
            dialog.close();
            if (onAccept) onAccept();
        },
        default: true,
    });

    dialog.open();
    return dialog;
}
