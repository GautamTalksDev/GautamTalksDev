"""Vector pictograms for the hero's second row: a lightning bolt and a roller coaster.

They are plain paths (no emoji glyphs, no fonts) drawn to fill flap tiles of the board: the bolt fills one
tile, the coaster a double-wide tile. Each is drawn once in its own design units and scaled to the tile
it is given, so the wide and the narrow board share one drawing.
"""
import math
from common import AMBER, RED

INK = '#f3efe4'
BOLT_GLOW = 'bolt-glow'

# ---- lightning bolt -----------------------------------------------------------------------------
BOLT_PTS = [(29.5, 7.5), (12.0, 38.5), (22.0, 38.5), (16.5, 60.5), (34.5, 27.5), (24.5, 27.5)]
BOLT_STROKE = 2.4          # a round-joined outline in the same amber, so the corners are soft
BOLT_BOX = (12.0 - 1.2, 7.5 - 1.2, 34.5 + 1.2, 60.5 + 1.2)


def _fit(box, w, h, fill_h, fill_w=1.0):
    """Scale and offset that centre `box` (x0, y0, x1, y1) in a w x h tile, using `fill_h` of its height."""
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(h * fill_h / bh, w * fill_w / bw)
    return s, (w - bw * s) / 2 - box[0] * s, (h - bh * s) / 2 - box[1] * s


def bolt(w, h):
    """An amber lightning bolt with a soft lit-sign glow behind it, in tile-local coordinates."""
    s, ox, oy = _fit(BOLT_BOX, w, h, 0.84, 0.8)
    d = 'M' + 'L'.join(f'{x:.2f} {y:.2f}' for x, y in BOLT_PTS) + 'Z'
    return (f'<g transform="translate({ox:.2f} {oy:.2f}) scale({s:.4f})">'
            f'<circle cx="23.5" cy="34" r="28" fill="url(#{BOLT_GLOW})"/>'
            f'<path d="{d}" fill="{AMBER}" stroke="{AMBER}" stroke-width="{BOLT_STROKE}" stroke-linejoin="round"/>'
            f'</g>')


# ---- roller coaster -----------------------------------------------------------------------------
def _loop(x0, yb, b, a, n=48):
    """The loop-the-loop as a prolate trochoid: forward at the bottom, backward at the top.
    Starts at (x0, yb), the bottom of the loop, and ends 2*pi*a further right on the same height."""
    pts = []
    for i in range(n + 1):
        th = 2 * math.pi * i / n
        pts.append((x0 + a * th + b * math.sin(th), yb - b * (1 - math.cos(th))))
    return pts


def _cubic(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out


def _y_at(poly, x):
    """Height of the rail at x on the hill (single valued there, so the first crossing is the one)."""
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        if x0 <= x <= x1 and x1 > x0:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    raise ValueError(x)


TRACK = 4.2                 # rail thickness
BASE, GROUND = 56.0, 63.0   # rail height at the foot of the loop, and the ground line under the trestle
LOOP_B, LOOP_A, LOOP_X = 16.5, 2.2, 64.0   # loop radius, how far it leans forward, where it starts


def coaster(w, h):
    """A lift hill, a drop and a loop on a thin trestle, with a red car climbing the hill, in tile-local coordinates."""
    lp = _loop(LOOP_X, BASE, LOOP_B, LOOP_A)
    ex = lp[-1][0]
    foot = _cubic((5, BASE), (10.5, BASE), (12.2, 52.4), (14, 50))
    crest = _cubic((32, 26), (36.5, 20), (43, 13.5), (47, 25))
    drop = _cubic((47, 25), (51, 36.5), (53, BASE), (LOOP_X, BASE))
    hill = foot[:-1] + [(14, 50), (32, 26)] + crest[:-1] + drop
    track = (f'M5 {BASE:.0f}H7C10.5 {BASE:.0f} 12.2 52.4 14 50L32 26C36.5 20 43 13.5 47 25C51 36.5 53 {BASE:.0f} {LOOP_X:.0f} {BASE:.0f}'
             + 'L' + 'L'.join(f'{x:.2f} {y:.2f}' for x, y in lp[1:]) + f'L{ex + 13:.1f} {BASE:.0f}')
    # the car climbs the straight part of the hill, pointing up the slope
    ang = math.degrees(math.atan2(26 - 50, 32 - 14))
    t = 0.5
    cx, cy = 14 + 18 * t, 50 - 24 * t
    car = (f'<g transform="translate({cx:.2f} {cy:.2f}) rotate({ang:.2f})">'
           f'<rect x="-9" y="-11.6" width="18" height="8" rx="2.8" fill="{RED}"/>'
           f'<circle cx="-5.2" cy="-2.8" r="2" fill="{INK}"/><circle cx="5.2" cy="-2.8" r="2" fill="{INK}"/></g>')
    legs = ''.join(f'<path d="M{x} {_y_at(hill, x):.1f}V{GROUND}"/>' for x in (22, 31.5, 41))
    # bounding box of everything drawn, for centring
    box = (4 - 1.0, min(y for _, y in hill + lp) - TRACK / 2, ex + 13 + TRACK / 2 + 1.0, GROUND + 1.0)
    s, ox, oy = _fit(box, w, h, 0.86, 0.94)
    return (f'<g transform="translate({ox:.2f} {oy:.2f}) scale({s:.4f})">'
            f'<g fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" opacity=".42">{legs}<path d="M4 {GROUND}H{ex + 14:.1f}"/></g>'
            f'<path d="{track}" fill="none" stroke="{INK}" stroke-width="{TRACK}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'{car}</g>')


def defs():
    """Shared gradient for the bolt's glow (goes in the file's <defs>)."""
    return (f'<radialGradient id="{BOLT_GLOW}"><stop offset="0" stop-color="{AMBER}" stop-opacity=".30"/>'
            f'<stop offset=".55" stop-color="{AMBER}" stop-opacity=".10"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>')
