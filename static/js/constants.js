export const MAPTILER_API_KEY = 'KxWbLysHDIRHxmljrz4c';

// Map bounds which user can see
export const GLOBAL_MAP_BOUNDS = [
    [38.045410, 38.724089], // south-west corner [lon, lat]
    [53.273682, 44.150681]  // north-east corner [lon, lat]
];

// The main page panel covers the lower part of the map on mobile and the left part on desktop. maxBounds
// limits the whole viewport, panel included, so to show the south (Yerevan, Baku) or the west (Batumi)
// next to the panel the map has to be able to scroll further south and west
export const MAIN_PAGE_MAP_BOUNDS = [
    [34.0, 34.0],
    GLOBAL_MAP_BOUNDS[1]
];

// Georgian part of the network with the POIs (Abkhazia to Kakheti, Kars line to Zugdidi), fitted on
// the main page on desktop so that the western stations are not under the panel
export const GEORGIA_NETWORK_BOUNDS = [
    [41.3, 41.2],
    [45.7, 42.8]
];

export const DEFAULT_MAP_CENTER = [44.799748, 41.721700]; // [lon, lat]

export const DEFAULT_MAP_ZOOM = 7;

export const DESKTOP_THRESHOLD = 768;

export const DESKTOP_BOUNDS_PADDING = 30;

export const MOBILE_BOUNDS_PADDING = 30;

export const ANIMATION_DURATION = 500;

// Visible height of the mobile panel in its "half" position, which it takes when a station or a train is selected
export const MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO = 0.46;

// Width of the panel column on the left of the main page map (see sidebar.css)
export const DESKTOP_SIDEBAR_WIDTH_IN_PIXELS = 420;