"""Shared helpers for the cards: a keyframe builder and small drawing shortcuts.

Every card is a loop whose frame 0 is the finished design, so a renderer that never runs
animations (or a visitor with reduced motion) still sees the complete card.
"""
import glyphs as G


class Anim:
    """Looping keyframe classes. `off` seconds of the finished card are held at the start of
    every loop before it replays, so frame 0 is always complete."""

    def __init__(self, period, prefix='k', off=0.0):
        self.base = period
        self.off = off
        self.period = period + off
        self.css = []
        self.n = 0
        self.prefix = prefix

    def _emit(self, frames, timing, origin):
        name = f'{self.prefix}{self.n}'
        self.n += 1
        P = self.period
        body = ''.join(f'{min(100, max(0, t / P * 100)):.3f}%{{{props}}}' for t, props in frames)
        o = f';transform-origin:{origin}' if origin else ''
        self.css.append(f'@keyframes {name}{{{body}}}.{name}{{animation:{name} {P}s {timing} infinite{o}}}')
        return name

    def kf(self, frames, timing='linear', origin=None):
        """frames on the base timeline; shifted by `off` (time 0 stays 0)."""
        sh = [(0 if t == 0 else t + self.off, p) for t, p in frames]
        return self._emit(sh, timing, origin)

    def reveal(self, steps, timing='ease-out', origin=None):
        """steps: [(t, props)], first = hidden, last = final. The final state shows at frame 0,
        during the hold, and from the reveal to the end of the loop; the element vanishes just
        before its own re-entry."""
        final = steps[-1][1]
        o = self.off
        if o:
            t0 = steps[0][0]
            frames = [(0, final), (o + t0 - 0.3, final), (o + t0 - 0.12, steps[0][1])]
            frames += [(o + t, p) for t, p in steps]
            frames.append((self.period, final))
        else:
            frames = [(0, steps[0][1])] + list(steps) + [(self.period, final)]
        return self._emit(frames, timing, origin)

    def show(self, t_in, dur=0.35, dy=10):
        tr = (lambda v: f'transform:translateY({v}px);') if dy else (lambda v: '')
        return self.reveal([(t_in, f'opacity:0;{tr(dy)}'), (t_in + dur, f'opacity:1;{tr(0)}')])

    def window(self, t_on, t_off, eps=0.004):
        """Visible only in [t_on, t_off) of each loop (base timeline). Pair with style="opacity:0"."""
        return self.kf([(0, 'opacity:0'), (max(0.001, t_on - eps), 'opacity:0'), (t_on, 'opacity:1'),
                        (t_off, 'opacity:1'), (t_off + eps, 'opacity:0'), (self.base, 'opacity:0')])

    def light(self, t, dim='opacity:.18', lit='opacity:1', dur=0.18):
        """Lit at frame 0 and through the hold, dims together with the others as the replay
        starts, then lights at t (base timeline). For steps that light up in order."""
        o, P = self.off, self.period
        frames = [(0, lit), (max(0.01, o - 0.45), lit), (max(0.02, o - 0.25), dim), (o + t, dim), (o + t + dur, lit), (P, lit)]
        return self._emit(frames, 'ease-out', None)

    def style(self):
        return ''.join(self.css) + f'@media (prefers-reduced-motion:reduce){{[class^={self.prefix}]{{animation:none!important}}}}'


def g(cls, inner):
    return f'<g class="{cls}">{inner}</g>'


def frame(W, H, bg, r=28, extra_defs=''):
    return (f'<defs><clipPath id="cardclip"><rect width="{W}" height="{H}" rx="{r}"/></clipPath>{extra_defs}</defs>'
            f'<rect width="{W}" height="{H}" rx="{r}" fill="{bg}"/>')


def border(W, H, stroke, r=28):
    return f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="{r}" fill="none" stroke="{stroke}"/>'


def T(txt, font, size, x, y, fill, anchor='start', ls=0.0):
    return G.text(txt, font, size, x, y, anchor, ls=ls, fill=fill)


def mono(txt, font, size, x, y, fill, anchor='start', ls=None):
    return G.text(txt, font, size, x, y, anchor, ls=(size * 0.12 if ls is None else ls), fill=fill)


def fit(txt, font, size, maxw, ls=0.0):
    while G.measure(txt, font, size, ls) > maxw and size > 8:
        size -= 0.5
    return size


def pill(x, y, w, h, fill, stroke=None, opacity=1):
    s = f' stroke="{stroke}"' if stroke else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{fill}"{s} opacity="{opacity}"/>'


def arrow_ne(x, y, s, color, w=2.6):
    """A small north-east arrow (the 'opens a link' mark) with its box at (x, y), size s."""
    return (f'<path d="M{x} {y+s}L{x+s} {y}M{x+s*0.28} {y}H{x+s}V{y+s*0.72}" fill="none" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


def cta(x, y, label, font, size, fg, bg, h=None, pad=None, arrow=True, stroke=None):
    """A drawn button: images cannot have hover states, so the affordance has to be visible."""
    h = h or size * 2.3
    pad = pad or size * 1.05
    tw = G.measure(label, font, size)
    aw = size * 0.62 if arrow else 0
    w = pad * 2 + tw + (aw + size * 0.5 if arrow else 0)
    upm, cap, _ = G.metrics(font)
    ty = y + h / 2 + cap * size / upm / 2
    out = pill(x, y, w, h, bg, stroke)
    out += G.text(label, font, size, x + pad, ty, fill=fg)
    if arrow:
        ax = x + pad + tw + size * 0.5
        out += arrow_ne(ax, y + h / 2 - aw / 2, aw, fg, w=max(2, size * 0.09))
    return out, w
