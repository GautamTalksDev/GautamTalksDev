"""A small terrain kit in plain Python (no numpy), so the nightly Action needs nothing installed.

heightfield()  a mountain on a unit square, zero at the edges, peak normalised to 1
contours()     marching squares: every level's closed loops, in plane coordinates
height_at()    bilinear lookup
"""
import math


def _smooth(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def heightfield(n, peaks, ripple=0.03, seed=1.0):
    """peaks: (x, y, amplitude, sigma_x, sigma_y). Returns an (n+1) x (n+1) grid, rows are y."""
    grid = []
    for j in range(n + 1):
        y = j / n
        row = []
        for i in range(n + 1):
            x = i / n
            v = sum(a * math.exp(-((x - px) / sx) ** 2 - ((y - py) / sy) ** 2) for px, py, a, sx, sy in peaks)
            v += ripple * (math.sin(x * 17 + seed) * math.cos(y * 13 - .7) + .6 * math.sin(x * 31 - y * 23 + seed * 2))
            w = _smooth(0, .1, x) * _smooth(0, .1, 1 - x) * _smooth(0, .1, y) * _smooth(0, .1, 1 - y)
            row.append(max(v, 0.0) * w)
        grid.append(row)
    top = max(max(r) for r in grid) or 1.0
    return [[v / top for v in r] for r in grid]


def height_at(grid, x, y):
    n = len(grid) - 1
    fx, fy = min(max(x, 0), 1) * n, min(max(y, 0), 1) * n
    i, j = min(int(fx), n - 1), min(int(fy), n - 1)
    tx, ty = fx - i, fy - j
    a, b = grid[j][i], grid[j][i + 1]
    c, d = grid[j + 1][i], grid[j + 1][i + 1]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


# marching squares: corner bits a=8 (top left), b=4 (top right), c=2 (bottom right), d=1 (bottom left)
_T, _R, _B, _L = 'T', 'R', 'B', 'L'
_CASES = {1: [(_L, _B)], 2: [(_B, _R)], 3: [(_L, _R)], 4: [(_T, _R)], 6: [(_T, _B)], 7: [(_L, _T)],
          8: [(_L, _T)], 9: [(_T, _B)], 11: [(_T, _R)], 12: [(_L, _R)], 13: [(_B, _R)], 14: [(_L, _B)]}


def contours(grid, level):
    """Closed loops (lists of (x, y) in 0..1) where the field crosses `level`. The field must be zero at the edges."""
    n = len(grid) - 1
    adj = {}

    def key(edge, i, j):
        return {'T': ('h', i, j), 'B': ('h', i, j + 1), 'L': ('v', i, j), 'R': ('v', i + 1, j)}[edge]

    for j in range(n):
        for i in range(n):
            a, b, c, d = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]
            case = (8 if a >= level else 0) | (4 if b >= level else 0) | (2 if c >= level else 0) | (1 if d >= level else 0)
            if case in (0, 15):
                continue
            if case == 5:
                segs = [(_L, _T), (_B, _R)] if (a + b + c + d) / 4 >= level else [(_L, _B), (_T, _R)]
            elif case == 10:
                segs = [(_T, _R), (_L, _B)] if (a + b + c + d) / 4 >= level else [(_L, _T), (_B, _R)]
            else:
                segs = _CASES[case]
            for e1, e2 in segs:
                k1, k2 = key(e1, i, j), key(e2, i, j)
                adj.setdefault(k1, []).append(k2)
                adj.setdefault(k2, []).append(k1)

    def point(k):
        kind, i, j = k
        if kind == 'h':
            v0, v1 = grid[j][i], grid[j][i + 1]
            t = (level - v0) / (v1 - v0) if v1 != v0 else .5
            return ((i + t) / n, j / n)
        v0, v1 = grid[j][i], grid[j + 1][i]
        t = (level - v0) / (v1 - v0) if v1 != v0 else .5
        return (i / n, (j + t) / n)

    loops, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [k for k in adj[cur] if k != prev]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            if cur == start:
                break
            if cur in seen:
                break
            seen.add(cur)
            loop.append(cur)
        if len(loop) >= 4:
            loops.append([point(k) for k in loop])
    return loops
