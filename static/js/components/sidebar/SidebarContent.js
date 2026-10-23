import { LanguageService } from "../../services/LanguageService.js";
import stateManager from "../../state/mapStateManager.js";
import { fromCityForms } from "../../services/translations.js";
import { stations } from "../station/stations-list.js";
import { routes } from "../route/routes-list.js";
import { groupRouteLines, lineName, lineDirections, formatRefs } from "../route/routeLines.js";

const FEATURED_STATION_CODES = [
    'tbilisicentralstation',
    'batumicentral',
    'kutaisi1',
    'kutaisiinternationalairport',
    'borjomiparki',
    'zugdidi',
    'poti',
    'ozurgeti',
    'gori',
    'yerevan',
    'baku',
];

export class SidebarContent {
    constructor(entity, type) {
        this.entity = entity;
        this.type = type;
        this.content = document.createElement('div');
        this.currentLanguage = LanguageService.getCurrentLanguage();
    }

    generateRouteDetailsLink() {
        const baseUrl = '';
        const routeRef = this.entity.ref;
        
        if (this.currentLanguage === 'en') {
            return `${baseUrl}/routes/${routeRef}/`;
        } else {
            return `${baseUrl}/${this.currentLanguage}/routes/${routeRef}/`;
        }
    }

    generateStationDetailsLink() {
        const baseUrl = '';
        const stationCode = this.entity.code;
        
        if (this.currentLanguage === 'en') {
            return `${baseUrl}/stations/${stationCode}/`;
        } else {
            return `${baseUrl}/${this.currentLanguage}/stations/${stationCode}/`;
        }
    }

    getTitle() {
        if (this.type === 'default') {
            return LanguageService.translate('default_panel_title');
        }
        if (this.type === 'poi') {
            return this.entity.title;
        }
        if (this.type === 'line') {
            return lineName(this.entity, this.currentLanguage);
        }
        if (this.type === 'station') {
            return this.entity[`name_${this.currentLanguage}`];
        }
        if (this.type === 'route') {
            return `
                <span class="train-number-badge">${this.entity.ref}</span>
                <span>${this.entity.routeData[`name:${this.currentLanguage}`]}</span>
            `;
        }
    }

    // A train is opened from a station's or a line's train list, so "back" leads there
    getBackButton() {
        if (this.type !== 'route') return '';
        const station = stateManager.selectedStation;
        const line = stateManager.selectedLine;
        let label = LanguageService.translate('back_to_train_list');
        if (station) {
            label = station[`name_${this.currentLanguage}`] || station.name_en;
        } else if (line) {
            label = lineName(line, this.currentLanguage);
        }
        return `
            <button type="button" class="sidebar-back" data-action="back-to-train-list">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"></path></svg>
                <span>${label}</span>
            </button>
        `;
    }

    getSubtitle() {
        if (this.type === 'route') {
            return `<a href="${this.generateRouteDetailsLink()}" class="sidebar-subtitle-link" target="_blank">${LanguageService.translate('view_route_details')}</a>`;
        }
        if (this.type === 'station') {
            return `<a href="${this.generateStationDetailsLink()}" class="sidebar-subtitle-link" target="_blank">${LanguageService.translate('view_station_details')}</a>`;
        }
        if (this.type === 'line') {
            const refs = formatRefs(this.entity.trains.map(train => train.ref));
            return `<span class="sidebar-subtitle-text">${LanguageService.translate('train_number_sign')} ${refs}</span>`;
        }
        return '';
    }

    // "4 h 1 min" from travel_time "04:01"
    formatDuration(travelTime) {
        const match = /^(\d+):(\d+)$/.exec(travelTime || '');
        if (!match) return '';
        const hours = parseInt(match[1], 10);
        const minutes = parseInt(match[2], 10);
        const parts = [];
        if (hours) parts.push(`${hours} ${LanguageService.translate('hours_short')}`);
        if (minutes) parts.push(`${minutes} ${LanguageService.translate('minutes_short')}`);
        return parts.join(' ');
    }

