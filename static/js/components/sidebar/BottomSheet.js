import { MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO } from "../../constants.js";

const SNAP_ORDER = ['collapsed', 'half', 'expanded'];
// Site header height (64px) plus a gap, so the expanded panel doesn't cover the header
const EXPANDED_TOP_GAP = 76;
const DRAG_THRESHOLD = 6;
const FLICK_VELOCITY = 0.5;

// Draggable mobile panel with three snap positions. The panel always has the expanded height
// and is moved down with translateY, so the body below the visible part stays off screen.
export class BottomSheet {
    constructor(element) {
        this.el = element;
        this.handleArea = element.querySelector('.sidebar-handle-area');
        this.header = element.querySelector('.sidebar-header');
        this.body = element.querySelector('.sidebar-body');
        this.enabled = false;
        this.snap = 'half';
        this.drag = null;
        this.suppressClick = false;

        this.onPointerDown = this.onPointerDown.bind(this);
        this.onPointerMove = this.onPointerMove.bind(this);
        this.onPointerUp = this.onPointerUp.bind(this);
        this.onClickCapture = this.onClickCapture.bind(this);
        this.refresh = this.refresh.bind(this);
    }

    enable() {
        if (this.enabled) return;
        this.enabled = true;
        this.el.addEventListener('pointerdown', this.onPointerDown);
        // A drag that ends over a link must not open it
        this.el.addEventListener('click', this.onClickCapture, true);
        window.addEventListener('resize', this.refresh);
        this.setSnap(this.snap);
    }

    disable() {
        if (!this.enabled) return;
        this.enabled = false;
        this.el.removeEventListener('pointerdown', this.onPointerDown);
        this.el.removeEventListener('click', this.onClickCapture, true);
        window.removeEventListener('resize', this.refresh);
        this.stopDrag();
        this.el.classList.remove('is-dragging');
        this.el.style.removeProperty('--sheet-offset');
        this.el.style.removeProperty('--sheet-height');
        delete this.el.dataset.snap;
    }

    // Recalculate the position: the header height depends on the content, the panel height on the viewport
    refresh() {
        if (this.enabled) {
            this.setSnap(this.snap);
        }
    }

    getHeight() {
        return window.innerHeight - EXPANDED_TOP_GAP;
    }

    getOffsets() {
        const height = this.getHeight();
        const collapsedVisible = this.handleArea.offsetHeight + this.header.offsetHeight;
        const halfVisible = Math.round(window.innerHeight * MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO);
        return {
            expanded: 0,
            half: Math.max(0, height - halfVisible),
            collapsed: Math.max(0, height - collapsedVisible)
        };
    }

    setSnap(snap) {
        this.snap = snap;
        this.el.dataset.snap = snap;
        this.el.style.setProperty('--sheet-height', `${this.getHeight()}px`);
        if (snap !== 'expanded') {
            this.body.scrollTop = 0;
        }
        this.setOffset(this.getOffsets()[snap]);
    }

    setOffset(offset) {
        this.el.style.setProperty('--sheet-offset', `${offset}px`);
    }

    moveTo(snap) {
        if (this.enabled && this.snap !== snap) {
            this.setSnap(snap);
        }
    }

    collapse() {
        this.moveTo('collapsed');
    }

    toggle() {
        const next = { collapsed: 'half', half: 'expanded', expanded: 'half' };
        this.setSnap(next[this.snap]);
    }

    onPointerDown(e) {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        this.suppressClick = false;

        const fromHeader = this.handleArea.contains(e.target) || this.header.contains(e.target);
        // In the expanded state the body scrolls, so only the handle and the header drag the panel
        if (!fromHeader && this.snap === 'expanded') return;

        const offsets = this.getOffsets();
        this.drag = {
            fromHeader,
            offsets,
            startY: e.clientY,
            startOffset: offsets[this.snap],
            offset: offsets[this.snap],
            lastY: e.clientY,
            lastTime: e.timeStamp,
            velocity: 0,
            moved: false
        };
        window.addEventListener('pointermove', this.onPointerMove);
        window.addEventListener('pointerup', this.onPointerUp);
        window.addEventListener('pointercancel', this.onPointerUp);
    }

    onPointerMove(e) {
        const d = this.drag;
        if (!d) return;

        const dy = e.clientY - d.startY;
        if (!d.moved) {
            if (Math.abs(dy) < DRAG_THRESHOLD) return;
            d.moved = true;
            this.el.classList.add('is-dragging');
        }

        d.offset = Math.min(Math.max(d.startOffset + dy, 0), d.offsets.collapsed);
        this.setOffset(d.offset);

        const dt = e.timeStamp - d.lastTime;
        if (dt > 0) {
            d.velocity = (e.clientY - d.lastY) / dt;
        }
        d.lastY = e.clientY;
        d.lastTime = e.timeStamp;
    }

    onPointerUp(e) {
        const d = this.drag;
        this.stopDrag();
        if (!d) return;

        if (!d.moved) {
            if (e.type === 'pointerup' && d.fromHeader && !e.target.closest('button, a')) {
                this.toggle();
            }
            return;
        }

        this.el.classList.remove('is-dragging');
        this.suppressClick = true;
        this.setSnap(this.pickSnap(d.offset, d.velocity, d.offsets));
    }

    // A fast flick goes to the next position in its direction, otherwise the nearest position wins
    pickSnap(offset, velocity, offsets) {
        const points = SNAP_ORDER.map(name => ({ name, offset: offsets[name] }));
        let candidates = points;
        if (Math.abs(velocity) > FLICK_VELOCITY) {
            const ahead = points.filter(p => velocity > 0 ? p.offset > offset : p.offset < offset);
            if (ahead.length) candidates = ahead;
        }
        return candidates.reduce((best, p) =>
            Math.abs(p.offset - offset) < Math.abs(best.offset - offset) ? p : best
        ).name;
    }

    stopDrag() {
        this.drag = null;
        window.removeEventListener('pointermove', this.onPointerMove);
        window.removeEventListener('pointerup', this.onPointerUp);
        window.removeEventListener('pointercancel', this.onPointerUp);
    }

    onClickCapture(e) {
        if (this.suppressClick) {
            this.suppressClick = false;
            e.preventDefault();
            e.stopPropagation();
        }
    }
}
