import { railwayNetworkData } from "./railway-network-data.js"
import stateManager from "../../state/mapStateManager.js"

const NETWORK_COLOR = '#32373B';
const KUKUSHKA_COLOR = '#1F5FBF';
const SHADOW_COLOR = '#808080';

export class RailwayNetwork {
    constructor(map) {
        this.map = map;
        // The Kukushka line is a separate feature with kind=kukushka (see make_railway_network_file.py);
        // in the shadow state it is greyed out together with the rest of the network
        this.brightColor = ['case', ['==', ['get', 'kind'], 'kukushka'], KUKUSHKA_COLOR, NETWORK_COLOR];
        this.isShadow = false;

        stateManager.subscribe((data) => {
            if (data.selectedRoute) {
                this.showShadow();
            } else {
                this.showBright();
            }
        });
    }

    show() {
        if (this.map.getSource('railwayNetwork')) {
            return
        }
        this.map.addSource('railwayNetwork', { type: 'geojson', data: railwayNetworkData });
        this.map.addLayer({
                  id: 'railwayNetwork',
                  type: 'line',
                  source: 'railwayNetwork',
                  paint: {
                      'line-color': this.isShadow ? SHADOW_COLOR : this.brightColor,
                      'line-width': 3
                  }
              });
    }

    showBright() {
        this.setShadow(false);
    }

    showShadow() {
        this.setShadow(true);
    }

    setShadow(isShadow) {
        if (this.isShadow === isShadow) {
            return
        }
        this.isShadow = isShadow;
        if (this.map.getLayer('railwayNetwork')) {
            this.map.setPaintProperty('railwayNetwork', 'line-color', isShadow ? SHADOW_COLOR : this.brightColor);
        }
    }
}
