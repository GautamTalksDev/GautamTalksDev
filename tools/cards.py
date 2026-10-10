"""Product cards. Each product keeps its own world (palette, type, motion) from its own site.

Wide cards are 1600 x 800 (shown 560 to 846 px wide); narrow cards are 720 wide (278 to 700 px).
A card is one link, so it draws its own call to action: an image cannot have a hover state.
"""
import base64, math, os, random
import glyphs as G
from common import svg_doc
from anim import Anim, g, frame, border, T, mono, fit, cta

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(HERE, 'media')   # small WebP stills cut from the products' own renders


def data_uri(name):
    with open(os.path.join(MEDIA, name), 'rb') as f:
        return 'data:image/webp;base64,' + base64.b64encode(f.read()).decode()


# ==========================================================================================
# COUNTERSEAL  (site tokens: bg #08090b, ink #f5f6f7, dim #a1a5ad, lime #c8f560, warn #f5b748,
#               wax #1d5e43 / #3f9a72; Geist, Geist Mono, Instrument Serif italic)
# ==========================================================================================
PRESS = {  # cut from the press loop on counterseal.gautamkhosla.com (media/press.mp4)
    'rest': 'press-01.webp',
    'seq': ['press-15.webp', 'press-17.webp', 'press-19.webp', 'press-21.webp', 'press-23.webp', 'press-27.webp',
            'press-39.webp', 'press-41.webp', 'press-43.webp', 'press-45.webp', 'press-47.webp', 'press-49.webp', 'press-51.webp'],
    'hold': 'press-27.webp',
}


def _press(A, t0):
    """The brass seal presses the wax: a flipbook of real render frames over the resting frame (unit square)."""
    dt = 1 / 12.0
    out = [f'<image href="{data_uri(PRESS["rest"])}" width="1" height="1"/>']
    t = t0
    for name in PRESS['seq']:
        dur = dt * (6.5 if name == PRESS['hold'] else 1)
        cls = A.window(t, t + dur + 0.02)
        out.append(f'<image class="{cls}" style="opacity:0" href="{data_uri(name)}" width="1" height="1"/>')
        t += dur
    return ''.join(out), t