    formatArrivalAndDuration(arrival, travelTime) {
        const parts = [];
        if (arrival && arrival !== '-') {
            parts.push(`${LanguageService.translate('arrival_at')} ${arrival}`);
        }
        const duration = this.formatDuration(travelTime);
        if (duration) {
            parts.push(`${LanguageService.translate('travel_time_label')} ${duration}`);
        }
        return parts.join(', ');
    }

    renderLineTrains() {
        return lineDirections(this.entity, this.currentLanguage).map(direction => {
            const rowsHTML = direction.trains.map(train => {
                const last = train.stations.at(-1);
                const arrival = last.arrival_time && last.arrival_time !== '-' ? last.arrival_time : last.departure_time;
                return `
                    <li>
                        <button type="button" class="route-link station-train has-meta" data-route-ref="${train.ref}">
                            <span class="station-train-time">${train.stations[0].departure_time}</span>
                            <span class="train-number-badge is-small">${train.ref}</span>
                            <span class="station-train-name">
                                ${train[`name:${this.currentLanguage}`]}
                                <span class="station-train-meta">${this.formatArrivalAndDuration(arrival, train.travel_time)}</span>
                            </span>
                        </button>
                    </li>
                `;
            }).join('');
            return `
                <div class="station-train-group">
                    <h3 class="station-train-group-title">${this.fromCityLabel(direction)}</h3>
                    <ul class="station-trains">${rowsHTML}</ul>
                </div>
            `;
        }).join('');
    }

    stationName(code) {
        const station = stations[code] || {};
        return station[`name_${this.currentLanguage}`] || station.name_en || code;
    }

    // Departure at the first station, arrival at the last one. Intermediate stations show arrival
    // when the train has both times, otherwise the only time it has (stored as departure_time)
    getStopTime(stop) {
        const hasTime = time => time && time !== '-';
        if (stop.role === 'start') {
            return stop.departure_time;
        }
        if (stop.role === 'end') {
            return hasTime(stop.arrival_time) ? stop.arrival_time : stop.departure_time;
        }
        if (this.entity.routeData.has_arrival_time && hasTime(stop.arrival_time)) {
            return stop.arrival_time;
        }
        return stop.departure_time;
    }

    renderRouteStops() {
        const currentCode = stateManager.selectedStation?.code;
        const stopsHTML = (this.entity.routeData.stations || []).map(stop => {
            const classes = ['route-stop'];
            if (stop.role !== 'middle') classes.push('is-terminal');
            if (stop.code === currentCode) classes.push('is-current');
            return `
                <li class="${classes.join(' ')}">
                    <span class="route-stop-time">${this.getStopTime(stop) || ''}</span>
                    <span class="route-stop-line" aria-hidden="true"></span>
                    <span class="route-stop-name">${this.stationName(stop.code)}</span>
                </li>
            `;
        }).join('');
        return `<ol class="route-stops">${stopsHTML}</ol>`;
    }

    getBody() {
        if (this.type === 'default') {
            const footer = document.getElementById('sidebar-default-footer');
            this.content.innerHTML = this.renderRouteLines()
                + this.renderFeaturedStations()
                + (footer ? footer.innerHTML : '');
            return this.content;
        }

        if (this.type === 'poi') {
            this.content.innerHTML = `<p class="poi-description">${this.entity.description}</p>`;
            return this.content;
        }

        if (this.type === 'line') {
            this.content.innerHTML = this.renderLineTrains();
            return this.content;
        }

        if (this.type === 'station') {
            this.content.innerHTML = '';

            // A departure board: every train you can board here (starting or passing through) in one
            // list, and trains that end their route here separately
            const routeGroups = [
                {
                    key: 'departure',
                    titleKey: 'departures',
                    routes: [...(this.entity.routes.departure || []), ...(this.entity.routes.via || [])]
                },
                {
                    key: 'arrival',
                    titleKey: 'arrivals',
                    routes: this.entity.routes.arrival || []
                }
            ];

            // Generate HTML for each group
            routeGroups.forEach(group => {
                if (group.routes.length > 0) {
                    const groupHTML = this.renderRouteGroup(group);
                    this.content.innerHTML += groupHTML;
                }
            });

            return this.content;
        }

        if (this.type === 'route') {
            this.content.innerHTML = this.renderRouteStops();
            return this.content;
        }
    }

