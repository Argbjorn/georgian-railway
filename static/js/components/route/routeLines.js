// Copy of LINE_NAME_CITY_PRIORITY from scripts/gtfs/config.py, keep them in sync.
// Matched against the city names in the trains' `name:en` ("Borjomi → Tbilisi").
const LINE_NAME_CITY_PRIORITY = ['Yerevan', 'Baku', 'Tbilisi', 'Batumi', 'Kutaisi'];

function nameCities(train, lang) {
    return train[`name:${lang}`].split('→').map(part => part.trim());
}

function startCode(train) {
    return train.stations[0].code;
}

function isRunning(train) {
    return train.active && train.stations && !(train.start_date && train.start_date > Date.now());
}

function makeLine(trains) {
    const [origin, destination] = nameCities(trains[0], 'en');
    const priority = LINE_NAME_CITY_PRIORITY.findIndex(city => city === origin || city === destination);
    const leadingCity = priority === -1 ? origin : LINE_NAME_CITY_PRIORITY[priority];
    return {
        trains,
        leadingCity,
        priority: priority === -1 ? LINE_NAME_CITY_PRIORITY.length : priority
    };
}

// Groups running trains into lines the same way as group_lines() in scripts/gtfs/routes.py:
// trains with the same terminal stations in either direction. Lines are ordered by the leading
// city's priority, then by the lowest train ref.
export function groupRouteLines(routes) {
    const trainsByTerminals = new Map();
    routes
        .filter(isRunning)
        .sort((a, b) => a.ref - b.ref)
        .forEach(train => {
            const key = [startCode(train), train.stations.at(-1).code].sort().join('|');
            if (!trainsByTerminals.has(key)) {
                trainsByTerminals.set(key, []);
            }
            trainsByTerminals.get(key).push(train);
        });

    return [...trainsByTerminals.values()]
        .map(makeLine)
        .sort((a, b) => a.priority - b.priority || a.trains[0].ref - b.trains[0].ref);
}

function departsFromLeadingCity(line, train) {
    return nameCities(train, 'en')[0] === line.leadingCity;
}

export function lineName(line, lang) {
    const cities = nameCities(line.trains[0], lang);
    if (!departsFromLeadingCity(line, line.trains[0])) {
        cities.reverse();
    }
    return cities.join(' — ');
}

// Directions of the line, the one from the leading city first, each with sorted departure times
export function lineDirections(line, lang) {
    const trainsByStart = new Map();
    const ordered = [...line.trains].sort((a, b) =>
        departsFromLeadingCity(line, b) - departsFromLeadingCity(line, a)
    );
    ordered.forEach(train => {
        if (!trainsByStart.has(startCode(train))) {
            trainsByStart.set(startCode(train), []);
        }
        trainsByStart.get(startCode(train)).push(train);
    });

    return [...trainsByStart.values()].map(trains => ({
        origin: nameCities(trains[0], lang)[0],
        originEn: nameCities(trains[0], 'en')[0],
        times: trains.map(train => train.stations[0].departure_time).sort()
    }));
}

// "801–804" for runs of three or more consecutive refs, "869, 870" otherwise
export function formatRefs(refs) {
    const sorted = [...refs].sort((a, b) => a - b);
    const runs = [];
    sorted.forEach(ref => {
        const run = runs.at(-1);
        if (run && ref === run.at(-1) + 1) {
            run.push(ref);
        } else {
            runs.push([ref]);
        }
    });
    return runs
        .flatMap(run => run.length >= 3 ? [`${run[0]}–${run.at(-1)}`] : run.map(String))
        .join(', ');
}