def counterseal(narrow=False):
    bg, ink, dim, mute, acc, warn, ok = '#08090b', '#f5f6f7', '#a1a5ad', '#80848d', '#c8f560', '#f5b748', '#4fd39a'
    A = Anim(7.5, 'c', off=2.0)
    W, H = (720, 1180) if narrow else (1600, 800)
    defs = ('<radialGradient id="cg1" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#3f9a72" stop-opacity=".26"/><stop offset="1" stop-color="#3f9a72" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="cg2" cx=".12" cy=".05" r=".8"><stop offset="0" stop-color="#c8f560" stop-opacity=".09"/><stop offset="1" stop-color="#c8f560" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="cm" cx=".5" cy=".5" r=".5"><stop offset=".6" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
            '<mask id="sm" maskContentUnits="objectBoundingBox"><rect width="1" height="1" fill="url(#cm)"/></mask>'
            '<pattern id="cgrid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="rgba(255,255,255,.03)"/></pattern>')
    b = [frame(W, H, bg, extra_defs=defs),
         f'<g clip-path="url(#cardclip)"><rect width="{W}" height="{H}" fill="url(#cgrid)"/><rect width="{W}" height="{H}" fill="url(#cg2)"/>']
    sx, sy, ss = (70, 330, 580) if narrow else (900, 36, 650)
    b.append(f'<circle cx="{sx+ss/2}" cy="{sy+ss*0.56}" r="{ss*0.5}" fill="url(#cg1)"/>')
    press, _ = _press(A, 2.0)
    b.append(f'<g transform="translate({sx} {sy}) scale({ss})"><g mask="url(#sm)">{press}</g></g></g>')
    # status chips under the seal, lit in the order the request goes through
    chips = [('428', 'HELD', warn, 1.0), ('PASSKEY', 'OK', acc, 2.35), ('204', 'SEALED', ok, 3.3)]
    cy0, cfs, cgap = (918, 24, 12) if narrow else (712, 21, 14)
    widths = [G.measure(a, 'gmono600', cfs, 1) + G.measure(bb, 'gmono500', cfs, 1) + cfs * 0.6 + 44 for a, bb, _, _ in chips]
    total = sum(widths) + cgap * (len(chips) - 1)
    cx = sx + ss / 2 - total / 2
    ch = cfs * 2.3
    upm, cap, _ = G.metrics('gmono600')
    for (a, bb, col, t), w in zip(chips, widths):
        lit = A.light(t)
        ty = cy0 + ch / 2 + cap * cfs / upm / 2
        inner = (f'<rect x="{cx:.1f}" y="{cy0}" width="{w:.1f}" height="{ch:.1f}" rx="{ch/2:.1f}" fill="{col}" fill-opacity=".10" stroke="{col}" stroke-opacity=".55"/>'
                 + G.text(a, 'gmono600', cfs, cx + 22, ty, ls=1, fill=col)
                 + G.text(bb, 'gmono500', cfs, cx + 22 + G.measure(a, 'gmono600', cfs, 1) + cfs * 0.6, ty, ls=1, fill=ink))
        b.append(g(lit, inner))
        cx += w + cgap
    if narrow:
        L = 56
        b.append(f'<circle cx="{L+6}" cy="64" r="7" fill="{acc}"/>')
        b.append(mono('COUNTERSEAL · LIVE · FREE BETA', 'gmono500', 24, L + 26, 72, mute))
        b.append(T('Every irreversible', 'geist600', 66, L - 3, 168, ink, ls=-1.8))
        b.append(T('action gets a', 'geist600', 66, L - 3, 244, ink, ls=-1.8))
        w2 = G.measure('second ', 'geist600', 66, -1.8)
        b.append(T('second ', 'geist600', 66, L - 3, 320, ink, ls=-1.8))
        b.append(T('seal.', 'iserif', 92, L - 3 + w2, 322, acc))
        for i, ln in enumerate(['Your AI agent never holds a real API key.', 'Anything it can’t take back waits for your passkey.']):
            b.append(T(ln, 'geist400', fit(ln, 'geist400', 28, W - 2 * L), L, 1018 + i * 38, dim))
        btn, bw = cta(L, 1086, 'counterseal.gautamkhosla.com', 'geist600', 26, '#0b0d05', acc, h=60)
        b.append(btn)
    else:
        L = 80
        b.append(f'<circle cx="{L+6}" cy="104" r="6.5" fill="{acc}"/>')
        b.append(mono('COUNTERSEAL · LIVE · FREE PUBLIC BETA', 'gmono500', 21, L + 24, 112, mute))
        b.append(T('Every irreversible', 'geist600', 78, L - 4, 208, ink, ls=-2.2))
        b.append(T('action gets a', 'geist600', 78, L - 4, 292, ink, ls=-2.2))
        w2 = G.measure('second ', 'geist600', 78, -2.2)
        b.append(T('second ', 'geist600', 78, L - 4, 376, ink, ls=-2.2))
        b.append(T('seal.', 'iserif', 104, L - 2 + w2, 380, acc))
        lines = ['Your AI agent never holds a real API key, and',
                 'anything it can’t take back waits for your passkey.',
                 'Every decision on a write becomes a receipt.']
        for i, ln in enumerate(lines):
            b.append(T(ln, 'geist400', 29, L, 462 + i * 42, dim))
        b.append(f'<rect x="{L}" y="606" width="720" height="1" fill="rgba(255,255,255,.08)"/>')
        b.append(mono('10 APIS · GITHUB · STRIPE · CLOUDFLARE · RAILWAY · +6', 'gmono500', 20, L, 648, mute))
        btn, bw = cta(L, 684, 'counterseal.gautamkhosla.com', 'geist600', 25, '#0b0d05', acc, h=58)
        b.append(btn)
        b.append(mono('npx counterseal login', 'gmono500', 22, L + bw + 28, 721, ink, ls=0.4))
    b.append(border(W, H, 'rgba(255,255,255,.08)'))
    title = ('Counterseal: every irreversible action gets a second seal. A brass seal presses green wax while the request goes '
             '428 held, passkey OK, 204 sealed. Opens counterseal.gautamkhosla.com.')
    return svg_doc(W, H, title, ''.join(b), A.style())


