"""Section headers and the projects departures board (one image per row, so every row is a link)."""
import random
import glyphs as G
from flap import Board, tiles_width, word_multi
from common import THEMES, AMBER, GREEN, SKY, housing, label, svg_doc, BLINK
from anim import fit

GREY, LILAC = '#a7a9b0', '#c3aaff'

HEADS = {
    'products': dict(title='PRODUCTS', sub='Now boarding', right='3 DEPARTURES', right2='EVERY CARD IS A LINK', cols=False),
    'projects': dict(title='PROJECTS', sub='En route', right='PUBLIC · LIGHTER UPKEEP', right2='EVERY ROW IS A LINK', cols=True),
}

# Static rows. DODGE's row is drawn by live.py from DODGE's own daily data.
ROWS = {
    'mcp-pin': dict(since='02 SEP', name='MCP-PIN', status='LIVE', color=GREEN,
                    what='Pins the MCP tools you approved. Blocks them if they change.',
                    what_n='Pins the MCP tools you approved. Blocks drift.',
                    meta_n='SINCE 02 SEP · NPM 0.2.3 · MIT'),
    'markd': dict(since='07 OCT', name='MARKD', status='PAUSED', color=GREY,
                  what='Signed marks for AI output (EU AI Act Art. 50). Paused.',
                  what_n='Signed marks for AI output. Paused for now.',
                  meta_n='SINCE 07 OCT · WORKS, NOT IN ACTIVE WORK'),
    'merged': dict(since='07 OCT', name='LEASH', names=['LEASH', 'WITNESS', 'SIGIL'], status='MERGED', color=LILAC,
                   what='LEASH, WITNESS and SIGIL are now one product: Counterseal.',
                   what_n='LEASH, WITNESS and SIGIL: now Counterseal.',
                   meta_n='3 PROJECTS · 1 PRODUCT'),
}


def panel_face(B, S, fid, txt, font, size, color, anchor='start', pad=22):
    upm, cap, _ = G.metrics(font)
    y = S['h'] / 2 + cap * size / upm / 2
    x = pad if anchor == 'start' else S['w'] / 2
    return B.face_custom(S, fid, G.text(txt, font, size, x, y, anchor, fill=color) if txt else '')


def lamp(x, y, color, r=5.5, blink=False):
    cls = ' class="blink"' if blink else ''
    return (f'<circle cx="{x}" cy="{y}" r="{r*2}" fill="{color}" opacity=".16"/>'
            f'<circle{cls} cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')


def header(theme, narrow=False, kind='products'):
    Hd = HEADS[kind]
    T = THEMES[theme]
    rng = random.Random(11 if kind == 'products' else 12)
    B = Board()
    body = []
    if not narrow:
        W = 1600
        H = 206 if Hd['cols'] else 156
        body.append(housing(W, H, T, r=20))
        S = B.size(60, 88, r=6, fsize=60); S['gap'] = 6
        body.append(B.word(S, 32, 34, Hd['title'], 0.5, rng, spins=3))
        body.append(G.text(Hd['sub'], 'iserif', 66, 32 + tiles_width(8, 60, 6) + 30, 104, fill=T['label']))
        body.append(label(Hd['right'], W - 36, 72, 21, T['label'], 'end'))
        body.append(label(Hd['right2'], W - 36, 108, 20, T['label2'], 'end'))
        if Hd['cols']:
            body.append(f'<rect x="32" y="150" width="{W-64}" height="1" fill="{T["rule"]}"/>')
            for txt, x in (('SINCE', 32), ('PROJECT', 280), ('DESTINATION', 642), ('STATUS', 1378)):
                body.append(label(txt, x, 186, 19, T['label2']))
    else:
        W, H = 720, 196
        body.append(housing(W, H, T, r=18))
        S = B.size(52, 76, r=5, fsize=52); S['gap'] = 5
        body.append(B.word(S, 28, 26, Hd['title'], 0.5, rng, spins=3))
        body.append(G.text(Hd['sub'], 'iserif', 48, 30, 160, fill=T['label']))
        body.append(label(Hd['right2'], W - 28, 156, 22, T['label2'], 'end'))
    title = f"{Hd['title'].title()}. {Hd['sub']}."
    return svg_doc(W, H, title, B.defs_svg() + ''.join(body), B.style() + BLINK)