    renderRouteLines() {
        return `
            <div class="sidebar-section">
                <h3 class="sidebar-section-title">${LanguageService.translate('routes_section_title')}</h3>
                <div class="route-line-cards">
                    ${groupRouteLines(routes).map(line => this.renderRouteLine(line)).join('')}
                </div>
            </div>
        `;
    }

    renderFeaturedStations() {
        const chipsHTML = FEATURED_STATION_CODES
            .filter(code => stations[code])
            .map(code => {
                const station = stations[code];
                const name = station[`name_${this.currentLanguage}`] || station.name_en;
                return `<button type="button" class="station-chip" data-station-code="${code}">${name}</button>`;
            })
            .join('');
        const stationsPageLink = this.currentLanguage === 'en' ? '/stations/' : `/${this.currentLanguage}/stations/`;

        return `
            <div class="sidebar-section">
                <h3 class="sidebar-section-title">${LanguageService.translate('stations_section_title')}</h3>
                <div class="station-chips">${chipsHTML}</div>
                <a href="${stationsPageLink}" class="sidebar-section-link">${LanguageService.translate('all_stations')}</a>
            </div>
        `;
    }

    fromCityLabel(direction) {
        if (this.currentLanguage === 'en') {
            return `From ${direction.origin}`;
        }
        return fromCityForms[this.currentLanguage]?.[direction.originEn] ?? `${direction.origin} →`;
    }

    renderRouteLine(line) {
        const refs = formatRefs(line.trains.map(train => train.ref));
        const directionsHTML = lineDirections(line, this.currentLanguage).map(direction => `
            <span class="route-line-origin">${this.fromCityLabel(direction)}</span>
            <span class="route-line-times">${direction.times.join(', ')}</span>
        `).join('');

        return `
            <button type="button" class="route-line-card" data-line-key="${line.key}">
                <span class="route-line-card-header">
                    <span class="route-line-name">${lineName(line, this.currentLanguage)}</span>
                    <span class="route-line-refs">${LanguageService.translate('train_number_sign')} ${refs}</span>
                </span>
                <span class="route-line-directions">${directionsHTML}</span>
            </button>
        `;
    }

    renderRouteGroup(group) {
        const groupTitle = LanguageService.translate(group.titleKey);
        
        // Sort routes by time
        const sortedRoutes = [...group.routes].filter(route => !route.start_date || route.start_date <= Date.now()).sort((a, b) => {
            const timeA = this.getTimeInfo(a, group.key);
            const timeB = this.getTimeInfo(b, group.key);
            
            // If one of the routes has no time, place it at the end
            if (!timeA && !timeB) return 0;
            if (!timeA) return 1;
            if (!timeB) return -1;
            
            // Compare time in HH:MM format
            return timeA.localeCompare(timeB);
        });
        
        const routesHTML = sortedRoutes.map(route => {
            const routeName = route[`name_${this.currentLanguage}`] || route.name_en;
            const timeInfo = this.getTimeInfo(route, group.key);
            
            return `
                <li>
                    <button type="button" class="route-link station-train" data-route-ref="${route.ref}">
                        <span class="station-train-time">${timeInfo || ''}</span>
                        <span class="train-number-badge is-small">${route.ref}</span>
                        <span class="station-train-name">${routeName}</span>
                    </button>
                </li>
            `;
        }).join('');

        return `
            <div class="station-train-group">
                <h3 class="station-train-group-title">${groupTitle}</h3>
                <ul class="station-trains">${routesHTML}</ul>
            </div>
        `;
    }

    getTimeInfo(route, groupType) {
        switch (groupType) {
            case 'departure':
                return route.departure_time && route.departure_time !== '-' ? route.departure_time : route.arrival_time;
            case 'arrival':
                return route.arrival_time && route.arrival_time !== '-' ? route.arrival_time : route.departure_time;
            default:
                return null;
        }
    }
}