import stateManager from "./mapStateManager.js";

// Mirrors the panel's selection (station, train, line, POI) in the browser history on mobile, so the
// system back button or gesture closes what is open instead of leaving the site.
// Selected objects can't be stored in history.state, so it holds only an index into `entries`.

const SELECTION_KEYS = ['selectedRoute', 'selectedStation', 'selectedLine', 'selectedPoi'];

function sameSelection(a, b) {
    return SELECTION_KEYS.every(key => (a?.[key] ?? null) === (b?.[key] ?? null));
}

function isEmpty(selection) {
    return SELECTION_KEYS.every(key => !selection[key]);
}

export function initHistorySync() {
    const entries = [stateManager.selection];
    let depth = 0;
    let restoring = false;

    history.replaceState({ ...history.state, panelDepth: 0 }, '');

    stateManager.subscribe(() => {
        if (restoring || stateManager.deviceType !== 'mobile') return;
        const selection = stateManager.selection;
        if (sameSelection(selection, entries[depth])) return;

        if (depth > 0 && sameSelection(selection, entries[depth - 1])) {
            // In-panel "back" (to the station or the line) is the same as the browser's back
            history.back();
        } else if (depth > 0 && isEmpty(selection)) {
            // Closing the panel drops all the steps that led to it
            history.go(-depth);
        } else {
            depth += 1;
            entries.length = depth;
            entries.push(selection);
            history.pushState({ ...history.state, panelDepth: depth }, '');
        }
    });

    window.addEventListener('popstate', (e) => {
        depth = e.state?.panelDepth ?? 0;
        const selection = entries[depth] ?? entries[0];
        if (sameSelection(selection, stateManager.selection)) return;
        restoring = true;
        stateManager.restoreSelection(selection);
        restoring = false;
    });
}
