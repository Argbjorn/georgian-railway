// Train photo gallery: see layouts/shortcodes/train-gallery.html for the markup.
// Browsing is a native scroll-snap track; this script adds arrows, thumbnails, the counter
// and the fullscreen mode, which is the same gallery element switched to position: fixed.
(() => {
    let fullscreenGallery = null;

    function setup(gallery) {
        const track = gallery.querySelector('.tg-track');
        const slides = Array.from(track.children);
        const images = Array.from(gallery.querySelectorAll('.tg-img'));
        const prev = gallery.querySelector('.tg-prev');
        const next = gallery.querySelector('.tg-next');
        const counter = gallery.querySelector('.tg-counter');
        const closeButton = gallery.querySelector('.tg-close');
        const thumbsBox = gallery.querySelector('.tg-thumbs');
        const thumbs = thumbsBox ? Array.from(thumbsBox.children) : [];
        const inlineSizes = images.map((img) => img.sizes);
        let index = 0;

        function goTo(i) {
            const target = Math.max(0, Math.min(slides.length - 1, i));
            track.scrollTo({ left: target * track.clientWidth, behavior: 'instant' });
        }

        function revealThumb(thumb) {
            const left = thumb.offsetLeft;
            const right = left + thumb.offsetWidth;
            if (left < thumbsBox.scrollLeft || right > thumbsBox.scrollLeft + thumbsBox.clientWidth) {
                thumbsBox.scrollTo({
                    left: left - (thumbsBox.clientWidth - thumb.offsetWidth) / 2,
                    behavior: 'instant',
                });
            }
        }

        function update() {
            const i = Math.round(track.scrollLeft / track.clientWidth);
            if (i === index || i < 0 || i >= slides.length) return;
            index = i;
            if (prev) prev.disabled = index === 0;
            if (next) next.disabled = index === slides.length - 1;
            if (counter) counter.textContent = `${index + 1} / ${slides.length}`;
            thumbs.forEach((thumb, n) => {
                if (n === index) {
                    thumb.setAttribute('aria-current', 'true');
                    revealThumb(thumb);
                } else {
                    thumb.removeAttribute('aria-current');
                }
            });
        }

        let scheduled = false;
        track.addEventListener('scroll', () => {
            if (scheduled) return;
            scheduled = true;
            requestAnimationFrame(() => {
                scheduled = false;
                update();
            });
        }, { passive: true });

        if (prev) prev.addEventListener('click', () => goTo(index - 1));
        if (next) next.addEventListener('click', () => goTo(index + 1));
        thumbs.forEach((thumb) => {
            thumb.addEventListener('click', () => goTo(Number(thumb.dataset.index)));
        });

        // Switching layouts changes the slide width, so the current slide is re-aligned explicitly.
        function setFullscreen(on) {
            const current = index;
            gallery.classList.toggle('is-fullscreen', on);
            document.documentElement.classList.toggle('tg-lock', on);
            // Lets the browser pick a larger srcset candidate for the full-screen slot.
            images.forEach((img, n) => { img.sizes = on ? '100vw' : inlineSizes[n]; });
            goTo(current);
        }

        function open() {
            if (fullscreenGallery) return;
            setFullscreen(true);
            fullscreenGallery = api;
            // An extra history entry lets the system Back button close the fullscreen view.
            history.pushState({ trainGallery: true }, '');
            closeButton.focus({ preventScroll: true });
        }

        function close(fromHistory = false) {
            if (fullscreenGallery !== api) return;
            if (!fromHistory && history.state && history.state.trainGallery) {
                history.back(); // the popstate handler finishes the job
                return;
            }
            fullscreenGallery = null;
            setFullscreen(false);
            track.focus({ preventScroll: true });
        }

        gallery.querySelectorAll('.tg-frame').forEach((frame) => {
            frame.addEventListener('click', open);
        });
        closeButton.addEventListener('click', () => close());

        const api = {
            close,
            prev: () => goTo(index - 1),
            next: () => goTo(index + 1),
        };
    }

    window.addEventListener('popstate', () => {
        if (fullscreenGallery && !(history.state && history.state.trainGallery)) {
            fullscreenGallery.close(true);
        }
    });

    document.addEventListener('keydown', (e) => {
        if (!fullscreenGallery) return;
        if (e.key === 'Escape') fullscreenGallery.close();
        else if (e.key === 'ArrowLeft') fullscreenGallery.prev();
        else if (e.key === 'ArrowRight') fullscreenGallery.next();
        else return;
        e.preventDefault();
    });

    // After a reload in fullscreen the entry still carries our state, but the page opens inline;
    // left as is, the next close would step back onto it and never see the state change.
    if (history.state && history.state.trainGallery) history.replaceState(null, '');

    document.querySelectorAll('[data-train-gallery]').forEach(setup);
})();
