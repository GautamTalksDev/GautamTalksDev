"""Split-flap engine for SVG images (no JavaScript, no fonts).

A flap tile is drawn as two halves. A flip from face A to face B is:
  1. A's top half falls (scaleY 1 -> 0 around the split line), revealing B's top half underneath.
  2. B's bottom half unfolds (scaleY 0 -> 1) over A's bottom half.
Tops are stacked newest-at-the-bottom and bottoms newest-on-top, so a one-shot sequence needs
nothing but an animation-delay per element. Non-final halves carry class "x" so that
prefers-reduced-motion shows the final board immediately.
"""
import random
import glyphs as G


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;'))


class Board:
    """Collects defs and CSS for one SVG file."""

    def __init__(self, font='inter600', ink='#f3efe4', top=('#2b2d31', '#1f2124'), bot=('#1b1c1f', '#141517'), split=1.4):
        self.font = font
        self.ink = ink
        self.top, self.bot = top, bot
        self.split = split
        self.defs = []
        self.css = []
        self.have = set()
        self.ids = {}
        self.sizes = {}
        self.defs.append(
            f'<linearGradient id="fT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top[0]}"/><stop offset="1" stop-color="{top[1]}"/></linearGradient>'
            f'<linearGradient id="fB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{bot[0]}"/><stop offset="1" stop-color="{bot[1]}"/></linearGradient>')

    # ---- sizes -------------------------------------------------------------------------
    def size(self, w, h, r=None, fsize=None, backing='#060607'):
        key = (round(w, 1), round(h, 1))
        if key in self.sizes:
            return self.sizes[key]
        sid = f's{len(self.sizes)}'
        r = r if r is not None else max(3, h * 0.07)
        hh = h / 2
        g = self.split / 2
        # clip shapes: top half with rounded top corners, bottom half with rounded bottom corners
        tp = f'M0 {hh-g:.1f}V{r:.1f}Q0 0 {r:.1f} 0H{w-r:.1f}Q{w} 0 {w} {r:.1f}V{hh-g:.1f}Z'
        bp = f'M0 {hh+g:.1f}H{w}V{h-r:.1f}Q{w} {h} {w-r:.1f} {h}H{r:.1f}Q0 {h} 0 {h-r:.1f}Z'
        self.defs.append(f'<clipPath id="{sid}t"><path d="{tp}"/></clipPath><clipPath id="{sid}b"><path d="{bp}"/></clipPath>')
        self.css.append(f'.{sid}t{{transform-origin:0 {hh:.1f}px}}.{sid}b{{transform-origin:0 {hh:.1f}px}}')
        self.sizes[key] = {'id': sid, 'w': w, 'h': h, 'r': r, 'fsize': fsize or h * 0.62, 'backing': backing}
        return self.sizes[key]

    # ---- faces -------------------------------------------------------------------------
    def glyph(self, ch, font=None):
        font = font or self.font
        key = ('g', font, ch)
        gid = self.ids.get(key)
        if gid is None:
            gid = self.ids[key] = f'g{len(self.ids)}'
            adv, d = G.glyph_path(ch, font)
            self.defs.append(f'<path id="{gid}" d="{d}"/>')
        return gid

    def face_char(self, S, ch, color=None, font=None):
        font = font or self.font
        color = color or self.ink
        key = ('f', S['id'], ch, color, font)
        fid = self.ids.get(key)
        if fid is not None:
            return fid
        fid = self.ids[key] = f'f{len(self.ids)}'
        w, h = S['w'], S['h']
        content = ''
        if ch != ' ':
            gid = self.glyph(ch, font)
            upm, cap, _ = G.metrics(font)
            s = S['fsize'] / upm
            adv, _ = G.glyph_path(ch, font)
            x = (w - adv * s) / 2
            y = h / 2 + cap * s / 2
            content = f'<use href="#{gid}" transform="translate({x:.1f} {y:.1f}) scale({s:.4f})" fill="{color}"/>'
        self._face(fid, S, content)
        return fid

    def face_custom(self, S, fid, content):
        if fid not in self.have:
            self.have.add(fid)
            self._face(fid, S, content)
        return fid

    def _face(self, fid, S, content):
        sid, w, h = S['id'], S['w'], S['h']
        if len(content) > 120:
            self.defs.append(f'<g id="{fid}c">{content}</g>')
            content = f'<use href="#{fid}c"/>'
        self.defs.append(
            f'<g id="{fid}T" clip-path="url(#{sid}t)"><rect width="{w}" height="{h}" fill="url(#fT)"/>{content}</g>'
            f'<g id="{fid}B" clip-path="url(#{sid}b)"><rect width="{w}" height="{h}" fill="url(#fB)"/>{content}</g>')

    # ---- sequences ---------------------------------------------------------------------
    def flip(self, S, x, y, faces, times, d=0.13):
        """faces: list of face ids; times[i] = moment the flip from faces[i] to faces[i+1] starts.
        Halves that are covered are hidden too, so no anti-aliased sliver of a hidden glyph shows at the split."""
        sid = S['id']
        n = len(faces) - 1
        out = [f'<g transform="translate({x:.1f} {y:.1f})"><rect width="{S["w"]}" height="{S["h"]}" rx="{S["r"]:.1f}" fill="{S["backing"]}"/>']

        def use(fid, cls, delays):
            st = f' style="animation-delay:{", ".join(f"{v:.2f}s" for v in delays)}"' if delays else ''
            c = f' class="{cls}"' if cls else ''
            return f'<use href="#{fid}"{c}{st}/>'
        for i in range(n, -1, -1):
            T = faces[i] + 'T'
            if n == 0:
                out.append(use(T, '', []))
            elif i == n:
                out.append(use(T, 's', [times[n - 1]]))
            elif i == 0:
                out.append(use(T, f't {sid}t x', [times[0]]))
            else:
                out.append(use(T, f'ts {sid}t x', [times[i - 1], times[i]]))
        for i in range(0, n + 1):
            Bf = faces[i] + 'B'
            if n == 0:
                out.append(use(Bf, '', []))
            elif i == 0:
                out.append(use(Bf, 'h x', [times[0] + d]))
            elif i == n:
                out.append(use(Bf, f'b {sid}b', [times[n - 1] + d / 2]))
            else:
                out.append(use(Bf, f'bh {sid}b x', [times[i - 1] + d / 2, times[i] + d]))
        out.append('</g>')
        return ''.join(out)

    def word(self, S, x, y, target, start, rng, spins=2, color=None, alphabet='ABCDEFGHIJKLMNOPRSTUVWXYZ0123456789', interval=0.06, stagger=0.03):
        """A row of character tiles that already read `target` at frame 0 (so a frozen or first-frame
        render is complete), then scramble through random characters and settle back on `target`."""
        out = []
        w = S['w']
        gap = S.get('gap', w * 0.1)
        for j, ch in enumerate(target):
            seq = [ch]
            k = rng.randint(spins, spins + 1) if ch != ' ' else 0
            for _ in range(k):
                seq.append(rng.choice(alphabet))
            seq.append(ch)
            # drop consecutive duplicates
            clean = [seq[0]]
            for c in seq[1:]:
                if c != clean[-1]:
                    clean.append(c)
            faces = [self.face_char(S, c, color) for c in clean]
            t0 = start + j * stagger + rng.uniform(0, 0.04)
            times = [t0 + i * interval for i in range(len(faces) - 1)]
            out.append(self.flip(S, x + j * (w + gap), y, faces, times))
        return ''.join(out)

    def style(self):
        return ('.t{animation:ft .065s ease-in both}.b{animation:fb .075s ease-out both}'
                '.ts{animation:sh 1ms linear backwards,ft .065s ease-in both}.s{animation:sh 1ms linear backwards}'
                '.bh{animation:fb .075s ease-out both,hd 1ms linear forwards}.h{animation:hd 1ms linear forwards}'
                '@keyframes sh{from{opacity:0}to{opacity:0}}@keyframes hd{from{opacity:0}to{opacity:0}}'
                '@keyframes ft{0%{transform:scaleY(1)}96%{transform:scaleY(.04);opacity:1}100%{transform:scaleY(0);opacity:0}}'
                '@keyframes fb{0%{transform:scaleY(0);opacity:0}4%{opacity:1}100%{transform:scaleY(1);opacity:1}}'
                + ''.join(self.css) +
                '@media (prefers-reduced-motion:reduce){.t,.b,.ts,.s,.bh,.h{animation:none!important}.x{display:none}}')

    def defs_svg(self):
        return '<defs>' + ''.join(self.defs) + '</defs>'


