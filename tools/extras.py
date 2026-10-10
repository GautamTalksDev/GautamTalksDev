"""The black box: the summary image of the <details> that holds the pre-registered experiments.
The recorder is a still from the WITNESS flight recorder render (WITNESS is now part of Counterseal)."""
from common import svg_doc
from anim import frame, border, T, mono, fit, pill
from cards import data_uri


def blackbox(narrow=False):
    bg, text, dim, orange = '#0a0a0b', '#f2f0eb', '#a8a59e', '#ff5b14'
    W, H = (720, 830) if narrow else (1600, 440)
    stripes = ''.join(f'<path d="M{x} 0l-60 {H}h26l60 {-H}z" fill="#ff5b14" opacity=".06"/>'
                      for x in (range(1120, 1700, 46) if not narrow else range(360, 800, 46)))
    defs = '<radialGradient id="bbg" cx=".76" cy=".55" r=".5"><stop offset="0" stop-color="#ff5b14" stop-opacity=".2"/><stop offset="1" stop-color="#ff5b14" stop-opacity="0"/></radialGradient>'
    b = [frame(W, H, bg, r=24, extra_defs=defs), f'<g clip-path="url(#cardclip)"><rect width="{W}" height="{H}" fill="url(#bbg)"/>{stripes}']
    rec = data_uri('recorder.webp')
    if narrow:
        b.append(f'<image href="{rec}" x="150" y="448" width="520" height="368"/></g>')
        L = 52
        b.append(f'<circle cx="{L+6}" cy="64" r="7" fill="{orange}"/>')
        b.append(mono('FLIGHT RECORDER · DO NOT OPEN', 'b612mono', 24, L + 26, 72, orange))
        b.append(T('Open the', 'manrope700', 76, L - 3, 170, text, ls=-2))
        b.append(T('black box.', 'manrope700', 76, L - 3, 252, text, ls=-2))
        for i, ln in enumerate(['Every experiment inside had a pass', 'or fail rule, written down first.']):
            b.append(T(ln, 'manrope500', 29, L, 316 + i * 40, dim))
        b.append(pill(L, 392, 290, 62, 'none', orange, 1))
        b.append(f'<path d="M{L+26} 412l16 11-16 11z" fill="{orange}"/>')
        b.append(mono('TAP TO OPEN', 'b612mono', 24, L + 58, 432, text, ls=3))
    else:
        b.append(f'<image href="{rec}" x="1012" y="24" width="560" height="396"/></g>')
        L = 80
        b.append(f'<circle cx="{L+6}" cy="92" r="6.5" fill="{orange}"/>')
        b.append(mono('FLIGHT RECORDER · DO NOT OPEN', 'b612mono', 21, L + 24, 100, orange))
        b.append(T('Open the black box.', 'manrope700', 80, L - 4, 204, text, ls=-2))
        b.append(T('Every experiment inside had a pass or fail rule, written down in advance.', 'manrope500', 27, L, 266, dim))
        b.append(T('This is how each one ended. Crashes included.', 'manrope500', 27, L, 304, dim))
        b.append(pill(L, 342, 290, 54, 'none', orange, 1))
        b.append(f'<path d="M{L+24} 359l14 10-14 10z" fill="{orange}"/>')
        b.append(mono('CLICK TO OPEN', 'b612mono', 20, L + 52, 377, text, ls=3))
    b.append(border(W, H, 'rgba(255,255,255,.08)', r=24))
    return svg_doc(W, H, 'Open the black box: five experiments, each judged by a pass or fail rule written down in advance. Click to open.', ''.join(b))


def build_all():
    return [('blackbox.svg', blackbox()), ('blackbox-n.svg', blackbox(narrow=True))]