# ==========================================================================================
# CRA Clock  (Swiss station: #f3f3f1, ink #0e0f10, red #e2231a, flaps #141516, Inter)
# ==========================================================================================
def _flap_digit_loop(x, y, w, h, values, period, tag, css, defs_have, d=0.14):
    """A flap digit inside a looping period. values: [(t, char)], first t = 0. Every flip finishes
    before its nominal second, so frame 0 of every cycle is a clean, settled digit."""
    P = period
    eps = max(0.002, P * 3e-7)

    def pc(v):
        return f'{min(100.0, max(0.0, v / P * 100)):.5f}%'
    states = [values[0][1]]
    starts = [None]
    for t, ch in values[1:]:
        states.append(ch)
        starts.append(t - d)
    wrap_flip = None
    if len(states) > 1 and states[-1] == states[0]:
        wrap_flip = starts[-1]
        states.pop(); starts.pop()
    elif len(states) > 1 and values[-1][0] < P and P % 10 == 0 and P <= 3600:
        wrap_flip = P - d
    m = len(states)
    hh = h / 2
    out = [f'<g transform="translate({x} {y})"><rect width="{w}" height="{h}" rx="6" fill="#050506"/>']
    for i in range(m):
        nxt = starts[i + 1] if i + 1 < m else wrap_flip
        tf = []
        if i == 0:
            tf.append('0%{opacity:1;transform:scaleY(1)}')
        else:
            tf += ['0%{opacity:0;transform:scaleY(1)}', f'{pc(starts[i] + d/2 - eps)}{{opacity:0;transform:scaleY(1)}}',
                   f'{pc(starts[i] + d/2)}{{opacity:1;transform:scaleY(1)}}']
        if nxt is not None:
            tf += [f'{pc(nxt)}{{opacity:1;transform:scaleY(1)}}', f'{pc(nxt + d/2)}{{opacity:0;transform:scaleY(0)}}']
            if i == 0 and wrap_flip is not None and m > 1:
                tf += [f'{pc(wrap_flip + d/2 - eps)}{{opacity:0;transform:scaleY(1)}}', f'{pc(wrap_flip + d/2)}{{opacity:1;transform:scaleY(1)}}',
                       '100%{opacity:1;transform:scaleY(1)}']
            else:
                tf.append('100%{opacity:0;transform:scaleY(0)}')
        else:
            tf.append('100%{opacity:1;transform:scaleY(1)}')
        bf = []
        if i == 0:
            bf.append('0%{opacity:1;transform:scaleY(1)}')
        else:
            bf += ['0%{opacity:0;transform:scaleY(0)}', f'{pc(starts[i] + d/2)}{{opacity:1;transform:scaleY(0)}}',
                   f'{pc(starts[i] + d)}{{opacity:1;transform:scaleY(1)}}']
        if nxt is not None:
            last_wrap = (i == m - 1 and nxt == wrap_flip)
            hide_at = nxt + (d / 2 if last_wrap else d)
            bf += [f'{pc(hide_at)}{{opacity:1;transform:scaleY(1)}}', f'{pc(hide_at + eps)}{{opacity:0;transform:scaleY(1)}}']
            if i == 0 and wrap_flip is not None and m > 1:
                bf += [f'{pc(wrap_flip + d/2)}{{opacity:1;transform:scaleY(0)}}', f'{pc(min(wrap_flip + d, P))}{{opacity:1;transform:scaleY(1)}}',
                       '100%{opacity:1;transform:scaleY(1)}']
            else:
                bf.append('100%{opacity:0;transform:scaleY(1)}')
        else:
            bf.append('100%{opacity:1;transform:scaleY(1)}')
        top_name, bot_name = f'{tag}t{i}', f'{tag}b{i}'
        it = 'infinite' if P <= 3600 else '1 forwards'
        css.append(f'@keyframes {top_name}{{{"".join(tf)}}}.{top_name}{{animation:{top_name} {P}s linear {it};transform-origin:0 {hh}px}}')
        css.append(f'@keyframes {bot_name}{{{"".join(bf)}}}.{bot_name}{{animation:{bot_name} {P}s linear {it};transform-origin:0 {hh}px}}')
        ch = states[i]
        fid = f'cf{ord(ch)}'
        x_ = ' x' if i > 0 else ''
        st = ' style="opacity:0"' if i > 0 else ''
        out.append(f'<use href="#{fid}T" class="{top_name}{x_}"{st}/>')
        out.append(f'<use href="#{fid}B" class="{bot_name}{x_}"{st}/>')
        defs_have.add(ch)
    out.append('</g>')
    return ''.join(out)


