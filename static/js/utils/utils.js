import stateManager from "../state/mapStateManager.js";
import {
  DESKTOP_BOUNDS_PADDING,
  MOBILE_BOUNDS_PADDING,
  MOBILE_SIDEBAR_HEIGHT_WINDOW_HEIGHT_RATIO,
  DESKTOP_SIDEBAR_WIDTH_IN_PIXELS,
} from "../constants.js";

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
      left: DESKTOP_BOUNDS_PADDING,
      right: DESKTOP_BOUNDS_PADDING + DESKTOP_SIDEBAR_WIDTH_IN_PIXELS,
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
