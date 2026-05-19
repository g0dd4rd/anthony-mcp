import Meta from 'gi://Meta';

export function findWindow(windowId) {
    for (const actor of global.get_window_actors()) {
        const win = actor.get_meta_window();
        if (win && win.get_stable_sequence() === windowId)
            return win;
    }
    return null;
}

export function listWindows() {
    return global.get_window_actors().map(actor => {
        const win = actor.get_meta_window();
        if (!win || win.get_window_type() !== Meta.WindowType.NORMAL)
            return null;
        const rect = win.get_frame_rect();
        return {
            id: win.get_stable_sequence(),
            title: win.get_title(),
            wmClass: win.get_wm_class(),
            wmClassInstance: win.get_wm_class_instance(),
            pid: win.get_pid(),
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height,
            minimized: win.minimized,
            maximized: typeof win.get_maximized === 'function'
                ? win.get_maximized() !== 0
                : (win.maximized_horizontally || win.maximized_vertically || false),
            focused: win.has_focus(),
            above: win.is_above(),
            monitor: win.get_monitor(),
            workspace: win.get_workspace()?.index() ?? -1,
        };
    }).filter(w => w !== null);
}

export function getWindow(win) {
    const rect = win.get_frame_rect();
    return {
        id: win.get_stable_sequence(),
        title: win.get_title(),
        wmClass: win.get_wm_class(),
        wmClassInstance: win.get_wm_class_instance(),
        pid: win.get_pid(),
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height,
        minimized: win.minimized,
        maximized: typeof win.get_maximized === 'function'
            ? win.get_maximized() !== 0
            : (win.maximized_horizontally || win.maximized_vertically || false),
        focused: win.has_focus(),
        above: win.is_above(),
        canClose: win.can_close(),
        canMinimize: win.can_minimize(),
        canMaximize: win.can_maximize(),
        monitor: win.get_monitor(),
        workspace: win.get_workspace()?.index() ?? -1,
        layer: win.get_layer(),
    };
}

export function listWorkspaces() {
    const manager = global.workspace_manager;
    const active = manager.get_active_workspace_index();
    const workspaces = [];
    for (let i = 0; i < manager.get_n_workspaces(); i++) {
        const ws = manager.get_workspace_by_index(i);
        workspaces.push({
            index: i,
            name: (typeof ws.get_name === 'function' ? ws.get_name() : null) || `Workspace ${i + 1}`,
            active: i === active,
            nWindows: ws.list_windows().filter(
                w => w.get_window_type() === Meta.WindowType.NORMAL
            ).length,
        });
    }
    return workspaces;
}

export function activateWorkspace(index) {
    const manager = global.workspace_manager;
    if (index < 0 || index >= manager.get_n_workspaces())
        return false;
    const ws = manager.get_workspace_by_index(index);
    ws.activate(global.get_current_time());
    return true;
}
