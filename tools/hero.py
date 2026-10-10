"""The hero: a split-flap departures board that spells his name, alternates the line
"Don't take my word for it" / "Check the receipts below", and lists the products boarding now.

Wide art is 1600 wide (shown at 560 to 846 px). Narrow art is 720 wide (shown at 278 to 700 px).
"""
import random
import glyphs as G
from flap import Board, tiles_width, word_multi
from anim import fit
from common import THEMES, AMBER, GREEN, SKY, housing, label, svg_doc, sheen, BLINK

PRODUCTS = [  # since = first public release (repo / npm / Marketplace), checked 10 Oct 2026
    dict(since='10 OCT', name='COUNTERSEAL', what='A second seal on irreversible agent calls', status='LIVE', color=GREEN),
    dict(since='10 OCT', name='CRA CLOCK', what='The EU CRA Article 14 clock for GitHub', status='LIVE', color=GREEN),
    dict(since='06 OCT', name='HOLDOUT', what='Phones down, together. A squad goes dark', status='BETA', color=SKY),
]
P1, P2 = "DON'T TAKE MY WORD FOR IT.", 'CHECK THE RECEIPTS BELOW.'
CYCLE = [0.8, 8.0, 15.0, 22.0, 29.0, 36.0, 43.0]   # line 2 alternates, then rests on the first phrase


def panel_face(B, S, fid, txt, font, size, color, anchor='start', pad=20):
    upm, cap, _ = G.metrics(font)
    y = S['h'] / 2 + cap * size / upm / 2
    x = pad if anchor == 'start' else S['w'] / 2
    return B.face_custom(S, fid, G.text(txt, font, size, x, y, anchor, fill=color) if txt else '')


def lamp(x, y, color, r=6):
    return (f'<circle cx="{x}" cy="{y}" r="{r*2}" fill="{color}" opacity=".16"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')


def mini_clock(cx, cy, r, T):
    """A station clock that starts at 12:00 when the page opens (second hand sweeps, stops at 12)."""
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f4f4f0" stroke="{T["label2"]}" stroke-width="1.5"/>']
    for k in range(12):
        out.append(f'<rect x="{cx-1}" y="{cy-r+2.5}" width="2" height="{r*0.22:.1f}" fill="#141516" transform="rotate({k*30} {cx} {cy})"/>')
    out.append(f'<g class="clkm"><rect x="{cx-1.4}" y="{cy-r*0.78:.1f}" width="2.8" height="{r*0.86:.1f}" rx="1" fill="#141516"/></g>')
    out.append(f'<rect x="{cx-1.6}" y="{cy-r*0.55:.1f}" width="3.2" height="{r*0.62:.1f}" rx="1" fill="#141516"/>')
    out.append(f'<g class="clks"><rect x="{cx-0.7}" y="{cy-r*0.7:.1f}" width="1.4" height="{r*0.9:.1f}" fill="#e2231a"/>'
               f'<circle cx="{cx}" cy="{cy-r*0.62:.1f}" r="{r*0.13:.1f}" fill="#e2231a"/></g>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="1.8" fill="#e2231a"/>')
    css = (f'.clkm{{transform-origin:{cx}px {cy}px;animation:clkm 3600s steps(60,end) infinite}}@keyframes clkm{{to{{transform:rotate(360deg)}}}}'
           f'.clks{{transform-origin:{cx}px {cy}px;animation:clks 60s linear infinite}}'
           '@keyframes clks{0%{transform:rotate(0)}97.5%{transform:rotate(360deg)}100%{transform:rotate(360deg)}}'
           '@media (prefers-reduced-motion:reduce){.clkm,.clks{animation:none}}')
    return ''.join(out), css


def center_pad(s, n):
    s = s.strip()
    left = (n - len(s)) // 2
    return (' ' * left + s).ljust(n)