def _countdown(x, y, tw, thh, gap, css, have, ink):
    """24:00:00 counting down from the moment the image loads (hours, minutes, seconds flaps)."""
    P_DAY = 86400
    out = []

    def seq_for(fn, period):
        vals, last = [], None
        for s in range(0, period):
            v = fn(s)
            if v != last:
                vals.append((s, v)); last = v
        return vals

    def hh_(s): return f'{(P_DAY - s) // 3600 if s else 24:02d}'
    digits = [('h1', lambda s: hh_(s)[0], P_DAY), ('h0', lambda s: hh_(s)[1], P_DAY), None,
              ('m1', lambda s: f'{((P_DAY - s) % 3600) // 60:02d}'[0], 3600), ('m0', lambda s: f'{((P_DAY - s) % 3600) // 60:02d}'[1], 600), None,
              ('s1', lambda s: f'{(P_DAY - s) % 60:02d}'[0], 60), ('s0', lambda s: f'{(P_DAY - s) % 60:02d}'[1], 10)]
    for dspec in digits:
        if dspec is None:
            out.append(f'<circle cx="{x+9}" cy="{y+thh*0.33}" r="5.5" fill="{ink}"/><circle cx="{x+9}" cy="{y+thh*0.67}" r="5.5" fill="{ink}"/>')
            x += 18 + gap
            continue
        tag, fn, period = dspec
        if tag in ('h1', 'h0'):
            vals = [(0, fn(0))]
            for k in range(24):
                s = 1 + k * 3600
                v = fn(s)
                if v != vals[-1][1]:
                    vals.append((s, v))
        else:
            vals = seq_for(fn, period)
        out.append(_flap_digit_loop(x, y, tw, thh, vals, period, tag, css, have))
        x += tw + gap
    return ''.join(out), x


def _digit_faces(have, tw, thh):
    fd = []
    upm, cap, _ = G.metrics('inter600')
    s_ = thh * 0.7 / upm
    for ch in sorted(have):
        adv, d = G.glyph_path(ch, 'inter600')
        gx = (tw - adv * s_) / 2
        gy = thh / 2 + cap * s_ / 2
        content = f'<path transform="translate({gx:.1f} {gy:.1f}) scale({s_:.4f})" d="{d}" fill="#f4f4f0"/>'
        fd.append(f'<g id="cf{ord(ch)}c">{content}</g>'
                  f'<g id="cf{ord(ch)}T" clip-path="url(#cft)"><rect width="{tw}" height="{thh}" fill="url(#cfT)"/><use href="#cf{ord(ch)}c"/></g>'
                  f'<g id="cf{ord(ch)}B" clip-path="url(#cfb)"><rect width="{tw}" height="{thh}" fill="url(#cfB)"/><use href="#cf{ord(ch)}c"/></g>')
    r6 = 6
    fd.append(f'<clipPath id="cft"><path d="M0 {thh/2-0.8}V{r6}Q0 0 {r6} 0H{tw-r6}Q{tw} 0 {tw} {r6}V{thh/2-0.8}Z"/></clipPath>'
              f'<clipPath id="cfb"><path d="M0 {thh/2+0.8}H{tw}V{thh-r6}Q{tw} {thh} {tw-r6} {thh}H{r6}Q0 {thh} 0 {thh-r6}Z"/></clipPath>')
    return ''.join(fd)


