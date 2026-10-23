import stateManager from "../../state/mapStateManager.js";
import { SidebarContent } from "./SidebarContent.js";
import { InteractiveRoute } from "../route/InteractiveRoute.js";
import { BottomSheet } from "./BottomSheet.js";
import { routes } from "../route/routes-list.js";
import { findLine } from "../route/routeLines.js";

class Sidebar {
    constructor(map, container, stationsGroup) {
        this.map = map;
        this.container = container;
        this.stationsGroup = stationsGroup;
        this.sidebar = null;

        // Only user gestures have originalEvent; camera moves started by code (fitBounds, easeTo) don't
        this.map.on('movestart', e => {
            if (e.originalEvent) {
                this.sheet?.collapse();
            }
        });

        stateManager.subscribe(state => this.onStateChange(state));
        // The device type is set before the map is created, so render the initial state explicitly
        this.onStateChange(stateManager.state);
    }

    onStateChange(state) {
        // On mobile the panel is always on screen: with nothing selected it shows the default content
        if (state.deviceType === 'mobile') {
            this.show();
            this.updateContent();
            this.sheet.enable();
            this.sheet.refresh();
        }

        if (state.deviceType === 'desktop') {
            this.sheet?.disable();
            if (state.selectedRoute || state.selectedStation) {
                this.show();
                this.updateContent();
            } else {
                this.close();
            }
        }
    }

    // Show sidebar
    show() {
        if (!this.sidebar) {
            this.create();
        }
        this.sidebar.classList.add('active');
        this.sidebar.classList.remove('collapsed-auto');
    }

    // Close sidebar
    close() {
        if (this.sidebar) {
            this.sidebar.classList.remove('active', 'collapsed-auto');
        }
    }

    // Update sidebar content
    updateContent() {
        if (!this.sidebar) return;
        let sidebarContent;
        if (stateManager.selectedRoute) {
            sidebarContent = new SidebarContent(stateManager.selectedRoute, 'route');
        } else if (stateManager.selectedStation) {
            sidebarContent = new SidebarContent(stateManager.selectedStation, 'station');
        } else if (stateManager.selectedLine) {
            sidebarContent = new SidebarContent(stateManager.selectedLine, 'line');
        } else if (stateManager.selectedPoi) {
            sidebarContent = new SidebarContent(stateManager.selectedPoi, 'poi');
        } else {
            sidebarContent = new SidebarContent(null, 'default');
        }
        this.sidebar.classList.toggle('is-default', sidebarContent.type === 'default');
        this.sidebar.querySelector('.sidebar-back-slot').innerHTML = sidebarContent.getBackButton();
        this.sidebar.querySelector('.sidebar-title').innerHTML = sidebarContent.getTitle();
        this.sidebar.querySelector('.sidebar-subtitle').innerHTML = sidebarContent.getSubtitle();
        const body = this.sidebar.querySelector('.sidebar-body');
        body.innerHTML = '';
        body.appendChild(sidebarContent.getBody());

        // Content is re-rendered on every state change, so keep the scroll unless something else is shown
        const shownEntity = stateManager.selectedRoute || stateManager.selectedStation
            || stateManager.selectedLine || stateManager.selectedPoi;
        if (shownEntity !== this.shownEntity) {
            this.shownEntity = shownEntity;
            body.scrollTop = 0;
            // The map padding for selected objects assumes this position (see getBoundsPadding)
            if (shownEntity) {
                this.sheet?.moveTo('half');
            }
        }
    }

    // Create sidebar
    create() {
        this.createDOM();
        this.setupEvents();
        this.sheet = new BottomSheet(this.sidebar);
    }

    // Returns template for sidebar content
    getTemplate() {
        return `
            <div class="sidebar-handle-area">
                <div class="sidebar-handle"></div>
            </div>
            <div class="sidebar-header">
                <div class="sidebar-heading">
                    <div class="sidebar-back-slot"></div>
                    <h2 class="sidebar-title"></h2>
                    <div class="sidebar-subtitle"></div>
                </div>
                <button class="sidebar-close" id="sidebar-close-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="sidebar-body"></div>
        `;
    }

    createDOM() {
        this.sidebar = document.createElement('div');
        this.sidebar.id = 'sidebar';
        this.sidebar.className = 'sidebar';
        this.sidebar.innerHTML = this.getTemplate();
        document.body.appendChild(this.sidebar);
    }

    // Setup event listeners
    setupEvents() {
        const sidebarBody = this.sidebar.querySelector('.sidebar-body');
        const sidebarHeader = this.sidebar.querySelector('.sidebar-header');
        const closeButton = this.sidebar.querySelector('#sidebar-close-btn');

        // Clearing the selection closes the sidebar on desktop and returns it to the default state on mobile
        closeButton.addEventListener('click', () => {
            stateManager.clearSelectedRouteAndStation();
        });

        sidebarHeader.addEventListener('click', (e) => {
            if (e.target.closest('[data-action="back-to-train-list"]')) {
                stateManager.clearSelectedRoute();
            }
        });

        // Route click handler
        sidebarBody.addEventListener('click', async (e) => {
            const lineCard = e.target.closest('.route-line-card');
            if (lineCard) {
                const line = findLine(routes, lineCard.dataset.lineKey);
                if (line) {
                    stateManager.selectLine(line);
                }
                return;
            }

            const stationChip = e.target.closest('.station-chip');
            if (stationChip) {
                const station = this.stationsGroup.stations.find(s => s.code === stationChip.dataset.stationCode);
                if (station) {
                    stateManager.selectStation(station);
                }
                return;
            }

            // Find the route-link element (could be the clicked element or a parent)
            const routeLink = e.target.closest('.route-link');
            if (routeLink) {
                const routeRef = routeLink.getAttribute('data-route-ref');
                if (routeRef) {
                    if (stateManager.createdRoutes.find(route => route.ref === parseInt(routeRef))) {
                        stateManager.selectRoute(stateManager.createdRoutes.find(route => route.ref === parseInt(routeRef)));
                        return;
                    }
                    const route = new InteractiveRoute(this.map, routeRef);
                    stateManager.createRoute(route);
                    stateManager.selectRoute(route);
                    await route.createLayer();
                    route.show();
                }
            }
        });
    }
}

export { Sidebar }