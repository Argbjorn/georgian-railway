import { BaseStation } from "./BaseStation.js"
import stateManager from "../../state/mapStateManager.js";

export class InteractiveStation extends BaseStation {
    constructor(map, stationData) {
        super(map, stationData)

        stateManager.subscribe((data) => {
            if (data.selectedStation === this) {
              this.setActive();
            } else if (!data.selectedRoute && data.selectedLine?.terminals.includes(this.code)) {
              // The line's thread is framed by RouteLineLayer, so the terminals don't fly to themselves
              this.marker.addClassName("active");
            } else {
              this.setDefault();
            }
          });

        this.addClickEvent();
    }

    addClickEvent() {
        const markerEl = this.marker.getElement();
        markerEl.addEventListener('click', (e) => {
            e.stopPropagation();
            stateManager.selectStation(this);
        });
      }
}   