def _station_clock(cx, cy, R, ink, red, css):
    k_ = R / 292
    c = [f'<circle cx="{cx+10*k_:.1f}" cy="{cy+18*k_:.1f}" r="{R+26*k_:.1f}" fill="url(#shadow)"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#bez)"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{R-16*k_:.1f}" fill="#d4d6d9"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{R-22*k_:.1f}" fill="url(#face)"/>']
    for k in range(60):
        if k % 5 == 0:
            c.append(f'<rect x="{cx-7*k_:.1f}" y="{cy-R+40*k_:.1f}" width="{14*k_:.1f}" height="{52*k_:.1f}" fill="{ink}" transform="rotate({k*6} {cx} {cy})"/>')
        else:
            c.append(f'<rect x="{cx-2.6*k_:.1f}" y="{cy-R+40*k_:.1f}" width="{5.2*k_:.1f}" height="{16*k_:.1f}" fill="{ink}" transform="rotate({k*6} {cx} {cy})"/>')
    c.append(mono('CRA CLOCK', 'inter600', 16 * k_, cx, cy + 128 * k_, '#55585d', 'middle', ls=3 * k_))
    hour = f'<path d="M{cx-11*k_:.1f} {cy+56*k_:.1f}L{cx-8*k_:.1f} {cy-150*k_:.1f}H{cx+8*k_:.1f}L{cx+11*k_:.1f} {cy+56*k_:.1f}Z" fill="{ink}"/>'
    minute = f'<path d="M{cx-9*k_:.1f} {cy+64*k_:.1f}L{cx-6*k_:.1f} {cy-232*k_:.1f}H{cx+6*k_:.1f}L{cx+9*k_:.1f} {cy+64*k_:.1f}Z" fill="{ink}"/>'
    second = (f'<rect x="{cx-2.4*k_:.1f}" y="{cy-156*k_:.1f}" width="{4.8*k_:.1f}" height="{236*k_:.1f}" fill="{red}"/>'
              f'<circle cx="{cx}" cy="{cy-160*k_:.1f}" r="{22*k_:.1f}" fill="{red}"/>')
    css.append(f'.hh{{transform-origin:{cx}px {cy}px;animation:hh 43200s linear infinite}}@keyframes hh{{to{{transform:rotate(360deg)}}}}'
               f'.mh{{transform-origin:{cx}px {cy}px;animation:mh 3600s steps(60,end) infinite}}@keyframes mh{{to{{transform:rotate(360deg)}}}}'
               f'.sh{{transform-origin:{cx}px {cy}px;animation:sh 60s linear infinite}}@keyframes sh{{0%{{transform:rotate(0)}}97.5%{{transform:rotate(360deg)}}100%{{transform:rotate(360deg)}}}}')
    c.append(f'<g class="hh">{hour}</g><g class="mh">{minute}</g><g class="sh">{second}</g>')
    c.append(f'<circle cx="{cx}" cy="{cy}" r="{9*k_:.1f}" fill="{red}"/>')
    return ''.join(c)


