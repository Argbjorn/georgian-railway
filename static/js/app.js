import { MainPageMap } from "./components/map/MainPageMap.js";
import stateManager from "./state/mapStateManager.js";
import { DeviceTypeDetector } from "./utils/DeviceTypeDetector.js";
import { initHistorySync } from "./state/historySync.js";

const deviceTypeDetector = new DeviceTypeDetector();
stateManager.setDeviceType(deviceTypeDetector.getDeviceType());

const map = new MainPageMap('map');
map.initialize();
initHistorySync();

window.addEventListener('resize', () => {
    const previousDeviceType = stateManager.deviceType;
    const currentDeviceType = deviceTypeDetector.getDeviceType();
    if (previousDeviceType !== currentDeviceType) {
        stateManager.setDeviceType(currentDeviceType);
    }
});