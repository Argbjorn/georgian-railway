import { BaseMap } from "./BaseMap.js"
import { RailwayNetwork } from "../railway-network/RailwayNetwork.js"
import { InteractiveStationsGroup } from "../stations-group/InteractiveStationsGroup.js"
import { Sidebar } from "../sidebar/sidebar.js"
import { PoiGroup } from "../poi/poiGroup.js"
import { RouteLineLayer } from "../route/RouteLineLayer.js"
import stateManager from "../../state/mapStateManager.js"
import { MOBILE_GLOBAL_MAP_BOUNDS, MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO } from "../../constants.js"

export class MainPageMap extends BaseMap {
    constructor(container) {
        super(container)
        this.railwayNetwork = new RailwayNetwork(this.map)
        this.stationsGroup = new InteractiveStationsGroup(this.map)
        this.poiGroup = new PoiGroup(this.map)
        this.routeLineLayer = new RouteLineLayer(this.map)
        this.sidebar = new Sidebar(this.map, container, this.stationsGroup)

        if (stateManager.deviceType === 'mobile') {
            this.map.setMaxBounds(MOBILE_GLOBAL_MAP_BOUNDS)
            // Keep the initial center in the part of the map above the panel
            this.map.setPadding({
                top: 0,
                right: 0,
                left: 0,
                bottom: window.innerHeight * MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO
            })
        }
    }

    onMapLoad() {
        this.railwayNetwork.show();
        this.stationsGroup.show();
        this.poiGroup.show();
    }
}