def craclock(narrow=False):
    bg, ink, ink2, dim, red = '#f3f3f1', '#0e0f10', '#36383b', '#5f6166', '#e2231a'
    css, have, b = [], set(), []
    W, H = (720, 1180) if narrow else (1600, 800)
    defs = ('<linearGradient id="bez" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fbfbfb"/><stop offset=".45" stop-color="#b9bcc0"/>'
            '<stop offset=".55" stop-color="#e9eaec"/><stop offset="1" stop-color="#8e9196"/></linearGradient>'
            '<radialGradient id="face" cx=".45" cy=".4" r=".7"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#ececea"/></radialGradient>'
            '<radialGradient id="shadow" cx=".5" cy=".5" r=".5"><stop offset=".7" stop-color="#000" stop-opacity=".18"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="cfT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2a2c2f"/><stop offset="1" stop-color="#1d1f21"/></linearGradient>'
            '<linearGradient id="cfB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#18191b"/><stop offset="1" stop-color="#121314"/></linearGradient>')
    b.append(frame(W, H, bg, extra_defs=defs))
    css.append('.cb{animation:cbl 1s steps(1) infinite}@keyframes cbl{50%{opacity:.2}}')
    tw, thh, gap = 66, 100, 6
    if narrow:
        L = 56
        b.append(f'<circle cx="{L+6}" cy="64" r="7" fill="{red}"/>')
        b.append(mono('CRA CLOCK · LIVE · GITHUB MARKETPLACE', 'gmono500', 22, L + 26, 72, ink2))
        b.append(T('24 hours starts', 'inter700', 70, L - 3, 172, ink, ls=-2.2))
        b.append(T('the moment', 'inter700', 70, L - 3, 252, ink, ls=-2.2))
        wy = G.measure('you ', 'inter700', 70, -2.2)
        b.append(T('you ', 'inter700', 70, L - 3, 332, ink, ls=-2.2))
        b.append(T('know.', 'inter700', 70, L - 3 + wy, 332, red, ls=-2.2))
        b.append(_station_clock(W / 2, 590, 205, ink, red, css))
        b.append(f'<circle cx="{L+6}" cy="853" r="6" fill="{red}" class="cb"/>')
        b.append(mono('EARLY WARNING DUE IN', 'gmono600', 22, L + 24, 861, ink2))
        cd, _ = _countdown(L, 884, tw, thh, gap, css, have, ink)
        b.append(cd)
        ln = 'Both clocks started when you opened this page.'
        b.append(T(ln, 'iserif', fit(ln, 'iserif', 33, W - 2 * L), L, 1032, ink2))
        btn, bw = cta(L, 1072, 'Add the Action', 'inter600', 27, '#ffffff', ink, h=62)
        b.append(btn)
        b.append(mono('FREE · APACHE-2.0', 'gmono500', 22, L + bw + 24, 1111, dim))
    else:
        L = 80
        b.append(f'<circle cx="{L+6}" cy="104" r="6.5" fill="{red}"/>')
        b.append(mono('CRA CLOCK · LIVE ON GITHUB MARKETPLACE · v1.0.0', 'gmono500', 21, L + 24, 112, ink2))
        b.append(T('24 hours starts', 'inter700', 78, L - 4, 212, ink, ls=-2.4))
        wy = G.measure('the moment you ', 'inter700', 78, -2.4)
        b.append(T('the moment you ', 'inter700', 78, L - 4, 298, ink, ls=-2.4))
        b.append(T('know.', 'inter700', 78, L - 4 + wy, 298, red, ls=-2.4))
        b.append(T('Reads 12 lockfile formats, checks OSV, CISA KEV and EPSS.', 'inter500', 27, L, 372, dim))
        b.append(T('Exploited? It opens an issue with the Article 14 deadlines.', 'inter500', 27, L, 412, dim))
        b.append(f'<circle cx="{L+8}" cy="474" r="6" fill="{red}" class="cb"/>')
        b.append(mono('EARLY WARNING DUE IN', 'gmono600', 20, L + 24, 481, ink2))
        cd, _ = _countdown(L, 502, tw, thh, gap, css, have, ink)
        b.append(cd)
        b.append(T('Both clocks started when you opened this page.', 'iserif', 31, L, 660, ink2))
        btn, bw = cta(L, 692, 'Add the Action', 'inter600', 25, '#ffffff', ink, h=58)
        b.append(btn)
        b.append(mono('uses: GautamTalksDev/cra-clock@v1', 'gmono500', 21, L + bw + 26, 729, ink2, ls=0.3))
        b.append(_station_clock(1215, 400, 292, ink, red, css))
    b.append(border(W, H, 'rgba(14,15,16,.12)'))
    style = ''.join(css) + '@media (prefers-reduced-motion:reduce){*{animation:none!important}.x{display:none}}'
    body = '<defs>' + _digit_faces(have, tw, thh) + '</defs>' + ''.join(b)
    return svg_doc(W, H, 'CRA Clock: 24 hours starts the moment you know. A countdown and a station clock start when you open the page. '
                   'Opens craclock.gautamkhosla.com.', body, style)


# ==========================================================================================
# HOLDOUT  (night #0e0b14, ember #ff8a3d, Fraunces + Nunito; Ember from the app's Ember.kt)
# ==========================================================================================
def _flame(cx, bottom, w, h, sway):
    top = bottom - h
    return (f'M {cx + sway:.1f} {top:.1f} C {cx + sway + w*0.18:.1f} {top + h*0.28:.1f} {cx + w*0.58:.1f} {top + h*0.45:.1f} {cx + w*0.5:.1f} {bottom - h*0.22:.1f} '
            f'C {cx + w*0.44:.1f} {bottom + h*0.02:.1f} {cx - w*0.44:.1f} {bottom + h*0.02:.1f} {cx - w*0.5:.1f} {bottom - h*0.22:.1f} '
            f'C {cx - w*0.58:.1f} {top + h*0.45:.1f} {cx + sway - w*0.18:.1f} {top + h*0.28:.1f} {cx + sway:.1f} {top:.1f} Z')