def row(R, theme, narrow=False, seed=100):
    """R: since, name (final), names (optional cycle), status, color, what, what_n, meta_n."""
    T = THEMES[theme]
    rng = random.Random(seed)
    B = Board()
    t0 = 0.7
    names = R.get('names')
    body = []
    if not narrow:
        W, H = 1600, 96
        body.append(housing(W, H, T, r=14))
        S = B.size(34, 52, r=4, fsize=31); S['gap'] = 4
        ab = ''.join(sorted(set((R['since'] + ''.join(names or [R['name']])).replace(' ', '')))) + 'AEO1'
        body.append(B.word(S, 32, 22, R['since'].ljust(6), t0, rng, spins=2, alphabet=ab))
        if names:
            seq = [n.ljust(9) for n in (names * 4)] + [R['name'].ljust(9)]
            starts = [t0 + 0.1 + k * 3.2 for k in range(len(seq))]
            body.append(word_multi(B, S, 280, 22, seq, starts, rng, spins=1, alphabet=ab))
        else:
            body.append(B.word(S, 280, 22, R['name'].ljust(9), t0 + 0.1, rng, spins=3, alphabet=ab))
        SW = B.size(694, 52, r=4, backing='#121315')
        size = fit(R['what'], 'inter500', 25, 694 - 44)
        f_blank = panel_face(B, SW, 'wb', '', 'inter500', size, '#f3efe4')
        f_what = panel_face(B, SW, 'ww', R['what'], 'inter500', size, '#f3efe4')
        body.append(B.flip(SW, 642, 22, [f_what, f_blank, f_what], [t0 + 0.25, t0 + 0.45]))
        SS = B.size(190, 52, r=4, backing='#121315')
        f_sb = panel_face(B, SS, 'sb', '', 'inter600', 25, '#f3efe4')
        f_st = panel_face(B, SS, 'st', R['status'], 'inter600', 25, R['color'], 'middle')
        body.append(B.flip(SS, 1378, 22, [f_st, f_sb, f_st], [t0 + 0.35, t0 + 0.55]))
        body.append(lamp(1356, 48, R['color']))
    else:
        W, H = 720, 208
        body.append(housing(W, H, T, r=16))
        S = B.size(44, 64, r=4, fsize=40); S['gap'] = 4
        ab = ''.join(sorted(set(''.join(names or [R['name']]).replace(' ', '')))) + 'AEO1'
        if names:
            seq = [n.ljust(9) for n in (names * 4)] + [R['name'].ljust(9)]
            starts = [t0 + k * 3.2 for k in range(len(seq))]
            body.append(word_multi(B, S, 26, 24, seq, starts, rng, spins=1, alphabet=ab))
        else:
            body.append(B.word(S, 26, 24, R['name'].ljust(9), t0, rng, spins=3, alphabet=ab))
        SS = B.size(176, 64, r=4, backing='#121315')
        f_sb = panel_face(B, SS, 'sb', '', 'inter600', 28, '#f3efe4')
        f_st = panel_face(B, SS, 'st', R['status'], 'inter600', 28, R['color'], 'middle')
        body.append(B.flip(SS, W - 26 - 176, 24, [f_st, f_sb, f_st], [t0 + 0.3, t0 + 0.5]))
        body.append(lamp(W - 26 - 176 - 22, 56, R['color']))
        ink = '#e6e2d8' if theme == 'dark' else '#232528'
        size = fit(R['what_n'], 'inter500', 29, W - 52)
        body.append(G.text(R['what_n'], 'inter500', size, 28, 140, fill=ink))
        body.append(label(R['meta_n'], 28, 182, 21, T['label2']))
    nice = {'MCP-PIN': 'mcp-pin'}.get(R['name'], R['name'].title() if R['name'] != 'DODGE' else 'DODGE')
    if names:
        nice = ', '.join(names[:-1]) + ' and ' + names[-1]
    title = R.get('title') or f"{nice}: {R['what']} Status: {R['status'].lower()}."
    return svg_doc(W, H, title, B.defs_svg() + ''.join(body), B.style() + BLINK)


def build_all():
    out = []
    for th in ('dark', 'light'):
        for n in (False, True):
            sfx = f'-{th}' + ('-n' if n else '')
            for kind in HEADS:
                out.append((f'head-{kind}{sfx}.svg', header(th, n, kind)))
            for i, (slug, R) in enumerate(ROWS.items()):
                out.append((f'row-{slug}{sfx}.svg', row(R, th, n, seed=100 + i)))
    return out
