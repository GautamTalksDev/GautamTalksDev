"""Text to SVG paths, so every image renders identically everywhere.

GitHub serves README images from raw.githubusercontent.com with a strict CSP, and an SVG
shown through <img> cannot load web fonts. So no SVG in this repo uses a font: every
letter is a path, cut from OFL fonts at build time.

Two backends:
  * fontTools (local build): reads the font files given in FONTS.
  * glyphs.json cache (CI): the GitHub Action only redraws the live card, from the cache.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'glyphs.json')

# key -> (file, variable-font location)
FONTS = {
    'inter600':   ('inter.woff2', {'wght': 600}),
    'inter500':   ('inter.woff2', {'wght': 500}),
    'inter700':   ('inter.woff2', {'wght': 700}),
    'geist400':   ('geist.woff2', {'wght': 400}),
    'geist500':   ('geist.woff2', {'wght': 500}),
    'geist600':   ('geist.woff2', {'wght': 600}),
    'gmono400':   ('geist-mono.woff2', {'wght': 400}),
    'gmono500':   ('geist-mono.woff2', {'wght': 500}),
    'gmono600':   ('geist-mono.woff2', {'wght': 600}),
    'iserif':     ('instrument-serif-italic.woff2', {}),
    'manrope700': ('manrope.woff2', {'wght': 700}),
    'manrope500': ('manrope.woff2', {'wght': 500}),
    'b612mono':   ('b612-mono.woff2', {}),
    'fraunces400': ('Fraunces[SOFT,WONK,opsz,wght].ttf', {'wght': 400, 'opsz': 96, 'SOFT': 0, 'WONK': 0}),
    'fraunces600': ('Fraunces[SOFT,WONK,opsz,wght].ttf', {'wght': 600, 'opsz': 96, 'SOFT': 0, 'WONK': 0}),
    'frauncesit': ('Fraunces-Italic[SOFT,WONK,opsz,wght].ttf', {'wght': 400, 'opsz': 96, 'SOFT': 0, 'WONK': 0}),
    'plex400':    ('IBMPlexMono-Regular.ttf', {}),
    'plex600':    ('IBMPlexMono-SemiBold.ttf', {}),
    'hanken600':  ('HankenGrotesk[wght].ttf', {'wght': 600}),
    'hanken400':  ('HankenGrotesk[wght].ttf', {'wght': 400}),
    'nunito500':  ('nunito.ttf', {'wght': 500}),
    'nunito700':  ('nunito.ttf', {'wght': 700}),
}

_fonts = {}
_cache = None
_record = {}


def _load_cache():
    global _cache
    if _cache is None:
        _cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    return _cache


class Face:
    def __init__(self, key, fontdir):
        self.key = key
        self.glyphs = {}
        if fontdir:
            from fontTools.ttLib import TTFont
            fname, loc = FONTS[key]
            f = TTFont(os.path.join(fontdir, fname))
            self.upm = f['head'].unitsPerEm
            self.cmap = f.getBestCmap()
            self.gs = f.getGlyphSet(location=loc or None)
            hhea = f['hhea']
            self.asc, self.desc = hhea.ascent, hhea.descent
            os2 = f['OS/2']
            self.cap = getattr(os2, 'sCapHeight', 0) or int(self.upm * 0.7)
            self.xh = getattr(os2, 'sxHeight', 0) or int(self.upm * 0.5)
            self.live = True
        else:
            c = _load_cache()[key]
            self.upm, self.cap, self.xh = c['upm'], c['cap'], c['xh']
            self.glyphs = {ch: tuple(v) for ch, v in c['g'].items()}
            self.live = False

    def glyph(self, ch):
        """(advance, path-in-font-units with y flipped) for one character."""
        if ch in self.glyphs:
            return self.glyphs[ch]
        if not self.live:
            raise KeyError(f'{self.key}: glyph {ch!r} not in cache; rebuild locally')
        from fontTools.pens.svgPathPen import SVGPathPen
        from fontTools.pens.transformPen import TransformPen
        gname = self.cmap.get(ord(ch))
        if gname is None:
            gname = self.cmap.get(ord('?'))
        g = self.gs[gname]
        pen = SVGPathPen(self.gs, ntos=lambda v: ('%.0f' % v))
        g.draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
        out = (g.width, pen.getCommands())
        self.glyphs[ch] = out
        _record.setdefault(self.key, set()).add(ch)
        return out


def face(key):
    if key not in _fonts:
        fontdir = os.environ.get('PROFILE_FONTS')
        _fonts[key] = Face(key, fontdir if fontdir and os.path.isdir(fontdir) else None)
    return _fonts[key]


def measure(text, key, size, ls=0.0):
    f = face(key)
    s = size / f.upm
    w = 0.0
    for i, ch in enumerate(text):
        adv, _ = f.glyph(ch)
        w += adv * s + (ls if i < len(text) - 1 else 0)
    return w


def text(txt, key, size, x, y, anchor='start', ls=0.0, fill=None, extra=''):
    """One <path> for a whole line of text. y is the baseline."""
    f = face(key)
    s = size / f.upm
    w = measure(txt, key, size, ls)
    if anchor == 'middle':
        x -= w / 2
    elif anchor == 'end':
        x -= w
    parts = []
    cx = 0.0
    for ch in txt:
        adv, d = f.glyph(ch)
        if d:
            parts.append((cx, _ref(key, ch, d)))
        cx += adv + ls / s
    if not parts:
        return ''
    body = ''.join(f'<use href="#{r}" x="{cx:.0f}"/>' if round(cx) else f'<use href="#{r}"/>' for cx, r in parts)
    fill_attr = f' fill="{fill}"' if fill else ''
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({s:.5f})"{fill_attr}{extra}>{body}</g>'


_doc = {}


def _ref(key, ch, d):
    k = (key, ch)
    if k not in _doc:
        _doc[k] = (f'q{len(_doc)}', d)
    return _doc[k][0]


def take_defs():
    """Glyph outlines used since the last call, as <defs>. Called once per SVG document."""
    if not _doc:
        return ''
    out = '<defs>' + ''.join(f'<path id="{i}" d="{d}"/>' for i, d in _doc.values()) + '</defs>'
    _doc.clear()
    return out


def glyph_path(ch, key):
    return face(key).glyph(ch)


def metrics(key):
    f = face(key)
    return f.upm, f.cap, f.xh


def save_cache(keys_full_ascii=()):
    """Write glyphs used (plus full printable ASCII for the given keys) to glyphs.json."""
    data = _load_cache()
    for key in keys_full_ascii:
        f = face(key)
        for o in range(32, 127):
            f.glyph(chr(o))
        for ch in '·→≤≥':
            try:
                f.glyph(ch)
            except Exception:
                pass
    for key, f in _fonts.items():
        if not f.live:
            continue
        entry = data.get(key, {'upm': f.upm, 'cap': f.cap, 'xh': f.xh, 'g': {}})
        entry.update({'upm': f.upm, 'cap': f.cap, 'xh': f.xh})
        if key in keys_full_ascii:
            entry['g'].update({ch: list(v) for ch, v in f.glyphs.items()})
            data[key] = entry
    with open(CACHE, 'w') as fh:
        json.dump(data, fh, separators=(',', ':'), sort_keys=True)