def _ember(A, cx, base, unit):
    b = []
    sz = 0.86
    flameH = unit * 0.62 * sz
    flameW = unit * 0.4 * (0.7 + 0.3 * sz)
    b.append(f'<circle class="{A.kf([(0, "opacity:.85"), (3.6, "opacity:1"), (7.2, "opacity:.85")], timing="ease-in-out")}" cx="{cx}" cy="{base - unit*0.12}" r="{unit*0.62}" fill="url(#eg)"/>')
    logW, logH = unit * 0.62, unit * 0.075
    for rot, col in ((-11, '#6E3A20'), (11, '#8A4B2A')):
        b.append(f'<rect x="{cx-logW/2:.1f}" y="{base-logH/2:.1f}" width="{logW:.1f}" height="{logH:.1f}" rx="{logH/2:.1f}" fill="{col}" transform="rotate({rot} {cx} {base})"/>')
    sways = [0, 0.022, 0, -0.022, 0]

    def anim_d(wm, hm, bo, k, dur):
        vals = ';'.join(_flame(cx, base - unit * bo, flameW * wm, flameH * hm * (1 + 0.02 * math.sin(i)), unit * s * k) for i, s in enumerate(sways))
        return f'<animate attributeName="d" dur="{dur}s" repeatCount="indefinite" values="{vals}" calcMode="spline" keySplines="{";".join(["0.45 0 0.55 1"] * (len(sways) - 1))}"/>'
    b.append(f'<path d="{_flame(cx, base - unit*0.04, flameW, flameH, 0)}" fill="url(#eo)">{anim_d(1, 1, 0.04, 1, 1.8)}</path>')
    b.append(f'<path d="{_flame(cx, base - unit*0.05, flameW*0.66, flameH*0.7, 0)}" fill="#FFC15E">{anim_d(0.66, 0.7, 0.05, 1.3, 1.8)}</path>')
    b.append(f'<path d="{_flame(cx, base - unit*0.06, flameW*0.34, flameH*0.38, 0)}" fill="#FFF1C9" opacity=".9">{anim_d(0.34, 0.38, 0.06, 1.6, 1.8)}</path>')
    faceY = base - unit * 0.04 - flameH * 0.4
    fu = unit * (0.6 + 0.4 * sz)
    gap, ew, eh = fu * 0.075, fu * 0.026, fu * 0.036
    blink = A.kf([(0, 'transform:scaleY(1)'), (3.4, 'transform:scaleY(1)'), (3.5, 'transform:scaleY(.12)'), (3.62, 'transform:scaleY(1)'), (7.2, 'transform:scaleY(1)')],
                 origin=f'{cx}px {faceY:.1f}px')
    eyes = ''.join(f'<ellipse cx="{cx + s*gap:.1f}" cy="{faceY:.1f}" rx="{ew:.1f}" ry="{eh:.1f}" fill="#2A1408"/>' for s in (-1, 1))
    b.append(f'<g class="{blink}">{eyes}</g>')
    b.append(f'<path d="M {cx - ew*1.4:.1f} {faceY + eh*1.7:.1f} Q {cx:.1f} {faceY + eh*2.5:.1f} {cx + ew*1.4:.1f} {faceY + eh*1.7:.1f}" stroke="#2A1408" stroke-width="{fu*0.011:.1f}" stroke-linecap="round" fill="none"/>')
    for i in range(7):
        x0 = cx + (i - 3) * unit * 0.035
        delay = i * 1.0
        sp = A.kf([(0, 'opacity:0;transform:translate(0,0)'), (delay % 7.2, 'opacity:0;transform:translate(0,0)'),
                   ((delay + 0.2) % 7.2 if delay + 0.2 < 7.2 else 7.19, 'opacity:.95;transform:translate(0,-10px)'),
                   (min(7.2, delay + 2.4), f'opacity:0;transform:translate({(-1)**i * 26}px,-{unit*0.42:.0f}px)'), (7.2, 'opacity:0')], timing='ease-out')
        b.append(f'<circle class="{sp}" cx="{x0:.1f}" cy="{base - flameH*0.6:.1f}" r="{unit*0.011:.1f}" fill="#FFC15E"/>')
    return ''.join(b)


