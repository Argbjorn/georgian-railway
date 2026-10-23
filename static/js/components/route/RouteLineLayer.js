import stateManager from "../../state/mapStateManager.js";
import { extractWayLines } from "./BaseRoute.js";
import { fitBoundsClearOfSidebar } from "../../utils/utils.js";

// Draws the selected line (all trains between the same terminal stations) as one thread on the map.
// The geometry is the union of all the line's trains: they may take different tracks.
export class RouteLineLayer {
    constructor(map) {
        this.map = map;
        this.loaded = new Map();
        this.shownKey = null;

        stateManager.subscribe(state => this.onStateChange(state));
    }

    async onStateChange(state) {
        // A train opened from the line draws its own route instead
        const line = state.selectedRoute ? null : state.selectedLine;
        const key = line ? line.key : null;
        if (key === this.shownKey) return;

        if (this.shownKey) {
            this.map.setLayoutProperty(this.layerId(this.shownKey), 'visibility', 'none');
        }
        this.shownKey = key;
        if (!line) return;

        const bounds = await this.load(line);
        // The selection may have changed while the geometry was loading
        if (this.shownKey !== key) return;
        this.map.setLayoutProperty(this.layerId(key), 'visibility', 'visible');
        fitBoundsClearOfSidebar(this.map, bounds);
    }

    layerId(key) {
        return `route-line-${key}`;
    }

    // Cached as a promise, so a line selected again while loading is not added twice
    load(line) {
        if (!this.loaded.has(line.key)) {
            this.loaded.set(line.key, this.addLayer(line));
        }
        return this.loaded.get(line.key);
    }

    async addLayer(line) {
        const files = await Promise.all(line.trains.map(train =>
            fetch(`/data/routes_geodata/${train.id}.json`).then(response => response.json())
        ));
        const bounds = [
            [Math.min(...files.map(f => f.bounds.minlon)), Math.min(...files.map(f => f.bounds.minlat))],
            [Math.max(...files.map(f => f.bounds.maxlon)), Math.max(...files.map(f => f.bounds.maxlat))]
        ];

        this.map.addLayer({
            id: this.layerId(line.key),
            type: 'line',
            source: {
                type: 'geojson',
                data: {
                    type: 'Feature',
                    geometry: { type: 'MultiLineString', coordinates: files.flatMap(extractWayLines) },
                    properties: {}
                }
            },
            paint: {
                'line-color': '#ff0000',
                'line-width': 3,
            },
            layout: {
                'visibility': 'none'
            }
        });

        return bounds;
    }
}
