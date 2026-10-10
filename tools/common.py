"""Shared design tokens and SVG helpers for the profile images."""
import os
import glyphs as G
from flap import esc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'assets')

# Profile chrome: a departures hall. Flaps stay dark in both themes (real boards are dark);
# the housing follows the page: night hall in dark mode, a Swiss-station grey in light mode.
THEMES = {
    'dark': dict(house0='#121316', house1='#0a0b0c', edge='rgba(255,255,255,.08)', inner='#060707',
                 label='#8d9098', label2='#5d6068', ink='#f3efe4', page='#0d1117', rule='rgba(255,255,255,.07)',
                 text='#d9d5cb'),
    'light': dict(house0='#f4f4f1', house1='#e5e6e2', edge='rgba(14,15,16,.10)', inner='#d9dad5',
                  label='#4a4d52', label2='#7d8085', ink='#f3efe4', page='#ffffff', rule='rgba(14,15,16,.08)',
                  text='#2b2d31'),
}
AMBER, GREEN, SKY, RED = '#ffb627', '#3ee08f', '#8ab4ff', '#ff4a3d'
BLINK = '.blink{animation:bl 1.6s steps(1) infinite}@keyframes bl{50%{opacity:.15}}@media (prefers-reduced-motion:reduce){.blink{animation:none}}'


def write(name, svg):
    os.makedirs(A, exist_ok=True)
    p = os.path.join(A, name)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(svg)
    return os.path.getsize(p)


def svg_doc(w, h, title, body, style='', desc=''):
    t = esc(title)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{t}">'
            f'<title>{t}</title>' + (f'<desc>{esc(desc)}</desc>' if desc else '') +
            f'<style>{style}</style>{G.take_defs()}{body}</svg>')


def housing(w, h, T, r=26, screws=False):
    out = (f'<defs><linearGradient id="hs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{T["house0"]}"/>'
           f'<stop offset="1" stop-color="{T["house1"]}"/></linearGradient>'
           f'<linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".05"/>'
           f'<stop offset=".45" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
           f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="{r}" fill="url(#hs)" stroke="{T["edge"]}"/>')
    if screws:
        for cx, cy, a in ((24, 24, 30), (w - 24, 24, -20), (24, h - 24, -40), (w - 24, h - 24, 15)):
            out += (f'<circle cx="{cx}" cy="{cy}" r="6" fill="{T["label2"]}" opacity=".55"/>'
                    f'<path d="M{cx-4} {cy}h8" stroke="{T["house1"]}" stroke-width="1.6" transform="rotate({a} {cx} {cy})"/>')
    return out


def sheen(w, h, r=26):
    return f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="{r}" fill="url(#sheen)" pointer-events="none"/>'


def label(txt, x, y, size, color, anchor='start', font='gmono500', ls=None):
    return G.text(txt, font, size, x, y, anchor, ls=(size * 0.12 if ls is None else ls), fill=color)
