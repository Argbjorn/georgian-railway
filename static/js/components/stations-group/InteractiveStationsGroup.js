import { BaseStationsGroup } from "./BaseStationsGroup.js"
import stateManager from "../../state/mapStateManager.js"
import { InteractiveStation } from "../station/InteractiveStation.js"
import { stations } from "../station/stations-list.js"
import { HALTS_MIN_ZOOM } from "../../constants.js"

export class InteractiveStationsGroup extends BaseStationsGroup {
    constructor(map) {
        super(map)
        this.stations = Object.values(stations).map(stationData => new InteractiveStation(this.map, stationData));
        this.showingAllStations = true;

        stateManager.subscribe((data) => {
            this.showingAllStations = !data.selectedRoute && !data.selectedLine;
            if (data.selectedRoute) {
                this.showOnlyRouteStations(data.selectedRoute.routeData);
            } else if (data.selectedLine) {
                // Trains of one line may stop at different stations, so only the terminals are shown
                this.showOnlyStations(data.selectedLine.terminals);
            } else {
                this.show();
            }
            this.updateHaltsVisibility();
        });
        this.map.on('zoom', () => this.updateHaltsVisibility());
        this.updateHaltsVisibility();
    }

    // A selected route shows its halts at any zoom, and a selected halt stays visible (CSS skips .active)
    updateHaltsVisibility() {
        this.map.getContainer().classList.toggle(
            'halts-hidden',
            this.showingAllStations && this.map.getZoom() < HALTS_MIN_ZOOM
        );
    }
}
