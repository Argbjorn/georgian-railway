import { Poi, poiInfo } from "./poi.js"

export class PoiGroup {
    constructor(map) {
        this.map = map;
        this.pois = poiInfo.map((poi, index) => new Poi(this.map, poi, index))
    }

    show() {
        this.pois.forEach(poi => poi.show())
    }

    hide() {
        this.pois.forEach(poi => poi.hide())
    }
}