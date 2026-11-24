// An inline map covered by a transparent overlay, so that the page scrolls over it, and an "Expand map"
// button that moves the map into a fullscreen container where it reacts to gestures. The markup is
// rendered by layouts/partials/map-expand-controls.html
export function makeMapExpandable(mapContainer, map) {
    const overlay = mapContainer.querySelector('.map-overlay');
    const expandBtn = mapContainer.querySelector('.map-expand-button');
    const inlineClassName = mapContainer.className;

    let isFullscreen = false;
    let originalParent = null;
    let originalNextSibling = null;
    let scrollX = 0;
    let scrollY = 0;
    // The inline map does not react to gestures, so its view only changes in fullscreen
    let inlineCenter = null;
    let inlineZoom = null;

    function enterFullscreen() {
        if (isFullscreen) return;

        // Save the scroll position first: blocking the page scroll resets it
        scrollX = window.pageXOffset || document.documentElement.scrollLeft;
        scrollY = window.pageYOffset || document.documentElement.scrollTop;
        inlineCenter = map.getCenter();
        inlineZoom = map.getZoom();

        originalParent = mapContainer.parentNode;
        originalNextSibling = mapContainer.nextSibling;

        const fullscreenContainer = document.createElement('div');
        fullscreenContainer.id = 'fullscreen-container';
        fullscreenContainer.className = 'fullscreen-container';

        // The same button as in the fullscreen gallery (layouts/shortcodes/train-gallery.html)
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'fullscreen-close';
        closeBtn.setAttribute('aria-label', expandBtn.dataset.closeLabel);
        closeBtn.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
        closeBtn.onclick = exitFullscreen;

        mapContainer.className = 'fullscreen-map-container';
        overlay.style.display = 'none';
        expandBtn.style.display = 'none';

        fullscreenContainer.appendChild(closeBtn);
        fullscreenContainer.appendChild(mapContainer);
        document.body.appendChild(fullscreenContainer);

        document.body.style.top = `-${scrollY}px`;
        document.body.style.left = `-${scrollX}px`;
        document.body.classList.add('fullscreen-open');
        document.documentElement.classList.add('fullscreen-open');

        setTimeout(() => map.resize(), 100);

        isFullscreen = true;
        document.addEventListener('keydown', handleEscape);
    }

    function exitFullscreen() {
        if (!isFullscreen) return;

        const fullscreenContainer = document.getElementById('fullscreen-container');

        mapContainer.className = inlineClassName;
        overlay.style.display = 'block';
        expandBtn.style.display = 'flex';

        if (originalNextSibling) {
            originalParent.insertBefore(mapContainer, originalNextSibling);
        } else {
            originalParent.appendChild(mapContainer);
        }
        fullscreenContainer?.remove();

        document.body.classList.remove('fullscreen-open');
        document.documentElement.classList.remove('fullscreen-open');
        document.body.style.top = '';
        document.body.style.left = '';

        setTimeout(() => window.scrollTo(scrollX, scrollY), 0);

        // Back to the view the inline map had before
        setTimeout(() => {
            map.resize();
            map.setCenter(inlineCenter);
            map.setZoom(inlineZoom);
        }, 150);

        isFullscreen = false;
        document.removeEventListener('keydown', handleEscape);
    }

    function handleEscape(e) {
        if (e.key === 'Escape') {
            exitFullscreen();
        }
    }

    expandBtn.addEventListener('click', enterFullscreen);
}
