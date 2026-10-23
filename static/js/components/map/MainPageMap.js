import { BaseMap } from "./BaseMap.js"
import { RailwayNetwork } from "../railway-network/RailwayNetwork.js"
import { InteractiveStationsGroup } from "../stations-group/InteractiveStationsGroup.js"
import { Sidebar } from "../sidebar/sidebar.js"
import { PoiGroup } from "../poi/poiGroup.js"

export class MainPageMap extends BaseMap {
    constructor(container) {
        super(container)
        this.railwayNetwork = new RailwayNetwork(this.map)
        this.stationsGroup = new InteractiveStationsGroup(this.map)
        this.poiGroup = new PoiGroup(this.map)
        this.sidebar = new Sidebar(this.map, container, this.stationsGroup)
    }

    onMapLoad() {
        this.railwayNetwork.show();
        this.stationsGroup.show();
        this.poiGroup.show();
    }
}