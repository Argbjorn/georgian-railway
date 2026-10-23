import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM, GLOBAL_MAP_BOUNDS } from "../../constants.js"
import { LanguageService } from "../../services/LanguageService.js"

export class BaseMap {
    constructor(container) {
        this.map = new maplibregl.Map({
            container: container,
            style: this.selectTilesByLanguage(),
            center: DEFAULT_MAP_CENTER,
            zoom: DEFAULT_MAP_ZOOM,
            maxBounds: GLOBAL_MAP_BOUNDS
        })
    }

    initialize() {
        this.map.addControl(new maplibregl.NavigationControl(), this.getNavigationControlPosition());
        this.map.on('load', () => {
            this.onMapLoad();
        })
    }

    getNavigationControlPosition() {
        return 'top-left';
    }

    onMapLoad() {
    }

    selectTilesByLanguage() {
        const lang = LanguageService.getCurrentLanguage();
        switch (lang) {
            case 'en':
                return '/map_styles/osm_bright_en_v1.json';
            case 'ru':
                return '/map_styles/osm_bright_ru_v2.json';
            case 'ka':
                return '/map_styles/osm_bright_ka_v1.json';
            default:
                return '/map_styles/osm_bright_en_v1.json';
        }
    }
}

export default BaseMap