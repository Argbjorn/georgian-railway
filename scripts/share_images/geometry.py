# Geometry helpers for share-preview images. Everything here works on pixel coordinates
# (frame.project), except merge_lines, which matches lon/lat endpoints exactly.
from collections import defaultdict


def merge_lines(lines):
    """Joins lines that meet end to end, where exactly two line ends share a point.

    OSM splits a railway into many short ways; smoothing them one by one would leave kinks and
    gaps at every joint.
    """
    ends = defaultdict(list)
    for i, line in enumerate(lines):
        ends[tuple(line[0])].append(i)
        ends[tuple(line[-1])].append(i)

    used = set()

    def extend(chain):
        while True:
            key = tuple(chain[-1])
            if len(ends[key]) != 2:
                return chain
            following = [j for j in ends[key] if j not in used]
            if not following:
                return chain
            j = following[0]
            used.add(j)
            segment = lines[j] if tuple(lines[j][0]) == key else lines[j][::-1]
            chain = chain + segment[1:]

    merged = []
    for i, line in enumerate(lines):
        if i in used:
            continue
        used.add(i)
        chain = extend(list(line))
        merged.append(extend(chain[::-1]))
    return merged


def length(points):
    return sum(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 for (x1, y1), (x2, y2) in zip(points, points[1:]))


def resample(points, step):
    """Points evenly spaced along the polyline, both ends kept."""
    result = [points[0]]
    carried = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        seg = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        t = step - carried
        while t <= seg:
            result.append((x1 + (x2 - x1) * t / seg, y1 + (y2 - y1) * t / seg))
            t += step
        carried = seg - (t - step)
    if result[-1] != points[-1]:
        result.append(points[-1])
    return result


def smooth(points, radius):
    """Moving average over 2*radius+1 points (resample first so that is a fixed distance).

    The window shrinks towards the ends, so the end points stay in place and lines still meet
    at junctions. Unlike Douglas-Peucker, parallel tracks get the same shape and stay together.
    """
    n = len(points)
    result = []
    for i in range(n):
        k = min(radius, i, n - 1 - i)
        window = points[i - k:i + k + 1]
        result.append((sum(p[0] for p in window) / len(window), sum(p[1] for p in window) / len(window)))
    return result


def drop_stubs(lines, max_length, snap):
    """Removes short dead ends (sidings, depot tracks): lines shorter than max_length with an end
    farther than snap from every other line. Lines are lists of pixel points, densely resampled."""
    cell = max(snap, 1.0)
    grid = defaultdict(set)
    for i, line in enumerate(lines):
        for x, y in line:
            grid[(int(x // cell), int(y // cell))].add(i)

    def touches_other(i, point):
        x, y = point
        cx, cy = int(x // cell), int(y // cell)
        for gx in (cx - 1, cx, cx + 1):
            for gy in (cy - 1, cy, cy + 1):
                for j in grid.get((gx, gy), ()):
                    if j != i and any((px - x) ** 2 + (py - y) ** 2 <= snap * snap for px, py in lines[j]):
                        return True
        return False

    return [line for i, line in enumerate(lines)
            if length(line) >= max_length or (touches_other(i, line[0]) and touches_other(i, line[-1]))]


def inside(point, ring):
    """Even-odd point-in-polygon test."""
    x, y = point
    result = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            result = not result
    return result


def split_inside(points, ring):
    """Pieces of a densely resampled polyline that lie inside the ring."""
    pieces, piece = [], []
    for point in points:
        if inside(point, ring):
            piece.append(point)
        else:
            if len(piece) > 1:
                pieces.append(piece)
            piece = []
    if len(piece) > 1:
        pieces.append(piece)
    return pieces


def trim_at(lines, point, max_distance):
    """Cuts the line passing within max_distance of point there and drops the shorter side:
    OSM route relations often run on past the terminal station into the depot or yard."""
    best = None
    for li, line in enumerate(lines):
        for pi, (x, y) in enumerate(line):
            d = (x - point[0]) ** 2 + (y - point[1]) ** 2
            if d <= max_distance ** 2 and (best is None or d < best[0]):
                best = (d, li, pi)
    if best is None:
        return lines
    _, li, pi = best
    line = lines[li]
    head, tail = line[:pi + 1], line[pi:]
    kept = head if length(head) >= length(tail) else tail
    return lines[:li] + [kept] + lines[li + 1:]


def simplify(points, tolerance):
    """Douglas-Peucker for an open polyline."""
    if len(points) < 3:
        return list(points)
    (x1, y1), (x2, y2) = points[0], points[-1]
    dx, dy = x2 - x1, y2 - y1
    seg = (dx * dx + dy * dy) ** 0.5
    best_i, best_d = 0, -1.0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if seg:
            d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / seg
        else:
            d = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        if d > best_d:
            best_i, best_d = i, d
    if best_d <= tolerance:
        return [points[0], points[-1]]
    return simplify(points[:best_i + 1], tolerance)[:-1] + simplify(points[best_i:], tolerance)


def simplify_ring(points, tolerance):
    # Split the ring at its farthest point from the start so both halves are open polylines.
    start = points[0]
    far = max(range(len(points)), key=lambda i: (points[i][0] - start[0]) ** 2 + (points[i][1] - start[1]) ** 2)
    first = simplify(points[:far + 1], tolerance)
    second = simplify(points[far:] + points[:1], tolerance)
    return first[:-1] + second[:-1]


def clip_ring(points, x_min, y_min, x_max, y_max):
    """Sutherland-Hodgman clipping of a closed ring to a rectangle."""
    edges = [
        (lambda p: p[0] >= x_min, lambda a, b: _cross_x(a, b, x_min)),
        (lambda p: p[0] <= x_max, lambda a, b: _cross_x(a, b, x_max)),
        (lambda p: p[1] >= y_min, lambda a, b: _cross_y(a, b, y_min)),
        (lambda p: p[1] <= y_max, lambda a, b: _cross_y(a, b, y_max)),
    ]
    for keep, cross in edges:
        if not points:
            break
        source, points = points, []
        prev = source[-1]
        for cur in source:
            if keep(cur):
                if not keep(prev):
                    points.append(cross(prev, cur))
                points.append(cur)
            elif keep(prev):
                points.append(cross(prev, cur))
            prev = cur
    return points


def _cross_x(a, b, x):
    t = (x - a[0]) / (b[0] - a[0])
    return x, a[1] + t * (b[1] - a[1])


def _cross_y(a, b, y):
    t = (y - a[1]) / (b[1] - a[1])
    return a[0] + t * (b[0] - a[0]), y


def ring_area(points):
    return abs(sum(points[i - 1][0] * p[1] - p[0] * points[i - 1][1] for i, p in enumerate(points))) / 2