def holdout(narrow=False):
    night, text, text2, muted, ember = '#0e0b14', '#f5ede3', '#b8ac9f', '#8f8489', '#ff8a3d'
    A = Anim(7.2, 'e')
    W, H = (720, 1140) if narrow else (1600, 800)
    defs = ('<radialGradient id="eg" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ff8a3d" stop-opacity=".42"/><stop offset="1" stop-color="#ff8a3d" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="eg2" cx=".72" cy=".62" r=".55"><stop offset="0" stop-color="#ff7a3d" stop-opacity=".16"/><stop offset="1" stop-color="#ff7a3d" stop-opacity="0"/></radialGradient>'
            '<linearGradient id="eo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FF7A3D"/><stop offset="1" stop-color="#FF7A3D" stop-opacity=".85"/></linearGradient>')
    b = [frame(W, H, night, extra_defs=defs), f'<g clip-path="url(#cardclip)"><rect width="{W}" height="{H}" fill="url(#eg2)"/></g>']
    rng = random.Random(5)
    sky = (40, W - 40, 330, 520) if narrow else (760, 1580, 20, 420)
    for _ in range(40):
        x, y = rng.uniform(sky[0], sky[1]), rng.uniform(sky[2], sky[3])
        tw = A.kf([(0, 'opacity:.2'), (rng.uniform(0.5, 6.5), 'opacity:.9'), (7.2, 'opacity:.2')])
        b.append(f'<circle class="{tw}" cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(.8, 1.8):.1f}" fill="#e9e2ff"/>')
    if narrow:
        L = 56
        b.append(mono('HOLDOUT · ANDROID BETA · FREE', 'nunito700', 24, L, 74, ember, ls=2.6))
        b.append(T('Phones down.', 'fraunces600', 92, L - 4, 190, text, ls=-2))
        b.append(T('Together.', 'fraunces600', 92, L - 4, 292, ember, ls=-2))
        b.append(_ember(A, W / 2, 700, 440))
        b.append(mono('NOBODY BREAKS, EMBER BURNS BRIGHTER', 'nunito700', 23, W / 2, 796, text, 'middle', ls=2.2))
        for i, ln in enumerate(['A campfire you keep alive with your friends.', 'Everyone goes dark at the same time.', 'If anyone breaks, everyone sees.']):
            b.append(T(ln, 'nunito500', fit(ln, 'nunito500', 29, W - 2 * L), L, 872 + i * 40, text2))
        btn, bw = cta(L, 1006, 'Join the Android beta', 'nunito700', 27, '#1a0f08', ember, h=62)
        b.append(btn)
        b.append(mono('NO ACCOUNT · NO ADS · NO TRACKING', 'nunito700', 20, L, 1108, muted, ls=2.2))
    else:
        L = 80
        b.append(mono('HOLDOUT · ANDROID BETA · FREE', 'nunito700', 21, L, 112, ember, ls=3))
        b.append(T('Phones down.', 'fraunces600', 98, L - 6, 244, text, ls=-2))
        b.append(T('Together.', 'fraunces600', 98, L - 6, 356, ember, ls=-2))
        b.append(T('A campfire you keep alive with your friends.', 'nunito500', 29, L, 446, text2))
        b.append(T('Everyone goes dark at the same time.', 'nunito500', 29, L, 488, text2))
        b.append(T('If anyone breaks, everyone sees.', 'nunito500', 29, L, 530, text2))
        btn, bw = cta(L, 600, 'Join the Android beta', 'nunito700', 25, '#1a0f08', ember, h=58)
        b.append(btn)
        b.append(mono('NO ACCOUNT · NO ADS · NO TRACKING', 'nunito700', 19, L, 712, muted, ls=2.4))
        b.append(mono('YOUR PHONE IS YOUR KEY', 'nunito700', 19, L, 746, muted, ls=2.4))
        b.append(_ember(A, 1180, 640, 600))
        b.append(mono('NOBODY BREAKS, EMBER BURNS BRIGHTER', 'nunito700', 21, 1180, 732, text, 'middle', ls=2.6))
    b.append(border(W, H, 'rgba(245,237,227,.09)'))
    return svg_doc(W, H, 'Holdout: phones down, together. Ember, the campfire mascot, burns while the squad holds out. '
                   'Opens holdout.gautamkhosla.com.', ''.join(b), A.style())


def build_all():
    out = []
    for name, fn in (('counterseal', counterseal), ('cra-clock', craclock), ('holdout', holdout)):
        out.append((f'card-{name}.svg', fn()))
        out.append((f'card-{name}-n.svg', fn(narrow=True)))
    return out