def hero(theme, narrow=False):
    T = THEMES[theme]
    rng = random.Random(7)
    B = Board(ink='#f3efe4')
    body = []
    css_extra = ''
    if not narrow:
        W, H = 1600, 760
        body.append(housing(W, H, T, screws=True))
        body.append(label('OTTAWA, CANADA', 116, 66, 22, T['label']))
        body.append(label('COMPUTER ENGINEERING · UOTTAWA', W / 2, 66, 22, T['label2'], 'middle'))
        clk, css_extra = mini_clock(1484 - G.measure('NOW BOARDING', 'gmono500', 22, 22 * 0.12) - 70, 58, 17, T)
        body.append(clk)
        body.append(f'<circle class="blink" cx="{1484 - G.measure("NOW BOARDING", "gmono500", 22, 22 * 0.12) - 26}" cy="58" r="7" fill="{AMBER}"/>')
        body.append(label('NOW BOARDING', 1484, 66, 22, T['label'], 'end'))
        body.append(f'<rect x="64" y="100" width="{W-128}" height="1" fill="{T["rule"]}"/>')
        S1 = B.size(96, 138, r=8, fsize=96); S1['gap'] = 10
        name = 'GAUTAM KHOSLA'
        x1 = (W - tiles_width(len(name), 96, 10)) / 2
        body.append(B.word(S1, x1, 128, name, 0.6, rng, spins=3, interval=0.055))
        S2 = B.size(46, 68, r=5, fsize=44); S2['gap'] = 6
        x2 = (W - tiles_width(len(P1), 46, 6)) / 2
        body.append(word_multi(B, S2, x2, 294, [P1, P2, P1, P2, P1, P2, P1], CYCLE, rng, spins=3, interval=0.06))
        body.append(f'<rect x="64" y="396" width="{W-128}" height="1" fill="{T["rule"]}"/>')
        cols = (('SINCE', 116), ('PRODUCT', 340), ('DESTINATION', 744), ('STATUS', 1294))
        for txt, x in cols:
            body.append(label(txt, x, 438, 19, T['label2']))
        SR = B.size(30, 52, r=4, fsize=30); SR['gap'] = 4
        SD = B.size(520, 52, r=4, backing='#121315')
        SS = B.size(190, 52, r=4, backing='#121315')
        f_blank_d = panel_face(B, SD, 'db', '', 'inter500', 24, '#f3efe4')
        f_blank_s = panel_face(B, SS, 'sb', '', 'inter600', 25, '#f3efe4')
        for i, R in enumerate(PRODUCTS):
            y = 458 + i * 66
            t0 = 1.6 + i * 0.22
            ab = ''.join(sorted(set((R['since'] + R['name']).replace(' ', '')))) + 'AEO1'
            body.append(B.word(SR, 116, y, R['since'], t0, rng, spins=2, alphabet=ab))
            body.append(B.word(SR, 340, y, R['name'].ljust(11), t0 + 0.1, rng, spins=3, alphabet=ab))
            fd = panel_face(B, SD, f'dd{i}', R['what'], 'inter500', fit(R['what'], 'inter500', 24, 520 - 40), '#f3efe4')
            body.append(B.flip(SD, 744, y, [fd, f_blank_d, fd], [t0 + 0.3, t0 + 0.5]))
            fs = panel_face(B, SS, f'st{i}', R['status'], 'inter600', 25, R['color'], 'middle')
            body.append(B.flip(SS, 1294, y, [fs, f_blank_s, fs], [t0 + 0.42, t0 + 0.62]))
            body.append(lamp(1276, y + 26, R['color'], 5))
        body.append(G.text('Software you can check instead of trust. Even the failures are on the record.',
                           'iserif', 33, W / 2, 712, 'middle', fill=T['label'] if theme == 'dark' else '#34363a'))
        body.append(sheen(W, H, 26))
    else:
        W, H = 720, 1000
        body.append(housing(W, H, T, r=22, screws=True))
        body.append(label('OTTAWA, CANADA', 52, 64, 26, T['label']))
        body.append(f'<circle class="blink" cx="{668 - G.measure("NOW BOARDING", "gmono500", 26, 26 * 0.12) - 22}" cy="55" r="7" fill="{AMBER}"/>')
        body.append(label('NOW BOARDING', 668, 64, 26, T['label'], 'end'))
        body.append(f'<rect x="40" y="92" width="{W-80}" height="1" fill="{T["rule"]}"/>')
        S1 = B.size(96, 132, r=8, fsize=94); S1['gap'] = 8
        for i, word in enumerate(['GAUTAM', 'KHOSLA']):
            x = (W - tiles_width(6, 96, 8)) / 2
            body.append(B.word(S1, x, 116 + i * 146, word, 0.6 + i * 0.15, rng, spins=3, interval=0.055))
        S2 = B.size(38, 58, r=4, fsize=37); S2['gap'] = 3.5
        n = 15
        rows = [("DON'T TAKE", 'CHECK THE'), ('MY WORD FOR IT.', 'RECEIPTS BELOW.')]
        for i, (a, b2) in enumerate(rows):
            a, b2 = center_pad(a, n), center_pad(b2, n)
            x = (W - tiles_width(n, 38, 3.5)) / 2
            body.append(word_multi(B, S2, x, 430 + i * 68, [a, b2, a, b2, a, b2, a], [c + i * 0.1 for c in CYCLE], rng, spins=3, interval=0.06))
        body.append(f'<rect x="40" y="590" width="{W-80}" height="1" fill="{T["rule"]}"/>')
        body.append(label('PRODUCT', 52, 632, 22, T['label2']))
        body.append(label('STATUS', 668, 632, 22, T['label2'], 'end'))
        SR = B.size(36, 56, r=4, fsize=35); SR['gap'] = 3.6
        SS = B.size(138, 56, r=4, backing='#121315')
        f_blank_s = panel_face(B, SS, 'sb', '', 'inter600', 28, '#f3efe4')
        for i, R in enumerate(PRODUCTS):
            y = 652 + i * 70
            t0 = 1.6 + i * 0.22
            ab = ''.join(sorted(set(R['name'].replace(' ', '')))) + 'AEO1'
            body.append(B.word(SR, 52, y, R['name'].ljust(11), t0, rng, spins=3, alphabet=ab))
            fs = panel_face(B, SS, f'st{i}', R['status'], 'inter600', 28, R['color'], 'middle')
            body.append(B.flip(SS, 668 - 138, y, [fs, f_blank_s, fs], [t0 + 0.4, t0 + 0.6]))
            body.append(lamp(508, y + 28, R['color'], 5.5))
        ink = T['label'] if theme == 'dark' else '#34363a'
        body.append(G.text('Software you can check instead of trust.', 'iserif', 37, W / 2, 900, 'middle', fill=ink))
        body.append(G.text('Even the failures are on the record.', 'iserif', 37, W / 2, 946, 'middle', fill=ink))
        body.append(sheen(W, H, 22))
    style = B.style() + BLINK + css_extra
    title = "Gautam Khosla. Don't take my word for it. Check the receipts below."
    desc = ('A split-flap departure board flips to spell Gautam Khosla. The second line alternates between "Don\'t take my word for it" '
            'and "Check the receipts below". Now boarding: Counterseal, live. CRA Clock, live. Holdout, in beta.')
    return svg_doc(W, H, title, B.defs_svg() + ''.join(body), style, desc=desc)
