class MapStateManager {
    constructor() {
        this.state = {
            deviceType: null,
            selectedStation: null,
            selectedRoute: null,
            selectedRouteStations: null,
            selectedPoi: null,
            selectedLine: null,
            createdRoutes: []
        };

        this.listeners = [];
    }

    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            const index = this.listeners.indexOf(callback);
            if (index !== -1) {
                this.listeners.splice(index, 1);
            }
        }
    }

    emit(data) {
        this.listeners.forEach(callback => callback(data));
    }

    clearSelectedStation() {
        this.state = {
            ...this.state,
            selectedStation: null
        }
        this.emit(this.state);
    }

    selectStation(station) {
        try {
            this.state = {
                ...this.state,
                selectedStation: station,
                selectedPoi: null,
                selectedLine: null
            }
            this.emit(this.state);
        } catch (error) {
            console.log(error);
        }
    }

    selectRoute(route) {
        this.state = {
            ...this.state,
            selectedRoute: route
        }
        this.emit(this.state);
    }

    clearSelectedRoute() {
        this.state = {
            ...this.state,
            selectedRoute: null
        }
        this.emit(this.state);
    }

    clearSelectedRouteAndStation() {
        this.state = {
            ...this.state,
            selectedRoute: null,
            selectedStation: null,
            selectedPoi: null,
            selectedLine: null
        }
        this.emit(this.state);
    }

    // POI descriptions open in the panel instead of the station or train
    selectPoi(poi) {
        this.state = {
            ...this.state,
            selectedRoute: null,
            selectedStation: null,
            selectedPoi: poi,
            selectedLine: null
        }
        this.emit(this.state);
    }

    // A line (all trains between the same terminal stations) from the mobile panel's route list.
    // A train opened from the line keeps it selected, so "back" returns to the line
    selectLine(line) {
        this.state = {
            ...this.state,
            selectedRoute: null,
            selectedStation: null,
            selectedPoi: null,
            selectedLine: line
        }
        this.emit(this.state);
    }

    // Snapshot of what the panel shows, used by the browser history (see historySync.js)
    get selection() {
        return {
            selectedRoute: this.state.selectedRoute,
            selectedStation: this.state.selectedStation,
            selectedLine: this.state.selectedLine,
            selectedPoi: this.state.selectedPoi
        };
    }

    restoreSelection(selection) {
        this.state = {
            ...this.state,
            selectedRoute: null,
            selectedStation: null,
            selectedLine: null,
            selectedPoi: null,
            ...selection
        }
        this.emit(this.state);
    }

    createRoute(route) {
        this.state = {
            ...this.state,
            createdRoutes: [...this.state.createdRoutes, route]
        }
        this.emit(this.state);
    }

    setDeviceType(deviceType) {
        this.state = {
            ...this.state,
            deviceType: deviceType
        }
        this.emit(this.state);
    }

    get selectedStation() {
        return this.state.selectedStation;
    }

    get railwayNetwork() {
        return this.state.railwayNetwork;
    }

    get selectedRoute() {
        return this.state.selectedRoute;
    }

    get selectedLine() {
        return this.state.selectedLine;
    }

    get selectedPoi() {
        return this.state.selectedPoi;
    }

    get createdRoutes() {
        return this.state.createdRoutes;
    }

    get deviceType() {
        return this.state.deviceType;
    }

}

const stateManager = new MapStateManager();
export default stateManager;