def tiles_width(n, w, gap):
    return n * w + (n - 1) * gap


def word_multi(B, S, x, y, phrases, starts, rng, spins=3, alphabet='ABCDEFGHIJKLMNOPRSTUVWXYZ0123456789', interval=0.06):
    """Tiles that read phrases[0] at frame 0, scramble and settle on it at starts[0], then flip to each next phrase.
    Characters that stay the same between phrases do not move, like a real board."""
    n = max(len(p) for p in phrases)
    phrases = [p.ljust(n) for p in phrases]
    w = S['w']
    gap = S.get('gap', w * 0.1)
    out = []
    for j in range(n):
        seq, times = [phrases[0][j]], []
        t = starts[0] + j * 0.02 + rng.uniform(0, 0.04)
        for _ in range(rng.randint(spins, spins + 1) if phrases[0][j] != ' ' else 0):
            seq.append(rng.choice(alphabet)); times.append(t); t += interval
        seq.append(phrases[0][j]); times.append(t)
        for k in range(1, len(phrases)):
            if phrases[k][j] == seq[-1]:
                continue
            t = starts[k] + j * 0.03 + rng.uniform(0, 0.04)
            seq.append(rng.choice(alphabet)); times.append(t); t += interval
            seq.append(phrases[k][j]); times.append(t)
        clean, ctimes = [seq[0]], []
        for c, tt in zip(seq[1:], times):
            if c != clean[-1]:
                clean.append(c); ctimes.append(tt)
        faces = [B.face_char(S, c) for c in clean]
        out.append(B.flip(S, x + j * (w + gap), y, faces, ctimes))
    return ''.join(out)
