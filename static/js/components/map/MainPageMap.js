import { BaseMap } from "./BaseMap.js"
import { RailwayNetwork } from "../railway-network/RailwayNetwork.js"
import { InteractiveStationsGroup } from "../stations-group/InteractiveStationsGroup.js"
import { Sidebar } from "../sidebar/sidebar.js"
import { PoiGroup } from "../poi/poiGroup.js"
import { RouteLineLayer } from "../route/RouteLineLayer.js"
import stateManager from "../../state/mapStateManager.js"
import {
    MAIN_PAGE_MAP_BOUNDS,
    MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO,
    DESKTOP_SIDEBAR_WIDTH_IN_PIXELS,
    DESKTOP_BOUNDS_PADDING,
    GEORGIA_NETWORK_BOUNDS
} from "../../constants.js"

export class MainPageMap extends BaseMap {
    constructor(container) {
        super(container)
        this.railwayNetwork = new RailwayNetwork(this.map)
        this.stationsGroup = new InteractiveStationsGroup(this.map)
        this.poiGroup = new PoiGroup(this.map)
        this.routeLineLayer = new RouteLineLayer(this.map)
        this.sidebar = new Sidebar(this.map, container, this.stationsGroup)

        this.collapseAttributionOnInteraction()
        this.map.setMaxBounds(MAIN_PAGE_MAP_BOUNDS)
        // Keep the initial center in the part of the map not covered by the panel
        const isMobile = stateManager.deviceType === 'mobile'
        this.map.setPadding({
            top: 0,
            right: 0,
            left: isMobile ? 0 : DESKTOP_SIDEBAR_WIDTH_IN_PIXELS,
            bottom: isMobile ? window.innerHeight * MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO : 0
        })
        if (!isMobile) {
            // The padding above already keeps the panel clear, this one is a margin around the network
            this.map.fitBounds(GEORGIA_NETWORK_BOUNDS, { padding: DESKTOP_BOUNDS_PADDING, animate: false })
        }
    }

    // On desktop the panel covers the top left corner
    getNavigationControlPosition() {
        return stateManager.deviceType === 'mobile' ? 'top-left' : 'top-right'
    }

    // On mobile the panel covers the bottom of the map, and the attribution has to stay visible
    getAttributionControlPosition() {
        return stateManager.deviceType === 'mobile' ? 'top-right' : 'bottom-right'
    }

    // On a narrow map MapLibre shows the attribution expanded and collapses it into an icon on the
    // first drag only; collapse it on any user gesture and on any selection too
    collapseAttributionOnInteraction() {
        const collapse = () => {
            this.map.getContainer().querySelector('.maplibregl-ctrl-attrib')
                ?.classList.remove('maplibregl-compact-show')
        }
        this.map.on('movestart', e => {
            if (e.originalEvent) collapse()
        })
        stateManager.subscribe(state => {
            if (state.selectedStation || state.selectedRoute || state.selectedLine || state.selectedPoi) {
                collapse()
            }
        })
    }

    onMapLoad() {
        this.railwayNetwork.show();
        this.stationsGroup.show();
        this.poiGroup.show();
    }
}
