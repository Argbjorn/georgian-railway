export class BaseStationsGroup {
    constructor(map) {
        this.map = map;
        this.stations = [];
    }

    show() {
        this.stations.forEach(station => station.show());
    }

    hide() {
        this.stations.forEach(station => station.hide());
    }

    showOnlyRouteStations(route) {
        this.showOnlyStations(route.stations.map(station => station.code));
    }

    showOnlyStations(codes) {
        this.stations.forEach(station => {
            if (codes.includes(station.code)) {
                station.show();
            } else {
                station.hide();
            }
        });
    }
}