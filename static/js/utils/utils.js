import stateManager from "../state/mapStateManager.js";
import {
  DESKTOP_BOUNDS_PADDING,
  MOBILE_BOUNDS_PADDING,
  MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO,
  DESKTOP_SIDEBAR_WIDTH_IN_PIXELS,
  ANIMATION_DURATION,
} from "../constants.js";

// fitBounds adds its padding to the map's own padding, which easeTo to a station leaves behind,
// so only the difference to the target padding is passed
export function fitBoundsClearOfSidebar(map, bounds) {
  const target = getBoundsPadding();
  const current = map.getPadding();
  map.fitBounds(bounds, {
    padding: {
      top: target.top - current.top,
      bottom: target.bottom - current.bottom,
      left: target.left - current.left,
      right: target.right - current.right,
    },
    duration: ANIMATION_DURATION,
  });
}

// Padding that keeps a selected station or route clear of the sidebar on the main page.
// A selected station or route always opens the sidebar (on mobile in its "half" position), so the
// padding uses that size rather than the current one: the map starts moving before the sidebar does.
export function getBoundsPadding() {
  if (stateManager.deviceType === "mobile") {
    return {
      top: MOBILE_BOUNDS_PADDING,
      bottom: MOBILE_BOUNDS_PADDING + window.innerHeight * MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO,
      left: MOBILE_BOUNDS_PADDING,
      right: MOBILE_BOUNDS_PADDING,
    };
  }
  if (stateManager.deviceType === "desktop") {
    return {
      top: DESKTOP_BOUNDS_PADDING,
      bottom: DESKTOP_BOUNDS_PADDING,
      left: DESKTOP_BOUNDS_PADDING + DESKTOP_SIDEBAR_WIDTH_IN_PIXELS,
      right: DESKTOP_BOUNDS_PADDING,
    };
  }
  // Route and station pages have no sidebar and don't set the device type
  return {
    top: DESKTOP_BOUNDS_PADDING,
    bottom: DESKTOP_BOUNDS_PADDING,
    left: DESKTOP_BOUNDS_PADDING,
    right: DESKTOP_BOUNDS_PADDING,
  };
}
